from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import agendamento
from app.database import get_db
from app.models import Especialidade, Medico
from app.schemas import HorariosLivres, MedicoCriar, MedicoSaida

router = APIRouter(prefix="/medicos", tags=["Médicos"])


@router.get("", response_model=list[MedicoSaida])
def listar(especialidade_id: int | None = None, db: Session = Depends(get_db)):
    consulta = select(Medico).order_by(Medico.nome)
    if especialidade_id is not None:
        consulta = consulta.where(Medico.especialidade_id == especialidade_id)
    return db.scalars(consulta).all()


@router.post("", response_model=MedicoSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: MedicoCriar, db: Session = Depends(get_db)):
    if db.get(Especialidade, dados.especialidade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Especialidade não encontrada.")
    if db.scalar(select(Medico).where(Medico.crm == dados.crm)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe médico com esse CRM.")
    medico = Medico(**dados.model_dump())
    db.add(medico)
    db.commit()
    db.refresh(medico)
    return medico


@router.get("/{medico_id}", response_model=MedicoSaida)
def buscar(medico_id: int, db: Session = Depends(get_db)):
    medico = db.get(Medico, medico_id)
    if medico is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico não encontrado.")
    return medico


@router.get("/{medico_id}/horarios-livres", response_model=HorariosLivres)
def horarios_livres(medico_id: int, data: date, db: Session = Depends(get_db)):
    """Mostra os horários em que o médico ainda pode receber consultas no dia."""
    horarios = agendamento.horarios_livres(db, medico_id, data)
    return HorariosLivres(medico_id=medico_id, data=data, horarios=horarios)
