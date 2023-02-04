import os
from sqlite3 import OperationalError

import nest_asyncio
from pytest_asyncio.plugin import SubRequest
from tortoise import Tortoise
from tortoise.contrib.test import finalizer
from tortoise.contrib.test import initializer
from tortoise.contrib.test import getDBConfig
from tortoise.exceptions import DBConnectionError

from tests.fixtures import *


nest_asyncio.apply()


@pytest.fixture(autouse=True, scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def db(request: SubRequest) -> None:
    config = getDBConfig(app_label="app_models", modules=["tests.app_models", "tests.app_models.tortoise_orm"])

    async def _init_db() -> None:
        await Tortoise.init(config)
        try:
            await Tortoise._drop_databases()
        except (DBConnectionError, OperationalError):  # pragma: nocoverage
            pass

        await Tortoise.init(config, _create_db=True)
        await Tortoise.generate_schemas(safe=False)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_init_db())

    request.addfinalizer(lambda: loop.run_until_complete(Tortoise._drop_databases()))


# @pytest.fixture(scope="session", autouse=True)
# def initialize_database(request):
#     db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
#     initializer(["tests.app_models.tortoise_orm"], db_url=db_url, app_label="app_models")
#     request.addfinalizer(finalizer)
