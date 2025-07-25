# Makefile for Dockerized Flask App

# Build production image
build:
	docker build -t "processing" .

build-nocache:
	docker build --no-cache -t "processing" .

# Restart dev containers (stop and start)
restart:
	docker compose down
	docker compose -f docker-compose-prod.yml up -d