#!/bin/bash
set -e

# Appliquer les migrationssss
echo "Appliquer les migrations..."
python manage.py makemigrations
python manage.py migrate

# Démarrer le serveur Django
echo "Démarrer le serveur Django..."
exec "$@"
