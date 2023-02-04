# FilterNegationMixin

---

`FilterNegationMixin` is like `FilterMixin` but filter queryset by excluding. 

## Example
```python
import dataclasses
import datetime
from typing import Optional

from fastapi import Query
from fastapi_querysets.mixins.filters import FilterNegationMixin
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


class WorkersRouterQuerySet(FilterNegationMixin, RouterQuerySet):
    filter_class = RouterQuerySetFilter
    model = Task
    pk_model = 'id'
```

## Properties

`filter_class` - `dataclasses.dataclass` class that defined possible filters with source and type annotations. [Read more about filtering](/user_guide/Filtering). `FilterNegationMixin` generate `exclude_class` automatically depends on `filter_class` by appending `!` to property name.

## Methods

`get_request_queryset` - return filtered queryset by excluding

- request - `starlette.requests.Request`
- filters - `dataclasses.dataclass` instance of `exclude_class` with defined fields by request
- queryset - `QuerySet`. Get it from parent class using mro. Return it filtered.

`exclude_class` - **read only**, automatically generates from [FilterClass](/user_guide/Filtering/#filterclass). It would be looks like below definition. 
```python
import dataclasses
import datetime
from typing import Optional

from fastapi import Query

@dataclasses.dataclass
class RouterQuerySetFilterNegation:
    id__in: Optional[list[int]] = Query(None, alias='id[]!')
    approved: Optional[bool] = Query(None, alias='approved!')
    approved__isnull: Optional[bool] = Query(None, alias='approved__isnull!')
    code: Optional[str] = Query(None, alias='!')
    created_at__lte: Optional[datetime.datetime] = Query(None, alias='created_at__lte!')
    created_at__gte: Optional[datetime.datetime] = Query(None, alias='created_at__gte!')
```