.PHONY: install migrate runserver test seed

install:
python -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

migrate:
python manage.py migrate

runserver:
python manage.py runserver 0.0.0.0:8000

seed:
python manage.py seed_dynamic

test:
pytest
