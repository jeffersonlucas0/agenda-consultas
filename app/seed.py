"""Dados de exemplo: especialidades e médicos fictícios.

Rode manualmente com:  python -m app.seed
A API também chama isso ao iniciar, se o banco estiver vazio.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Especialidade, Medico

MEDICOS_POR_ESPECIALIDADE = {
    "Cardiologia": ["Dr. João Almeida", "Dra. Maria Souza"],
    "Pediatria": ["Dra. Clara Lima", "Dr. Pedro Rocha"],
    "Dermatologia": ["Dra. Ana Ribeiro", "Dr. Marcos Pinto"],
    "Ortopedia": ["Dr. Lucas Martins", "Dra. Helena Costa"],
    "Clínica Geral": ["Dr. Fernando Alves", "Dra. Paula Mendes"],
    "Neurologia": ["Dr. Roberto Dias", "Dra. Juliana Freitas"],
    "Oftalmologia": ["Dr. Carlos Nunes", "Dra. Sofia Barros"],
}


def carregar_dados_exemplo(db: Session) -> bool:
    """Cadastra os dados de exemplo se ainda não houver especialidades.

    Retorna True se cadastrou alguma coisa.
    """
    if db.scalar(select(Especialidade.id)) is not None:
        return False

    numero_crm = 10001
    for nome_especialidade, medicos in MEDICOS_POR_ESPECIALIDADE.items():
        especialidade = Especialidade(nome=nome_especialidade)
        db.add(especialidade)
        for nome_medico in medicos:
            db.add(Medico(nome=nome_medico, crm=f"CRM-CE {numero_crm}",
                          especialidade=especialidade))
            numero_crm += 1
    db.commit()
    return True


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as sessao:
        if carregar_dados_exemplo(sessao):
            print("Dados de exemplo cadastrados.")
        else:
            print("O banco já tem dados. Nada foi alterado.")
