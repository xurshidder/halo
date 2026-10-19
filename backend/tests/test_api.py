from halo.bot.links import parse_brand_payload
from halo.models import ShortlistEntry
from tests.factories import make_creator


async def test_brand_creator_brief_flow(api, jobs, session):
    brand = (await api.post("/brands", json={"name": "Nur Cosmetics", "pillars": ["honest reviews"]})).json()
    assert brand["telegram_connected"] is False

    link = (await api.get(f"/brands/{brand['id']}/telegram-link")).json()
    payload = link["url"].split("?start=")[1]
    assert parse_brand_payload(payload) == brand["id"]

    resp = await api.post(
        "/creators",
        json={
            "display_name": "Malika",
            "accounts": [{"platform": "instagram", "handle": "malika.uz"}, {"platform": "youtube", "handle": "@malika"}],
        },
    )
    assert resp.status_code == 201
    creator = resp.json()
    assert {a["platform"] for a in creator["accounts"]} == {"instagram", "youtube"}

    assert (await api.post(f"/creators/{creator['id']}/refresh")).status_code == 202
    assert jobs.jobs[-1] == ("refresh_creator_task", creator["id"])

    brief = (await api.post(f"/brands/{brand['id']}/briefs", json={"title": "Spring launch", "text": "Skincare"})).json()
    assert brief["status"] == "draft"
    assert (await api.post(f"/briefs/{brief['id']}/run")).status_code == 202
    assert jobs.jobs[-1] == ("run_brief_task", brief["id"])
    assert (await api.post(f"/briefs/{brief['id']}/run")).status_code == 409  # already running


async def test_shortlist_entry_update(api, session):
    brand = (await api.post("/brands", json={"name": "Nur"})).json()
    brief = (await api.post(f"/brands/{brand['id']}/briefs", json={"title": "T", "text": "x"})).json()
    creator = await make_creator(session, "Malika", ["skincare"])
    entry = ShortlistEntry(brief_id=brief["id"], creator_id=creator.id, score=88, reasons="video 1 fits")
    session.add(entry)
    await session.commit()

    resp = await api.patch(f"/shortlist/{entry.id}", json={"status": "starred", "outreach_message": "Salom!"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "starred"

    detail = (await api.get(f"/briefs/{brief['id']}")).json()
    assert detail["entries"][0]["creator"]["display_name"] == "Malika"
    assert detail["entries"][0]["outreach_message"] == "Salom!"


async def test_upload_video_queues_analysis(api, jobs, session, sample_video):
    creator = await make_creator(session, "Malika", ["skincare"], videos=0)
    with sample_video.open("rb") as f:
        resp = await api.post(
            f"/creators/{creator.id}/videos", files={"file": ("v.mp4", f, "video/mp4")}, data={"caption": "Salom"}
        )
    assert resp.status_code == 201
    video = resp.json()
    assert video["status"] == "pending"
    assert jobs.jobs[-1] == ("analyze_video_task", video["id"])

    detail = (await api.get(f"/creators/{creator.id}")).json()
    assert [v["id"] for v in detail["videos"]] == [video["id"]]


async def test_creator_filters_and_lookalikes(api, session):
    await make_creator(session, "Malika", ["skincare", "beauty"])
    await make_creator(session, "Dilnoza", ["skincare", "lifestyle"], languages=("uz", "ru"))
    await make_creator(session, "Bobur", ["cars"], languages=("ru",))

    by_tag = (await api.get("/creators", params={"tag": "skincare"})).json()
    assert {c["display_name"] for c in by_tag} == {"Malika", "Dilnoza"}
    by_lang = (await api.get("/creators", params={"language": "ru"})).json()
    assert {c["display_name"] for c in by_lang} == {"Dilnoza", "Bobur"}

    malika = next(c for c in by_tag if c["display_name"] == "Malika")
    similar = (await api.get(f"/creators/{malika['id']}/lookalikes")).json()
    assert [s["creator"]["display_name"] for s in similar] == ["Dilnoza"]

    assert (await api.get("/creators/9999")).status_code == 404
