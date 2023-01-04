import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from tortoise.expressions import F
from tortoise.queryset import QuerySet

from fastapi_querysets.mixins.ordering import OrderingMixin
from fastapi_querysets.queryset import RouterQuerySet
from tests.app_models.pydantic import ProjectModelOut
from tests.app_models.tortoise_orm import Task


app = FastAPI()


class TasksRouterQuerySet(OrderingMixin, RouterQuerySet):
    ordering_fields = (
        "id",
        "annotated_field",
        "project_id",  # fk
        "project__description",
        "workers_required_min",
        "workers_required_max",
        "workers__id",  # m2m
    )
    model = Task

    def get_queryset(self):
        return Task.all().annotate(annotated_field=F("description"))


@app.get("/")
async def app_test(queryset: QuerySet[Task] = TasksRouterQuerySet()) -> dict:
    return await ProjectModelOut.from_queryset(queryset)


client = AsyncClient(app=app, base_url="http://test")


@pytest.mark.usefixtures("db_fill")
async def test_ordering_mixin__no_ordering_query__queryset_not_ordered(mocker):
    spy_from_queryset = mocker.spy(ProjectModelOut, "from_queryset")

    tasks_ids = await Task.all().values_list("id", flat=True)
    assert tasks_ids

    response = await client.get("/")

    assert response.status_code == 200
    assert sorted([task["id"] for task in response.json()]) == tasks_ids

    queryset, *_ = spy_from_queryset.call_args[0]
    assert "ORDER BY" not in queryset.sql()


@pytest.mark.parametrize(
    "ordering",
    [
        ("id",),
        ("-id",),
        ("workers_required_max", "id"),
        ("-workers_required_max", "id"),
        ("annotated_field",),
        ("-annotated_field",),
        ("workers_required_max", "annotated_field"),
        ("workers_required_max", "-annotated_field"),
        ("project_id",),
        ("-project_id",),
        ("workers__id",),
        ("-workers__id",),
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_ordering_mixin__ordering__ordered(ordering):
    tasks_ids = await TasksRouterQuerySet().get_queryset().order_by(*ordering).values_list("id", flat=True)
    assert tasks_ids

    response = await client.get("/", params={"ordering[]": ordering})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == tasks_ids


@pytest.mark.usefixtures("db_fill")
async def test_ordering_mixin__ordering_field_not_allowed__error():
    response = await client.get("/", params={"ordering[]": ["contract"]})

    assert response.status_code == 422

    error = response.json()["detail"][0]
    assert error["loc"] == ["query", "ordering[]", 0]
    assert error["msg"] == "Invalid value"
    assert error["type"] == "value_error"
