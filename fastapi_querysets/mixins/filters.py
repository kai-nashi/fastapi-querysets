import copy
import dataclasses
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Protocol
from typing import Tuple

from fastapi_depends_ext import DependsMethod
from pydantic.fields import FieldInfo
from starlette.requests import Request
from tortoise.queryset import QuerySet


class DataclassProtocol(Protocol):
    __dataclass_fields__: Dict
    __dataclass_params__: Dict
    __post_init__: Optional[Callable]


class BaseFilterMixin:
    def _get_model_filters(self, request: Request, filters: DataclassProtocol) -> Dict[str, Any]:
        fields_map = {field.default.alias or field.name: field.name for field in dataclasses.fields(filters)}
        _fields = set(request.query_params) & set(fields_map)
        return {fields_map[field]: getattr(filters, fields_map[field]) for field in _fields}


class FilterNegationMixin(BaseFilterMixin):
    # todo: allow to configure exclude_class directly
    filter_class: DataclassProtocol

    @property
    def exclude_class(self) -> type:
        # todo: dedicate method to create NegationClass from dataclass
        fields: List[Tuple[str, type, dataclasses.Field]] = []
        for field in dataclasses.fields(self.filter_class):
            _field = copy.copy(field)
            if isinstance(_field.default, FieldInfo):
                _field.default = copy.copy(_field.default)
                _field.default.alias = f"{_field.default.alias or _field.name}!"

            fields.append((_field.name, _field.type, _field))

        return dataclasses.make_dataclass(f"{self.filter_class.__name__}Negation", fields=fields, frozen=True)

    def get_request_queryset(
        self,
        request: Request,
        exclude: DataclassProtocol = DependsMethod("exclude_class"),
        queryset: QuerySet = DependsMethod("get_request_queryset", from_super=True),
    ) -> QuerySet:
        if model_exclude := self._get_model_filters(request, exclude):
            queryset = queryset.exclude(**model_exclude)
        return queryset


class FilterMixin(BaseFilterMixin):
    filter_class: DataclassProtocol

    def get_request_queryset(
        self,
        request: Request,
        filters: DataclassProtocol = DependsMethod("filter_class"),
        queryset: QuerySet = DependsMethod("get_request_queryset", from_super=True),
    ) -> QuerySet:

        if model_filters := self._get_model_filters(request, filters):
            queryset = queryset.filter(**model_filters)
        return queryset
