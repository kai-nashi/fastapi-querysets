import os

import nest_asyncio
from tortoise.contrib.test import finalizer, initializer

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
def initialize_database(request):
    db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(["tests.app_models", "tests.app_models.tortoise_orm"], db_url=db_url, app_label="app_models")
    request.addfinalizer(finalizer)
