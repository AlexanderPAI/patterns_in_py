from domain.model import Product

import abc


class AbstractProductRepository(abc.ABC):
    """Самый простой из возможных абстрактных репозиториев"""

    @abc.abstractmethod
    def add(self, product: Product):
        raise NotImplementedError()

    @abc.abstractmethod
    def get(self, sku: str) -> Product:
        raise NotImplementedError()


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference: str):
        return self.session.query(Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(Batch).all()

