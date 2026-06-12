"""
Database connection management for FitAI.

Provides per-request SQLite connections via Flask's application context (g).
Usage:
    from database.db import get_db
    db = get_db()
"""

import os
import sqlite3

from flask import current_app, g


def get_db():
    """Return the SQLite connection for the current request, creating one if needed."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Execute schema.sql to create all tables and indexes."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        db.executescript(f.read())


def init_app(app):
    """Register the database teardown hook with the Flask application."""
    app.teardown_appcontext(close_db)
