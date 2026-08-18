from datetime import date
from typing import Optional

from domain import model
from adapters.repository import AbstractRepository
from domain.model import OrderLine
from service_layer import unit_of_work

class InvalidSku(Exception):
    pass


class InvalidOrder(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date], uow: unit_of_work.AbstractUnitOfWork
) -> None:
    with uow:
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow: # 1 Запускаем контекстный менеджер
        batches = uow.batches.list() # 2 uow.batches - это репозиторий партий товара
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Недопустимый артикул {line.sku}")
        batchref = model.allocate(line, batches)
        uow.commit() # 3 в конце делаем коммит или откат
    return batchref
