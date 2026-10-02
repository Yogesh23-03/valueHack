"""Analytics tests: stock cover and supplier dependency."""

from __future__ import annotations


def test_stock_cover_days(business):
    from app.engine.analytics import stock_cover

    cover = {row["product_id"]: row for row in stock_cover(business)}
    # fans 36/4 = 9, wiring 54/6 = 9, switches 300/15 = 20.
    assert cover["fans"]["cover_days"] == 9.0
    assert cover["wiring"]["cover_days"] == 9.0
    assert cover["switches"]["cover_days"] == 20.0
    assert cover["fans"]["next_restock_day"] == 8
    assert cover["switches"]["next_restock_day"] is None


def test_supplier_a_supplies_all_fans_and_wiring(business):
    from app.engine.analytics import dependency_shares

    data = dependency_shares(business)
    per_product = {row["product_id"]: row for row in data["products"]}
    assert per_product["fans"]["suppliers"][0]["name"] == "Supplier A"
    assert per_product["fans"]["suppliers"][0]["share_pct"] == 100.0
    assert per_product["wiring"]["suppliers"][0]["name"] == "Supplier A"

    dep = {row["supplier_id"]: row for row in data["supplier_dependency"]}
    assert dep["sup_a"]["concentration"] == "high"
    assert dep["sup_a"]["purchase_value_share_pct"] > 50.0


def test_attention_inputs_are_plain_objects(business):
    from app.engine.analytics import attention_inputs

    items = attention_inputs(business)
    assert items
    for item in items:
        assert set(item.keys()) == {"kind", "entity", "severity", "day", "evidence"}
    assert any(item["kind"] == "supplier_concentration" for item in items)


def test_business_endpoint_has_analytics(client):
    body = client.get("/api/business").json()
    analytics = body["analytics"]
    assert "dependency_shares" in analytics
    assert "stock_cover" in analytics
    assert "attention_inputs" in analytics
    cover = {row["product_id"]: row["cover_days"] for row in analytics["stock_cover"]}
    assert cover == {"fans": 9.0, "wiring": 9.0, "switches": 20.0}
