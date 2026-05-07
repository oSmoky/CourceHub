web: python scripts/init_db.py && python scripts/seed.py && python scripts/set_webhook.py && gunicorn --bind 0.0.0.0:$PORT run:app
worker: python scripts/set_webhook.py && python -c "import time; time.sleep(31536000)"
release: python scripts/init_db.py
