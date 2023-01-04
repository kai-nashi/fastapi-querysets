import dataclasses
import datetime
from typing import Optional

import pytest
from fastapi import FastAPI
from fastapi import Query
from httpx import AsyncClient
from tortoise.queryset import QuerySet

from fastapi_querysets.mixins.filters import FilterMixin
from fastapi_querysets.mixins.filters import FilterNegationMixin
from fastapi_querysets.mixins.ordering import OrderingMixin
from fastapi_querysets.mixins.pagination import PaginationMixin
from fastapi_querysets.mixins.pagination import RouterPagination
from fastapi_querysets.queryset import RouterQuerySet
from tests.app_models.pydantic import TaskModelOut
from tests.app_models.tortoise_orm import Task


@dataclasses.dataclass
class RouterQuerySetFilter:
    id: Optional[int] = Query(None)
    created_at__gte: Optional[datetime.datetime] = Query(None)
    project_id: Optional[int] = Query(None, alias="project")  # way to create join
    project__name: Optional[str] = Query(None)
    workers__id: Optional[int] = Query(None)


class TestRouterPagination(RouterPagination):
    per_page = 25
    per_page_max = 50


class TasksRouterQuerySet(FilterMixin, FilterNegationMixin, OrderingMixin, PaginationMixin, RouterQuerySet):
    filter_class = RouterQuerySetFilter
    ordering_default = "id"
    ordering_fields = (
        "id",
        "cost",
        "created_at",
        "description",
        "project_id",
        "project__id",
        "workers_required_max",
        "workers_required_min",
    )
    pagination_class = TestRouterPagination
    model = Task


app = FastAPI()


@app.get("/")
async def app_test(queryset: QuerySet[Task] = TasksRouterQuerySet().paginated) -> dict:
    return await TaskModelOut.from_queryset(queryset)


client = AsyncClient(app=app, base_url="http://test")


@pytest.mark.parametrize(
    "page,per_page",
    [
        (None, None),
        (1, None),
        (None, 5),
        (None, 25),
        (None, 50),
        (None, 55),
        (2, 4),
        (3, 4),
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_utility_endpoint__filter_and_exclude__filtered_queryset(page, per_page):
    project_id = 1
    created_at__gte = datetime.datetime.now() + datetime.timedelta(days=5)
    per_page_expected = min(TestRouterPagination.per_page_max, per_page or TestRouterPagination.per_page)

    tasks_ids = (
        await Task.all()
        .filter(project_id=project_id)
        .exclude(created_at__gte=created_at__gte)
        .order_by("id")
        .offset(((page or 1) - 1) * per_page_expected)
        .limit(per_page_expected)
        .values_list("id", flat=True)
    )

    assert tasks_ids

    params = {
        "project": 1,
        "created_at__gte!": datetime.datetime.now() + datetime.timedelta(days=5),
        "page": page,
        "per_page": per_page,
    }

    response = await client.get("/", params={k: v for k, v in params.items() if v})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == tasks_ids


@pytest.mark.parametrize(
    "page,per_page",
    [
        (None, None),
        (1, None),
        (None, 5),
        (None, 25),
        (None, 50),
        (None, 55),
        (2, None),
        (2, 5),
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_utility_endpoint__filtering_by_related__correct_pagination(page, per_page):
    per_page_expected = min(TestRouterPagination.per_page_max, per_page or TestRouterPagination.per_page)

    tasks_ids = (
        await Task.all()
        .distinct()
        .filter(workers__id=2)
        .order_by("id")
        .offset(((page or 1) - 1) * per_page_expected)
        .limit(per_page_expected)
        .values_list("id", flat=True)
    )

    assert tasks_ids

    params = {"workers__id": 2, "page": page, "per_page": per_page}
    response = await client.get("/", params={k: v for k, v in params.items() if v})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == tasks_ids


@pytest.mark.parametrize(
    "page,per_page,ordering",
    [
        (None, None, ("id",)),
        (None, None, ("project__id",)),
        (None, None, ("project__id", "id")),
        (2, None, ("project__id", "id")),
        (2, 25, ("project__id", "id")),
        (2, 30, ("project__id", "id")),
        (3, 10, ("project__id", "id")),
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_utility_endpoint__change_ordering__correct_pagination(page, per_page, ordering):
    per_page_expected = min(TestRouterPagination.per_page_max, per_page or TestRouterPagination.per_page)

    tasks_ids = (
        await Task.all()
        .distinct()
        .filter(workers__id=2)
        .order_by(*ordering)
        .offset(((page or 1) - 1) * per_page_expected)
        .limit(per_page_expected)
        .values_list("id", flat=True)
    )

    assert tasks_ids

    params = {"ordering[]": ordering, "workers__id": 2, "page": page, "per_page": per_page}
    response = await client.get("/", params={k: v for k, v in params.items() if v})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == tasks_ids


@pytest.mark.usefixtures("db_fill")
async def test_utility_endpoint__page_out_of_total__empty():
    response = await client.get("/", params={"page": 5, "per_page": 25})

    assert response.status_code == 200
    assert not response.json()

    assert response.headers["x-page"] == "5"
    assert response.headers["x-pages"] == "4"
    assert response.headers["x-per-page"] == "25"
    assert response.headers["x-total"] == "100"


@pytest.mark.usefixtures("db_fill")
async def test_utility_endpoint__filter_not_exist__default_queryset():
    tasks_ids = (
        await TasksRouterQuerySet().get_queryset().limit(TestRouterPagination.per_page).values_list("id", flat=True)
    )

    response = await client.get("/", params={"filter_not_exist": 5})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == tasks_ids


@pytest.mark.usefixtures("db_fill")
async def test_utility_endpoint__ordering_field_not_allowed__default_queryset():
    response = await client.get("/", params={"ordering[]": ["id", "ordering_field_not_allowed"]})

    assert response.status_code == 422

    error = response.json()["detail"][0]
    assert error["loc"] == ["query", "ordering[]", 1]
    assert error["msg"] == "Invalid value"
    assert error["type"] == "value_error"
