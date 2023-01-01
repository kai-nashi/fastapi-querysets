import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from tortoise.queryset import QuerySet

from fastapi_querysets.mixins.ordering import OrderingMixin
from fastapi_querysets.queryset import RouterQuerySet
from tests.app_models.pydantic import WorkerModelOut
from tests.app_models.tortoise_orm import Worker


app = FastAPI()


class WorkersRouterQuerySet(OrderingMixin, RouterQuerySet):
    ordering_fields = ("id", "name", "custom_field")
    model = Worker

    def order_by_custom_field(self, queryset: QuerySet[Worker], desc: bool = False) -> QuerySet[Worker]:
        prefix = "-" if desc else ""
        return queryset.order_by(f"{prefix}contract_id")


@app.get("/")
async def app_test(queryset: QuerySet[Worker] = WorkersRouterQuerySet()) -> dict:
    return await WorkerModelOut.from_queryset(queryset)


client = AsyncClient(app=app, base_url="http://test")


@pytest.mark.usefixtures("db_fill")
async def test_ordering_mixin__no_ordering_query__queryset_not_ordered(mocker):
    spy_from_queryset = mocker.spy(WorkerModelOut, "from_queryset")

    workers_ids = await Worker.all().values_list("id", flat=True)
    assert workers_ids

    response = await client.get("/")

    assert response.status_code == 200
    assert sorted([worker["id"] for worker in response.json()]) == workers_ids

    queryset, *_ = spy_from_queryset.call_args[0]
    assert "ORDER BY" not in queryset.sql()


@pytest.mark.parametrize(
    "ordering",
    [
        ("id",),
        ("-id",),
        ("id", "name"),
        ("id", "-name"),
        ("-id", "name"),
        ("-id", "-name"),
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_ordering_mixin__ordering__ordered(ordering):
    workers_ids = await Worker.all().order_by(*ordering).values_list("id", flat=True)
    assert workers_ids

    response = await client.get("/", params={"ordering[]": ordering})

    assert response.status_code == 200
    assert [worker["id"] for worker in response.json()] == workers_ids


@pytest.mark.parametrize(
    "desc",
    [True, False],
)
@pytest.mark.usefixtures("db_fill")
async def test_ordering_mixin__ordering_custom_field__ordered(desc):
    workers_ids = await Worker.all().order_by("-contract_id" if desc else "contract_id").values_list("id", flat=True)
    assert workers_ids

    response = await client.get("/", params={"ordering[]": "-custom_field" if desc else "custom_field"})

    assert response.status_code == 200
    assert [worker["id"] for worker in response.json()] == workers_ids


@pytest.mark.usefixtures("db_fill")
async def test_ordering_mixin__ordering_field_not_allowed__error():
    response = await client.get("/", params={"ordering[]": ["contract"]})

    assert response.status_code == 422

    error = response.json()["detail"][0]
    assert error["loc"] == ["query", "ordering[]", 0]
    assert error["msg"] == "Invalid value"
    assert error["type"] == "value_error"
