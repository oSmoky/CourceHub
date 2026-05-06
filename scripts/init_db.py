import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from scripts.db_bootstrap import create_or_update_schema


app = create_app()


with app.app_context():
    create_or_update_schema()
    print("Database tables created.")
