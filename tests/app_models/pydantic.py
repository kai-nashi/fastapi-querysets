from tortoise.contrib.pydantic import pydantic_model_creator

from tests.app_models.tortoise_orm import Contract
from tests.app_models.tortoise_orm import Project
from tests.app_models.tortoise_orm import Task
from tests.app_models.tortoise_orm import Worker


ContractModelOut = pydantic_model_creator(
    Contract,
    name="ContractModelOut",
    include=("id", "salary", "worker_id"),
)


ProjectModelOut = pydantic_model_creator(
    Project,
    name="ProjectModelOut",
    include=("id", "description"),
)


TaskModelOut = pydantic_model_creator(
    Task,
    name="TaskModelOut",
    include=(
        "id",
        "cost",
        "created_at",
        "description",
        "estimated_date",
        "is_done",
        "project_id",
        "workers_required_max",
        "workers_required_min",
    ),
)


WorkerModelOut = pydantic_model_creator(
    Worker,
    name="WorkerModelOut",
    include=("id", "contract_id", "name"),
)
