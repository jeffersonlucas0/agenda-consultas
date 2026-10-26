from datetime import datetime, time, timedelta

from app.models import Consulta, StatusConsulta
from tests.conftest import OUTRO_CPF_VALIDO, horario_valido, proximo_dia_util


def agendar(cliente, paciente, medico, data_hora=None):
    return cliente.post(
        "/consultas",
        json={
            "paciente_id": paciente["id"],
            "medico_id": medico["id"],
            "data_hora": data_hora or horario_valido(),
            "descricao": "Dor no peito ao subir escadas",
        },
    )


def test_agenda_consulta(cliente, paciente, medico):
    resposta = agendar(cliente, paciente, medico)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "agendada"
    assert corpo["paciente"]["nome"] == "Ana Beatriz"
    assert corpo["medico"]["especialidade"]["nome"] == "Cardiologia"


def test_nao_agenda_no_passado(cliente, paciente, medico):
    ontem = (datetime.now() - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    resposta = agendar(cliente, paciente, medico, ontem.isoformat())
    assert resposta.status_code == 400
    assert "passado" in resposta.json()["detail"]


def test_nao_agenda_no_fim_de_semana(cliente, paciente, medico):
    dia = proximo_dia_util()
    while dia.weekday() != 5:  # avança até o sábado
        dia += timedelta(days=1)
    resposta = agendar(cliente, paciente, medico, datetime.combine(dia, time(10)).isoformat())
    assert resposta.status_code == 400


def test_nao_agenda_fora_do_horario_de_atendimento(cliente, paciente, medico):
    assert agendar(cliente, paciente, medico, horario_valido(7, 30)).status_code == 400
    assert agendar(cliente, paciente, medico, horario_valido(18, 0)).status_code == 400


def test_nao_agenda_em_minuto_quebrado(cliente, paciente, medico):
    assert agendar(cliente, paciente, medico, horario_valido(10, 15)).status_code == 400


def test_medico_nao_pode_ter_duas_consultas_no_mesmo_horario(cliente, paciente, medico):
    agendar(cliente, paciente, medico)
    outro_paciente = cliente.post(
        "/pacientes",
        json={"nome": "Carlos Eduardo", "cpf": OUTRO_CPF_VALIDO, "data_nascimento": "1985-03-10"},
    ).json()
    resposta = agendar(cliente, outro_paciente, medico)
    assert resposta.status_code == 409


def test_horario_volta_a_ficar_livre_depois_de_cancelar(cliente, paciente, medico):
    consulta = agendar(cliente, paciente, medico).json()
    cliente.patch(f"/consultas/{consulta['id']}/cancelar")
    assert agendar(cliente, paciente, medico).status_code == 201


def test_nao_cancela_consulta_ja_cancelada(cliente, paciente, medico):
    consulta = agendar(cliente, paciente, medico).json()
    assert cliente.patch(f"/consultas/{consulta['id']}/cancelar").status_code == 200
    assert cliente.patch(f"/consultas/{consulta['id']}/cancelar").status_code == 409


def test_nao_conclui_consulta_futura(cliente, paciente, medico):
    consulta = agendar(cliente, paciente, medico).json()
    assert cliente.patch(f"/consultas/{consulta['id']}/concluir").status_code == 409


def test_conclui_consulta_que_ja_aconteceu(cliente, sessao, paciente, medico):
    # A API não deixa agendar no passado, então criamos direto no banco.
    passada = Consulta(
        paciente_id=paciente["id"], medico_id=medico["id"],
        data_hora=datetime.now() - timedelta(hours=2), status=StatusConsulta.AGENDADA,
    )
    sessao.add(passada)
    sessao.commit()
    resposta = cliente.patch(f"/consultas/{passada.id}/concluir")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "realizada"


def test_horarios_livres_some_quando_agendado(cliente, paciente, medico):
    dia = proximo_dia_util().isoformat()
    antes = cliente.get(f"/medicos/{medico['id']}/horarios-livres", params={"data": dia}).json()
    assert len(antes["horarios"]) == 20  # das 08:00 às 17:30
    assert "10:00" in antes["horarios"]

    agendar(cliente, paciente, medico, horario_valido(10, 0))

    depois = cliente.get(f"/medicos/{medico['id']}/horarios-livres", params={"data": dia}).json()
    assert "10:00" not in depois["horarios"]
    assert len(depois["horarios"]) == 19


def test_filtra_consultas_por_status(cliente, paciente, medico):
    primeira = agendar(cliente, paciente, medico, horario_valido(9, 0)).json()
    agendar(cliente, paciente, medico, horario_valido(11, 0))
    cliente.patch(f"/consultas/{primeira['id']}/cancelar")

    canceladas = cliente.get("/consultas", params={"status": "cancelada"}).json()
    assert [c["id"] for c in canceladas] == [primeira["id"]]


def test_nao_remove_paciente_com_historico(cliente, paciente, medico):
    agendar(cliente, paciente, medico)
    assert cliente.delete(f"/pacientes/{paciente['id']}").status_code == 409
