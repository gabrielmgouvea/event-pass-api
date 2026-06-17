import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base
from app.core.dependencies import get_db

# 1. Conecta no PostgreSQL padrão apenas para criar o banco de testes isolado
default_engine = create_engine(
    "postgresql://postgres:postgres@db:5432/postgres", 
    isolation_level="AUTOCOMMIT"
)
with default_engine.connect() as conn:
    try:
        conn.execute(text("CREATE DATABASE eventos_test_db"))
    except Exception:
        pass  # Se o banco já existir, ele apenas ignora e segue

# 2. Configura a conexão exclusiva para os testes
TEST_DATABASE_URL = "postgresql://postgres:postgres@db:5432/eventos_test_db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    #Cria as tabelas limpas antes de cada teste e as destrói depois.
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    #Substitui o banco de produção da API pelo banco de testes durante as requisições
    def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

import uuid
from datetime import datetime, timedelta, timezone
from app.models.models import Usuario, Evento, LoteIngresso

@pytest.fixture(scope="function")
def usuario_comum(db_session):
    usuario = Usuario(nome="João", email="joao@teste.com")
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario

@pytest.fixture(scope="function")
def usuario_organizador(db_session):
    usuario = Usuario(nome="Maria", email="maria@organiza.com")
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario

@pytest.fixture(scope="function")
def evento_valido(db_session, usuario_organizador):
    data_futura = datetime.now(timezone.utc) + timedelta(days=30)
    evento = Evento(
        organizador_id=usuario_organizador.id, 
        titulo="Tech Conference 2026", 
        data_hora=data_futura
    )
    db_session.add(evento)
    db_session.commit()
    db_session.refresh(evento)
    return evento

@pytest.fixture(scope="function")
def lote_valido(db_session, evento_valido):
    lote = LoteIngresso(
        evento_id=evento_valido.id, 
        nome="Pista", 
        preco=100.0, 
        capacidade_total=2 # Capacidade baixa proposital para testar Overbooking
    )
    db_session.add(lote)
    db_session.commit()
    db_session.refresh(lote)
    return lote