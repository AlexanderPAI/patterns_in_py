from src.allocation.service_layer import unit_of_work
from src.allocation.adapters.repository import AbstractRepository
from src.allocation.service_layer import messagebus
from src.allocation.domain import events


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


class FakeRepository(AbstractRepository):

    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestAddBatch:

    def test_for_new_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_for_existing_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("b1", "GARISH-RUG", 100, None), uow)
        messagebus.handle(events.BatchCreated("b2", "GARISH-RUG", 99, None), uow)
        assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


class TestAllocate:

    def test_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
        result = messagebus.handle(events.AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow)
        assert result.pop(0) == "batch1"
