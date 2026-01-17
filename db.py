from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str
    sql_echo: bool

def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///glowhub.db").strip()
    sql_echo = os.getenv("SQL_ECHO", "0").strip() in {"1", "true", "TRUE", "yes", "YES"}
    return Settings(database_url=database_url, sql_echo=sql_echo)

def make_engine():
    s = get_settings()
    return create_engine(s.database_url, echo=s.sql_echo, future=True)

def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)

def get_session(engine) -> Session:
    SessionLocal = make_session_factory(engine)
    return SessionLocal()
