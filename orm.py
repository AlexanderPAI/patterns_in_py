from sqlalchemy import Table, Column, Integer, String

from sqlalchemy.orm import mapper, relationship
from sqlalchemy.sql.schema import MetaData

from model import  OrderLine

metadata = MetaData()

order_lines = Table(
    "order_lines", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

...

def start_mappers():
    lines_mapper = mapper(OrderLine, order_lines)
