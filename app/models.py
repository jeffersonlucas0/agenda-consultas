"""Tabelas do banco de dados, escritas como classes Python (ORM)."""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StatusConsulta(str, enum.Enum):
    AGENDADA = "agendada"
    CANCELADA = "cancelada"
    REALIZADA = "realizada"


class Especialidade(Base):
    __tablename__ = "especialidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)

    medicos: Mapped[list["Medico"]] = relationship(back_populates="especialidade")


class Medico(Base):
    __tablename__ = "medicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    crm: Mapped[str] = mapped_column(String(20), unique=True)
    especialidade_id: Mapped[int] = mapped_column(ForeignKey("especialidades.id"))

    especialidade: Mapped[Especialidade] = relationship(back_populates="medicos")
    consultas: Mapped[list["Consulta"]] = relationship(back_populates="medico")


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    data_nascimento: Mapped[date] = mapped_column(Date)
    telefone: Mapped[str | None] = mapped_column(String(20))

    consultas: Mapped[list["Consulta"]] = relationship(back_populates="paciente")


class Consulta(Base):
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"))
    medico_id: Mapped[int] = mapped_column(ForeignKey("medicos.id"))
    data_hora: Mapped[datetime] = mapped_column(DateTime, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusConsulta] = mapped_column(
        Enum(StatusConsulta, values_callable=lambda e: [s.value for s in e]),
        default=StatusConsulta.AGENDADA,
    )
    criada_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    paciente: Mapped[Paciente] = relationship(back_populates="consultas")
    medico: Mapped[Medico] = relationship(back_populates="consultas")
