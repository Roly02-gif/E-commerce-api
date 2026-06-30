#!/bin/sh

uv run python manage.py migrate
uv run python manage.py create_default_superuser
uv run python manage.py runserver 0.0.0.0:8000