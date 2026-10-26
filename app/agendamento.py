"""Regras de negócio do agendamento.

Ficam separadas das rotas para serem fáceis de ler, mudar e testar.
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Consulta, Medico, Paciente, StatusConsulta

# Horário de funcionamento da clínica
ABERTURA = time(8, 0)
FECHAMENTO = time(18, 0)
DURACAO_CONSULTA = timedelta(minutes=30)
DIAS_UTEIS = {0, 1, 2, 3, 4}  # segunda (0) a sexta (4)


class ErroDeNegocio(Exception):
    """Erro de regra de negócio. A API transforma em resposta HTTP."""

    def __init__(self, mensagem: str, status_code: int = 400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code


def horarios_do_dia(dia: date) -> list[datetime]:
    """Todos os horários de início possíveis num dia, de 30 em 30 minutos."""
    if dia.weekday() not in DIAS_UTEIS:
        return []
    horarios = []
    atual = datetime.combine(dia, ABERTURA)
    ultimo_inicio = datetime.combine(dia, FECHAMENTO) - DURACAO_CONSULTA
    while atual <= ultimo_inicio:
        horarios.append(atual)
        atual += DURACAO_CONSULTA
    return horarios


def validar_horario(data_hora: datetime, agora: datetime | None = None) -> None:
    """Verifica se o horário pedido pode receber uma consulta."""
    agora = agora or datetime.now()
    if data_hora <= agora:
        raise ErroDeNegocio("Não é possível agendar no passado.")
    if data_hora.weekday() not in DIAS_UTEIS:
        raise ErroDeNegocio("A clínica atende apenas de segunda a sexta.")
    if data_hora not in horarios_do_dia(data_hora.date()):
        raise ErroDeNegocio(
            "Horário inválido. Atendemos das 08:00 às 18:00, "
            "com consultas começando em horas cheias ou meias horas (ex.: 09:00, 09:30)."
        )


def _horario_ocupado(db: Session, data_hora: datetime, **filtro) -> bool:
    consulta = db.scalar(
        select(Consulta.id).filter_by(
            data_hora=data_hora, status=StatusConsulta.AGENDADA, **filtro
        )
    )
    return consulta is not None


def agendar(db: Session, paciente_id: int, medico_id: int,
            data_hora: datetime, descricao: str | None) -> Consulta:
    paciente = db.get(Paciente, paciente_id)
    if paciente is None:
        raise ErroDeNegocio("Paciente não encontrado.", 404)
    medico = db.get(Medico, medico_id)
    if medico is None:
        raise ErroDeNegocio("Médico não encontrado.", 404)

    validar_horario(data_hora)

    if _horario_ocupado(db, data_hora, medico_id=medico_id):
        raise ErroDeNegocio("O médico já tem consulta nesse horário.", 409)
    if _horario_ocupado(db, data_hora, paciente_id=paciente_id):
        raise ErroDeNegocio("O paciente já tem outra consulta nesse horário.", 409)

    consulta = Consulta(
        paciente_id=paciente_id,
        medico_id=medico_id,
        data_hora=data_hora,
        descricao=descricao,
        status=StatusConsulta.AGENDADA,
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return consulta


def mudar_status(db: Session, consulta_id: int, novo_status: StatusConsulta) -> Consulta:
    """Cancela ou conclui uma consulta. Só consultas agendadas podem mudar."""
    consulta = db.get(Consulta, consulta_id)
    if consulta is None:
        raise ErroDeNegocio("Consulta não encontrada.", 404)
    if consulta.status != StatusConsulta.AGENDADA:
        raise ErroDeNegocio(
            f"Esta consulta já está {consulta.status.value} e não pode ser alterada.", 409
        )
    if novo_status == StatusConsulta.REALIZADA and consulta.data_hora > datetime.now():
        raise ErroDeNegocio("Não dá para concluir uma consulta que ainda não aconteceu.", 409)
    consulta.status = novo_status
    db.commit()
    db.refresh(consulta)
    return consulta


def horarios_livres(db: Session, medico_id: int, dia: date) -> list[str]:
    """Horários do dia em que o médico ainda está disponível."""
    if db.get(Medico, medico_id) is None:
        raise ErroDeNegocio("Médico não encontrado.", 404)

    inicio = datetime.combine(dia, time.min)
    fim = inicio + timedelta(days=1)
    ocupados = set(
        db.scalars(
            select(Consulta.data_hora).where(
                Consulta.medico_id == medico_id,
                Consulta.status == StatusConsulta.AGENDADA,
                Consulta.data_hora >= inicio,
                Consulta.data_hora < fim,
            )
        )
    )
    agora = datetime.now()
    return [
        h.strftime("%H:%M")
        for h in horarios_do_dia(dia)
        if h not in ocupados and h > agora
    ]
