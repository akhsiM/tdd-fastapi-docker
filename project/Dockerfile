FROM python:3.9.6-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERRED 1

RUN apt-get update\
 && apt-get -y install netcat gcc postgresql \
 && apt-get clean

RUN pip install --upgrade pip
COPY ./requirements.txt .
COPY ./requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY . .

COPY ./entrypoint.sh .
RUN chmod +x /usr/src/app/entrypoint.sh

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]