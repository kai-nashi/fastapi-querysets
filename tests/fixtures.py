import asyncio
import datetime

import pytest
from tortoise.expressions import F

from tests.app_models.tortoise_orm import Contract
from tests.app_models.tortoise_orm import Project
from tests.app_models.tortoise_orm import Task
from tests.app_models.tortoise_orm import Worker


@pytest.fixture(scope="function")
async def db_clean():
    await asyncio.gather(
        Contract.all().delete(),
        Project.all().delete(),
        Task.all().delete(),
        Worker.all().delete(),
    )


@pytest.fixture(scope="function")
async def db_create_contracts():
    await Contract.all().delete()
    await Contract.bulk_create(objects=[Contract(id=index + 1, salary=index * 100) for index in range(100)])


@pytest.fixture(scope="function")
async def db_create_tasks(db_create_projects):
    await Task.all().delete()
    await Task.bulk_create(
        objects=[
            Task(
                id=index + 1,
                cost=index // 5 * 100,
                created_at=datetime.datetime.now() + datetime.timedelta(days=index // 10),
                description=f"Test task {index}",
                estimated_date=datetime.datetime.now() + datetime.timedelta(days=index // 10 + index % 2),
                is_done=not (index % 4),  # 25% is_done = True
                project_id=index // 10 + 1,  # only first 10 projects have tasks
                workers_required_max=index % 10 or None,  # every ten task has workers_required_max = None
                workers_required_min=max(index % 5, 1),  # 1 to 4
            )
            for index in range(100)
        ]
    )


@pytest.fixture(scope="function")
async def db_create_projects():
    await Project.all().delete()
    await Project.bulk_create(objects=[Project(id=index + 1, description=f"Test project") for index in range(100)])


@pytest.fixture(scope="function")
async def db_create_workers():
    await Worker.all().delete()
    await Worker.bulk_create(objects=[Worker(id=index + 1, name=f"Test Worker {index}") for index in range(100)])


@pytest.fixture(scope="function")
async def db_fill(db_clean, db_create_contracts, db_create_projects, db_create_tasks, db_create_workers):
    await Worker.all().update(contract_id=F("id"))

    tasks = await Task.all()
    for worker in await Worker.filter(id__lte=10):  # only first 10 workers have tasks
        worker_tasks = [task for task in tasks if task.id % worker.id == 0]
        await worker.tasks.add(*worker_tasks)
