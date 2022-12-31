import asyncio

import pytest
from tortoise.expressions import F

from tests.app_models.tortoise_orm import Contract
from tests.app_models.tortoise_orm import Worker


@pytest.fixture(scope="function")
async def db_clean():
    await asyncio.gather(Worker.all().delete())


@pytest.fixture(scope="function")
async def db_create_contracts():
    await Contract.all().delete()
    await Contract.bulk_create(objects=[Contract(id=index + 1, salary=index * 100) for index in range(100)])


@pytest.fixture(scope="function")
async def db_create_workers():
    await Worker.all().delete()
    await Worker.bulk_create(objects=[Worker(id=index + 1, name=f"Test Worker {index}") for index in range(100)])


@pytest.fixture(scope="function")
async def db_fill(db_clean, db_create_contracts, db_create_workers):
    await Worker.all().update(contract_id=F("id"))
