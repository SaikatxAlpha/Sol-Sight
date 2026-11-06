import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.db import mongo
from app.main import app


@pytest.fixture
async def client():
    for c in (mongo.panels_collection, mongo.inspections_collection):
        await c.delete_many({})
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def make_panel(client, panel_id="PNL-001"):
    r = await client.post("/panels", json={
        "panel_id": panel_id, "location": "Rooftop A",
        "installation_date": "2024-01-15", "rated_power": 400,
    })
    assert r.status_code == 201, r.text
    return r.json()


async def inspect(client, panel_id="PNL-001", v=33.0, i=10.8, t=45.0, files=None):
    return await client.post("/predict-defect", files=files,
                             data={"panel_id": panel_id, "voltage": v, "current": i, "temperature": t})


async def test_no_login_needed(client):
    assert (await client.get("/panels")).status_code == 200
    assert (await client.get("/auth/login")).status_code == 404


async def test_full_inspection_flow(client):
    await make_panel(client)

    r = await inspect(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "Healthy"
    assert body["analysis_mode"]["defect"] in ("cnn", "rule-based")
    assert [p["day"] for p in body["degradation_forecast"]] == [30, 60, 90]

    r = await inspect(client, v=24.0, i=8.0, t=72.0)
    assert r.json()["status"] != "Healthy"

    panels = (await client.get("/panels")).json()
    assert panels[0]["latest_status"] == r.json()["status"]

    history = (await client.get("/panels/PNL-001/history")).json()
    assert len(history) == 2

    pred = (await client.get("/panels/PNL-001/prediction")).json()
    assert pred["recommendation"]


async def test_duplicate_panel_rejected(client):
    await make_panel(client)
    r = await client.post("/panels", json={
        "panel_id": "PNL-001", "location": "B", "installation_date": "2024-01-15", "rated_power": 400,
    })
    assert r.status_code == 400


async def test_unanalyzed_upload_does_not_break_reads(client):
    await make_panel(client)
    r = await client.post("/upload-inspection",
                          data={"panel_id": "PNL-001", "voltage": 30, "current": 8, "temperature": 40})
    assert r.status_code == 200
    assert (await client.get("/panels")).status_code == 200
    assert (await client.get("/panels/PNL-001")).status_code == 200
    assert (await client.get("/panels/PNL-001/history")).json() == []
    assert (await client.get("/panels/PNL-001/prediction")).status_code == 404


async def test_image_upload(client):
    await make_panel(client)
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (40, 60, 120)).save(buf, format="PNG")
    files = {"image": ("panel.png", buf.getvalue(), "image/png")}
    r = await inspect(client, files=files)
    assert r.status_code == 200, r.text
    assert r.json()["has_image"] is True


async def test_bad_image_is_a_400_not_a_500(client):
    await make_panel(client)
    files = {"image": ("panel.png", b"definitely not a png", "image/png")}
    r = await inspect(client, files=files)
    assert r.status_code == 400


async def test_out_of_range_reading_rejected(client):
    await make_panel(client)
    r = await inspect(client, v=500)
    assert r.status_code == 422


async def test_unknown_panel_is_404(client):
    assert (await client.get("/panels/NOPE")).status_code == 404
    assert (await inspect(client, panel_id="NOPE")).status_code == 404


async def test_delete_panel_removes_inspections(client):
    await make_panel(client)
    await inspect(client)
    r = await client.delete("/panels/PNL-001")
    assert r.status_code == 204
    assert (await client.get("/panels/PNL-001")).status_code == 404
    assert await mongo.inspections_collection.count_documents({"panel_id": "PNL-001"}) == 0


async def test_future_install_date_rejected(client):
    r = await client.post("/panels", json={
        "panel_id": "PNL-9", "location": "X", "installation_date": "2999-01-01", "rated_power": 400,
    })
    assert r.status_code == 422
