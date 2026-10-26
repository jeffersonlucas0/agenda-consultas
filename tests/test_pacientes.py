from tests.conftest import CPF_VALIDO, OUTRO_CPF_VALIDO


def test_cadastra_paciente_e_guarda_cpf_so_com_numeros(cliente):
    resposta = cliente.post(
        "/pacientes",
        json={"nome": "Ana Beatriz", "cpf": CPF_VALIDO, "data_nascimento": "2001-05-20"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["cpf"] == "52998224725"


def test_recusa_cpf_invalido(cliente):
    resposta = cliente.post(
        "/pacientes",
        json={"nome": "Ana Beatriz", "cpf": "123.456.789-00", "data_nascimento": "2001-05-20"},
    )
    assert resposta.status_code == 422


def test_recusa_cpf_com_todos_digitos_iguais(cliente):
    resposta = cliente.post(
        "/pacientes",
        json={"nome": "Ana Beatriz", "cpf": "111.111.111-11", "data_nascimento": "2001-05-20"},
    )
    assert resposta.status_code == 422


def test_recusa_cpf_repetido(cliente, paciente):
    resposta = cliente.post(
        "/pacientes",
        json={"nome": "Outra Pessoa", "cpf": CPF_VALIDO, "data_nascimento": "1990-01-01"},
    )
    assert resposta.status_code == 409


def test_recusa_nascimento_no_futuro(cliente):
    resposta = cliente.post(
        "/pacientes",
        json={"nome": "Bebê do Futuro", "cpf": OUTRO_CPF_VALIDO, "data_nascimento": "2999-01-01"},
    )
    assert resposta.status_code == 422


def test_busca_paciente_por_parte_do_nome(cliente, paciente):
    cliente.post(
        "/pacientes",
        json={"nome": "Carlos Eduardo", "cpf": OUTRO_CPF_VALIDO, "data_nascimento": "1985-03-10"},
    )
    resposta = cliente.get("/pacientes", params={"nome": "beat"})
    nomes = [p["nome"] for p in resposta.json()]
    assert nomes == ["Ana Beatriz"]


def test_atualiza_so_o_telefone(cliente, paciente):
    resposta = cliente.patch(f"/pacientes/{paciente['id']}", json={"telefone": "(88) 99999-0000"})
    assert resposta.status_code == 200
    assert resposta.json()["telefone"] == "(88) 99999-0000"
    assert resposta.json()["nome"] == "Ana Beatriz"


def test_remove_paciente_sem_consultas(cliente, paciente):
    assert cliente.delete(f"/pacientes/{paciente['id']}").status_code == 204
    assert cliente.get(f"/pacientes/{paciente['id']}").status_code == 404
