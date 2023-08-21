#!/bin/sh
gunicorn -c gunicorn_conf.py wsgi:app