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

Then, we'll set up Tortoise ORM and configure a model