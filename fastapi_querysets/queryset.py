from typing import Any
from fastapi import Depends
from fastapi import Path
from fastapi import params
from fastapi.dependencies.utils import get_typed_signature
from fastapi_depends_ext import DependsMethod
from fastapi_depends_ext import DependsMethodBinder
from starlette import status
from tortoise import Model
from tortoise.queryset import QuerySet

from fastapi_querysets.exceptions import create_validation_exception


class RouterQuerySet(DependsMethodBinder, params.Depends):
    model: Model
    pk_model: str = "id"

    def __init__(self, *, use_cache: bool = True):
        super(RouterQuerySet, self).__init__(use_cache=use_cache)
        self.dependency = self.get_request_queryset
        self.instance = Depends(self.get_request_instance)

    def get_queryset(self):
        return self.model.all()

    async def get_request_queryset(
        self,
        queryset: QuerySet = DependsMethod("get_queryset"),
    ) -> QuerySet:
        return queryset

    async def get_request_instance(
        self,
        queryset: QuerySet = DependsMethod("get_request_queryset"),
        pk: Any = Path(None, alias="instance_pk"),
    ) -> Model:
        if instance := await queryset.get_or_none(**{self.pk_model: pk}):
            return instance

        signature = get_typed_signature(self.get_request_instance)
        pk_parameter = signature.parameters["pk"]

        pk_alias = getattr(pk_parameter.default, "alias") if pk_parameter.default else "pk"
        raise create_validation_exception(
            status_code=status.HTTP_404_NOT_FOUND,
            loc=[type(pk_parameter.default).__name__.lower(), pk_alias],
            msg="Instance not found",
            _type="value_error",
        )
