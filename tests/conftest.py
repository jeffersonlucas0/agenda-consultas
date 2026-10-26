"""Configuração compartilhada dos testes.

Cada teste usa um banco SQLite novo, em memória.
Assim os testes não dependem uns dos outros nem do MySQL.
"""

import os
from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

CPF_VALIDO = "529.982.247-25"
OUTRO_CPF_VALIDO = "111.444.777-35"


def _criar_engine():
    # Para rodar os testes num MySQL de verdade, defina TEST_DATABASE_URL.
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        return create_engine(url)
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def sessao():
    engine = _criar_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Sessao() as db:
        yield db
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def cliente(sessao):
    app.dependency_overrides[get_db] = lambda: sessao
    # Sem "with", o ciclo de vida da API não roda, então o banco real não é tocado.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def medico(cliente):
    especialidade = cliente.post("/especialidades", json={"nome": "Cardiologia"}).json()
    return cliente.post(
        "/medicos",
        json={"nome": "Dr. João Almeida", "crm": "CRM-CE 10001",
              "especialidade_id": especialidade["id"]},
    ).json()


@pytest.fixture
def paciente(cliente):
    return cliente.post(
        "/pacientes",
        json={"nome": "Ana Beatriz", "cpf": CPF_VALIDO, "data_nascimento": "2001-05-20"},
    ).json()


def proximo_dia_util(dias_a_frente: int = 7) -> date:
    """Um dia útil no futuro, para os testes nunca caírem no passado."""
    dia = date.today() + timedelta(days=dias_a_frente)
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia


def horario_valido(hora: int = 10, minuto: int = 0) -> str:
    return datetime.combine(proximo_dia_util(), time(hora, minuto)).isoformat()
