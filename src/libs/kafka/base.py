import asyncio
import json
import logging
import sys
from os import getenv
from threading import Thread

import confluent_kafka
import numpy
from confluent_kafka import KafkaException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from .core import kafka_base_loop
from ..ml.base import generate_embedding
from ..utils import is_valid_uuid

sys.path.append("...")
from models.main import Product


log = logging.getLogger(__name__)


class AIOProducer:
    def __init__(self, configs, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._producer = confluent_kafka.Producer(configs)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._poll_thread.start()

    def _poll_loop(self):
        while not self._cancelled:
            self._producer.poll(0.1)

    def close(self):
        self._cancelled = True
        self._poll_thread.join()

    def produce(self, topic, value):
        result = self._loop.create_future()

        def ack(err, msg):
            if err:
                self._loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
            else:
                self._loop.call_soon_threadsafe(result.set_result, msg)
        self._producer.produce(topic, value, on_delivery=ack)
        return result


class KafkaConsumers:
    pg_session_async = None

    def __init__(self, postgres_uri: str, kafka_config: dict):
        engine = create_async_engine(postgres_uri)
        self.pg_session_async = async_sessionmaker(engine, expire_on_commit=False)

        self.aio_producer = AIOProducer(kafka_config)

    async def product_add(self, message: dict):
        assert message.get('uuid'), "'uuid' field is required"
        assert is_valid_uuid(message.get('uuid')), "Product UUID is not valid"
        assert message.get('content'), "Content field is required and shouldn't be empty"

        embedding = generate_embedding(message.get('content'))
        print(embedding)

        async with self.pg_session_async() as session:
            async with session.begin():
                product_obj = Product(
                    external_uuid=message.get('uuid'),
                    content=message.get('content'),
                    embedding=embedding
                )
                session.add(product_obj)
                await session.flush()

                log.info(f"Product added to database with id: {product_obj.id}")

    async def product_search(self, message: dict):
        assert message.get('request_id'), "'request_id' field is required"
        assert message.get('products'), "'products' field is required"
        assert isinstance(message['products'], list), "'products' field should contain list of UUIDs"

        # Prevent application from precessing our own messages
        if message.get('response', False):
            return

        async with self.pg_session_async() as session:
            stmt = select(Product).filter(Product.external_uuid.in_(message['products']))

            result = await session.execute(stmt)
            embeddings_list = []
            for product in result.scalars():
                embeddings_list.append(product.embedding)

            # Converting numpy objects to native floats
            average_embedding = [
                float(value) for value in numpy.mean(embeddings_list, axis=0)
            ]

            sql = text(
                "SELECT external_uuid, 1 - (embedding <=> :avg_embedding) AS cosine_similarity FROM products "
                "ORDER BY cosine_similarity DESC LIMIT 100"
            )
            result = await session.execute(sql, {"avg_embedding": json.dumps(average_embedding)})
            response = {
                "request_id": message.get('request_id'),
                "response": True,
                "products": []
            }

            for product in result.scalars():
                response['products'].append(str(product))

            await self.aio_producer.produce('product-search', json.dumps(response))

async def kafka_main_loop() -> None:
    kafka_config = {
        "group.id": "wisher",
        "bootstrap.servers": f"{getenv('KAFKA_HOST')}:{getenv('KAFKA_PORT')}",
    }

    kafka_consumers = KafkaConsumers(
        f"postgresql+asyncpg://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}/{getenv('DB_DATABASE')}",
        kafka_config
    )

    await asyncio.gather(
        kafka_base_loop(kafka_config, 'product-add', kafka_consumers.product_add),
        kafka_base_loop(kafka_config, 'product-search', kafka_consumers.product_search),
    )
