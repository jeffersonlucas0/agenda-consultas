from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Especialidade
from app.schemas import EspecialidadeCriar, EspecialidadeSaida

router = APIRouter(prefix="/especialidades", tags=["Especialidades"])


@router.get("", response_model=list[EspecialidadeSaida])
def listar(db: Session = Depends(get_db)):
    return db.scalars(select(Especialidade).order_by(Especialidade.nome)).all()


@router.post("", response_model=EspecialidadeSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: EspecialidadeCriar, db: Session = Depends(get_db)):
    existe = db.scalar(select(Especialidade).where(Especialidade.nome == dados.nome))
    if existe:
        raise HTTPException(status.HTTP_409_CONFLICT, "Especialidade já cadastrada.")
    especialidade = Especialidade(nome=dados.nome)
    db.add(especialidade)
    db.commit()
    db.refresh(especialidade)
    return especialidade
