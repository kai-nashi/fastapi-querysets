# FilterMixin

---

`FilterMixin` to restrict `RouterQuerySet.get_router_queryset` according to user sent params

## Example
```python
import dataclasses
import datetime
from typing import Optional

from fastapi import Query
from fastapi_querysets.mixins.filters import FilterMixin
from fastapi_querysets.queryset import RouterQuerySet

from myproject.models.tortoise import Task


@dataclasses.dataclass
class RouterQuerySetFilter:
    id__in: Optional[list[int]] = Query(None, alias='id[]')
    approved: Optional[bool] = Query(None)
    approved__isnull: Optional[bool] = Query(None)
    code: Optional[str] = Query(None)
    created_at__lte: Optional[datetime.datetime] = Query(None)
    created_at__gte: Optional[datetime.datetime] = Query(None)


class WorkersRouterQuerySet(FilterMixin, RouterQuerySet):
    filter_class = RouterQuerySetFilter
    model = Task
    pk_model = 'id'
```

## Properties

`filter_class` - `dataclasses.dataclass` class that defined possible filters with source and type annotations. [Read more about filter class](#filterclass)

## Methods

`get_request_queryset` - return filtered queryset

- request - `starlette.requests.Request`
- filters - `dataclasses.dataclass` instance of `filter_class` with defined fields by request
- queryset - `QuerySet`. Get it from parent class using mro. Return it filtered.

## FilterClass

`dataclasses.dataclass` class. Property name is filter keyword. Typing use for `FastApi` data validation. Every property must have valid `FastAPI` source like `Query`, `Body`, `Path`, etc.

##### Example
```python
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
