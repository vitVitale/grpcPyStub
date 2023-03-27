FROM python:3.10.7 as base
MAINTAINER Vitaly Vasilyuk
USER root

RUN mkdir -m 777 app
RUN mkdir -m 777 proto

COPY app/ /app/
COPY requirements.txt /app/

RUN pip install --upgrade pip==23.0.1 \
    && pip install --no-cache-dir cython \
    && pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
ENTRYPOINT ["/app/launch.sh"]