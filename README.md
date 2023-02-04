# FastAPI Querysets
![CDNJS](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-2334D058)
![CDNJS](https://shields.io/badge/FastAPI-%3E=0.7.0-009485)

---
**Documentation**: <a href="https://fastapi.tiangolo.com" target="_blank">https://fastapi.tiangolo.com</a>

**Source Code**: <a href="https://github.com/Nikakto/fastapi-querysets" target="_blank">https://github.com/Nikakto/fastapi-querysets</a>

---

## Why to use?

While you are developing FastAPI applications you are using databases with ORM. Most of the endpoints are view of database tables and require restrict queryset by filtering, pagination, ordering. This project is generic and reusable way to create restricted querysets for your endpoints.

## Supported ORM
- <a href="https://github.com/tortoise/tortoise-orm" target="_blank">Tortoise ORM</a>

## Requirements
- python >=3.8,<4.0
- fastAPI >= 0.7.0
- tortoise-orm >= 0.18.1

## Installation

```
pip install fastapi-querysets
```

# Quick tutorial

---

## Tortoise model

Let’s start with our model

```python
# models/tortoise.py

import datetime
from typing import Optional

from tortoise import Model
from tortoise import fields


class Task(Model):
    id: int = fields.IntField(pk=True)
    approved: Optional[bool] = fields.BooleanField(default=False, null=True)
    code: str = fields.CharField(max_length=6)
    created_at: datetime.datetime = fields.DatetimeField(default=datetime.datetime.now)
```
---

## Pydantic model

Create database representation model

```python
# models/pydantic.py

from tortoise.contrib.pydantic import pydantic_model_creator

from myproject.models.tortoise import Task


TaskModelOut = pydantic_model_creator(
    Task,
    name="TaskModelOut",
    include=(
        "id",
        "approved",
        "code",
        "created_at"
    ),
)
```

---

## RouterQuerySet

### Filters

We have a number of fields we want to let our users filter based on them. We create a RouterQuerySetFilter for this. Filter class is argument for `FastAPI.Depends` at endpoint.  

You require to define ORM filter keyword, type of data and setup source of data (`Query`, `Path`, `Body`, etc).

```python
# querysets_filters.py

import dataclasses
import datetime
from typing import Optional

from fastapi import Query


@dataclasses.dataclass
class RouterQuerySetFilter:
    id__in: Optional[list[int]] = Query(None, alias='id[]')
    approved: Optional[bool] = Query(None)
    approved__isnull: Optional[bool] = Query(None)
    code: Optional[str] = Query(None)
    created_at__lte: Optional[datetime.datetime] = Query(None)
    created_at__gte: Optional[datetime.datetime] = Query(None)
```

### Model Queryset

Configure `RouterQueryset` properties

```python
# querysets.py

from fastapi_querysets.mixins.filters import FilterMixin
from fastapi_querysets.mixins.filters import FilterNegationMixin
from fastapi_querysets.mixins.ordering import OrderingMixin
from fastapi_querysets.mixins.pagination import PaginationMixin
from fastapi_querysets.mixins.pagination import RouterPagination
from fastapi_querysets.queryset import RouterQuerySet

from myproject.models.tortoise import Task
from myproject.querysets_filters import RouterQuerySetFilter


class TasksRouterQuerySet(FilterMixin, FilterNegationMixin, OrderingMixin, PaginationMixin, RouterQuerySet):
    filter_class = RouterQuerySetFilter
    ordering_default = "id"
    ordering_fields = (
        "id",
        "approved",
        "code",
        "created_at",
    )
    pagination_class = RouterPagination
    model = Task
```

---

## Application

Create application, register list, list with pagination and retrieve endpoints.
```python
# app.py

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from tortoise.queryset import QuerySet

from myproject.models.pydantic import TaskModelOut
from myproject.models.tortoise import Task
from myproject.querysets import TasksRouterQuerySet


app = FastAPI()


register_tortoise(
    app,
    db_url="sqlite://:memory:",
    modules={"models": ["myproject.models.tortoise"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get("tasks/", response_model=list[TaskModelOut])
async def tasks_list_paginated(queryset: QuerySet[Task] = TasksRouterQuerySet()) -> list[TaskModelOut]:
    return await TaskModelOut.from_queryset(queryset)


@app.get("tasks/paginated", response_model=list[TaskModelOut])
async def tasks_list_paginated(queryset: QuerySet[Task] = TasksRouterQuerySet().paginated) -> list[TaskModelOut]:
    return await TaskModelOut.from_queryset(queryset)


@app.get("tasks/{instance_id}", response_model=list[TaskModelOut])
async def tasks_retrieve(task: QuerySet[Task] = TasksRouterQuerySet().instance) -> list[TaskModelOut]:
    return TaskModelOut.from_orm(task)
```

---

## Requests

### List

On request effective queryset will be filtered and ordered by query params.

For example, user has requested endpoint with some query params
```json
{
    "created_at__lte": "2023-01-01T00:00:00",
    "approved": false,
    "ordering[]": "created_at",
}
```

Request URL looks like  
```http://localhost:8000/tasks/?created_at__lte=2023-01-01T00:00:00&approved=false&ordering[]=created_at```

Effective queryset at the endpoint method will be
```python
(
    Task
    .filter(created_at__lte=datetime.datetime(2023, 1, 1, 0, 0, 0), approved=False)
    .order_by("created_at")
)
```

### List paginated

Like not paginated endpoint at this queryset will be filtered, ordering and additional paginated.

For example, user has requested endpoint with some query params
```json
{
    "page": 2,
    "per_page": 10,
    "created_at__lte": "2023-01-01T00:00:00",
    "approved": false,
    "ordering[]": "created_at",
}
```

Request URL looks like   
```http://localhost:8000/tasks/?page=2&per_page=10&created_at__lte=2023-01-01T00:00:00&approved=false&ordering[]=created_at```


Effective queryset at endpoint method will be
```python
(
    Task
    .filter(created_at__lte=datetime.datetime(2023, 1, 1, 0, 0, 0), approved=False)
    .order_by("created_at")
    .offset(10)
    .limit(10)
)
```

As well as to `Response` will be added pagination information. Pagination information always matches effective queryset
```json
{
    "x-page": "2",
    "x-pages": "4",
    "x-per-page": "10",
    "x-total": "32"
}
```

### Retrieve

Request URL looks like   
```http://localhost:8000/tasks/10/```

Endpoint method will get `Task` with `id == 10` as argument `task`.     
If `Task` with `id == 10` does not exist then endpoint return `Response(404)` 