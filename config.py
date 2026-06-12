"""
Application configuration for FitAI.
Loads environment variables from .env and exposes config constants.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

# Load .env from project root
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # Flask secret key – falls back to a random value if not set
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()

    # Groq AI API key
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

    # SQLite database path
    DATABASE_PATH = os.path.join(basedir, 'database', 'fitai.db')

    # Session lifetime
    SESSION_LIFETIME = timedelta(hours=24)
