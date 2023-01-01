from typing import List
from typing import Optional
from typing import Sequence

from fastapi import Query
from fastapi_depends_ext import DependsMethod
from starlette import status
from tortoise.queryset import QuerySet

from fastapi_querysets.exceptions import create_validation_exception


QUERY_ORDERING = List[str]


class OrderingMixin:
    ordering_fields: Sequence[str] = tuple()

    def get_request_queryset(
        self,
        ordering: Optional[QUERY_ORDERING] = Query(None, alias="ordering[]"),
        queryset: QuerySet = DependsMethod("get_request_queryset", from_super=True),
    ) -> QuerySet:
        if not ordering:
            return queryset

        for index, field in enumerate(ordering):
            field_name = field.replace("-", "")

            # todo: allow to patch method typing to remove custom error
            if field_name not in self.ordering_fields:
                raise create_validation_exception(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    loc=["query", "ordering[]", index],
                    msg="Invalid value",
                    _type="value_error",
                )

            if method := getattr(self, f"order_by_{field_name}", None):
                queryset = method(queryset, desc=field.startswith("-"))
            else:
                queryset = queryset.order_by(*ordering)

        return queryset
