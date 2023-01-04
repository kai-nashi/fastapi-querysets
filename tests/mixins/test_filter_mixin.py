import dataclasses
from typing import List
from typing import Optional

import pytest
from fastapi import FastAPI
from fastapi import Query
from httpx import AsyncClient
from tortoise.queryset import QuerySet

from fastapi_querysets.mixins.filters import FilterMixin
from fastapi_querysets.queryset import RouterQuerySet
from tests.app_models.pydantic import WorkerModelOut
from tests.app_models.tortoise_orm import Worker


app = FastAPI()


@dataclasses.dataclass
class RouterQuerySetFilter:
    id: Optional[int] = Query(None)
    id__in: Optional[List[int]] = Query(None, alias="id[]")
    contract_id: Optional[int] = Query(None, alias="contract")
    name: Optional[str] = Query(None)


class WorkersRouterQuerySet(FilterMixin, RouterQuerySet):
    filter_class = RouterQuerySetFilter
    model = Worker


@app.get("/")
async def app_test(queryset: QuerySet[Worker] = WorkersRouterQuerySet()) -> dict:
    return await WorkerModelOut.from_queryset(queryset)


client = AsyncClient(app=app, base_url="http://test")


@pytest.mark.usefixtures("db_fill")
async def test_filter_mixin__params_empty__not_filtered(db_create_workers):
    workers_ids = await Worker.all().order_by("id").values_list("id", flat=True)
    assert workers_ids

    response = await client.get("/")

    assert response.status_code == 200
    assert sorted([worker["id"] for worker in response.json()]) == workers_ids


@pytest.mark.parametrize(
    "model_filters,params",
    [
        ({"id": 1}, {"id": 1}),
        ({"id__in": [1, 2, 3]}, {"id[]": [1, 2, 3]}),
        ({"name": "Test Worker 1"}, {"name": "Test Worker 1"}),
        ({"contract_id": 1}, {"contract": 1}),
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_filter_mixin__params_filter__filter_with_params(model_filters, params):
    workers_ids = await Worker.filter(**model_filters).order_by("id").values_list("id", flat=True)
    assert workers_ids

    response = await client.get("/", params=params)

    assert response.status_code == 200
    assert sorted([worker["id"] for worker in response.json()]) == workers_ids


@pytest.mark.usefixtures("db_fill")
async def test_filter_mixin__param_not_in_model__ignored():
    workers_ids = await Worker.all().order_by("id").values_list("id", flat=True)
    assert workers_ids

    response = await client.get("/", params={"not_exist_param": 1})

    assert response.status_code == 200
    assert sorted([worker["id"] for worker in response.json()]) == workers_ids


@pytest.mark.parametrize(
    "params",
    [
        {"id": None},
        {"id": "abc"},
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_filter_mixin__param_wrong_type__error(params):
    response = await client.get("/", params=params)

    assert response.status_code == 422
    error = response.json()["detail"][0]

    assert error["loc"] == ["query", list(params.keys())[0]]


@pytest.mark.parametrize(
    "params",
    [
        {"id[]": None},
        {"id[]": "abc"},
    ],
)
@pytest.mark.usefixtures("db_fill")
async def test_filter_mixin__param_list_element_wrong_type__error(params):
    response = await client.get("/", params=params)

    assert response.status_code == 422
    error = response.json()["detail"][0]

    assert error["loc"] == ["query", list(params.keys())[0], 0]
