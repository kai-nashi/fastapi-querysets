import datetime
import decimal
from typing import Optional

from tortoise import Model
from tortoise import Tortoise
from tortoise import fields
from tortoise.queryset import QuerySet


class Contract(Model):
    id: int = fields.IntField(pk=True)
    salary: float = fields.FloatField(null=True)

    worker: fields.OneToOneNullableRelation["Worker"]


class Project(Model):
    id: int = fields.IntField(pk=True)
    description: str = fields.CharField(max_length=255)

    tasks: fields.ForeignKeyRelation["Task"]


class Task(Model):
    id: int = fields.IntField(pk=True)
    cost: decimal.Decimal = fields.DecimalField(max_digits=16, decimal_places=8)
    created_at: datetime.datetime = fields.DatetimeField(default=datetime.datetime.now)
    description: str = fields.CharField(max_length=255)
    estimated_date: datetime.date = fields.DateField()
    is_done: bool = fields.BooleanField(default=False)
    project = fields.ForeignKeyField("app_models.Project", related_name="tasks")
    workers_required_max: Optional[int] = fields.IntField(null=True)
    workers_required_min: int = fields.IntField(default=1)

    workers: QuerySet["Worker"] = fields.ManyToManyField("app_models.Worker", related_name="tasks")


class Worker(Model):
    id: int = fields.IntField(pk=True)
    contract = fields.OneToOneField("app_models.Contract", related_name="worker", null=True)
    name: str = fields.CharField(max_length=255)

    tasks: fields.ManyToManyRelation["Task"]


Tortoise.init_models(
    [
        "tests.app_models.tortoise_orm",
    ],
    "app_models",
)
