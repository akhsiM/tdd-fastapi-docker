- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Init](#init)
    - [Why Uvicorn?](#why-uvicorn)
  - [Running with auto-reload](#running-with-auto-reload)
  - [Configuration](#configuration)
    - [Dependency Injection](#dependency-injection)
  - [Playing around with environment variable](#playing-around-with-environment-variable)
    - [Using lru_cache](#using-lru_cache)
  - [Async Handlers](#async-handlers)
- [Docker Configuration](#docker-configuration)
  - [Dockerfile](#dockerfile)
  - [`docker-compose.yml`](#docker-composeyml)
- [Postgres Setup](#postgres-setup)
  - [`web-db` Dockerfile](#web-db-dockerfile)
  - [Re-configuring the `web` service](#re-configuring-the-web-service)
  - [Add configuration to FastAPI app](#add-configuration-to-fastapi-app)
  - [Build the new image & spin the containers](#build-the-new-image--spin-the-containers)
- [Toirtoise ORM](#toirtoise-orm)
  - [Setting UP](#setting-up)
  - [Defining the model](#defining-the-model)
  - [Registering `tortoise`](#registering-tortoise)
  - [Fire up containers](#fire-up-containers)
- [Migrations](#migrations)
  - [Kill the containers](#kill-the-containers)
  - [Turn off schema auto-generation](#turn-off-schema-auto-generation)
  - [Install and configure Aerich](#install-and-configure-aerich)
- [Pytest](#pytest)
  - [Setup](#setup)
  - [Setting up Fixtures](#setting-up-fixtures)
  - [Fire up](#fire-up)
  - [Writing Tests](#writing-tests)
  - [How to write tests](#how-to-write-tests)
- [Others](#others)
  - [Anatomy of a test](#anatomy-of-a-test)
  - [GivenWhenThen](#givenwhenthen)

# Introduction

An asynchronous text summarization API built with Test-Driven Development. The API follows RESTful design principles, using basic HTTP verbs: GET, POST, PUT and DELETE.

| Endpoint | HTTP Method | CRUD Method | Result |
| -------- | ----------- | ----------- | ------ |
| /summaries | GET | READ | get all summaries |
| /summaries/:id | GET | READ  | get a single summary |
| /summaries | POST | CREATE | add a summary |
| /summaries/:id | PUT | UPDATE | update a summary |
| /summaries/:id | DELETE | DELETE | delete a summary |

Along with **FastAPI**, we'll use **Docker** to quickly set up our local development environment and simplify deployment. A **PostgreSQL** database will be used, with **Tortoise ORM**, an async ORM, being used to interact with this it. `pytest` will be used instead of `unittest` for writing unit and integration test to test the API.

Finally, the code will be stored on a Github repository. We'll then use **GitHub Actions** to run tests, before deploying the app to Heroku.

`pytest`
# Getting Started

## Init

With in the **app/** directory, we need to add some files:
```
../project
├── app
│   ├── __init__.py
│   ├── main.py
```

Then, in **main.py**, an instance of FastAPI can be created. Doing the below sets up a route just for sanity check:
```py
from fastapi import FastAPI

app = FastAPI()


@app.get('/ping')
def pong():
    return {
        'ping': 'pong!'
    }
```

..then the server can be started by:
```sh
$ uvicorn app.main:app
```

![](./code_img/README-2021-09-12-22-05-37.png)

What does this command mean? `app.main:app` tells Uvicorn where to find the FastAPI application: within the **app** module, in the **main.py** file, and the object created is named **app**.

FastAPI automatically generates a schema based on the [OpenAPI standard](https://swagger.io/docs/specification/about/). 

We can also view the raw JSON at http://localhost:8000/openapi.json. This can be used to automatically generate client-side code for a front-end or mobile application.

![](./code_img/README-2021-09-12-22-07-04.png)

FastAPI uses this Open API json along with **Swagger UI** to create interactive API documentation, which can be viewed at http://localhost:8000/docs

![](./code_img/README-2021-09-12-22-09-26.png)

### Why Uvicorn?

Unlike Django or Flask, FastAPI does not have a built-in development server. There are pros and cons to this.

On one hand, it takes a bit more to serve up the app in development mode. On the other hand, this helps to conceptually seperate the web framework from the web server. This is often a source of confusion for beginners when one moves from development to production with a web framework that does have a built-in development server (like Django).

Uvicorn is a ligtning-fast ASGI server implementation. We can read more about ASGI here:
[Introduction to ASGI: Emergence of an Async Python Web Ecosystem](https://florimond.dev/en/posts/2019/08/introduction-to-asgi-async-python-web/)

## Running with auto-reload

We should run Fast API with auto-reload so that the server would restart after changes to the code base. This should only be done during development.

```sh
$ uvicorn app.main:app --reload
```

## Configuration

A new file **config.py** is created in the **app** directory to define environment-specific configuration variables.

```python
# project/app/config.py
import logging
import os
from pydantic import BaseSettings


log = logging.getLogger('uvicorn')


class Settings(BaseSettings):
    environment: str = os.getenv('ENVIRONMENT', 'dev')
    testing: bool = os.getenv('TESTING', 0)


def get_settings() -> BaseSettings:
    log.info('Loading configuration...')
    return Settings()

```

Here we define `Settings` with two attributes:
- `environment`: defines the environment (dev/test/uat..)
- `testing`: defines whether or not we are in test mode

`Pydantic` is a useful library for data parsing and validation. It leverages Python type hints to coerce input types to declared type, accumulating all errors using `ValidationError`. `pydantic` enforces type hints at runtime and provides user-friendly errors when data is invalid. In our case, we are using it for settings management.

The `BaseSettings` class from Pydantic validates the data so that when we create an instance of `Settings`, `environment` and `testing` will have types of `str` and `bool` respectively.

Then, **main.py** needs to be updated to use this new configuration:
```py
# project/app/main.py
from fastapi import FastAPI, Depends
from app.config import get_settings, Settings

app = FastAPI()


@app.get('/ping')
def pong(settings: Settings=Depends(get_settings)):
    return {
        'ping': 'pong!',
        'environment': settings.environment,
        'testing': settings.testing
    }
```

### Dependency Injection

`settings: Settings=Depends(get_settings)`: The `Depend` function is a dependency that declares another dependency: `get_settings`. Put another way, `Depend` depends on the result of `get_settings`. The value returned by `get_settings`, `Settings` is then assigned to the `settings` parameter. This is FastAPI **dependency injection** system. We use it by importing `Depend` and give it a single parameter, a function.

When a new request arrives, FastAPI will take care of:
- Calling our dependency function,*that is passed to `Depend()`*, with the correct parameter.
- Get the result from the dependency function, then
- Assign the result to the parameter in our *path operation function*

## Playing around with environment variable

If we browse to http://localhost:8000/ping again, we'd see:
```json
{
  "ping": "pong!",
  "environment": "dev",
  "testing": false
}
```

We can kill the server and set the environment variable in shell:
```sh
$ export ENVIRONMENT=prod 
$ export TESTING=1
```

```json
{
  "ping": "pong!",
  "environment": "prod",
  "testing": true
}
```

If we try setting the `TESTING` variable to something that is not a boolean, such as:
```sh
$ export TESTING=hello
```

..and browse to the route, Fast API would throw an error:
```
...
  File "pydantic/main.py", line 406, in pydantic.main.BaseModel.__init__
pydantic.error_wrappers.ValidationError: 1 validation error for Settings
testing
  value could not be parsed to a boolean (type=type_error.bool)
```

Essentially, `get_settings` gets called for each individual request. For performance reason, it is best for `get_settings`, or any function that returns the configuration/setting values for that matter, to read from environment variables (instead of a file).

### Using lru_cache

```py
@functools.lru_cache(user_function, maxsize=128, typed=False)
```

`lru_cache` (Least recently used cache) can be used to call `get_settings` only once. This decorator wraps the function with a memoizing callable that serves up to the *maxsize* most recent calls.

```py
# project/app/config.py
import logging
import os
from pydantic import BaseSettings
from functools import lru_cache


log = logging.getLogger('uvicorn')


class Settings(BaseSettings):
    environment: str = os.getenv('ENVIRONMENT', 'dev')
    testing: bool = os.getenv('TESTING', 0)


@lru_cache()
def get_settings() -> BaseSettings:
    log.info('Loading configuration...')
    return Settings()
```

The difference can be inspected by looking at the server logs:

- **Without** `lru_cache()`:
```
INFO:     Loading configuration...
INFO:     127.0.0.1:49590 - "GET /ping HTTP/1.1" 200 OK
INFO:     Loading configuration...
INFO:     127.0.0.1:49590 - "GET /ping HTTP/1.1" 200 OK
INFO:     Loading configuration...
INFO:     127.0.0.1:49590 - "GET /ping HTTP/1.1" 200 OK
```
- **With** `lru_cache()`:
```
INFO:     Loading configuration...
INFO:     127.0.0.1:49614 - "GET /ping HTTP/1.1" 200 OK
INFO:     127.0.0.1:49614 - "GET /ping HTTP/1.1" 200 OK
INFO:     127.0.0.1:49614 - "GET /ping HTTP/1.1" 200 OK
INFO:     127.0.0.1:49614 - "GET /ping HTTP/1.1" 200 OK
```

## Async Handlers

Now, we can convert the synchronouse handler over to an asynchronous one. 

FastAPI makes it easy to deliver routes asynchronously. Rather than having to go through the trouble of spinning up a task queue (like Celery or RQ), or utilizing threads, as long as we don't have any blocking I/O calls in the handler, we can simply declare the handler as asynchronous by adding the `async` keyword:
```py
@app.get('/ping')
async def pong(settings: Settings=Depends(get_settings)):
    return {
        'ping': 'pong!',
        'environment': settings.environment,
        'testing': settings.testing
    }
```

# Docker Configuration

## Dockerfile

```Dockerfile
FROM python:3.9.6-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERRED 1

RUN apt-get update\
 && apt-get -y install netcat gcc \
 && apt-get clean

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
```

We start with a slim-buster-based Docker image for Python 3.9.6. Then, we set a working directory, as well as two environment variables:
- `PYTHONDONTWRITEBYTECODE`: Prevents Python from writing `pyc` files to disc (equivalent to `python -B`).
- `PYTHONBUFFERRED`: Prevents Python from buffering stdout and stderr (equivalent to `python -u`)

We also need a `.dockerignore` to exclude specific files and folders from being copied over to the image.
```
.dockerignore
Dockerfile
Dockerfile.prod
```

At this stage, I tried running `docker build .` and everything completed successfuly.

## `docker-compose.yml`

```yml
version: '3.8'

services:
  web:
    build: ./project/
    command: uvicorn app.main:app --reload --workers 1 --host 0.0.0.0 --port 8000
    volumes:
      - ./project:/usr/src/app
    ports:
      - 8004:8000
    environment:  
      - ENVIRONMENT=dev
      - TESTING=0
```

This configuration will create a service called `web` from the Dockerfile.

When the container spins up, Uvicorn will run with the following settings:
- `reload` enables auto reload.
- `workers 1` provides single worker process.
- `host 0.0.0.0` defines the address to host the server on.
- `port 8000` defines the port to host the server on.

The `volume` is used to mount the base directory `project/` into the container, within the working directory `/usr/src/app`. **This is a must** for development environment, in order to update the container whenever a change to the source code is made. Without this option, we'd need to rebuild the image each time we make changes to the codebase. That'would be inconvenient.

The docker compose file version we used is `3.8`. This has no relation with the version of docker compose installed. It simply specifies the file format that we want to use.

We can build the image now:
```sh
$ docker-compose build
```

Then, we can fire up the container in **detached mode**:
```sh
$ docker-compose up -d
```

At this point, we should be able to browse to http://localhost:8004/ping:
![](./code_img/README-2021-09-12-23-25-04.png)

# Postgres Setup

What we need to do now is to configure Postgres, get it up and running in another container, then link it to the `web` service.

Then, we'll set up Tortoise ORM and configure a model.

First, we need to configure Postgres by adding a new service to `docker-compose.yml` with the appropriate environment variables and install `asyncpg`.

```
$ mkdir project/db
$ touch create.sql
```

```sql
CREATE DATABASE web_dev;
CREATE DATABASE web_test;
```

## `web-db` Dockerfile

Within this `db/` directory, we'd also add a Dockerfile.
```dockerfile
FROM postgres:13-alpine

# run create.sql on init
ADD create.sql /docker-entrypoint-initdb.d
```

Here, we pull an Alpine-based Postgres image. We then extend this image by adding `create.sql` to `docker-entrypoint-initdb.d` directory in the container. By doing this, **the file will execute on init**.

Quote from https://hub.docker.com/_/postgres:
> ## Initialization scripts
> 
> If you would like to do additional initialization in an image derived from this one, add one or more *.sql, *.sql.gz, or *.sh scripts under /docker-entrypoint-initdb.d (creating the directory if necessary). After the entrypoint calls initdb to create the default postgres user and database, it will run any *.sql files, run any executable *.sh scripts, and source any non-executable *.sh scripts found in that directory to do further initialization before starting the service.
> 
> Warning: scripts in /docker-entrypoint-initdb.d are only run if you start the container with a data directory that is empty; any pre-existing database will be left untouched on container startup. One common problem is that if one of your /docker-entrypoint-initdb.d scripts fails (which will cause the entrypoint script to exit) and your orchestrator restarts the container with the already initialized data directory, it will not continue on with your scripts.

After setting up our Postgres image, we'll add a new service `web-db` to `docker-compose.yml`:
```yml
version: '3.8'

services:
  web:
    build: ./project/
    command: uvicorn app.main:app --reload --workers 1 --host 0.0.0.0 --port 8000
    volumes:
      - ./project:/usr/src/app
    ports:
      - 8004:8000
    environment:  
      - ENVIRONMENT=dev
      - TESTING=0
      - DATABASE_URL=postgres://postgres:postgres@web-db:5432/web_dev
      - DATABASE_TEST_URL=postgres://postgres:postgres@web-db:5432/web_test
    depends_on:
      - web-db

  web-db:
    build:
      context: ./project/db/
      dockerfile: Dockerfile
    expose:
      - 5432
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
```

The `depends_on` config expresses dependency between services. This configuration leads to the following behaviours:

- `docker-compose up` will start the services in dependency order. In our case, `web-db` are started before `web`.
- `docker-compose up SERVICE` automatically includes `SERVICE`'s dependencies. In our case, if we do `docker-compose up web`, `web-db` is also created and started.
- `docker-compose stop` stops services in dependency order. In our case, `web` is stopped before `web-db`.

Once spun up, Postgres will be available on port `5432` for services running in other containers. 

## Re-configuring the `web` service

The `web` service is dependent not only on the container being up and running, but also the actual Postgres instance being up and healthy. Therefore, let's add `entrypoint.sh` file to the `project/` directory:
```sh
#!/bin/sh

echo "Waiting for Postgres..."

while ! nc -z web-db 5432; do
    sleep 0.1
done

echo "PostgreSQL started."

exec "$@"
```

What we are doing here is using `netcat` to scan the service using its name `web-db`, until `Connection to web-db port 5432 [tcp/postgresql] succeeded!` is returned.

`exec "$@"` run the command given by the command line parameters in such a way that the current process is replaced by it. Without this, the parent shell process survives and waits for the child to exit. With this, the child process **replaces** the parent process entirely when there's nothing for the parent to do after forking the child. It is a form of **optimization**. The ELI5 definition is: "Do everything in this `.sh` script, then in the same shell run the command the user passes in on the command line."

Then, we update `project/Dockerfile` to install the appropriate dependency packages and supply an entrypoint.

```dockerfile
FROM python:3.9.6-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERRED 1

RUN apt-get update\
 && apt-get -y install netcat gcc postgresql\
 && apt-get clean

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

COPY ./entrypoint.sh .
RUN chmod +x /usr/src/app/entrypoint.sh

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
```

We also need to add `asyncpg` to our project requirements:
```sh
$ poetry add asyncpg
```

## Add configuration to FastAPI app

Next, we need to update `config.py` to read `DATABASE_URL` and assign the value to `database_url`. 
```py
import logging
import os
from pydantic import BaseSettings, AnyUrl
from functools import lru_cache


log = logging.getLogger('uvicorn')


class Settings(BaseSettings):
    environment: str = os.getenv('ENVIRONMENT', 'dev')
    testing: bool = os.getenv('TESTING', 0)
    database_url: AnyUrl = os.environ.get('DATABASE_URL')


@lru_cache()
def get_settings() -> BaseSettings:
    log.info('Loading configuration...')
    return Settings()
```

`AnyUrl` from `pydantic` is used for URL validation.

## Build the new image & spin the containers

After we have done this, we can build the new image and spin up the two container. We also need to add execution to the `entrypoint.sh`'s permission.  
```sh
$ chmod +x project/entrypont.sh
$ docker-compose up -d --build
```

We can also inspect the **logs** for `web` service:
```sh
$ docker-compose logs web
```
```
web_1     | Waiting for Postgres...
web_1     | PostgreSQL started.
web_1     | INFO:     Will watch for changes in these directories: ['/usr/src/app']
web_1     | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
web_1     | INFO:     Started reloader process [1] using statreload
web_1     | INFO:     Started server process [9]
web_1     | INFO:     Waiting for application startup.
web_1     | INFO:     Application startup complete.
web_1     | INFO:     Shutting down
web_1     | INFO:     Waiting for application shutdown.
web_1     | INFO:     Application shutdown complete.
web_1     | INFO:     Finished server process [9]
web_1     | INFO:     Stopping reloader process [1]
web_1     | Waiting for Postgres...
web_1     | PostgreSQL started.
web_1     | INFO:     Will watch for changes in these directories: ['/usr/src/app']
web_1     | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
web_1     | INFO:     Started reloader process [1] using statreload
web_1     | INFO:     Started server process [10]
web_1     | INFO:     Waiting for application startup.
web_1     | INFO:     Application startup complete.
web_1     | INFO:     Loading configuration...
web_1     | INFO:     172.18.0.1:38288 - "GET /ping HTTP/1.1" 200 OK
web_1     | INFO:     172.18.0.1:38304 - "GET /ping HTTP/1.1" 200 OK
```

If we want to access the database via psql, we could also use `docker-compose` for this:
```sh
$ docker-compose exec web-db psql -U postgres
```

# Toirtoise ORM

Tortoise ORM is an async ORM inspired by Django ORM that's designed for ease of use.

Tortoise ORM was built with relations in mind and admiration for the excellent and popular Django ORM.

## Setting UP

After install `tortoise-orm`, we create a new folder called `models/` within `app/`. Within this, we have:

```
app/models
├── __init__.py
└── tortoise.py
```

## Defining the model

```py
# tortoise.py

from tortoise import fields, models


class TextSummary(models.Model):
    url = fields.TextField()
    summary = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.url
```

Here we defined a database model named `TextSummary` with a few fields. The syntax is very similar to Django ORM, I felt right at home.

## Registering `tortoise`

Tortoise ORM has a lightweight integration util `tortoise.contrib.fastapi` that has one single function `register_tortoise` which sets up TortoiseORM on startupand cleans up on teardown.

```python
# project/app/main.py

from fastapi import FastAPI, Depends
from app.config import get_settings, Settings
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI()


register_tortoise(
    app,
    db_url=os.environ.get('DATABASE_URL'),
    modules={'models': ['app.models.tortoise']},
    generate_schemas=True,
    add_exception_handlers=True
)

@app.get('/ping')
async def pong(settings: Settings=Depends(get_settings)):
    return {
        'ping': 'pong!',
        'environment': settings.environment,
        'testing': settings.testing
    }
```

## Fire up containers

After this, we can sanity check by:
```sh
$ docker-compose up -d --build
```

Then, we can check if the FastApi app is running fine:
```sh
$ docker-compose logs web
```
```
...
web_1     | INFO:     Started server process [30]
web_1     | INFO:     Waiting for application startup.
web_1     | INFO:     Application startup complete.
```

We can should also ensure that the `textsummary` table was created:
```sh
$ docker-compose exec web-db psql -U postgres
psql (13.4)
Type "help" for help.

postgres=# \c web_dev
You are now connected to database "web_dev" as user "postgres".
web_dev=# \dt
            List of relations
 Schema |    Name     | Type  |  Owner   
--------+-------------+-------+----------
 public | textsummary | table | postgres
(1 row)

web_dev=# \q
```

http://localhost:8004/ping should also continue to work.


# Migrations

Similarly to Django ORM with its own migration solution, Tortoise-ORM also has a database migration tool [Aerich](https://github.com/tortoise/aerich). We need to take a few steps back to configure it.

First, we need to bring down and remove the containers to destroy the current database table since we want Aerich to manage the schema.

## Kill the containers

We'll run the following:
```sh
$ docker-compose down -v
```

Why not `docker-compose stop`? `docker-compose stop` will stop the containers, but it will not remove them. `docker-compose down` stops the containers, and also removes the stopped containers as well as any networks that were created. The `-v` flag is on step further, it doesn't stand for `--verbose` but rather `--volume`, i.e remove all volumes too.

```
$ docker-compose down -v       
Stopping tdd-fastapi-docker_web_1    ... done
Stopping tdd-fastapi-docker_web-db_1 ... done
Removing tdd-fastapi-docker_web_1    ... done
Removing tdd-fastapi-docker_web-db_1 ... done
Removing network tdd-fastapi-docker_default
```

## Turn off schema auto-generation

After this, we need to update `register_tortoise` helper in `project/app/models.tortoise.py` so that the schemas are **not** automatically generated.
```py
register_tortoise(
    app,
    db_url=os.environ.get("DATABASE_URL"),
    modules={"models": ["app.models.tortoise"]},
    generate_schemas=False,
    add_exception_handlers=True,
)
```

Now, we can try spinning up the containers and volumes, and make sure that the table `textsummary` is **not** created automatically.

```sh
$ docker-compose exec web-db psql -U postgres
psql (13.4)
Type "help" for help.

postgres=# \c web_dev
You are now connected to database "web_dev" as user "postgres".
web_dev=# \dt
Did not find any relations.
web_dev=# \q
```

## Install and configure Aerich

```sh
$ poetry add aerich
Using version ^0.5.8 for aerich

Updating dependencies
Resolving dependencies... (1.5s)

Writing lock file

Package operations: 3 installs, 0 updates, 0 removals

  • Installing ddlparse (1.10.0)
  • Installing dictdiffer (0.9.0)
  • Installing aerich (0.5.8)
```

Then, update and fire up the containers
```sh
$ docker-compose up -d --build
```

We now need to configure Aerich. We'll do this in a new file called `project/app/db.py`
```py
import os

TORTOISE_ORM = {
    "connections": {"default": os.environ.get('DATABASE_URL')},
    "apps": {
        "models": {
            "models": ["app.models.tortoise", "aerich.models"],
            "default_connection": "default",
        },
    },
}
```

Now, we are ready to **init Aerich**:
```sh
$ docker-compose exec web aerich init -t app.db.TORTOISE_ORM
Success create migrate location ./migrations
Success generate config file aerich.ini
```

Adding the `-t` lets `aerich` to fire up using the Tortoise-ORM config module dict we created above. 

After the command ran, a new config file `aerich.ini` was created.
```ini
[aerich]
tortoise_orm = app.db.TORTOISE_ORM
location = ./migrations
src_folder = ./.
```

Then, we can create our first migration:
```sh
$ docker-compose exec web aerich init-db
Success create app migrate location migrations/models
Success generate schema for app "models"
```

Similarly to how migrations are managed within Django, the above command created a new folder `migrations/models` within `project/`, with a migration file inside it `0_20210913132135_init.sql`:
```sql
-- upgrade --
CREATE TABLE IF NOT EXISTS "textsummary" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "url" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
```

Hooray! We should now see the new database tables within our Postgres DB:
```sh
$ docker-compose exec web-db psql -U postgres
psql (13.4)
Type "help" for help.

postgres=# \c web_dev
You are now connected to database "web_dev" as user "postgres".
web_dev=# \dt
            List of relations
 Schema |    Name     | Type  |  Owner   
--------+-------------+-------+----------
 public | aerich      | table | postgres
 public | textsummary | table | postgres
(2 rows)

web_dev=# \q
```

# Pytest

## Setup

`pytest` is a framework that makes building simple and scalable tests easy. Tests are expressive and read-able, no boilerplate code is required. We can get started in minutes with a small unit test, or even a complex functional test for our application.

```sh
$ mkdir project/tests
$ touch project/tests/{__init__.py,conftest.py,test_ping.py}
```

By default, `pytest` will **auto-discover** test files that start or end with `test` e.g `test_*.py` or `*_test.py`. Test functions must also begin with `test_`, and if we want to use class-based they must begin with `Test`.

## Setting up Fixtures

We need to define a `test_app` fixture in `conftest.py`.

**What are Fixtures?** 

A fixture provides a defined, reliable and consistent context for the test. This could include environment (e.g database) or content (i.e dataset). Fixtures define the steps and data that constitute the *arrange* phase of a test (see [Anatomy of a test](#anatomy-of-a-test)). They can also be used to defined a test's *act* phase.

The services, state, or other operating environments set up by fixtures are accessed by test functions through arguments. For each fixture used by a test function, there is typically a parameter (named after the fixture) in the test function's definition.

More about fixtures: [All You Need to Know to Start Using Fixtures in Your pytest Code](https://pybit.es/articles/pytest-fixtures/)

```py
# project/tests/conftest.py


```

Here, we imported `TestClient` from `starlette`. This allows us to make requests against our ASGI application, using the `requests` library. The test client exposts the same interface as any other `requests` session. By default, `TestClient` will raise any exceptions that occur in the application. In the occasions that we want to test the content of the 500 error messages rather than allowing the client to raise the exception, we can do `client = TestClient(app, raise_server_exceptions=False)`.

Then, we override the dependencies using the `dependency_overrides` attribute. We do this by putting the original dependency `get_setting` as a key and as a value, the dependency override `get_settings_override`.

Fixtures are reusable objects for tests. Fixtures that require network access depend on connectivity and are usually time-expensive to create. Therefore, we can add a scope parameter to configure how often a fixture is invoked:
1. function = once per test function (default)
2. class - once per test class
3. module - once per test module
4. session - once per test session

Within the `test_app` fixture, all code before the `yield` statement serves as **setup code**, whilst everything after serves as **teardown**. *([Fixture finalization / executing teardown code](https://docs.pytest.org/en/latest/explanation/fixtures.html#improvements-over-xunit-style-setup-teardown-functions))*

## Fire up

We also need to
```sh
$ poetry add pytest requests
```

Then, the docker images needs to be rebuilt:
```sh
$ docker-compose up -d --build
```

With the containers up and running, we can run the test:
```py
============================ test session starts ============================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 0 items                                                           

=========================== no tests ran in 0.01s ===========================
```

We have no test, so this is expected.

## Writing Tests

Let's add a quick test to `test_ping.py`
```py
from app import main


def test_ping(test_app):
    response = test_app.get('ping')
    assert response.status_code == 200
    assert response.json() == {
        'environment': 'dev',
        'ping': 'pong!',
        'testing': True    
    }
```

This is the beauty of `pytest` - simplicty. Unlike `unittest` where we need to import modules, create a class and define testing functions within that class, we simply need to write the testing function.

In order to use the fixture that we created in the previous step, we simply needed to pass it in as an argument.

Let's run the test again:
```sh
$ docker-compose exec web python -m pytest
============================ test session starts ============================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 1 item                                                            

tests/test_ping.py .                                                  [100%]

============================= 1 passed in 0.13s =============================
```

## How to write tests

When writing tests, we should try to follow the [GivenWhenThen](#givenwhenthen) pattern to help make the process of writing tests easier and faster.

Using this pattern also helps communicate the purpose of our tests better so that the code is easier to read by our future self, as well as our colleagues.

# Others

## Anatomy of a test

In the simplest terms, a test is meant to look at the result of a particular behaviour and **make sure that the result aligns with our expectation**. 

**Behaviour** is the way in which some system **acts in response** to a particular situation and/or stimuli. The most important thing is *what* was done, not *how* or *why*.

The challenging part of writing a test is the fact that behaviour isn't something that can be empirically measured.

A test can be broken down into four steps:
1. **Arrange**

    This is where we prepare the **context** for our test. In this step we line up the dominoes so that the next step **act** can do its thing in one, state-changing step. This can mean a range of things including preparing objects, starting/killing services, entering records into a database, or even things like defining a URL to query, generating some credentials for a user that doesn't exist or just simply waiting for some process to finish.

2. **Act**

    This is a singular, state-changing action that kicks off the **behaviour** we want to test. This behaviour is what carries out the changing of the state of the **system under test** (SUT). It is the resulting changed state that we look at to make a judgement about the behaviour. This is normally a function/method call.

3. **Assert**

    This is where we look at the resulting state and check if it looks how we'd expect after the dust has settled. In this step, we gather evidence to stay the behaviour does/ does not align with our expectation. For example, if something is expected to be green, we do `assert thing == 'green'`

4. **Cleanup**

    This is where the test picks up after itself so that the other tests aren't influenced by it.

At its heart, the test is ultimately the **act** and **assert** steps. The **behaviour** exists between **act** and **assert**.

## GivenWhenThen

Given-When-Then is a style of representing test to specify the behaviours of a system using Specifications By Example. It was developed as part of Behaviour-Driven-Development (BDD). It appears as a structuring approach of many testing frameworks. One can look at it as a **reformulation of the Four-Phase Test Pattern** above.

The essential idea is to break down writing a test (scenario) into **three** main sections:
- The **given** part describes the state of the world before we begin the behaviour we are specifying in this scenario. We can think of it as the **pre-conditions** to the test.
- The **when** section is that behaviour we are specifying.
- The **then** section describes the changes we expect due to the specified behaviour.

| **State** | **Explanation** | **Code** |
| :----: | :---: | :----: |
| Given | the state of the application before the test runs | setup code, fixtures, database state | 
| When | the behaviour/logic being tested | code under test |
| Then | the expected changes based on the behaviour | asserts |

Example:
```
Feature: User trading stocks
  Scenario: User requests a sell before close of trading
    Given I have 100 shares of MSFT stock
      And I have 150 shares of APPL stock
      And the time is before close of trading
    
    When I ask to sell 20 shares of MSFT stock
      
    Then I should have 80 shares of MSFT stock
     And I should have 150 shares of APPL stock
     And a sell order for 20 shares of MSFT stock should have been created and executed
```