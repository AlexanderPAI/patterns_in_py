from sqlalchemy import text

from model import OrderLine


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        text(
            """
            INSERT INTO order_lines (orderid, sku, qty)
            VALUES
                (:orderid1, :sku1, :qty1),
                (:orderid2, :sku2, :qty2),
                (:orderid3, :sku3, :qty3)
            """
        ),
        {
            "orderid1": "order1",
            "sku1": "RED-CHAIR",
            "qty1": 12,
            "orderid2": "order1",
            "sku2": "RED-TABLE",
            "qty2": 13,
            "orderid3": "order2",
            "sku3": "BLUE-LIPSTICK",
            "qty3": 14,
        },
    )

    expected = [
        OrderLine("order1", "RED-CHAIR", 12),
        OrderLine("order1", "RED-TABLE", 13),
        OrderLine("order2", "BLUE-LIPSTICK", 14),
    ]

    assert session.query(OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session):
    new_line = OrderLine("order1", "DECORATIVE-WIDGET", 12)

    session.add(new_line)
    session.commit()

    rows = list(
        session.execute(
            text('SELECT orderid, sku, qty FROM "order_lines"')
        )
    )

    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]