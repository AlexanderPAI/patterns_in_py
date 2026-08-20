from src.allocation.domain.model import Product

import abc


class AbstractRepository(abc.ABC):
    """Самый простой из возможных абстрактных репозиториев"""

    def __init__(self):
        self.seen = set()

    def add(self, product: Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku):
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: Product):
        raise NotImplementedError()

    @abc.abstractmethod
    def _get(self, sku: str) -> Product:
        raise NotImplementedError()


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, batch):
        self.session.add(batch)

    def _get(self, sku):
        return self.session.query(Product).filter_by(sku=sku).first()

    def list(self):
        return self.session.query(Product).all()

