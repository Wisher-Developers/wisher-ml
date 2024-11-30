import asyncio
import functools
import json
import logging
from collections.abc import Callable

import confluent_kafka


async def kafka_base_loop(config: dict, topic_name: str, processor: Callable) -> None:
    log = logging.getLogger(__name__)

    consumer = confluent_kafka.Consumer(config)
    consumer.subscribe([topic_name])
    loop = asyncio.get_running_loop()
    poll = functools.partial(consumer.poll, 0.1)
    try:
        log.info(f"Starting consumer: {topic_name}")
        while True:
            message = await loop.run_in_executor(None, poll)
            if message is None:
                continue
            if message.error():
                log.error(f"Consumer error: {message.error()}")
                continue

            try:
                message_decoded = json.loads(message.value())
            except json.decoder.JSONDecodeError:
                log.error(
                    f"Consumer error ({topic_name}): Incorrect message received. Valid JSON expected!\n"
                    f"{message.value()}"
                )
                continue

            log.info(f"Consuming message: {message.value()}")
            try:
                await processor(message_decoded)
            except Exception as e:
                log.error(e, exc_info=True)
    finally:
        log.info(f"Closing consumer: {topic_name}")
        consumer.close()
