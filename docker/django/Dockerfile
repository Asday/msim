FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1

RUN adduser --disabled-password --gecos '' msim

RUN mkdir /src
RUN mkdir /requirements
WORKDIR /requirements

COPY docker/django/docker-requirements.txt /requirements/
COPY requirements.txt /requirements/
RUN apk add --no-cache --virtual .build-deps \
  gcc \
  make \
  python3-dev \
  musl-dev \
  postgresql-dev \
  && pip install -U pip \
  && pip install -r requirements.txt -r docker-requirements.txt \
  && apk del --no-cache .build-deps \
  && apk add --no-cache libpq

WORKDIR /src

USER msim
