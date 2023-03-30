FROM python:3.11.2-slim-buster
MAINTAINER Gregory Wiedeman gwiedeman@albany.edu

ENV FLASK_APP=app
#ENV FLASK_DEBUG=1

EXPOSE 5000

COPY ./requirements.txt /code/requirements.txt
WORKDIR /code
RUN pip install -r requirements.txt

COPY . /code
RUN ["chmod", "+x", "./gunicorn.sh"]
RUN apt update
RUN apt install imagemagick -y
RUN apt install tesseract-ocr -y
RUN apt install rsync -y

ENTRYPOINT ["./gunicorn.sh"]
