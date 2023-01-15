# PaginationMixin

---

`PaginationMixin` to limit queryset. Endpoint will have `page` and `per_page` query params for pagination. Query params `page` and `per_page` must be greater than 1.

Mixing additionally add pagination information to response.

## Example
```python
from fastapi_querysets.mixins.pagination import PaginationMixin
from fastapi_querysets.mixins.pagination import RouterPagination
from fastapi_querysets.queryset import RouterQuerySet

from myproject.models.tortoise import Task

class WorkersRouterQuerySet(PaginationMixin, RouterQuerySet):
    model = Task
    pagination_class = RouterPagination
    pk_model = 'id'
```

## Properties

`pagination_class` - `Type[RouterPagination]`, you can define class one time and reuse it for all endpoints to them have same pagination settings. 

`ordering_fields` - `Sequence[str]`. List of allowed fields to order queryset. You can use related fields.


## Pagination class

Define pagination class require your project and use it instead `RouterPagination` as `pagination_class`

### Example

```python
from fastapi_querysets.mixins.pagination import RouterPagination

class ApiRouterPagination(RouterPagination):
    per_page_max: int = 25
    per_page: int = 50
```

### Properties
- `per_page_max` - `int`, limit max items in response. `per_page` will be reduced to `per_page_max` if user send `per_page` greater than `per_page_max`.
- `per_page` - `int`, that value will be used if user not send `per_page` query params