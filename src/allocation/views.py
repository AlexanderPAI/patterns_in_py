from src.allocation.service_layer import unit_of_work

from src.allocation.adapters import redis_eventpublisher


def allocations(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    batches = redis_eventpublisher.get_readmodel(orderid)
    return [
        {'batchref': b.decode(), 'sku': s.decode()}
        for s, b in batches.items()
    ]
