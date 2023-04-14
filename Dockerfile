FROM python:3.11.2-slim-buster
MAINTAINER Gregory Wiedeman gwiedeman@albany.edu

ENV FLASK_APP=app
ENV TZ=America/New_York

EXPOSE 5000

COPY ./requirements.txt /code/requirements.txt
WORKDIR /code
RUN pip install -r requirements.txt

COPY .archivessnake.yml /root
COPY .hyrax.yml /root
COPY . /code
RUN ["chmod", "+x", "./gunicorn.sh"]
RUN apt update
RUN apt install tzdata -y
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt install imagemagick -y
RUN apt install tesseract-ocr -y
RUN apt install rsync -y

ENTRYPOINT ["./gunicorn.sh"]
