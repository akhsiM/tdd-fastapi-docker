# Test-Driven Development with FastAPI and Docker

![Continuous Integration and Delivery](https://github.com/akhsim/tdd-fastapi-docker/workflows/Continuous%20Integration%20and%20Delivery/badge.svg?branch=main)

- [Test-Driven Development with FastAPI and Docker](#test-driven-development-with-fastapi-and-docker)
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
- [App Structure and Refactoring](#app-structure-and-refactoring)
  - [`APIRouter`](#apirouter)
  - [New Project Structure](#new-project-structure)
- [Database Init](#database-init)
- [Generate schema instead of using `aerich` (situational)](#generate-schema-instead-of-using-aerich-situational)
- [Using `aerich` instead](#using-aerich-instead)
- [Pydantic Model](#pydantic-model)
- [RESTful Routes using TDD](#restful-routes-using-tdd)
  - [POST Route](#post-route)
    - [Code](#code)
    - [Trying out the route with HTTPie](#trying-out-the-route-with-httpie)
  - [Testing](#testing)
  - [GET single summary Route](#get-single-summary-route)
  - [GET all summaries Route](#get-all-summaries-route)
  - [Selecting Tests](#selecting-tests)
- [Deployment](#deployment)
  - [Gunicorn and `Dockerfile.prod`](#gunicorn-and-dockerfileprod)
  - [Heroku](#heroku)
  - [Checking logs](#checking-logs)
  - [Running Migration](#running-migration)
  - [Sending a POST request](#sending-a-post-request)
- [Code Coverage and Quality](#code-coverage-and-quality)
  - [Code Coverage](#code-coverage)
  - [Code Quality](#code-quality)
- [Continuous Integration](#continuous-integration)
  - [GitHub Packages](#github-packages)
  - [GitHub Actions](#github-actions)
- [Continuous Delivery](#continuous-delivery)
- [Remaining Routes](#remaining-routes)
  - [DELETE route](#delete-route)
  - [PUT route](#put-route)
  - [Additional Validation](#additional-validation)
    - [GET](#get)
    - [POST](#post)
    - [PUT](#put)
    - [DELETE](#delete)
- [Parameterizing Test Functions](#parameterizing-test-functions)
- [Tests](#tests)
- [Pytest Monkeypatching](#pytest-monkeypatching)
  - [Unit Tests](#unit-tests)
    - [Add Summary](#add-summary)
    - [Get Summary](#get-summary)
    - [Remove Summary](#remove-summary)
    - [Update Summary](#update-summary)
    - [Tests](#tests-1)
    - [Running tests in Parallel](#running-tests-in-parallel)
- [Text Summarization](#text-summarization)
  - [Background Task](#background-task)
  - [Tests](#tests-2)
- [Advanced CI](#advanced-ci)
  - [Multistage Docker Build](#multistage-docker-build)
  - [Docker Caching](#docker-caching)
  - [Seperate Requirements](#seperate-requirements)
- [Others](#others)
  - [Anatomy of a test](#anatomy-of-a-test)
  - [GivenWhenThen](#givenwhenthen)
  - [`pytest` commands](#pytest-commands)

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

# App Structure and Refactoring

This is the current structure of our project:
```
├── docker-compose.yml
├── project
│   ├── aerich.ini
│   ├── app
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models
│   ├── db
│   │   ├── create.sql
│   │   └── Dockerfile
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── migrations
│   │   └── models
│   ├── poetry.lock
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── tests
│       ├── conftest.py
│       ├── __init__.py
│       └── test_ping.py
└── README.md
```

Now we are refactoring the app, adding in FastAPI's `APIRouter`, a new database function and a Pydantic `Model`.

## `APIRouter`

`APIRouter` can be thought of as "mini `FastAPI`" class, with all the same options supported. `APIRouter` are used to break apart our api into different routes.

```sh
$ mkdir project/app/api
$ touch project/app/api/__init__.py
```

Then, we move the logic for `/ping` route to `api/ping.py`:
```py
# project/app/api/ping.py
from fastapi import APIRouter, Depends
from app.config import get_settings, Settings


router = APIRouter()


@router.get('/ping')
async def pong(settings: Settings=Depends(get_settings)):
    return {
        'ping': 'pong!',
        'environment': settings.environment,
        'testing': settings.testing
    }
```

The view fucntion is exactly the same as that in the `main.py` file. Now, we come back to this file to remove the old route and wire the router up to the main app, and use a function to initialize a new app:
```py
# project/app/main.py
import os
from fastapi import FastAPI, Depends
from tortoise.contrib.fastapi import register_tortoise
from app.api import ping


app = FastAPI()


def create_application() -> FastAPI:
    application = FastAPI()

    register_tortoise(
        app,
        db_url=os.environ.get("DATABASE_URL"),
        modules={"models": ["app.models.tortoise"]},
        generate_schemas=False,
        add_exception_handlers=True,
    )

    application.include_router(ping.router)

    return application


app = create_application()
```

After this, we should make sure that http://localhost:8004/ping and http://localhost:8004/docs still work.

We also need to update the `test_app` fixture in `project/tests/conftest.py` to use the newly created `create_application` function to create a new instance of FastAPI for testing purposes:
```py
#project/tests/conftest.py
import os 
import pytest
from starlette.testclient import TestClient
from app.main import create_application
from app.config import get_settings, Settings


def get_settings_override():
    return Settings(testing=1, database_url=os.environ.get('DATABASE_TEST_URL'))


@pytest.fixture(scope='module')
def test_app():
    # setup
    app = create_application()
    main.app.dependency_overrides[get_settings] = get_settings_override
    with TestClient(app) as test_client:
        #testing
        yield test_client
    
    # teardown
```

Our test should still work:
```sh
$ docker-compose exec web python -m pytest
============================ test session starts ============================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 1 item                                                            

tests/test_ping.py .                                                  [100%]

============================= 1 passed in 0.10s =============================
```

## New Project Structure

```
├── docker-compose.yml
├── project
│   ├── aerich.ini
│   ├── app
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   └── ping.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   └── tortoise.py
│   │   └── __pycache__
│   │       ├── config.cpython-39.pyc
│   │       ├── __init__.cpython-39.pyc
│   │       └── main.cpython-39.pyc
│   ├── db
│   │   ├── create.sql
│   │   └── Dockerfile
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── migrations
│   │   └── models
│   │       └── 0_20210913132135_init.sql
│   ├── poetry.lock
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── tests
│       ├── conftest.py
│       ├── __init__.py
│       └── test_ping.py
└── README.md
```

# Database Init

Let's continue to clean up `project/app/main.py` by moving `register_tortoise` helper to `project/app/db.py`.

```py
#project/app/db.py
import os
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise


TORTOISE_ORM = {
    "connections": {"default": os.environ.get('DATABASE_URL')},
    "apps": {
        "models": {
            "models": ["app.models.tortoise", "aerich.models"],
            "default_connection": "default",
        },
    },
}


def init_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        db_url=os.environ.get("DATABASE_URL"),
        modules={"models": ["app.models.tortoise"]},
        generate_schemas=False,
        add_exception_handlers=True,
    )
```

```py
# project/app/main.py
import os
from fastapi import FastAPI, Depends
from tortoise.contrib.fastapi import register_tortoise
from app.api import ping
from app.db import init_db


log = logging.getLogger('uvicorn')

def create_application() -> FastAPI:
    application = FastAPI()
    application.include_router(ping.router)

    return application


app = create_application()


@app.on_event('startup')
async def startup_event():
    log.info('App starting up...')
    init_db(app)


@app.on_event('shutdown')
async def shutdown_event():
    log.info('App shutting down...')
```

What we have done here is adding the `startup` and `shutdown` event handlers. These are functions that are executed before the app starts up and when the app is shutting down respectively.

To test, we bring the containers and volumes down, then bring them back up:`
```sh
$ docker-compose down -v
$ docker-compose up -d --build
```

At this stage, with the brand new containers being fired up, we shouldn't see any tables in the database:
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

# Generate schema instead of using `aerich` (situational)

Instead of applying the migration via Aerich, which can be slow at times, there are scenarios where we just want to apply the schema to the database in its final desired state.

To do this, we add a `generate_schema` fucntion to `db.py`:
```py
# project/app/db.py
import os, logging
from fastapi import FastAPI
from tortoise import Tortoise, run_async
from tortoise.contrib.fastapi import register_tortoise


log = logging.getLogger('uvicorn')


TORTOISE_ORM = {
    "connections": {"default": os.environ.get('DATABASE_URL')},
    "apps": {
        "models": {
            "models": ["app.models.tortoise", "aerich.models"],
            "default_connection": "default",
        },
    },
}


def init_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        db_url=os.environ.get("DATABASE_URL"),
        modules={"models": ["app.models.tortoise"]},
        generate_schemas=False,
        add_exception_handlers=True,
    )


async def generate_schema() -> None:
    log.info('Initializing Tortoise...')

    await Tortoise.init(
        db_url=os.environ.get('DATABASE_URL'),
        modules={'models': ['models.tortoise']},
    )

    log.info("Generating Database schema via Tortoise...")

    await Tortoise.generate_schemas()
    await Tortoise.close_connecetions()


if __name__ == '__main__':
    run_async(generate_schema())
```

What happens here is `generate_schema` calls `Tortoise.init` to set up Tortoise, and then generates the schema.

The `Tortoise.generate_schemas()` call generates schemas according to models provided to the `init()` method.

Note how the `models` key provided within `register_tortoise` have the full name from with `app.`, however the one within `Tortoise.init()` only has `models.tortoise`.

Now, we can run this:
```sh
$ docker-compose exec web python app/db.py
```

Then check to see the schema:
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

# Using `aerich` instead

Since we do actually want to use `aerich` to manage database schema, we need to:

```sh
$ docker-compose down -v 
Stopping tdd-fastapi-docker_web_1    ... done
Stopping tdd-fastapi-docker_web-db_1 ... done
Removing tdd-fastapi-docker_web_1    ... done
Removing tdd-fastapi-docker_web-db_1 ... done
Removing network tdd-fastapi-docker_default

$ docker-compose up -d --build
...
Creating tdd-fastapi-docker_web-db_1 ... done
Creating tdd-fastapi-docker_web_1    ... done

Ⓜ mygit/tdd-fastapi-docker/project  main ✗                           23m ⚑  
$ docker-compose exec web aerich upgrade
Success upgrade 0_20210913132135_init.sql
```

# Pydantic Model

In addition to the Tortoise-ORM models, we'll also implement some Pydantic models. We'll create a simple model with just one required field - a `url`.
```py
# app/models/pydantic.py

from pydantic import BaseModel


class SummaryPayloadSchema(BaseModel):
    url: str
```

# RESTful Routes using TDD

Now, let's move on to setting up three new routes, following RESTful best practices with TDD:

| Endpoint | HTTP Method | CRUD Method | Result |
| :------ | :--------- | :--------- | :----- |
| /summaries | GET | READ | Get all summaries |
| /summaries/:id | GET | READ | Get a single summary |
| /summaries | POST | CREATE | Add a summary |

The steps that we are going to go through for each of these routes are:
1. Write a test
2. Run the test, ensure it fails
3. Write just enough code to get the test to pass
4. refactor (if needed)

## POST Route

Let's start with the POST route.

For this first route, we are going to break the normal TDD workflow in order to establish the coding pattern that we will use for the remaining routes.

### Code

```py
# project/app/api/summaries.py

from fastapi import APIRouter, HTTPException
from app.api import crud
from app.models.pydantic import SummaryPayloadSchema, SummaryResponseSchema


router = APIRouter()


@router.post('/', response_model=SummaryResponseSchema, status_code=201)
async def create_summary(payload: SummaryPayloadSchema) -> SummaryResponseSchema:
    summary_id = await crud.post(payload)

    response_object = {
        'id': summary_id,
        'url': payload.url
    }
    return response_object
```

What we have done here is:
- Defined a handler `create_summary` that accepts a payload of type `SummaryPayloadSchema` with a URL. Essentially, when the route is hit with a POST request, FastAPI will read the body of the request and validate the data.
- If the data is valid, the data will be available in the payload `parameter`. FastAPI also generates [JSON Schema](https://json-schema.org/) definitions that are used to automatically generate the OpenAPI schema and the API Documentation.
- If the data is not valid, an error is immediately returned.
- Here, we used the `async` declaration since the database communication will be asynchronous. With this, there are no blocking I/O operations in the handler.

Next, we move on to create the `crud.py` module in the `project/app/api` folder:
```py
# project/app/api/crud.py

from app.models.pydantic import SummaryPayloadSchema
from app.models.tortoise import TextSummary


async def post(payload: SummaryPayloadSchema) -> int:
    summary = TextSummary(
        url=payload.url,
        summary='dummy summary'
    )
    await summary.save()
    return summary.id
```

What we have done here is that we added a utility function called `post` for the creation of new summaries that takes a payload object, create a new `TextSummary` instance and returns the newly generated ID.

Next, we need to define a new Pydantic model to be used as the `response_model`:`
```py
@router.post('/', response_model=SummaryResponseSchema, status_code=201)
```

```py
# project/app/models/pydantic.py

from pydantic import BaseModel


class SummaryPayloadSchema(BaseModel):
    url: str


class SummaryResponseSchema(SummaryPayloadSchema):
    id: int
```

The newly created `SummaryResponseSchema` just inherits from the `SummaryPayloadSchema` model with the addition of a new `id` field.

With all of the components finished, we now need to write this new POST route with a new router in `main.py`.
```py
import logging
from fastapi import FastAPI, Depends
from tortoise.contrib.fastapi import register_tortoise
from app.api import ping, summaries
from app.db import init_db


log = logging.getLogger('uvicorn')

def create_application() -> FastAPI:
    application = FastAPI()
    application.include_router(ping.router)
    application.include_router(summaries.router, prefix='/summaries', tags=['summaries'])

    return application


app = create_application()


@app.on_event('startup')
async def startup_event():
    log.info('App starting up...')
    init_db(app)


@app.on_event('shutdown')
async def shutdown_event():
    log.info('App shutting down...')
```

The prefix URL and the tags will be applied to the OpenAPI schema for grouping operations.

### Trying out the route with HTTPie

```sh
$ http --json POST http://localhost:8004/summaries/ url=http://testdriven.io
HTTP/1.1 201 Created
content-length: 37
content-type: application/json
date: Fri, 17 Sep 2021 06:55:30 GMT
server: uvicorn

{
    "id": 1,
    "url": "http://testdriven.io"
}

```

You can also interact with the API via http://localhost:8004/docs/:
![](./code_img/README-2021-09-17-17-01-42.png)

## Testing

```sh
$ touch tests/test_summaries.py
```

```py
# project/tests/test_summaries.py
import json, pytest


def test_create_summary(test_app_with_db):

    url = 'http://foo.bar/'

    response = test_app_with_db.post(
        '/summaries/', data=json.dumps(
            {'url': url}
        )
    )

    assert response.status_code == 201
    assert response.json()['url'] == url
```

We now need to add the fixture `test_app_with_db` to `conftest.py`:
```py
# project/tests/conftest.py
...
from tortoise.contrib.fastapi import register_tortoise
...
@pytest.fixture(scope='module')
def test_app_with_db():
    app = create_application()
    app.dependency_overrides[get_settings] = get_settings_override
    register_tortoise(
        app,
        db_url=os.environ.get('DATABASE_TEST_URL'),
        modules={'models': ['app.models.tortoise']},
        generate_schemas=True,
        add_exception_handles=True
    )
    with TestClient(app) as test_client:
        
        # testing

        yield test_client

    #tear down
```

We can now run te test:
```sh
$ docker-compose exec web python -m pytest                                  
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 2 items                                                                                                

tests/test_ping.py .                                                                                       [ 50%]
tests/test_summaries.py .                                                                                  [100%]

=============================================== 2 passed in 0.13s ================================================
```

This test covers the happy path, if the payload matches `SummaryPayloadSchema`. We can also do the test for exception path.

If we send a POST request with an empty payload to `/summaries/`, we'd see this:
```sh
$ http --json POST http://localhost:8004/summaries/                         
HTTP/1.1 422 Unprocessable Entity
content-length: 81
content-type: application/json
date: Sun, 19 Sep 2021 14:03:16 GMT
server: uvicorn

{
    "detail": [
        {
            "loc": [
                "body"
            ],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}

```

So, let's build our test:
```py
# project/tests/text_summaries.py

...

def test_create_summary_invalid_json(test_app):
    response = test_app.post('/summaries/', data=json.dumps({}))

    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'url'],
                'msg': 'field required',
                'type': 'value_error.missing'
            }
        ]
    }
```
```sh
$ docker-compose exec web python -m pytest
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 3 items                                                                                                

tests/test_ping.py .                                                                                       [ 33%]
tests/test_summaries.py ..                                                                                 [100%]

=============================================== 3 passed in 0.13s ================================================
```

With this first route, we can move on to creating other routes.

## GET single summary Route

For this, we'll start to apply TDD and **start with a test first**.

```py
# project/tests/test_summaries

def test_read_summary(test_app_with_db):
    response = test_app_with_db.post('/summaries/', data=json.dumps({
        'url': 'http://foo.bar/'
    }))

    summary_id = response.json()['id']

    response = test_app_with_db.get(f'/summaries/{summary_id}/')
    assert response.status_code == 200

    response_dict = response.json()

    assert response_dict['id'] == summary_id
    assert response_dict['url'] == 'http://foo.bar/'
    assert response_dict['summary']
    assert response_dict['created_at']
```

The test should fail, as we haven't written the route yet:
```sh
$ docker-compose exec web python -m pytest
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 4 items                                                                                                

tests/test_ping.py .                                                                                       [ 25%]
tests/test_summaries.py ..F                                                                                [100%]

==================================================== FAILURES ====================================================
_______________________________________________ test_read_summary ________________________________________________

test_app_with_db = <starlette.testclient.TestClient object at 0x7fac2f44df40>

    def test_read_summary(test_app_with_db):
        response = test_app_with_db.post('/summaries/', data=json.dumps({
            'url': 'http://foo.bar/'
        }))
    
        summary_id = response.json()['id']
    
        response = test_app_with_db.get(f'/summaries/{summary_id}/')
>       assert response.status_code == 200
E       assert 404 == 200
E        +  where 404 = <Response [404]>.status_code

tests/test_summaries.py:40: AssertionError
============================================ short test summary info =============================================
FAILED tests/test_summaries.py::test_read_summary - assert 404 == 200
========================================== 1 failed, 3 passed in 0.18s ===========================================
```

Let's add the route handler now:
```py
# project/app/api/summaries.py

...

@router.get('/{id}/', response_model=SummarySchema)
async def read_summary(id: int) -> SummarySchema:
    summary = await crud.get(id)

    return summary
```

Here, instead of taking a payload, we configure the URL to accept an integer parameter `{id}` instead. This is just Python f-string syntax. The `id` will come from the path, i.e `/summaries/` 

We also need to add `get()` utility function to `crud.py`.
```py
# project/app/api/crud.py
...
from typing import Union

...

async def get(id: int) -> Union[dict, None]:
    summary = await TextSummary.filter(id=id).first().values()
    if summary:
        return summary[0]
    return None
```

Here we use the `values()` method to create a [`ValuesQuery`](https://tortoise-orm.readthedocs.io/en/latest/query.html?highlight=values#tortoise.queryset.ValuesQuery) object. This is similar to Django ORM syntax.

`Union[dict, None]` is equivalent to `Optional[dict]`.


Last but not least, we need to update `project/app/models/tortoise.py` to generate a Pydantic Model from the Tortoise Model. This is the `SummarySchema` that we use for `response_model` in `read_summary`.
```py
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

...

SummarySchema = pydantic_model_creator(TextSummary)
```

..Ensure the test passes:

```sh
$ docker-compose exec web python -m pytest
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 4 items                                                                                                

tests/test_ping.py .                                                                                       [ 25%]
tests/test_summaries.py ...                                                                                [100%]

=============================================== 4 passed in 0.14s ================================================
```

What if the summary ID doesn't exist?
```py
def test_read_summary_incorrect_id(test_app_with_db):
    response = test_app_with_db.get('/summaries/999999999/')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'
```

This test should fail, because in our `read_summary` handler, we call the utility `get()` method, which returns a `None` object even if the summary doesn't exist. The response would still be a `200`, not `404`.

```sh
$ docker-compose exec web python -m pytest             
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 5 items                                                                                                

tests/test_ping.py .                                                                                       [ 20%]
tests/test_summaries.py ...F                                                                               [100%]

==================================================== FAILURES ====================================================
_________________________________________ test_read_summary_incorrect_id _________________________________________

test_app_with_db = <starlette.testclient.TestClient object at 0x7f4aafe59b50>

    def test_read_summary_incorrect_id(test_app_with_db):
        response = test_app_with_db.get('/summaries/999999999/')
    
>       assert response.status_code == 404
E       assert 200 == 404
E        +  where 200 = <Response [200]>.status_code

tests/test_summaries.py:53: AssertionError
============================================ short test summary info =============================================
FAILED tests/test_summaries.py::test_read_summary_incorrect_id - assert 200 == 404
========================================== 1 failed, 4 passed in 0.20s ===========================================
```

So, we need to update the handler so that incorrect id are handled appropriately:
```py
@router.get('/{id}/', response_model=SummarySchema)
async def read_summary(id: int) -> SummarySchema:
    summary = await crud.get(id)

    if not summary:
        raise HTTPException(status_code=404, detail='Summary not found')

    return summary
```

The test should now pass:
```sh
$ docker-compose exec web python -m pytest
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 5 items                                                                                                

tests/test_ping.py .                                                                                       [ 20%]
tests/test_summaries.py ....                                                                               [100%]

=============================================== 5 passed in 0.15s ================================================
```

## GET all summaries Route

Following TDD, we first start with a test:
```py
def test_read_all_summaries(test_app_with_db):
    response = test_app_with_db.post('/summaries/', data=json.dumps({
        'url': 'http://foo.bar/'
    }))

    summary_id = response.json()['id']

    response = test_app_with_db.get('/summaries/')
    assert response.status_code == 200

    response_list = response.json()
    assert (len(list(filter(lambda d: d['id'] == summary_id, response_list)))) == 1
```

The test should fail:
```sh
$ docker-compose exec web python -m pytest
...
E       assert 405 == 200
E        +  where 405 = <Response [405]>.status_code
...
```

We add the handler:
```py
# project/app/api/summaries.py
...
from typing import List
...
@router.get('/', response_model=List[SummarySchema])
async def read_all_summaries() -> List[SummarySchema]:
    return await crud.get_all()
```

Here, the `response_model` is a List of `SummarySchema` subtype.

Then, the `get_all()` utility function:
```py
async def get_all() -> List:
    summaries = await TextSummary.all().values()
    return summaries
```

The test should pass now:
```sh
$ docker-compose exec web python -m pytest
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 6 items                                                                                                

tests/test_ping.py .                                                                                       [ 16%]
tests/test_summaries.py .....                                                                              [100%]

=============================================== 6 passed in 0.17s ================================================
```

## Selecting Tests

We can also select specific tests to run using substring matching. *([More here](https://docs.pytest.org/en/latest/how-to/usage.html#specifying-tests-selecting-tests))*

```sh
$ docker-compose exec web python -m pytest -k ping
============================================== test session starts ===============================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
collected 6 items / 5 deselected / 1 selected                                                                    

tests/test_ping.py .                                                                                       [100%]

======================================== 1 passed, 5 deselected in 0.11s =========================================
```

# Deployment

## Gunicorn and `Dockerfile.prod`

Now that we have our routes up and tested, let's move on to getting this app deployed to Heroku.

We are going to be using both **Gunicorn**, a production-grade WSGI server, and Uvicorn, in order to get the best of both worlds - concurrency and parallelism. Gunicorn will be responsible for managing multiple, concurrent Uvicorn processes.

Uvicorn includes a Gunicorn worker class. This means we can set up with very little configuration. 

```sh
$ poetry add gunicorn
```

Then, we are going to be adding a new Dockerfile `Dockerfile.prod`
```dockerfile
FROM python:3.9.6-slim-buster

RUN mkdir -p /home/app

RUN addgroup --system app && adduser --system --group app

ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

ENV PYTHONBUFFERRED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV ENVIRONMENT prod
ENV TESTING 0

RUN apt-get update\
 && apt-get -y install netcat gcc postgresql \
 && apt-get clean

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN pip install "uvicorn[standard]==0.14.0"
```

The difference between `Dockerfile.prod` and `Dockerfile`:
- We started with using a Python 3.8.11 image rather than 3.9.6 because `uvloop`, used by `uvicorn.workers.UvicornWorker`, doesn't support Python 3.9 yet.
- Next, we added a `CMD` to run Gunicorn with a uvicorn worker class with two configured environment variables: `ENVIRONMENT=prod` and `TESTING=0`.
- We also created and switched a non-root user, which is good pratice ([recommended by Heroku](https://devcenter.heroku.com/articles/container-registry-and-runtime#run-the-image-as-a-non-root-user))
  
## Heroku

First, we need to sign up for Heroku, if we don't have an account, then install Heroku CLI.

Create a new app
```sh
$ heroku create
```

Login to Heroku Container Registry, which allows us to deploy Docker images to Heroku.
```sh
$ heroku container:login
```

Provision a new Postgres database with the [`hobby-dev`](https://devcenter.heroku.com/articles/heroku-postgres-plans#hobby-tier) plan tier.
```sh
$ heroku addons:create heroku-postgresql:hobby-dev --app pure-depths-94465
Creating heroku-postgresql:hobby-dev on ⬢ pure-depths-94465... free
Database has been created and is available
 ! This database is empty. If upgrading, you can transfer
 ! data from another database with pg:copy
Created postgresql-regular-26847 as DATABASE_URL
Use heroku addons:docs heroku-postgresql to view documentation
```
![](./code_img/README-2021-09-24-17-34-17.png)

Build the production image and tag it with the following format. We need to replace `<app>` with the name of the Heroku app that we just created. The `<process-type>` needs to replaced with `web` since it will just be a [web dyno](https://www.heroku.com/dynos).
```
registry.heroku.com/<app>/<process-type>
```

```sh
$ docker build -f project/Dockerfile.prod -t registry.heroku.com/pure-depths-94465/web ./project
```

We can test this production image locally by spinning it up:
```sh
docker run --name fastapi-tdd -e PORT=8765 -e DATABASE_URL=sqlite://sqlite.db -p 5003:8765 registry.heroku.com/pure-depths-94465/web:latest
```

With this container running, we can navigate to http://localhost:5003/ping and verify that the server is OK.
```json
{
  "ping": "pong!",
  "environment": "prod",
  "testing": false
}
```

We can bring down the container by:
```sh
docker rm fastapi-tdd -f
```

Then, push the image to the registry:
```sh
$ docker push registry.heroku.com/pure-depths-94465/web:latest
```

After this, we need to release the image
```sh
$ heroku container:release web --app pure-depths-94465
Releasing images web to pure-depths-94465... done
```

This will run the container on Heroku server. We can now view the app at http://pure-depths-94465.herokuapp.com/ping/

## Checking logs

During this section, Heroku encountered a platform issues, during which my app was down. I could use `heroku` to check the logs of my application like so:

```sh
$ heroku logs --tail --app pure-depths-94465
```

## Running Migration

We can also apply the migrations using `heroku`:
```sh
$ heroku run aerich upgrade --app pure-depths-94465
Running aerich upgrade on ⬢ pure-depths-94465... up, run.8169 (Free)
Success upgrade 0_20210913132135_init.sql
```

## Sending a POST request

```sh
$ http --json POST https://pure-depths-94465.herokuapp.com/summaries/ url=https://hello.world
HTTP/1.1 201 Created
Connection: keep-alive
Content-Length: 36
Content-Type: application/json
Date: Mon, 27 Sep 2021 12:13:02 GMT
Server: uvicorn
Via: 1.1 vegur

{
    "id": 1,
    "url": "https://hello.world"
}
```

# Code Coverage and Quality

## Code Coverage

Code coverage is the measure of much code is executed during testing. By adding Code Coverage to our test suite, we can find out who much of our code is being tested, or areas of our code that aren't covered by tests.

For this, we will be using `pytest-cov`.
```py
$ poetry add pytest-cov==2.12.1
```

Next, we need to configure the coverage reports in a `.coveragerc` file.
```sh
# project/.coveragerc
[run]
omit = tests/*
branch = True
```

What we have done here is excluding the test from the coverage results, as well as enabling [branch coverage measurement](https://coverage.readthedocs.io/en/latest/branch.html).

After this, update the container:
```sh
docker-compose up -d --build
```

Then, we can run the tests with coverage:
```sh
docker-compose exec web python -m pytest --cov="."
```

```
=============================================================== test session starts ===============================================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
plugins: cov-2.12.1
collected 6 items                                                                                                                                 

tests/test_ping.py .                                                                                                                        [ 16%]
tests/test_summaries.py .....                                                                                                               [100%]

----------- coverage: platform linux, python 3.9.6-final-0 -----------
Name                     Stmts   Miss Branch BrPart  Cover
----------------------------------------------------------
app/__init__.py              0      0      0      0   100%
app/api/__init__.py          0      0      0      0   100%
app/api/crud.py             15      0      2      0   100%
app/api/ping.py              6      0      0      0   100%
app/api/summaries.py        20      0      2      0   100%
app/config.py               13      2      0      0    85%
app/db.py                   16      7      2      1    56%
app/main.py                 19      3      0      0    84%
app/models/__init__.py       0      0      0      0   100%
app/models/pydantic.py       5      0      0      0   100%
app/models/tortoise.py       9      1      0      0    89%
----------------------------------------------------------
TOTAL                      103     13      6      1    87%
```

We can also view a HTML version by:
```sh
docker-compose exec web python -m pytest --cov="." --cov-report html
```

The HTML export will be savewd in `project/htmlcov/`.

We also need to add this directory, along with a newly created `.coverage` file, to `.dockerignore` and `.gitignore`.

## Code Quality

Linting is the process of checking code for stylistic or programming error. There are a number of commonly used linters for Python. We'll use `flake8`.

```sh
$ poetry add flake8=3.9.2
$ poetry export > requirements.txt --without-hashes
```

We can also [configure](https://flake8.pycqa.org/en/latest/user/configuration.html) flake8 by adding `setup.cfg` to the project directory:
```
[flake8]
max-line-length = 119
```

Then, update the container and run flake8.
```sh
$ docker-compose up -d --build
$ docker-compose exec web flake8 .
```
```
./app/config.py:20:1: W391 blank line at end of file
./app/db.py:1:10: E401 multiple imports on one line
./app/db.py:46:33: W292 no newline at end of file
./app/main.py:2:1: F401 'fastapi.Depends' imported but unused
./app/main.py:3:1: F401 'tortoise.contrib.fastapi.register_tortoise' imported but unused
./app/main.py:10:1: E302 expected 2 blank lines, found 1
./app/main.py:13:80: E501 line too long (89 > 79 characters)
./app/main.py:29:37: W292 no newline at end of file
./app/api/ping.py:9:34: E252 missing whitespace around parameter equals
./app/api/ping.py:9:35: E252 missing whitespace around parameter equals
./app/api/ping.py:14:6: W292 no newline at end of file
./app/api/summaries.py:12:80: E501 line too long (81 > 79 characters)
./app/api/summaries.py:34:32: W292 no newline at end of file
./app/api/crud.py:24:21: W292 no newline at end of file
./app/models/tortoise.py:4:1: E302 expected 2 blank lines, found 1
./app/models/tortoise.py:13:52: W292 no newline at end of file
./app/models/pydantic.py:9:12: W292 no newline at end of file
./tests/conftest.py:1:10: E401 multiple imports on one line
./tests/conftest.py:9:80: E501 line too long (80 > 79 characters)
./tests/conftest.py:18:9: E265 block comment should start with '# '
./tests/conftest.py:20:1: W293 blank line contains whitespace
./tests/conftest.py:40:5: E265 block comment should start with '# '
./tests/conftest.py:40:15: W292 no newline at end of file
./tests/conftest.py:40:15: W292 no newline at end of file
./tests/conftest.py:40:15: W292 no newline at end of file
./tests/test_ping.py:1:1: F401 'app.main' imported but unused
./tests/test_ping.py:10:24: W291 trailing whitespace
./tests/test_ping.py:11:6: W292 no newline at end of file
./tests/test_summaries.py:1:1: F401 'pytest' imported but unused
./tests/test_summaries.py:1:12: E401 multiple imports on one line
./tests/test_summaries.py:68:80: E501 line too long (83 > 79 characters)
./tests/test_summaries.py:68:84: W292 no newline at end of file
```

We need to correct all of these errors, before moving on.

Next, we can also add `black`, which is used for formatting the code so that it all looks the same formatting. This helps to speed up code reviews. 

> Formatting becomes transparent after a while and you can focus on the content instead.

```sh
$ poetry add black
```

```sh
$ docker-compose up -d --build
$ docker-compose exec web black . --check
```
```
would reformat app/api/ping.py
would reformat app/config.py
would reformat app/api/crud.py
would reformat tests/test_ping.py
would reformat app/main.py
would reformat app/api/summaries.py
would reformat app/db.py
would reformat tests/conftest.py
would reformat tests/test_summaries.py
Oh no! 💥 💔 💥
9 files would be reformatted, 6 files would be left unchanged.
```

We can first run black with the `--diff` option then apply the changes like so:
```sh
$ docker-compose exec web black . --diff

$ docker-compose exec web black .
```

Finally, we can add `isort` to the project to quickly sort all our imports alphabetically and automatically seperate them into sections.

```sh
poetry add isort
docker-compose up --build -d
```

Then, run with `--check-only`, and `--diff` option.
```sh
$ docker-compose exec web isort . --check-only
ERROR: /usr/src/app/app/config.py Imports are incorrectly sorted and/or formatted.
ERROR: /usr/src/app/app/db.py Imports are incorrectly sorted and/or formatted.
ERROR: /usr/src/app/app/main.py Imports are incorrectly sorted and/or formatted.
ERROR: /usr/src/app/app/api/ping.py Imports are incorrectly sorted and/or formatted.
ERROR: /usr/src/app/app/api/summaries.py Imports are incorrectly sorted and/or formatted.
ERROR: /usr/src/app/app/api/crud.py Imports are incorrectly sorted and/or formatted.
ERROR: /usr/src/app/tests/conftest.py Imports are incorrectly sorted and/or formatted.
```

```sh
$ docker-compose exec web isort . --diff
--- /usr/src/app/app/config.py:before   2021-09-27 12:32:16.606145
+++ /usr/src/app/app/config.py:after    2021-09-27 12:47:26.834057
@@ -1,8 +1,8 @@
 import logging
 import os
 from functools import lru_cache
-from pydantic import BaseSettings, AnyUrl
 
+from pydantic import AnyUrl, BaseSettings
 
...
```

Then, the changes can actually be applied like so:
```sh
docker-compose exec web isort .
```

Lastly, we can verify one last time that `flake8`, `black` and `isort` are all happy.

```sh
$ docker-compose exec web flake8 .
$ docker-compose exec web black . --check
$ docker-compose exec web isort . --check-only
```

# Continuous Integration

Next, we will add CI via GitHub Actions, to our project. We are also going to set up GitHub Packages, a package management service, to store Docker images.

## GitHub Packages

GitHub Packages is a package management service that is fully integrated with GitHub. It allows us to host our software packages, publicly or privately for use within our projects on GitHub.

First, we need to create a Personal Access Token with the following scope:
```
write:packages
read:packages
delete:packages
workflow
```

Then we can build and tag the image like so:
```sh
$ docker build -f project/Dockerfile.prod -t docker.pkg.github.com/akhsim/tdd-fastapi-docker/summarizer:latest ./project
```

Next, we need to authenticate to GitHub Packages with Docker, using the access token we got previously.

```sh
$ docker login docker.pkg.github.com -u <USERNAME> -p <TOKEN>
```

After successful authentication, we can push the image to the Docker registry on GitHub Packages.
```sh
docker push docker.pkg.github.com/akhsim/tdd-fastapi-docker/summarizer:latest
```

After this, we should be able to see the package at: https://github.com/akhsim/tdd-fastapi-docker/packages
![](./code_img/README-2021-09-27-23-03-50.png)

## GitHub Actions

In order to configure GitHub Actions, we start by adding a new directory called `.github` in the root of our project.

Within this directory, we add another directory `workflows/`.

Now, to configure one workflow, which is made up of one or more job, we create a new file `workflows/main.yml`:
```yml
name: Continuous Integration and Delivery

on: [push]

env:
  IMAGE: docker.pkg.github.com/$(echo $GITHUB_REPOSITORY | tr '[A-Z]' '[a-z]')/summarizer

jobs:
  
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    steps:
      - name: Checkout main
        uses: actions/checkout@v2.3.4
      - name: Log in to GitHub Packages
        run: echo ${GITHUB_TOKEN} | docker login -u ${GITHUB_ACTOR} --password-stdin docker.pkg.github.com
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Pull Image
        run: | 
          docker pull ${{ env.IMAGE }}:latest || true
      - name: Build Image
        run: |
          docker build \
            --cache-from ${{ env.IMAGE }}:latest \
            --tag ${{ env.IMAGE }}:latest \
            --file ./project/Dockerfile.prod \
            "./project"
      - name: Push Image
        run: | 
          docker push ${{ env.IMAGE }}:latest
  
  test:
    name: Test Docker Image
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Checkout main
        uses: actions/checkout@v2.3.4
      - name: Log in to GitHub Packages
        run: echo ${GITHUB_TOKEN} | docker login -u ${GITHUB_ACTOR} --password-stdin docker.pkg.github.com
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Pull Image
        run: |
          docker pull ${{ env.IMAGE }}:latest || true
      - name: Build Image
        run: |
          docker build \
            --cache-from ${{ env.IMAGE }}:latest \
            --tag ${{ env.IMAGE }}:latest \
            --file ./project/Dockerfile.prod \
            "./project"
      - name: Run Container
        run: |
          docker run \
            -d \
            --name fastapi-tdd \
            -e PORT=8765 \
            -e ENVIRONMENT=dev \
            -e DATABASE_TEST_URL=sqlite://sqlite.db \
            -p 5003:8765 \
            ${{ env.IMAGE }}:latest
      - name: Pytest
        run: docker exec fastapi-tdd python -m pytest .
      - name: Flake8
        run: docker exec fastapi-tdd python -m flake8 .
      - name: Black
        run: docker exec fastapi-tdd python -m black . -S --check
      - name: isort
        run: docker exec fastapi-tdd python -m isort . --check-only
```

Here, after setting the global `IMAGE` environment variable, we define two jobs: `build` and `test`.

In the `build` job, we:
1. Check out the repository, so the job has access to the code base
2. Log in to GitHub Packages
3. Pull the image if it exists
4. Build the image
5. Push the image to GitHub Packages

Then, after building and running the image, in the `test` job we run `pytest`, `flake8`, `black` and `isort`.

After we commit, and push to GitHub, this should trigger a new build, which should pass.

# Continuous Delivery

First, we need to retrieve the [Heroku auth token](https://devcenter.heroku.com/articles/authentication):
```sh
heroku auth:token
```

Then, we need to save this token to a variable named `HEROKU_AUTH_TOKEN` within the repository secrets.

With this secret configured, we need to add a new `deploy` job to the GitHub config file:
```yml
...

  deploy:
    name: Deploy to Heroku
    runs-on: ubuntu-latest
    needs: [build, test]
    env:
      HEROKU_APP_NAME: pure-depths-94465
      HEROKU_REGISTRY_IMAGE: registry.heroku.com/pure-depths-94465/summarizer
    steps:
      - name: Checkout main
        uses: actions/checkout@v2.3.4
      - name: Log in to GitHub Packages
        run: echo ${GITHUB_TOKEN} | docker login -u ${GITHUB_ACTOR} --password-stdin docker.pkg.github.com
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Pull image
        run: | 
          docker pull ${{ env.IMAGE }}:latest || true
      - name: Build image
        run: |
          docker build \
            --cache-from ${{ env.IMAGE }}:latest \
            --tag ${{ env.HEROKU_REGISTRY_IMAGE }}:latest \
            --file ./project/Dockerfile.prod \
            "./project"
      - name: Log in to the Heroku Container Registry
        run: docker login -u _ -p ${HEROKU_AUTH_TOKEN} registry.heroku.com
        env:
          HEROKU_AUTH_TOKEN: ${{ secrets.HEROKU_AUTH_TOKEN }}
      - name: Push to Heroku Registry
        run: docker push ${{ env.HEROKU_REGISTRY_IMAGE }}
      - name: Set environment variables
        run: |
          echo "HEROKU_REGISTRY_IMAGE=${{ env.HEROKU_REGISTRY_IMAGE }}" >> $GITHUB_ENV
          echo "HEROKU_AUTH_TOKEN=${{ secrets.HEROKU_AUTH_TOKEN }}" >> $GITHUB_ENV
      - name: Release
        run: |
          chmod +x ./release.sh
          ./release.sh
```

We also need to add `release.sh` to project root:
```sh
#!/bin/sh

set -e

IMAGE_ID=$(docker inspect ${HEROKU_REGISTRY_IMAGE} --format={{.Id}})
PAYLOAD='{"updates": [{"type": "web", "docker_image": "'"$IMAGE_ID"'"}]}'

curl -n -X PATCH https://api.heroku.com/apps/$HEROKU_APP_NAME/formation \
    -d "${PAYLOAD}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/vnd.heroku+json; version=3.docker-releases" \
    -H "Authorization: Bearer ${HEROKU_AUTH_TOKEN}"
```

What we are doing in this `deploy` stage is:
1. Check out the repository so the job has access to the code base.
2. Log in to GitHub Packages
3. Pull the image if it exists
4. Build and tag the new image
5. Log in to Heroku Container Registry
6. Push the newly built image up to the registry
7. Set two environment variables `HEROKU_REGISTRY_IMAGE` and `HEROKU_AUTH_TOKEN` so that they can be used in `release.sh` file
8. Run `release.sh` to create a new release via the Heroku API using the image ID

After this, our app will be automatically deployed to Heroku whenever we push to GitHub!

# Remaining Routes

For the remaining routes which are DELETE and PUT route, we'll follow the same steps which are:
1. Write a test
2. Run the test, ensuring it fails
3. Write just enough code to get the test to pass
4. Refactor (if needed)

## DELETE route

First, we'll write the tests:
```py
# project/tests/test_summaries.py
...
def test_delete_summary(test_app_with_db):
    response = test_app_with_db.post(
        '/summaries/', data=json.dumps({'url': 'https://delete.me/'})
    )
    summary_id = response.json()['id']

    response = test_app_with_db.delete(f'/summaries/{summary_id}/')
    assert response.status_code == 200
    assert response.json() == {'id': summary_id, 'url': 'https://delete.me/'}


def test_delete_summary_incorrect_id(test_app_with_db):
    response = test_app_with_db.delete('/summaries/999999999/')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'
```

When we run `pytest` now, the new tests will both fail. We better start writing the route handler:
```py
# project/app/api/summaries.py
...
@router.delete('/{id}/', response_model=SummaryResponseSchema)
async def delete_summary(id: int) -> SummaryResponseSchma:
    summary = await crud.get(id)
    if not summary:
        raise HTTPException(status_code=404, detail='Summary not found')
    
    await crud.delete(id)
    return summary
```

We'd also need to add the `delete()` method to the `crud` utility.
```py
# project/app/api/crud.py
...
async def delete(id: int) -> int:
    summary = await TextSummary.filter(id=id).first().delete()
    return summary
```

voila!
```
$ docker-compose exec web python -m pytest
========================================================================================== test session starts ===========================================================================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
plugins: cov-2.12.1
collected 8 items                                                                                                                                                                                        

tests/test_ping.py .                                                                                                                                                                               [ 12%]
tests/test_summaries.py .......                                                                                                                                                                    [100%]

=========================================================================================== 8 passed in 0.19s ============================================================================================
```

## PUT route

For this route, we need to add a bunch of tests:
```py
# project/tests/test_summaries
...
def test_update_summary(test_app_with_db):
    response = test_app_with_db.post(
        '/summaries/', data=json.dumps({'url': 'https://update.me/'})
    )
    summary_id = response.json()['id']

    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps({'url': 'https://updated.me/', 'summary': 'updated!'})
    )
    assert response.status_code == 200

    response_dict = response.json()
    assert response_dict['id'] == summary_id
    assert response_dict['url'] == 'https://updated.me/'
    assert respones_dict['summary'] == 'updated!'
    assert response_dict['created_at']


def test_update_summary_incorrect_id(test_app_with_db):
    response = test_app_with_db.put(
        '/summaries/99912321312/',
        data=json.dumps({
            'url': 'https://invalid.me/', 'summary': 'updated!'
        })
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'


def test_update_summary_invalid_json(test_app_with_db):
    response = test_app_with_db.post(
        '/summaries/', data=json.dumps({'url': 'https://foo.bar/'})
    )
    summary_id = response.json()['id']

    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps({})
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'url'],
                'msg': 'field required',
                'type': 'value_error.missing',
            },
            {
                'loc': ['body', 'summary'],
                'msg': 'field required',
                'type': 'value_error.missing'
            }
        ]
    }


def test_update_summary_invalid_keys(test_app_with_db):
    response = test_app_with_db.post(
        '/summaries/', data=json.dumps({'url': 'https://foo.bar/'})
    )
    summary_id = response.json()['id']

    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps({'url': 'https://foo.bar/'})
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'summary'],
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ]
    }
```

Then, add the handler:
```py
# project/app/api/summaries
...
@router.put('/{id}/', response_model=SummarySchema)
async def update_summary(id: int, payload: SummaryUpdatePayloadSchema) -> SummarySchema:
    summary = await crud.put(id, payload)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return summary
```

We also need to configure the new Pydantic model `SummaryUpdatePayloadSchema`, with the added summary field:
```py
# project/app/models/pydantic
...
class SummaryUpdatePayloadSchema(SummaryPayloadSchema):
    summary: str
```

When we import the pydantic models, we do it like so:
```py
from app.models.pydantic import (  # isort:skip
    SummaryPayloadSchema, 
    SummaryResponseSchema, 
    SummaryUpdatePayloadSchema
)
```

The `# isort:skip` bit is an action comment to prevent isort from formatting the associated import.

Last but not least, the utility function:
```py
# project/app/api/crud
...
async def put(id: int, payload:SummaryPayloadSchema) -> Union[dict. None]:
    sumamry = await TextSummary.filter(id=id).update(url=payload.url, summary=payload.summary)
    if summary:
        updated_summary = await TextSummary.filter(id=id).first().values()
        return updated_summary[0]
    
    return None
```

The tests should pass now!

## Additional Validation

Let's add some additional validation to the routes:
1. `id` should be greater than `0` for reading, updating, and deleting a single summary.
2. The URL is valid for adding and updating a summary


### GET

We'll add some extra tests to `test_read_summary_incorrect_id`:
```py
def test_read_summary_incorrect_id(test_app_with_db):
    response = test_app_with_db.get('/summaries/999999999/')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'

    response = test_app_with_db.get('/summaries/0/')
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['path', 'id'],
                'msg': 'ensure this value is greater than 0',
                'type': 'value_error.number.not_gt',
                'ctx': {'limit_value': 0},
            }
        ]
    }
```

The test fails because the HTTP Response status is a 404, not 422.

We'll update the route handler:
```py
from fastapi import Path
...
@router.get('/{id}/', response_model=SummarySchema)
async def read_summary(id: int = Path(..., gt=0)) -> SummarySchema:
    summary = await crud.get(id)

    if not summary:
        raise HTTPException(status_code=404, detail='Summary not found')

    return summary
```

`fastapi.Path` can be used to declare validation for path parameters. As a path parameter is always required, we should declare it with `...` to mark it as required. Nevertheless, even if we declare it with `None` or set a default value, it would not affect the value as it would still be required.

Here, we used `Path` to declare the following validation/metadata to the parameter:
1. `...` - the value is always required ([Ellipsis](https://docs.python.org/3/library/constants.html#Ellipsis))
2. `gt=0` - The value must always be greater than 0.

The tests will pass now.

If we tried the API documentation, we'd see the error as well:
![](./code_img/README-2021-10-11-23-02-42.png)

### POST

We'll add some more tests to `test_create_summary_invalid_json`:
```py
# test_summaries
...
def test_create_summary_invalid_json(test_app):
    response = test_app.post('/summaries/', data=json.dumps({}))

    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'url'],
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ]
    }

    response = test_app.post('/summaries/', data=json.dumps({'url': 'invalid://url'}))
    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'URL scheme not permitted'
```

The test will fail now, as the POST request will be successful.
```
>       assert response.status_code == 422
E       assert 201 == 422
E        +  where 201 = <Response [201]>.status_code
```

In order to get the `url` field to only accept URL, we'll update the Pydantic model `SummaryPayloadSchema` with the `AnyHttpUrl` validator:
```py
from pydantic import BaseModel, AnyHttpUrl


class SummaryPayloadSchema(BaseModel):
    url: AnyHttpUrl
```

With this small change, the new test will pass.

### PUT

We'll update `test_update_summary_invalid_id` and include the test with invalid URL.
```py
def test_update_summary_invalid_keys(test_app_with_db):
    response = test_app_with_db.post(
        '/summaries/', data=json.dumps({'url': 'https://foo.bar/'})
    )
    summary_id = response.json()['id']

    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps({'url': 'https://foo.bar/'})
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'summary'],
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ]
    }

    response = test_app_with_db.put(
        f'/summaries/{summary_id}',
        data=json.dumps({'url': 'invalid://url', 'summary': 'updated!'})
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'URL scheme not permitted'
```

..as well as `test_update_summary_incorrect_id`:
```py
def test_update_summary_incorrect_id(test_app_with_db):
    response = test_app_with_db.put(
        '/summaries/99912321312/',
        data=json.dumps({
            'url': 'https://invalid.me/', 'summary': 'updated!'
        })
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'

    response = test_app_with_db.put(
        '/summaries/0/',
        data=json.dumps({'url': 'http://foo.bar/', 'summary': 'updated!'})
    )
```

Update the handler as well:
```py
@router.put('/{id}/', response_model=SummarySchema)
async def update_summary(payload: SummaryUpdatePayloadSchema, id: int = Path(..., gt=0)) -> SummarySchema:
    summary = await crud.put(id, payload)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return summary
```

Note that we don't need to make any further update for the invalid URL validation, because the change we previously made was on the Pydantic model, that is consumed by `update_summary` router handler.

### DELETE

```py
def test_delete_summary_incorrect_id(test_app_with_db):
    response = test_app_with_db.delete('/summaries/999999999/')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'

    response = test_app_with_db.delete('/summaries/0/')
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['path', 'id'],
                'msg': 'ensure this value is greater than 0',
                'type': 'value_error.number.not_gt',
                'ctx': {'limit_value': 0}
            }
        ]
    }
```

The test will fail now. We just need to change the route handler:
```py
@router.delete('/{id}/', response_model=SummaryResponseSchema)
async def delete_summary(id: int = Path(..., gt=0)) -> SummaryResponseSchema:
    summary = await crud.get(id)
    if not summary:
        raise HTTPException(status_code=404, detail='Summary not found')

    await crud.delete(id)
    return summary
```

# Parameterizing Test Functions

Parameterized tests allow any developer to run the same tests multiple times with different data inputs, instead of having the inputs hardcoded and fixed.

We will be updating these three tests:
```py
def test_update_summary_incorrect_id(test_app_with_db):
    response = test_app_with_db.put(
        '/summaries/99912321312/',
        data=json.dumps({
            'url': 'https://invalid.me/', 'summary': 'updated!'
        })
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'

    response = test_app_with_db.put(
        '/summaries/0/',
        data=json.dumps({'url': 'http://foo.bar/', 'summary': 'updated!'})
    )


def test_update_summary_invalid_json(test_app_with_db):
    response = test_app_with_db.post(
        '/summaries/', data=json.dumps({'url': 'https://foo.bar/'})
    )
    summary_id = response.json()['id']

    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps({})
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'url'],
                'msg': 'field required',
                'type': 'value_error.missing',
            },
            {
                'loc': ['body', 'summary'],
                'msg': 'field required',
                'type': 'value_error.missing'
            }
        ]
    }


def test_update_summary_invalid_keys(test_app_with_db):
    response = test_app_with_db.post(
        '/summaries/', data=json.dumps({'url': 'https://foo.bar/'})
    )
    summary_id = response.json()['id']

    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps({'url': 'https://foo.bar/'})
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'summary'],
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ]
    }

    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps({'url': 'invalid://url', 'summary': 'updated!'})
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'URL scheme not permitted'
```

These three tests are pretty much the same, with difference in their inputs and expected outputs. For this, we can use `pytest.mark.parametrize` decorator to enable parameterization of arguments in order to run the same tests multiple time with different data inputs.

We'll replace the three tests above with the below:
```py
@pytest.mark.parametrize('summary_id, payload, status_code, detail', [
    [490128349012845, {'url': 'http://foo.bar/', 'summary': 'updated!'}, 404, 'Summary not found'], # invalid id
    [
        0,
        {'url': 'https://foo.bar/', 'summary': 'updated!'},
        422,
        [{'loc': ['path', 'id'], 'msg': 'ensure this value is greater than 0', 'type': 'value_error.number.not_gt', 'ctx': {'limit_value':0}}]
    ], # test id=0
    [
        1,
        {},
        422,
        [
            {'loc': ['body', 'url'], 'msg': 'field required', 'type': 'value_error.missing'},
            {'loc': ['body', 'summary'], 'msg': 'field required', 'type': 'value_error.missing'}
        ]
    ], # test invalid json
    [
        1,
        {'url': 'https://foo.bar/'},
        422,
        [{'loc': ['body', 'summary'], 'msg': 'field required', 'type': 'value_error.missing'}]
    ],
])
def test_update_summary_invalid(test_app_with_db, summary_id, payload, status_code, detail):
    response = test_app_with_db.put(
        f'/summaries/{summary_id}/',
        data=json.dumps(payload)
    )
    assert response.status_code == status_code
    assert response.json()['detail'] == detail


def test_update_summary_invalid_url(test_app):
    response = test_app.put(
        '/summaries/1/',
        data=json.dumps({'url': 'invalid://url', 'summary': 'updated!'})
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'URL scheme not permitted'
```

# Tests

Our test coverage looks OK now:
```
$ docker-compose exec web python -m pytest --cov="."
========================================================================================== test session starts ===========================================================================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
plugins: cov-2.12.1
collected 14 items                                                                                                                                                                                       

tests/test_ping.py .                                                                                                                                                                               [  7%]
tests/test_summaries.py .............                                                                                                                                                              [100%]

----------- coverage: platform linux, python 3.9.6-final-0 -----------
Name                     Stmts   Miss Branch BrPart  Cover
----------------------------------------------------------
app/__init__.py              0      0      0      0   100%
app/api/__init__.py          0      0      0      0   100%
app/api/crud.py             24      0      4      0   100%
app/api/ping.py              6      0      0      0   100%
app/api/summaries.py        33      0      6      0   100%
app/config.py               13      2      0      0    85%
app/db.py                   17      7      2      1    58%
app/main.py                 18      3      0      0    83%
app/models/__init__.py       0      0      0      0   100%
app/models/pydantic.py       7      0      0      0   100%
app/models/tortoise.py       9      1      0      0    89%
----------------------------------------------------------
TOTAL                      127     13     12      1    90%


=========================================================================================== 14 passed in 0.45s ===========================================================================================
```

After running these:
```py
$ docker-compose exec web flake8 .
$ docker-compose exec web black .
$ docker-compose exec web isort .
```
..we'll commit and push the code.

Once the deployment is complete, we can test the route with HTTPie.

# Pytest Monkeypatching

pytest `monkeypatch` is the act of dynamically changing a piece of code at runtime. Essentially, it allows us to override the default behaviour of a module, object, method or function without changing its source code. This is used to mock functionality in our tests.

Normally `monkeypatch` is used for network request calls because it both decreases the amount of time the test takes to run, as well as makes the test more predictable since there would be less variable involved. Variables such as network connectivity, authentication, rate limitting issues would simply not be present.

When `monkeypatch` is used, it replaces the function default behaviour with the new overriding behaviour. While monkeypatching (or mocking) speeds up the tests and make them more predictable, we still need to test all external communication at some points in the testing process (i.e staging), so that we can be confident that the system works as expected.

We'll be using `monkeypatch` fixture to mock database calls.

## Unit Tests

We'll write a new file:
```py
# project/tests/test_summaries_unit.py

import json
from datetime import datetime

import pytest

from app.api import crud, summaries


def test_create_summary(test_app, monkeypatch):
    pass


def test_create_summary_invalid_json(test_app):
    response = test_app.post('/summaries/', data=json.dumps({}))
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'url'],
                'msg': 'field required',
                'type': 'value_error.missing'
            }
        ]
    }

    response = test_app.post('/summaries/', data=json.dumps({'url': 'invalid://url'}))
    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'URL scheme not permitted'


def test_read_summary(test_app, monkeypatch):
    pass


def test_read_summary_incorrect_id(test_app, monkeypatch):
    pass


def test_read_all_summaries(test_app, monkeypatch):
    pass


def test_remove_summary(test_app, monkeypatch):
    pass


def test_remove_summary_incorrect_id(test_app, monkeypatch):
    pass


def test_update_summary(test_app, monkeypatch):
    pass


@pytest.mark.parametrize(
    "summary_id, payload, status_code, detail",
    [
        [
            490128349012845,
            {"url": "http://foo.bar/", "summary": "updated!"},
            404,
            "Summary not found",
        ],  # invalid id
        [
            0,
            {"url": "https://foo.bar/", "summary": "updated!"},
            422,
            [
                {
                    "loc": ["path", "id"],
                    "msg": "ensure this value is greater than 0",
                    "type": "value_error.number.not_gt",
                    "ctx": {"limit_value": 0},
                }
            ],
        ],  # test id=0
        [
            1,
            {},
            422,
            [
                {
                    "loc": ["body", "url"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ["body", "summary"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
            ],
        ],  # test invalid json
        [
            1,
            {"url": "https://foo.bar/"},
            422,
            [
                {
                    "loc": ["body", "summary"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ],
        ],
    ],
)
def test_update_summary_invalid(
    test_app, monkeypatch, summary_id, payload, status_code, detail
):
    pass


def test_update_summary_invalid_url(test_app):
    response = test_app.put(
        f'/summaries/1/',
        data=json.dumps({'url': 'invalid://url', 'summary': 'updated!'})
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'URL scheme not permitted'
```

This is essentially the same tests as before, however we'll monkeypatch the calls to the CRUD service. Instead of using `test_app_with_db`, we are also using `test_app`.

Let's make changes to individual tests:

### Add Summary
```py
def test_create_summary(test_app, monkeypatch):
    test_request_payload = {'url': 'https://foo.bar/'}
    test_response_payload = {'id', 1, 'url': 'https://foo.bar/'}

    async def mock_post(payload):
        return 1

    monkeypatch.setattr(crud, 'post', mock_post)

    response = test_app.post('/summaries/', data=json.dumps(test_request_payload))

    assert response.status_code == 201
    assert response.json() == test_response_payload
```

What we are doing here is:
- Set the request payload input, and the corresponding response payload output
- Within the `test_app.post()` route handler, use the custom function `mock_post` that mimics `crud.post` to monkeypatch the `crud.post()` call. This saves us from a database trip.

### Get Summary
```py
def test_read_summary(test_app, monkeypatch):
    test_data = {
        'id': 1,
        'url': 'https://foo.bar/',
        'summary': 'summary',
        'created_at': datetime.utcnow().isoformat()
    }

    async def mock_get(id):
        return test_data
    
    monkeypatch.setattr(crud, 'get', mock_get)

    response = test_app.get('/summaries/1/')
    assert response.status_code == 200
    assert response.json() == test_data



def test_read_summary_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None
    
    monkeypatch.setattr(crud, 'get', mock_get)

    response = test_app.get('/summaries/321321321312321')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Summary not found'


def test_read_all_summaries(test_app, monkeypatch):
    test_data = [
        {
            'id': 1,
            'url': 'https://foo.bar/',
            'summary': 'summary',
            'created_at': datetime.utcnow().isoformat(),
        },
        {
            'id': 2,
            'url': 'https://hello.world/',
            'summary': 'summary',
            'created_at': datetime.utcnow().isoformat()
        }
    ]

    async def mock_get_all():
        return test_data

    monkeypatch.setattr(crud, 'get_all', mock_get_all)

    response = test_app.get('/summaries/')
    assert response.status_code == 200
    assert response.json() == test_data
```

### Remove Summary
```py
def test_remove_summary(test_app, monkeypatch):
    async def mock_get(id):
        return {
            'id': 1,
            'url': 'https://foo.bar/',
            'summary': 'summary',
            'created_at': datetime.utcnow().isoformat()
        }

    monkeypatch.setattr(crud, 'get', mock_get)

    async def mock_delete(id):
        return id

    monkeypatch.setattr(crud, 'delete', mock_delete)

    response = test_app.delete('/summaries/1/')
    assert response.status_code == 200
    assert response.json() == {'id': 1, 'url': 'https://foo.bar/'}


def test_remove_summary_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None
    
    monkeypatch.setattr(crud, 'get', mock_get)

    response = test_app.delete('/summaries/2/')
    assert response.status_code == 404
    assert response.json()['detail'] = 'Summary not found'
```

### Update Summary
```py
def test_update_summary(test_app, monkeypatch):
    test_request_payload = {'url': 'http://foo.bar/', 'summary': 'updated!'}
    test_response_payload = {
        'id': 1,
        'url': 'https://foo.bar/',
        'summary': 'summary123',
        'created_at': datetime.utcnow().isoformat(),
    }

    async def mock_put(id, payload):
        return test_response_payload
    
    monkeypatch.setattr(crud, 'put', mock_put)

    response = test_app.put('/summaries/1/', data=json.dumps(test_request_payload))

    assert response.status_code == 200
    assert response.json() == test_response_payload


@pytest.mark.parametrize(
    "summary_id, payload, status_code, detail",
    [
        [
            490128349012845,
            {"url": "http://foo.bar/", "summary": "updated!"},
            404,
            "Summary not found",
        ],  # invalid id
        [
            0,
            {"url": "https://foo.bar/", "summary": "updated!"},
            422,
            [
                {
                    "loc": ["path", "id"],
                    "msg": "ensure this value is greater than 0",
                    "type": "value_error.number.not_gt",
                    "ctx": {"limit_value": 0},
                }
            ],
        ],  # test id=0
        [
            1,
            {},
            422,
            [
                {
                    "loc": ["body", "url"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ["body", "summary"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
            ],
        ],  # test invalid json
        [
            1,
            {"url": "https://foo.bar/"},
            422,
            [
                {
                    "loc": ["body", "summary"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ],
        ],
    ],
)
def test_update_summary_invalid(
    test_app, monkeypatch, summary_id, payload, status_code, detail
):
    async def mock_put(id, payload):
        return None
    
    monkeypatch.setattr(crud, 'put', mock_put)

    response = test_app.put(f'/summaries/{summary_id}/', data=json.dumps(payload))

    assert response.status_code == status_code
    assert response.json()['detail'] == detail


def test_update_summary_invalid_url(test_app):
    response = test_app.put(
        f'/summaries/1/',
        data=json.dumps({'url': 'invalid://url', 'summary': 'updated!'})
    )
    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'URL scheme not permitted'
```

### Tests

At this stage, all of our tests should pass:
```sh
$ docker-compose exec web python -m pytest --cov="." -s
========================================================================================== test session starts ===========================================================================================
platform linux -- Python 3.9.6, pytest-6.2.5, py-1.10.0, pluggy-0.13.1
rootdir: /usr/src/app
plugins: cov-2.12.1
collected 27 items                                                                                                                                                                                       

tests/test_ping.py .
tests/test_summaries.py .............
tests/test_summaries_unit.py .............

----------- coverage: platform linux, python 3.9.6-final-0 -----------
Name                     Stmts   Miss Branch BrPart  Cover
----------------------------------------------------------
app/__init__.py              0      0      0      0   100%
app/api/__init__.py          0      0      0      0   100%
app/api/crud.py             24      0      4      0   100%
app/api/ping.py              6      0      0      0   100%
app/api/summaries.py        33      0      6      0   100%
app/config.py               13      2      0      0    85%
app/db.py                   17      7      2      1    58%
app/main.py                 18      3      0      0    83%
app/models/__init__.py       0      0      0      0   100%
app/models/pydantic.py       7      0      0      0   100%
app/models/tortoise.py       9      1      0      0    89%
----------------------------------------------------------
TOTAL                      127     13     12      1    90%


=========================================================================================== 27 passed in 0.55s ===========================================================================================
```

### Running tests in Parallel

Thanks to `monkeypatch`, we are no longer hitting a database. So we can run these tests in parallel with `pytest-xdist`.

```sh
$ poetry add
$ docker-compose up -d --build
```

We can now run the unit tests in parallel:
```py

```

# Text Summarization

We have so far been building the skeletons and bones of our application. Let's move to the actualy functionality now.

Our objective is to create real time text summarization service used for creating arcile summaries from a given URL. For this, we will need to use a scraping library to extract the text of the article, then use a ML library to generate the actual library.

We could do this by using both `BeautifulSoup` for scpraing, and `Bart` for summarizing, however there is a library that will do both: `Newspaper3k`.

```sh
# install
$ poetry add newspaper3k==0.2.8

# build
$ docker-compose up -d build
```

Then, we add a new file:
```py
# project/app/summarizer.py

from newspaper import Article


def generate_summary(url: str)-> str:
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()
    return article.summary
```

Here, what we have done is:
- Create a new `Article` instance, providing it an URL
- Download the URL, then extract its meaningful content via `parse()`, and relevant keywords via `nlp()`
- Then, generate a summary of the article

The `nlp()` method requires the `punkt` tokenizer from `nltk`, so we need to update `summarizers.py` like so:
```py
import nltk
from newspaper import Article


def generate_summary(url: str)-> str:
    article = Article(url)
    article.download()
    article.parse()

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    finally:
        article.nlp()

    return article.summary
```

With this `generate_summary()` function, we now need to update the `post` function in `project/app/api.crud.py` to generate the summary whenever a new URL is added.
```py
async def post(payload: SummaryPayloadSchema) -> int:
    article_summary = generate_summary(payload.url)
    summary = TextSummary(url=payload.url, summary=article_summary)
    await summary.save()
    return summary.id
```

We can test it out:
```sh
$ http --json POST http://localhost:8004/summaries/ url=http://testdriven.io                                                         main ⬆ ✱
HTTP/1.1 201 Created
content-length: 37
content-type: application/json
date: Mon, 01 Nov 2021 13:03:59 GMT
server: uvicorn

{
    "id": 1,
    "url": "http://testdriven.io"
}

$ http GET http://localhost:8004/summaries/1/                                                                                        main ⬆ ✱
HTTP/1.1 200 OK
content-length: 779
content-type: application/json
date: Mon, 01 Nov 2021 13:05:21 GMT
server: uvicorn

{
    "created_at": "2021-11-01T13:04:01.635327+00:00",
    "id": 1,
    "summary": "Our courses and tutorials teach practical application of popular tech used by both enterprise and startups.\nYou will quickly become effective in your chosen stack, as we provide pragmatic examples and detailed walkthroughs of the workings of each technology.\nThrough our courses, you will not only become more comfortable with specific tools and technologies like AWS ECS, Docker, and Flask, to name a few -- but you will also gain skills necessary to contribute to a team or launch your own exciting project.\nEvery tool taught in our courses is supported by large communities and is in high-demand by hiring managers around the globe.\nWe teach tools we love and use every day.",
    "url": "http://testdriven.io"
}
```

## Background Task

Let's take a look at our CRUD `post` function right now:
```py
async def post(payload: SummaryPayloadSchema) -> int:
    article_summary = generate_summary(payload.url)
    summary = TextSummary(url=payload.url, summary=article_summary)
    await summary.save()
    return summary.id
```

The `generate_summary` function introduces a **blocking operation** into the `post` function. Both `article.download()` and `article.parse()` are fairly expensive.

This is where **Background Tasks** can be super helpful: https://fastapi.tiangolo.com/tutorial/background-tasks/.

With Background Task, we can return a response to the client, **before** the completion of the blocking operation.

First, we take the expensive operation out of the CRUD function:
```py
# project/app/api/crud.py

async def post(payload: SummaryPayloadSchema) -> int:
    # article_summary = generate_summary(payload.url)
    # summary = TextSummary(url=payload.url, summary=article_summary)

    summary = TextSummary(url=payload.url, summary="")
    await summary.save()
    return summary.id
```

Then, we update `create_summary` to handle the background task of generating the summary:
```py
# project/app/api/summaries.py
from app.summarizer import generate_summary
from fastapi import APIRouter, BackgroundTasks, HTTPException, Path

...
@router.post("/", response_model=SummaryResponseSchema, status_code=201)
async def create_summary(
    payload: SummaryPayloadSchema, background_tasks: BackgroundTasks
) -> SummaryResponseSchema:
    summary_id = await crud.post(payload)

    background_tasks.add_task(generate_summary, summary_id, payload.url)

    response_object = {"id": summary_id, "url": payload.url}
    return response_object
```

Finally, we need to update `generate_summary`:
```py
import nltk
from newspaper import Article

from app.models.tortoise import TextSummary


async def generate_summary(summary_id: int, url: str) -> str:
    article = Article(url)
    article.download()
    article.parse()

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")
    finally:
        article.nlp()

    summary = article.summary

    await TextSummary.filter(id=summary_id).update(summary=summary)

```

The concept is very simple. The summary is generated **after** the response is sent back to the client. Once the text summarization completes, the database is updated.

This is where `async` comes in handy. We can inspect the effect like so:
![](./code_img/README-2021-12-26-04-53-34.png)

`print("returning woo hoo!")` is executed **before** `print("going to sleep")`:
```
returning woo hoo!
INFO:     172.20.0.1:51558 - "POST /summaries/ HTTP/1.1" 201 Created
going to sleep...
```

## Tests

At present, if we run our test again..
```py
docker compose exec web python -m pytest
```

..we would see 6 failures.
```
E           newspaper.article.ArticleException: Article `download()` failed with HTTPSConnectionPool(host='foo.bar', port=443): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7f5c171b2be0>: Failed to establish a new connection: [Errno -5] No address associated with hostname')) on URL https://foo.bar/
```

We need to use `monkeypatch` again to mock the `generate_summary` call that is used within `summaries.py`:
```py
def test_create_summary(test_app_with_db, monkeypatch):
    def mock_generate_summary(summary_id, url):
        return None

    monkeypatch.setattr(summaries, "generate_summary", mock_generate_summary)

    url = "http://foo.bar/"

    response = test_app_with_db.post("/summaries/", data=json.dumps({"url": url}))

    assert response.status_code == 201
    assert response.json()["url"] == url
```

This same monkey-patching needs to be applied across all failed tests.

# Advanced CI

## Multistage Docker Build

In this section, we'll move on to update the CI process and set up a **multistage** Docker build for production.
```dockerfile
###########
# BUILDER #
###########

FROM python:3.8.11-slim-buster as builder 

# install system dependencies
RUN apt-get update \
  && apt-get -y install gcc postgresql \
  && apt-get clean

# set Work Directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# lint
COPY . /usr/src/app/
RUN pip install black==21.6b0 flake8==3.9.2 isort==5.9.1
RUN flake8 .
RUN black --exclude=migrations .
RUN isort .


#########
# FINAL #
#########

FROM python:3.8.11-slim-buster

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# set environment variable
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONMENT prod
ENV TESTING 0

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql \
  && apt-get clean

# install python dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*
RUN pip install "uvicorn[standard]==0.14.0"

# add app
COPY . .

# chown all the files to the app user
RUN chown -R app:app $HOME

# change to the app user
USER app

# run gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT app.main:app -k uvicorn.workers.UvicornWorker
```

How does this work? Essentially, we create a temporary image `builder` that is used for building the Python wheels. The wheels are then copied over to the final production image and the builder image is discarded.

To test locally:

- First, build the image
```sh
$ docker build -f project/Dockerfile.prod -t web ./project
```

- Spin up the container:
```sh
$ docker run --name fastapi-tdd -e PORT=8765 -e DATABASE_URL=sqlite://sqlite.db -p 5003:8765 web:latest
```

Then:
```
GET http://localhost:5003/ping

{
  "ping": "pong!",
  "environment": "prod",
  "testing": false
}
```

We need to remember to bring down the container once done:
```sh
$ docker rm fastapi-tdd -f
```

## Docker Caching

Next, to speed up the build on GitHub Actions, we can make changes to to `.github/workflows/main.yml`.

We are now pulling, building and pushing the `builder` image using the `--target` option.

See here for more on Docker caching: https://testdriven.io/blog/faster-ci-builds-with-docker-cache/

## Seperate Requirements

We can move development-only requirements to a new file

```
# project/requirements-dev.txt

black==21.6b0
flake8==3.9.2
isort==5.9.1
pytest==6.2.4
pytest-cov==2.12.1
pytest-xdist==2.3.0

-r requirements.txt
```

We also need to update `project/Dockerfile`:
```
...
RUN pip install --upgrade pip
COPY ./requirements.txt .
COPY ./requirements-dev.txt .
RUN pip install -r requirements-dev.txt
...
```

Then, test:

```sh
$ docker compose down -v
$ docker compose up -d --build
$ docker compose exec web aerich upgrade

$ docker compose exec web python -m pytest
$ docker compose exec web flake8 .
$ docker compose exec web black .
$ docker compose exec web isort .
```

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

## `pytest` commands

```sh
# normal run
$ docker-compose exec web python -m pytest

# disable warnings
$ docker-compose exec web python -m pytest -p no:warnings

# run only the last failed tests
$ docker-compose exec web python -m pytest --lf

# run only the tests with names that match the string expression
$ docker-compose exec web python -m pytest -k "summary and not test_read_summary"

# stop the test session after the first failure
$ docker-compose exec web python -m pytest -x

# enter PDB after first failure then end the test session
$ docker-compose exec web python -m pytest -x --pdb

# stop the test run after two failures
$ docker-compose exec web python -m pytest --maxfail=2

# show local variables in tracebacks
$ docker-compose exec web python -m pytest -l

# list the 2 slowest tests
$ docker-compose exec web python -m pytest --durations=2
```