FROM python:3.11.2-slim-buster
MAINTAINER Gregory Wiedeman gwiedeman@albany.edu

ENV FLASK_APP=app
ENV TZ=America/New_York

EXPOSE 5000

RUN apt update && apt install -y wget gnupg apt-transport-https

# Add repository and key correctly
RUN wget -O - https://notesalexp.org/debian/alexp_key.asc | gpg --dearmor -o /usr/share/keyrings/notesalexp-keyring.gpg

RUN echo "deb [signed-by=/usr/share/keyrings/notesalexp-keyring.gpg] https://notesalexp.org/tesseract-ocr5/buster/ buster main" | tee /etc/apt/sources.list.d/tesseract.list

# Update and install Tesseract
RUN apt update && apt install -y tesseract-ocr

RUN apt install poppler-utils -y
RUN apt install libvips-tools -y

RUN apt install tzdata -y
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt install poppler-utils -y
RUN apt install rsync -y
RUN apt install imagemagick -y
RUN rm /etc/ImageMagick-6/policy.xml
COPY conf/policy.xml /etc/ImageMagick-6/policy.xml

# Install ffmpeg
RUN apt update && apt install -y ffmpeg

# Install libreoffice
RUN apt install -y libreoffice

# wkhtmltopdf install
RUN apt-get install -y xfonts-75dpi xfonts-base curl dpkg-dev
RUN curl -L -o /tmp/wkhtmltox_0.12.6-1.buster_amd64.deb \ 
        https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb
RUN dpkg -i /tmp/wkhtmltox_0.12.6-1.buster_amd64.deb

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt

COPY .archivessnake.yml /root
COPY .iiiflow.yml /root
COPY .description_harvester.yml /root
COPY repositories.yml /root
COPY .hyrax.yml /root
COPY . /code
RUN ["chmod", "+x", "./gunicorn.sh"]

#ENTRYPOINT ["./gunicorn.sh"]
