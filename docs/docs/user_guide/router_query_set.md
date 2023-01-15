# RouterQuerySet

---

`RouterQuerySet` is base class for endpoints queryset. It has two method (`get_request_queryset` and `get_request_instance`) used for endpoints.

## Example
```python
from fastapi_querysets.queryset import RouterQuerySet

from myproject.models.tortoise import Task


class WorkersRouterQuerySet(RouterQuerySet):
    model = Task
    pk_model = 'id'
```

## Properties

`model` - you have to define ORM model for `RouterQuerySet`. `RouterQuerySet` will automatically use it for defining endpoint queryset and getting instance.

`pk_model` - `model` primary key. Default is `id`

`instance` - **read only**, use this property to get instance of `model` to your endpoint.

## Methods

`get_queryset` - base queryset. Generates form `model`. You can redefine it to prefetching some data, constant filtering, aggregation or annotating.


`get_request_queryset` - method will be called to get endpoint effective queryset.

- `queryset` - effective queryset. Value is result of method `get_request_queryset`. Basic class return it as result of method.


`get_request_instance` - method will be called to get instance of `model`. If instance does not exist will return `Response(404)`.

- `queryset` - base queryset to get instance by primary key. Base class will get it as result of method `get_request_queryset`.
- `pk` - source of primary key value. Primary key column defines as class property (`pk_model`).