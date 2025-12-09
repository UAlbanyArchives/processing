FROM python:3.11-slim-bookworm

ENV FLASK_APP=app
ENV TZ=America/New_York

EXPOSE 5000

# Install all dependencies in one go, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        gnupg \
        apt-transport-https \
        git \
        poppler-utils \
        libvips-tools \
        tzdata \
        rsync \
        imagemagick \
        ffmpeg \
        libreoffice \
        xfonts-75dpi \
        xfonts-base \
        curl \
        dpkg-dev \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy
RUN rm /etc/ImageMagick-6/policy.xml
COPY conf/policy.xml /etc/ImageMagick-6/policy.xml

# Add Tesseract repo + install
RUN wget -O - https://notesalexp.org/debian/alexp_key.asc \
    | gpg --dearmor -o /usr/share/keyrings/notesalexp-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/notesalexp-keyring.gpg] https://notesalexp.org/tesseract-ocr5/buster/ buster main" \
       > /etc/apt/sources.list.d/tesseract.list \
    && apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf
RUN curl -L -o /tmp/wkhtmltox.deb \
        https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && dpkg -i /tmp/wkhtmltox.deb \
    && rm -f /tmp/wkhtmltox.deb

WORKDIR /code

# Install Python deps before copying code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy configs and app
COPY .archivessnake.yml /root
COPY .iiiflow.yml /root
RUN mkdir -p /root/.description_harvester
COPY .description_harvester/ /root/.description_harvester/
COPY . /code

# Set up description harvester plugins
RUN git clone https://github.com/UAlbanyArchives/description_harvester_plugins.git

RUN chmod +x ./gunicorn.sh

#ENTRYPOINT ["./gunicorn.sh"]
