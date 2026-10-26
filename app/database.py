"""Conexão com o banco de dados.

A URL do banco vem da variável de ambiente DATABASE_URL.
Sem ela, o projeto usa um arquivo SQLite local, o que facilita rodar sem instalar nada.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./consultas.db")

# O SQLite precisa dessa opção para funcionar com o servidor da API.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe base de todos os modelos (tabelas)."""


def get_db():
    """Abre uma sessão por requisição e fecha no final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
