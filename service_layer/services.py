from domain import model
from adapters.repository import AbstractRepository


class InvalidSku(Exception):
    pass


class InvalidOrder(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: model.OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Недопустимый артикул {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref


def deallocate(orderid: str, sku: str, repo: AbstractRepository, session) -> None:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Недопустимый артикул {sku}")

    for batch in batches:
        for line in batch.allocations:
            if line.orderid == orderid and line.sku == sku:
                batch.deallocate(line)
                session.commit()
                return
    raise InvalidOrder(f"Заказ {orderid} не аллоцирован")
