#!/bin/bash
# VoicePilot backend — first-time setup script
set -e

echo "==> Creating virtual environment..."
python -m venv venv
source venv/bin/activate

echo "==> Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Copying env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "    .env created — fill in your API keys before running the server."
fi

echo "==> Running migrations..."
python manage.py migrate

echo "==> Creating superuser (optional — press Ctrl+C to skip)..."
python manage.py createsuperuser || true

echo ""
echo "Setup complete. To start all services:"
echo "  Terminal 1:  python manage.py runserver"
echo "  Terminal 2:  celery -A voicepilot worker --loglevel=info"
echo "  Terminal 3:  celery -A voicepilot beat --loglevel=info"
echo "  Terminal 4:  python -m agent.main dev"
