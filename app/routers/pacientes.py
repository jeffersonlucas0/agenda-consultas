from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Consulta, Paciente
from app.schemas import PacienteAtualizar, PacienteCriar, PacienteSaida

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def _buscar_ou_404(db: Session, paciente_id: int) -> Paciente:
    paciente = db.get(Paciente, paciente_id)
    if paciente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado.")
    return paciente


@router.get("", response_model=list[PacienteSaida])
def listar(nome: str | None = None, db: Session = Depends(get_db)):
    """Lista pacientes. Use ?nome= para buscar por parte do nome."""
    consulta = select(Paciente).order_by(Paciente.nome)
    if nome:
        consulta = consulta.where(Paciente.nome.ilike(f"%{nome}%"))
    return db.scalars(consulta).all()


@router.post("", response_model=PacienteSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: PacienteCriar, db: Session = Depends(get_db)):
    if db.scalar(select(Paciente).where(Paciente.cpf == dados.cpf)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe paciente com esse CPF.")
    paciente = Paciente(**dados.model_dump())
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    return paciente


@router.get("/{paciente_id}", response_model=PacienteSaida)
def buscar(paciente_id: int, db: Session = Depends(get_db)):
    return _buscar_ou_404(db, paciente_id)


@router.patch("/{paciente_id}", response_model=PacienteSaida)
def atualizar(paciente_id: int, dados: PacienteAtualizar, db: Session = Depends(get_db)):
    paciente = _buscar_ou_404(db, paciente_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(paciente, campo, valor)
    db.commit()
    db.refresh(paciente)
    return paciente


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(paciente_id: int, db: Session = Depends(get_db)):
    paciente = _buscar_ou_404(db, paciente_id)
    tem_consultas = db.scalar(select(Consulta.id).where(Consulta.paciente_id == paciente_id))
    if tem_consultas:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Paciente tem consultas no histórico e não pode ser removido.",
        )
    db.delete(paciente)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
