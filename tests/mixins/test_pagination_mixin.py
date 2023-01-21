import math
from typing import List

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from tortoise.queryset import QuerySet

from fastapi_querysets.mixins.pagination import PaginationMixin
from fastapi_querysets.mixins.pagination import RouterPagination
from fastapi_querysets.queryset import RouterQuerySet
from tests.app_models.pydantic import WorkerModelOut
from tests.app_models.tortoise_orm import Worker

app = FastAPI()


class TestRouterPagination(RouterPagination):
    per_page = 25
    per_page_max = 50


class TasksRouterQuerySet(PaginationMixin, RouterQuerySet):
    pagination_class = TestRouterPagination
    model = Worker

    def get_queryset(self):
        return Worker.all().order_by("id")


@app.get("/")
async def app_test(queryset: QuerySet[Worker] = TasksRouterQuerySet().paginated) -> List[WorkerModelOut]:
    return await WorkerModelOut.from_queryset(queryset)


client = AsyncClient(app=app, base_url="http://test")


@pytest.mark.usefixtures("db_clean")
async def test_pagination_mixin__db_is_clean__headers_is_zeros():
    response = await client.get("/")

    assert response.status_code == 200
    assert not response.json()
    assert response.headers["x-page"] == "1"
    assert response.headers["x-pages"] == "0"
    assert response.headers["x-per-page"] == str(TestRouterPagination.per_page)
    assert response.headers["x-total"] == "0"


@pytest.mark.usefixtures("db_create_workers")
async def test_pagination_mixin__no_pagination_params__limited_query():
    workers_ids = await Worker.all().order_by("id").limit(TestRouterPagination.per_page).values_list("id", flat=True)
    assert workers_ids

    workers_total = await Worker.all().count()

    response = await client.get("/")

    assert response.status_code == 200
    assert [worker["id"] for worker in response.json()] == workers_ids

    assert response.headers["x-page"] == "1"
    assert response.headers["x-pages"] == str(math.ceil(workers_total / TestRouterPagination.per_page))
    assert response.headers["x-per-page"] == str(TestRouterPagination.per_page)
    assert response.headers["x-total"] == str(workers_total)


@pytest.mark.parametrize("page", [0, -1, -10000])
@pytest.mark.usefixtures("db_create_workers")
async def test_pagination_mixin__page_lt_1__error(page):
    response = await client.get("/", params={"page": page})

    assert response.status_code == 422

    error = response.json()["detail"][0]
    assert error["loc"] == ["query", "page"]
    assert error["type"] == "value_error.number.not_ge"
    assert error["msg"] == "ensure this value is greater than or equal to 1"


async def test_pagination_mixin__page_gt_total_pages__empty():
    workers_total = await Worker.all().count()
    page = math.ceil(workers_total / TestRouterPagination.per_page) + 1

    response = await client.get("/", params={"page": page})

    assert response.status_code == 200
    assert not response.json()

    assert response.headers["x-page"] == str(page)
    assert response.headers["x-pages"] == str(math.ceil(workers_total / TestRouterPagination.per_page))
    assert response.headers["x-per-page"] == str(TestRouterPagination.per_page)
    assert response.headers["x-total"] == str(workers_total)


@pytest.mark.parametrize("page", [1, 2, 3])
@pytest.mark.usefixtures("db_create_workers")
async def test_pagination_mixin__page_gte_1__skipped_pages(page):
    workers_ids = (
        await Worker.all()
        .order_by("id")
        .offset((page - 1) * TestRouterPagination.per_page)
        .limit(TestRouterPagination.per_page)
        .values_list("id", flat=True)
    )
    assert workers_ids

    workers_total = await Worker.all().count()

    response = await client.get("/", params={"page": page})

    assert response.status_code == 200
    assert [worker["id"] for worker in response.json()] == workers_ids

    assert response.headers["x-page"] == str(page)
    assert response.headers["x-pages"] == str(math.ceil(workers_total / TestRouterPagination.per_page))
    assert response.headers["x-per-page"] == str(TestRouterPagination.per_page)
    assert response.headers["x-total"] == str(workers_total)


async def test_pagination_mixin__per_page_gt_per_page_max__limited_by_per_page_max():
    workers_ids = (
        await Worker.all().order_by("id").limit(TestRouterPagination.per_page_max).values_list("id", flat=True)
    )
    assert workers_ids

    workers_total = await Worker.all().count()

    response = await client.get("/", params={"per_page": TestRouterPagination.per_page_max + 1})

    assert response.status_code == 200
    assert [worker["id"] for worker in response.json()] == workers_ids

    assert response.headers["x-page"] == "1"
    assert response.headers["x-pages"] == str(math.ceil(workers_total / TestRouterPagination.per_page_max))
    assert response.headers["x-per-page"] == str(TestRouterPagination.per_page_max)
    assert response.headers["x-total"] == str(workers_total)


@pytest.mark.parametrize("per_page", [0, -1, -10000])
@pytest.mark.usefixtures("db_create_workers")
async def test_pagination_mixin__per_page_lt_1__error(per_page):
    response = await client.get("/", params={"per_page": per_page})

    assert response.status_code == 422

    error = response.json()["detail"][0]
    assert error["loc"] == ["query", "per_page"]
    assert error["type"] == "value_error.number.not_ge"
    assert error["msg"] == "ensure this value is greater than or equal to 1"


@pytest.mark.parametrize(
    "page,per_page",
    [
        (1, 25),
        (1, 50),
        (1, 51),
        (2, 5),
        (2, 55),
        (50, 1),
    ],
)
@pytest.mark.usefixtures("db_create_workers")
async def test_pagination_mixin__page_and_per_page_redefined__correct_pagination(page, per_page):
    per_page_expected = min(per_page, TestRouterPagination.per_page_max)

    workers_ids = (
        await Worker.all()
        .order_by("id")
        .offset((page - 1) * per_page_expected)
        .limit(per_page_expected)
        .values_list("id", flat=True)
    )
    assert workers_ids

    workers_total = await Worker.all().count()

    response = await client.get("/", params={"page": page, "per_page": per_page})

    assert response.status_code == 200
    assert [worker["id"] for worker in response.json()] == workers_ids

    assert response.headers["x-page"] == str(page)
    assert response.headers["x-pages"] == str(math.ceil(workers_total / per_page_expected))
    assert response.headers["x-per-page"] == str(per_page_expected)
    assert response.headers["x-total"] == str(workers_total)
