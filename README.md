# 🩺 Agenda de Consultas — API

![Testes](https://github.com/jeffersonlucas0/agenda-consultas/actions/workflows/testes.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688)
![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1)

API REST para uma clínica cadastrar pacientes e agendar, cancelar e concluir consultas médicas.
O sistema impede conflitos de horário, respeita o horário de funcionamento e mostra os horários livres de cada médico.

Este projeto é a evolução de um [app de gerenciamento de consultas](https://github.com/jeffersonlucas0/python/blob/main/gerenciamentoConsultas.py) que fiz no começo do curso, com interface em Flet e dados salvos num arquivo JSON. Aqui reescrevi a lógica como uma API, com banco de dados relacional, regras de negócio isoladas e testes automatizados.

<!-- Coloque aqui um print da página /docs:  ![Documentação da API](docs/swagger.png) -->

## Funcionalidades

- Cadastro, busca, edição e remoção de pacientes, com **validação real de CPF** (dígitos verificadores).
- Cadastro de médicos e especialidades.
- Agendamento de consultas com regras de negócio:
  - não permite agendar no passado nem em fim de semana;
  - atendimento das 08:00 às 18:00, em horários de 30 em 30 minutos;
  - um médico não pode ter duas consultas no mesmo horário;
  - um paciente não pode estar em duas consultas ao mesmo tempo;
  - consulta cancelada libera o horário de novo.
- Cancelamento e conclusão de consultas (só dá para concluir depois que a consulta aconteceu).
- Consulta de **horários livres** de um médico num dia.
- Filtros de consultas por médico, paciente, especialidade, data e status.
- Documentação interativa gerada automaticamente (Swagger) em `/docs`.

## Tecnologias

| Para quê | Tecnologia |
|---|---|
| API | [FastAPI](https://fastapi.tiangolo.com/) |
| Banco de dados | MySQL 8 (ou SQLite para rodar sem instalar nada) |
| Acesso ao banco | SQLAlchemy 2 (ORM) |
| Validação de dados | Pydantic 2 |
| Testes | pytest |
| Containers | Docker e Docker Compose |
| Integração contínua | GitHub Actions |

## Modelo de dados

```mermaid
erDiagram
    ESPECIALIDADE ||--o{ MEDICO : tem
    MEDICO ||--o{ CONSULTA : atende
    PACIENTE ||--o{ CONSULTA : marca

    ESPECIALIDADE { int id string nome }
    MEDICO { int id string nome string crm int especialidade_id }
    PACIENTE { int id string nome string cpf date data_nascimento string telefone }
    CONSULTA { int id int paciente_id int medico_id datetime data_hora string descricao enum status }
```

## Como rodar

### Opção 1: Docker (API + MySQL)

Precisa ter o [Docker](https://docs.docker.com/get-docker/) instalado.

```bash
docker compose up --build
```

Abra http://localhost:8000/docs. A API já sobe com 7 especialidades e 14 médicos de exemplo.

### Opção 2: Python direto (com SQLite)

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Abra http://127.0.0.1:8000/docs. Os dados ficam no arquivo `consultas.db`.

Para usar MySQL nessa opção, copie `.env.example` para `.env` e preencha `DATABASE_URL`.

## Rotas principais

| Método | Rota | O que faz |
|---|---|---|
| `GET` | `/especialidades` | Lista especialidades |
| `GET` | `/medicos?especialidade_id=1` | Lista médicos (filtro opcional) |
| `GET` | `/medicos/{id}/horarios-livres?data=2026-11-10` | Horários livres do médico no dia |
| `POST` | `/pacientes` | Cadastra paciente |
| `GET` | `/pacientes?nome=ana` | Lista ou busca pacientes pelo nome |
| `PATCH` | `/pacientes/{id}` | Atualiza nome ou telefone |
| `DELETE` | `/pacientes/{id}` | Remove paciente sem histórico de consultas |
| `POST` | `/consultas` | Agenda consulta |
| `GET` | `/consultas?status=agendada&data=2026-11-10` | Lista consultas com filtros |
| `PATCH` | `/consultas/{id}/cancelar` | Cancela consulta |
| `PATCH` | `/consultas/{id}/concluir` | Marca consulta como realizada |

### Exemplo: agendar uma consulta

```bash
curl -X POST http://localhost:8000/consultas \
  -H "Content-Type: application/json" \
  -d '{"paciente_id": 1, "medico_id": 1, "data_hora": "2026-11-10T09:30:00", "descricao": "Retorno"}'
```

Se o médico já tiver consulta nesse horário, a resposta é `409 Conflict`:

```json
{ "detail": "O médico já tem consulta nesse horário." }
```

## Testes

```bash
pytest -v
```

São 21 testes que cobrem as regras de agendamento, a validação de CPF e os filtros.
Cada teste usa um banco SQLite novo em memória, então não precisa do MySQL rodando.

Para rodar os mesmos testes num MySQL de verdade (por exemplo, o do `docker compose`):

```bash
TEST_DATABASE_URL="mysql+pymysql://agenda:agenda123@localhost:3306/agenda_consultas" pytest -v
```

> ⚠️ Os testes apagam e recriam as tabelas do banco indicado. Use um banco só para testes.

No GitHub Actions, os testes rodam a cada push duas vezes: uma com SQLite e outra com MySQL 8.4.

## Estrutura do projeto

```
agenda-consultas/
├── app/
│   ├── main.py            # cria a API e registra as rotas
│   ├── database.py        # conexão com o banco
│   ├── models.py          # tabelas (SQLAlchemy)
│   ├── schemas.py         # formatos de entrada e saída (Pydantic)
│   ├── agendamento.py     # regras de negócio do agendamento
│   ├── seed.py            # dados de exemplo
│   └── routers/           # rotas separadas por assunto
├── tests/                 # testes automatizados (pytest)
├── docker-compose.yml     # MySQL + API
└── Dockerfile
```

## Decisões que tomei

- **Regras de negócio separadas das rotas** (`agendamento.py`). As rotas só recebem e devolvem dados. Isso deixa as regras fáceis de ler e de testar.
- **Cancelar em vez de apagar.** Consultas nunca são excluídas, só mudam de status. Assim o histórico do paciente fica preservado.
- **SQLite como padrão, MySQL no Docker.** Qualquer pessoa consegue rodar o projeto em um minuto, e o MySQL fica disponível para um ambiente mais próximo do real.

## Próximos passos

- [ ] Login com JWT e perfis (recepção, médico).
- [ ] Migrações de banco com Alembic.
- [ ] Impedir agendamentos simultâneos no mesmo horário com uma trava no banco.
- [ ] Front-end para a recepção usar a API.
- [ ] Deploy público da API.

## Autor

Feito por **Jefferson Lucas**, estudante de Engenharia de Software.

[GitHub](https://github.com/jeffersonlucas0) · [LinkedIn](https://www.linkedin.com/in/jefferson-lucas-750608350/)

Os médicos e pacientes usados nos exemplos são fictícios.
