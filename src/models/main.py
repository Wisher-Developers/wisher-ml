from sqlalchemy import Text, Column, BigInteger, UUID
from pgvector.sqlalchemy import Vector

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = 'products'

    id = Column(BigInteger, primary_key=True)
    external_uuid = Column(UUID(), index=True, nullable=False)
    content = Column(Text())
    embedding = Column(Vector(768))
