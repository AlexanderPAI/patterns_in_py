from datetime import datetime

from flask import Flask, jsonify, request

from service_layer import unit_of_work
from domain import model
from adapters import orm
from service_layer import services

app = Flask(__name__)
orm.start_mappers()


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route('/add_batch', methods=['POST'])
def add_batch():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    services.add_batch(
        request.json['ref'],
        request.json['sku'],
        request.json['qty'],
        eta,
        uow,
    )
    return "OK", 201

@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        batchref = services.allocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty'],
            uow,
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batchref': batchref}), 201
