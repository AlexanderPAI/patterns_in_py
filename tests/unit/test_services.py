import pytest
from datetime import date, timedelta

from domain import model
from service_layer import services, unit_of_work
from adapters.repository import AbstractRepository


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


class FakeRepository(AbstractRepository):

    def __init__(self, batches):
        self._batches = batches

    @staticmethod
    def for_batch(ref, sku, qty, eta):
        return FakeRepository([model.Batch(ref, sku, qty, eta)])

    def add(self, batch):
        self._batches.append(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):

    def __init__(self):
        self._batches = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch():
    uow = FakeUnitOfWork()
    services.add_batch('b1', 'CRUNCHY-ARMCHAIR', 100, None, uow)
    assert uow.batches.get('b1') is not None
    assert uow.committed


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch('batch1', 'COMPLICATED-LAMP', 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == 'batch1'

#todo
def test_allocate_errors_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)
    with pytest.raises(services.InvalidSku, match="Недопустимый артикул NONEXISTENTSKU"):
        services.allocate("b1", "NONEXISTENTSKU", 10, repo, session)

#todo
def test_commits():
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate("o1", "OMINOUS-MIRROR", 10, repo, session)
    assert session.commited is True


def test_prefers_warehouse_batches_to_shipment():
    in_stock_batch = model.Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = model.Batch("shipment-batch", "RETRO-CLOCK", 100, eta=None)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()
    line = model.OrderLine("oref", "RETRO-CLOCK", 10)
    services.allocate("oref", "RETRO-CLOCK", 10 , repo, session)
    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


