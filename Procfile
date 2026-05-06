web: python scripts/init_db.py && python scripts/seed.py && gunicorn --bind 0.0.0.0:$PORT run:app
worker: python -m bot.main
release: python scripts/init_db.py
