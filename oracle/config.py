"""
Configuration settings for ORACLE.
Loads environment variables from .env if present.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    FALKORDB_HOST: str = os.getenv("FALKORDB_HOST", "localhost")
    FALKORDB_PORT: int = int(os.getenv("FALKORDB_PORT", "6379"))
    FALKORDB_GRAPH: str = os.getenv("FALKORDB_GRAPH", "oracle_incidents")
    ORACLE_HOST: str = os.getenv("ORACLE_HOST", "0.0.0.0")
    ORACLE_PORT: int = int(os.getenv("ORACLE_PORT", "8000"))


settings = Settings()
