"""
This module contains integration tests meant to run against a test Mastodon instance.

You can set up a test instance locally by following this guide:
https://docs.joinmastodon.org/dev/setup/

To enable integration tests, export the following environment variables to match
your test server and database:

```
export TOOT_TEST_BASE_URL="localhost:3000"
export TOOT_TEST_DATABASE_DSN="dbname=mastodon_development"
```
"""

import json
import re
import os
import psycopg2
import pytest
import uuid

from click.testing import CliRunner, Result
from pathlib import Path
from toot import api, App, User
from toot.cli import Context


def pytest_configure(config):
    import toot.settings
    toot.settings.DISABLE_SETTINGS = True


# Mastodon database name, used to confirm user registration without having to click the link
DATABASE_DSN = os.getenv("TOOT_TEST_DATABASE_DSN")
TOOT_TEST_BASE_URL = os.getenv("TOOT_TEST_BASE_URL")

# Toot logo used for testing image upload
TRUMPET = str(Path(__file__).parent.parent.parent / "trumpet.png")

ASSETS_DIR = str(Path(__file__).parent.parent / "assets")


def create_app(base_url):
    instance = api.get_instance(base_url).json()
    response = api.create_app(base_url)
    return App(instance["uri"], base_url, response["client_id"], response["client_secret"])


def register_account(app: App):
    username = str(uuid.uuid4())[-10:]
    email = f"{username}@example.com"

    response = api.register_account(app, username, email, "password", "en")
    confirm_user(email)
    return User(app.instance, username, response["access_token"])


def confirm_user(email):
    conn = psycopg2.connect(DATABASE_DSN)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET confirmed_at = now() WHERE email = %s;", (email,))
    conn.commit()


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


# Host name of a test instance to run integration tests against
# DO NOT USE PUBLIC INSTANCES!!!
@pytest.fixture(scope="session")
def base_url():
    if not TOOT_TEST_BASE_URL:
        pytest.skip("Skipping integration tests, TOOT_TEST_BASE_URL not set")

    return TOOT_TEST_BASE_URL


@pytest.fixture(scope="session")
def app(base_url):
    return create_app(base_url)


@pytest.fixture(scope="session")
def user(app):
    return register_account(app)


@pytest.fixture(scope="session")
def friend(app):
    return register_account(app)


@pytest.fixture(scope="session")
def user_id(app, user):
    return api.find_account(app, user, user.username)["id"]


@pytest.fixture(scope="session")
def friend_id(app, user, friend):
    return api.find_account(app, user, friend.username)["id"]


@pytest.fixture(scope="session", autouse=True)
def testing_env():
    os.environ["TOOT_TESTING"] = "true"


@pytest.fixture(scope="session")
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def run(app, user, runner):
    def _run(command, *params, input=None) -> Result:
        ctx = Context(app, user)
        return runner.invoke(command, params, obj=ctx, input=input)
    return _run


@pytest.fixture
def run_as(app, runner):
    def _run_as(user, command, *params, input=None) -> Result:
        ctx = Context(app, user)
        return runner.invoke(command, params, obj=ctx, input=input)
    return _run_as


@pytest.fixture
def run_json(app, user, runner):
    def _run_json(command, *params):
        ctx = Context(app, user)
        result = runner.invoke(command, params, obj=ctx)
        assert result.exit_code == 0
        return json.loads(result.stdout)
    return _run_json


@pytest.fixture
def run_anon(runner):
    def _run(command, *params) -> Result:
        ctx = Context(None, None)
        return runner.invoke(command, params, obj=ctx)
    return _run


# ------------------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------------------


def posted_status_id(out):
    pattern = re.compile(r"Toot posted: http://([^/]+)/([^/]+)/(.+)")
    match = re.search(pattern, out)
    assert match

    _, _, status_id = match.groups()

    return status_id
