import asyncio
import logging
import signal
import sys
from os import getenv

import sqlalchemy as pg_db
from pymilvus import connections, db as milvus_db
from sqlalchemy.orm import Session

from libs.kafka.base import kafka_main_loop
from models import Product

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *args: sys.exit())
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    print('Testing available connection...')

    # MILVUS
    conn = connections.connect(host=getenv('MILVUS_HOST'), port=getenv('MILVUS_PORT'))
    print(f'[Milvus] DBs available: {milvus_db.list_database()}')

    # POSTGRES
    engine = pg_db.create_engine(f"postgresql://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}/{getenv('DB_DATABASE')}")
    with Session(engine) as session:
        rows_count = session.query(Product).count()

    print(f"[Postgres] Rows in \"products\" table: {rows_count}")

    # Kafka
    try:
        asyncio.run(
            kafka_main_loop()
        )
    except (KeyboardInterrupt, SystemExit):
        log.info("Application shutdown complete")
