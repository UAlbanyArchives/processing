FROM python:3.11.2-slim-buster
MAINTAINER Gregory Wiedeman gwiedeman@albany.edu

ENV FLASK_APP=app

EXPOSE 5000

COPY ./requirements.txt /flask1/requirements.txt
WORKDIR /flask1
RUN pip install -r requirements.txt

COPY . /flask1

ENTRYPOINT ["./gunicorn.sh"]
