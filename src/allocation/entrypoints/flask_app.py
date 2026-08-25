from datetime import datetime

from flask import Flask, jsonify, request

from src.allocation.service_layer import unit_of_work, messagebus
from src.allocation.adapters import orm
from src.allocation.service_layer import handlers
from src.allocation.domain import events, commands
from src.allocation.service_layer.unit_of_work import SqlAlchemyUnitOfWork
from src.allocation import bootstrap, views

app = Flask(__name__)

bus = bootstrap.bootstrap()


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route('/add_batch', methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    command = commands.CreateBatch(
        request.json['ref'],
        request.json['sku'],
        request.json['qty'],
        eta,
    )
    bus.handle(command)
    return "OK", 201

@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        cmd = commands.Allocate(
            request.json["orderid"], request.json["sku"], request.json["qty"]
        )
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        messagebus.handle(cmd, uow)
    except handlers.InvalidSku as e:
        return {"message": str(e)}, 400

    return "OK", 202


@app.route('/allocations/<orderid>', methods=['GET'])
def allocations_view_endpoint(orderid):
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    result = views.allocations(orderid, uow)
    if not result:
        return 'not found', 404
    return jsonify(result), 200
