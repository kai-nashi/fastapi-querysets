import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from tortoise.queryset import QuerySet

from fastapi_querysets.queryset import RouterQuerySet
from tests.app_models.pydantic import WorkerModelOut
from tests.app_models.tortoise_orm import Worker

app = FastAPI()


class WorkersRouterQuerySet(RouterQuerySet):
    model = Worker


@app.get("/")
async def app_test_list(queryset: QuerySet[Worker] = WorkersRouterQuerySet()) -> dict:
    return await WorkerModelOut.from_queryset(queryset)


@app.get("/{instance_pk}")
async def app_test_retrieve(queryset: QuerySet[Worker] = WorkersRouterQuerySet().instance) -> dict:
    return await WorkerModelOut.from_tortoise_orm(queryset)


client = AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
@pytest.mark.usefixtures("db_clean", "db_create_workers")
async def test_get_workers_list__request__list_of_workers(mocker):
    spy_from_queryset = mocker.spy(WorkerModelOut, "from_queryset")

    expected_sql = Worker.all().sql()
    expected_data = sorted(await Worker.all().values("id", "contract_id", "name"), key=lambda d: d["id"])

    response = await client.get("/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()
    assert sorted(response.json(), key=lambda d: d["id"]) == expected_data

    queryset, *_ = spy_from_queryset.call_args[0]
    assert queryset.sql() == expected_sql


@pytest.mark.asyncio
@pytest.mark.usefixtures("db_clean")
async def test_get_workers_list__db_is_clean__list_is_empty(mocker):
    spy_from_queryset = mocker.spy(WorkerModelOut, "from_queryset")

    expected_sql = Worker.all().sql()

    response = await client.get("/")

    assert response.status_code == 200
    assert not response.json()
    assert isinstance(response.json(), list)

    queryset, *_ = spy_from_queryset.call_args[0]
    assert queryset.sql() == expected_sql


@pytest.mark.asyncio
@pytest.mark.usefixtures("db_clean", "db_create_workers")
async def test_get_workers_instance__request__worker(mocker):
    spy_from_tortoise_orm = mocker.spy(WorkerModelOut, "from_tortoise_orm")

    expected_worker = await Worker.all().first()
    expected_data = {"id": expected_worker.id, "contract_id": None, "name": expected_worker.name}

    response = await client.get(f"/{expected_worker.id}")

    assert response.status_code == 200
    assert response.json() == expected_data

    instance, *_ = spy_from_tortoise_orm.call_args[0]
    assert instance == expected_worker


@pytest.mark.asyncio
@pytest.mark.usefixtures("db_clean")
async def test_get_workers_instance__not_exists__error_not_found(mocker):
    spy_from_tortoise_orm = mocker.spy(WorkerModelOut, "from_tortoise_orm")

    response = await client.get("/1")

    assert response.status_code == 404

    error = response.json()
    assert "detail" in error
    assert error["detail"][0]["loc"] == ["path", "instance_pk"]
    assert error["detail"][0]["msg"] == "Instance not found"
    assert error["detail"][0]["type"] == "value_error"

    assert not spy_from_tortoise_orm.called
