import time
from email import policy
from email.parser import BytesParser

import pytest
import requests
from sqlalchemy.orm import clear_mappers

from src.allocation import bootstrap, config
from src.allocation.adapters import notifications
from src.allocation.domain import commands
from src.allocation.service_layer import unit_of_work
from tests.random_refs import random_sku


def parse_mailhog_message(email: dict):
    raw_data = email["Raw"]["Data"]
    raw_bytes = raw_data.encode("latin-1")
    return BytesParser(policy=policy.default).parsebytes(raw_bytes)


def get_email_from_mailhog(sku: str) -> dict:
    host, http_port = map(
        config.get_email_host_and_port().get,
        ["host", "http_port"],
    )
    url = f"http://{host}:{http_port}/api/v2/messages"

    deadline = time.monotonic() + 5
    last_emails = []

    while time.monotonic() < deadline:
        response = requests.get(url, timeout=2)
        response.raise_for_status()

        last_emails = response.json()["items"]

        for email in last_emails:
            raw_data = email.get("Raw", {}).get("Data", "")
            if sku in raw_data:
                return email

        time.sleep(0.1)

    raise AssertionError(
        f"MailHog не получил письмо для sku={sku!r}; "
        f"писем в очереди: {len(last_emails)}"
    )


@pytest.fixture
def bus(sqlite_session_factory):
    messagebus = bootstrap.bootstrap(
        start_orm=True,
        uow=unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory),
        notifications=notifications.EmailNotifications(),
        publish=lambda *args: None,
    )

    yield messagebus
    clear_mappers()


def test_out_of_stock_email(bus):
    sku = random_sku()

    bus.handle(commands.CreateBatch("batch1", sku, 9, None))
    bus.handle(commands.Allocate("order1", sku, 10))

    email = get_email_from_mailhog(sku)
    message = parse_mailhog_message(email)

    assert message["From"] == "allocations@example.com"
    assert message["To"] == "stock@made.com"
    assert message["Subject"] == "allocation service notification"
    assert message.get_content() == f"Артикула {sku} нет в наличии"
