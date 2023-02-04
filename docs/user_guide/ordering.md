# OrderingMixin

---

`OrderingMixin` for ordering queryset. To ordering queryset user should define `ordering[]` query params and values of list must be in `ordering_fields`. For descending ordering just prepend `-` to field name like `?ordering[]=-id`.

## Example
```python
from fastapi_querysets.mixins.ordering import OrderingMixin
from fastapi_querysets.queryset import RouterQuerySet

from myproject.models.tortoise import Task

class WorkersRouterQuerySet(OrderingMixin, RouterQuerySet):
    model = Task
    ordering_default = 'id'
    ordering_fields = (
        "id",
        "approved",
        "code",
        "created_at",
    )
    pk_model = 'id'
```

## Properties

`ordering_default` - `str` or `list[str]`. That ordering will apply if user not define `ordering[]` param.

`ordering_fields` - `Sequence[str]`. List of allowed fields to order queryset. You can use related fields.
