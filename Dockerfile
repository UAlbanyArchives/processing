FROM python:3.11.2-slim-buster
MAINTAINER Gregory Wiedeman gwiedeman@albany.edu

ENV FLASK_APP=app
ENV TZ=America/New_York

EXPOSE 5000

COPY ./requirements.txt /code/requirements.txt
WORKDIR /code

COPY .archivessnake.yml /root
COPY .hyrax.yml /root
COPY . /code
RUN ["chmod", "+x", "./gunicorn.sh"]
RUN apt update

RUN apt install apt-transport-https gnupg wget aptitude -y
RUN echo 'deb [trusted=yes] https://notesalexp.org/tesseract-ocr5/buster/ buster main' >> /etc/apt/sources.list
RUN apt update -oAcquire::AllowInsecureRepositories=true
RUN apt install notesalexp-keyring -oAcquire::AllowInsecureRepositories=true -y
RUN wget -O - https://notesalexp.org/debian/alexp_key.asc | apt-key add -
RUN apt update
RUN aptitude install tesseract-ocr -y

RUN apt install tzdata -y
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt install rsync imagemagick -y

RUN pip install -r requirements.txt

ENTRYPOINT ["./gunicorn.sh"]
