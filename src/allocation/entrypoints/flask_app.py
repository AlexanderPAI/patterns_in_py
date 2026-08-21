from datetime import datetime

from flask import Flask, jsonify, request

from src.allocation.service_layer import unit_of_work, messagebus
from src.allocation.domain import model
from src.allocation.adapters import orm
from src.allocation.service_layer import handlers
from src.allocation.domain import events
from src.allocation.service_layer.unit_of_work import SqlAlchemyUnitOfWork

app = Flask(__name__)
orm.start_mappers()


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route('/add_batch', methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    event = events.BatchCreated(
        request.json['ref'],
        request.json['sku'],
        request.json['qty'],
        eta,
    )
    handlers.add_batch(event, SqlAlchemyUnitOfWork())
    return "OK", 201

@app.route('/allocate', methods=['POST'])
def allocate_endpoint():
    try:
        event = events.AllocationRequired(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty'],
        )
        results = messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
        batchref = results.pop(0)
    except handlers.InvalidSku as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batchref': batchref}), 201
