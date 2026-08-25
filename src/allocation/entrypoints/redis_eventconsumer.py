import json
import logging

import redis

from src.allocation import bootstrap, config
from src.allocation.domain import commands


r = redis.Redis(**config.get_redis_host_and_port())


def main():
    bus = bootstrap.bootstrap()

    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")

    for message in pubsub.listen():
        handle_change_batch_quantity(message, bus)


def handle_change_batch_quantity(message, bus):
    logging.debug("handling %s", message)

    data = json.loads(message["data"])
    command = commands.ChangeBatchQuantity(
        ref=data["batchref"],
        qty=data["qty"],
    )
    bus.handle(command)


if __name__ == "__main__":
    main()
