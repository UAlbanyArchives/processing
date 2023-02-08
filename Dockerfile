FROM python:latest
MAINTAINER Gregory Wiedeman gwiedeman@albany.edu

ENV FLASK_APP=app \
    FLASK_DEBUG=1

EXPOSE 5000

WORKDIR /flask1

RUN pip install flask
RUN pip install wtforms
