# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env

env = Env()
env.read_env()

ENV = env.str("FLASK_ENV", default="production")
DEBUG = env.bool("FLASK_DEBUG", default=False)
SQLALCHEMY_DATABASE_URI = env.str("DATABASE_URL")
SECRET_KEY = env.str("SECRET_KEY")
SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT")
BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
DEBUG_TB_ENABLED = DEBUG  # toolbar only active when DEBUG is True; never in production
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = (
    "flask_caching.backends.SimpleCache"  # Can be "MemcachedCache", "RedisCache", etc.
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
AI_INTAKE_ENDPOINT = env.str("AI_INTAKE_ENDPOINT", default="")
AI_INTAKE_API_KEY = env.str("AI_INTAKE_API_KEY", default="")
AI_INTAKE_MODEL = env.str("AI_INTAKE_MODEL", default="")
AI_INTAKE_TIMEOUT = env.int("AI_INTAKE_TIMEOUT", default=20)
