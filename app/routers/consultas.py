from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import agendamento
from app.database import get_db
from app.models import Consulta, Medico, StatusConsulta
from app.schemas import ConsultaCriar, ConsultaSaida

router = APIRouter(prefix="/consultas", tags=["Consultas"])


@router.get("", response_model=list[ConsultaSaida])
def listar(
    medico_id: int | None = None,
    paciente_id: int | None = None,
    especialidade_id: int | None = None,
    data: date | None = None,
    status_consulta: StatusConsulta | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    """Lista consultas. Todos os filtros são opcionais e podem ser combinados."""
    consulta = select(Consulta).order_by(Consulta.data_hora)
    if medico_id is not None:
        consulta = consulta.where(Consulta.medico_id == medico_id)
    if paciente_id is not None:
        consulta = consulta.where(Consulta.paciente_id == paciente_id)
    if especialidade_id is not None:
        consulta = consulta.join(Medico).where(Medico.especialidade_id == especialidade_id)
    if data is not None:
        inicio = datetime.combine(data, time.min)
        consulta = consulta.where(
            Consulta.data_hora >= inicio, Consulta.data_hora < inicio + timedelta(days=1)
        )
    if status_consulta is not None:
        consulta = consulta.where(Consulta.status == status_consulta)
    return db.scalars(consulta).all()


@router.post("", response_model=ConsultaSaida, status_code=status.HTTP_201_CREATED)
def agendar(dados: ConsultaCriar, db: Session = Depends(get_db)):
    return agendamento.agendar(
        db, dados.paciente_id, dados.medico_id, dados.data_hora, dados.descricao
    )


@router.get("/{consulta_id}", response_model=ConsultaSaida)
def buscar(consulta_id: int, db: Session = Depends(get_db)):
    consulta = db.get(Consulta, consulta_id)
    if consulta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consulta não encontrada.")
    return consulta


@router.patch("/{consulta_id}/cancelar", response_model=ConsultaSaida)
def cancelar(consulta_id: int, db: Session = Depends(get_db)):
    return agendamento.mudar_status(db, consulta_id, StatusConsulta.CANCELADA)


@router.patch("/{consulta_id}/concluir", response_model=ConsultaSaida)
def concluir(consulta_id: int, db: Session = Depends(get_db)):
    return agendamento.mudar_status(db, consulta_id, StatusConsulta.REALIZADA)
