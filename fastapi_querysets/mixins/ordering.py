from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from fastapi import Query
from fastapi_depends_ext import DependsAttr
from starlette import status
from tortoise.queryset import QuerySet

from fastapi_querysets.exceptions import create_validation_exception


QUERY_ORDERING = List[str]


class OrderingMixin:
    ordering_default: Union[Sequence[str], str] = None
    ordering_fields: Sequence[str] = tuple()

    def get_request_queryset(
        self,
        ordering: Optional[QUERY_ORDERING] = Query(None, alias="ordering[]"),
        queryset: QuerySet = DependsAttr("get_request_queryset", from_super=True),
    ) -> QuerySet:
        if ordering:
            # todo: allow to patch method typing to remove custom error
            for index, field in enumerate(ordering):
                if field.replace("-", "") not in self.ordering_fields:
                    raise create_validation_exception(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        loc=["query", "ordering[]", index],
                        msg="Invalid value",
                        _type="value_error",
                    )

            queryset = queryset.order_by(*ordering)
            return queryset

        elif isinstance(self.ordering_default, str):
            return queryset.order_by(self.ordering_default)

        elif isinstance(self.ordering_default, (list, tuple, set)):
            return queryset.order_by(*self.ordering_default)

        return queryset
