"""Ponto de entrada da API.

Rode com:  uvicorn app.main:app --reload
Documentação interativa: http://127.0.0.1:8000/docs
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.agendamento import ErroDeNegocio
from app.database import Base, SessionLocal, engine
from app.routers import consultas, especialidades, medicos, pacientes
from app.seed import carregar_dados_exemplo


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Cria as tabelas que ainda não existem.
    Base.metadata.create_all(engine)
    if os.getenv("CARREGAR_DADOS_EXEMPLO", "true").lower() == "true":
        with SessionLocal() as sessao:
            carregar_dados_exemplo(sessao)
    yield


app = FastAPI(
    title="Agenda de Consultas",
    description="API para cadastrar pacientes e agendar consultas médicas.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


@app.exception_handler(ErroDeNegocio)
async def tratar_erro_de_negocio(request: Request, erro: ErroDeNegocio):
    return JSONResponse(status_code=erro.status_code, content={"detail": erro.mensagem})


@app.get("/", tags=["Status"])
def inicio():
    return {"mensagem": "API da Agenda de Consultas no ar.", "documentacao": "/docs"}


app.include_router(especialidades.router)
app.include_router(medicos.router)
app.include_router(pacientes.router)
app.include_router(consultas.router)
