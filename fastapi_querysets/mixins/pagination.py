import math
from collections import namedtuple
from typing import Type
from typing import cast

from fastapi import Depends
from fastapi import Query
from fastapi_depends_ext import DependsMethod
from starlette.responses import Response
from tortoise.queryset import QuerySet


Pagination = namedtuple("SkipLimit", "skip limit")


class RouterPagination:
    per_page_max: int = 25
    per_page: int = 25

    def __init__(self, per_page_max: int = None, per_page: int = None):
        self.per_page_max = per_page_max or self.per_page_max
        self.per_page = per_page or self.per_page

    def __call__(self, page: int = Query(1, ge=1), per_page: int = Query(None, ge=1)) -> Pagination:
        """Return value is tuple of (skip, limit)"""
        per_page = min(self.per_page_max, per_page or self.per_page)
        return Pagination(skip=(page - 1) * per_page, limit=per_page)


class PaginationMixin:
    # todo: add per_page_min
    pagination_class: Type[RouterPagination]

    def __init__(self, *args, per_page_max: int = None, per_page: int = None, **kwargs):
        self._pagination = self.pagination_class(per_page_max=per_page_max, per_page=per_page)
        super(PaginationMixin, self).__init__(*args, **kwargs)
        self.paginated = Depends(self.get_request_queryset_paginated)

    async def get_request_queryset_paginated(
        self,
        response: Response,
        queryset: QuerySet = DependsMethod("get_request_queryset"),
        pagination: Pagination = DependsMethod("_pagination"),
    ) -> QuerySet:
        total = await queryset.count()
        response.headers["x-page"] = str(math.ceil(pagination.skip / pagination.limit) + 1)
        response.headers["x-pages"] = str(math.ceil(total / pagination.limit))
        response.headers["x-per-page"] = str(pagination.limit)
        response.headers["x-total"] = str(total)

        # todo: refactor to yield queryset and the adding pagination info
        return queryset.offset(cast(int, pagination.skip)).limit(pagination.limit)
