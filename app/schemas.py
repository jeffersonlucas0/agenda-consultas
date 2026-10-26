"""Formatos de entrada e saída da API (validados pelo Pydantic)."""

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import StatusConsulta


def cpf_valido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores do CPF."""
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[tamanho]):
            return False
    return True


# ---------- Especialidades ----------

class EspecialidadeCriar(BaseModel):
    nome: str = Field(min_length=3, max_length=80)


class EspecialidadeSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


# ---------- Médicos ----------

class MedicoCriar(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    crm: str = Field(min_length=4, max_length=20, examples=["CRM-CE 12345"])
    especialidade_id: int


class MedicoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    crm: str
    especialidade: EspecialidadeSaida


# ---------- Pacientes ----------

class PacienteBase(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    data_nascimento: date
    telefone: str | None = Field(default=None, max_length=20)

    @field_validator("data_nascimento")
    @classmethod
    def nascimento_no_passado(cls, valor: date) -> date:
        if valor > date.today():
            raise ValueError("a data de nascimento não pode estar no futuro")
        return valor


class PacienteCriar(PacienteBase):
    cpf: str = Field(examples=["529.982.247-25"])

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        somente_numeros = re.sub(r"\D", "", valor)
        if not cpf_valido(somente_numeros):
            raise ValueError("CPF inválido")
        return somente_numeros


class PacienteAtualizar(BaseModel):
    """Todos os campos são opcionais: só muda o que for enviado."""

    nome: str | None = Field(default=None, min_length=3, max_length=120)
    telefone: str | None = Field(default=None, max_length=20)


class PacienteSaida(PacienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cpf: str


class PacienteResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


# ---------- Consultas ----------

class ConsultaCriar(BaseModel):
    paciente_id: int
    medico_id: int
    data_hora: datetime = Field(examples=["2026-11-10T09:30:00"])
    descricao: str | None = Field(default=None, max_length=1000)

    @field_validator("data_hora")
    @classmethod
    def sem_fuso_horario(cls, valor: datetime) -> datetime:
        # Se vier com fuso (ex.: "...Z"), converte para o horário local da clínica.
        if valor.tzinfo is not None:
            valor = valor.astimezone().replace(tzinfo=None)
        return valor


class ConsultaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_hora: datetime
    descricao: str | None
    status: StatusConsulta
    paciente: PacienteResumo
    medico: MedicoSaida


class HorariosLivres(BaseModel):
    medico_id: int
    data: date
    horarios: list[str]
