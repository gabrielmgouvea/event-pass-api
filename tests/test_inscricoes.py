import uuid
from datetime import datetime, timedelta, timezone
from app.models.models import EstadoInscricao

def test_criar_inscricao_sucesso(client, usuario_comum, lote_valido):
    """Testa o fluxo feliz: um usuário comum conseguindo se inscrever com vagas disponíveis."""
    payload = {
        "usuario_id": str(usuario_comum.id),
        "lote_id": str(lote_valido.id)
    }
    
    response = client.post("/inscricoes/", json=payload)
    
    assert response.status_code == 201
    dados = response.json()
    assert dados["estado"] == EstadoInscricao.PENDENTE.value
    assert "id" in dados

def test_rn002_organizador_nao_pode_inscrever_proprio_evento(client, usuario_organizador, lote_valido):
    """RN-002: O organizador do evento não pode comprar ingresso para ele mesmo."""
    payload = {
        "usuario_id": str(usuario_organizador.id),
        "lote_id": str(lote_valido.id)
    }
    
    response = client.post("/inscricoes/", json=payload)
    
    assert response.status_code == 403
    erro = response.json()
    assert erro["error"] == "ORGANIZER_CANNOT_PARTICIPATE"

def test_rn001_bloqueio_overbooking(client, usuario_comum, lote_valido):
    """RN-001: Valida se a API bloqueia inscrições quando a capacidade máxima é atingida."""
    # A fixture lote_valido tem capacidade_total = 2. Vamos esgotar as vagas.
    
    # 1ª Inscrição (Deve passar)
    client.post("/inscricoes/", json={"usuario_id": str(usuario_comum.id), "lote_id": str(lote_valido.id)})
    
    # 2ª Inscrição (Deve passar)
    client.post("/inscricoes/", json={"usuario_id": str(usuario_comum.id), "lote_id": str(lote_valido.id)})
    
    # 3ª Inscrição (Deve falhar por Overbooking)
    payload_excedente = {
        "usuario_id": str(usuario_comum.id),
        "lote_id": str(lote_valido.id)
    }
    response = client.post("/inscricoes/", json=payload_excedente)
    
    assert response.status_code == 409
    erro = response.json()
    assert erro["error"] == "CAPACITY_EXCEEDED"

def test_rn003_transicao_pagamento_valida(client, usuario_comum, lote_valido):
    """RN-003: Valida a transição de estado e geração do código de check-in."""
    # Primeiro cria a inscrição
    payload = {"usuario_id": str(usuario_comum.id), "lote_id": str(lote_valido.id)}
    criacao_resp = client.post("/inscricoes/", json=payload)
    inscricao_id = criacao_resp.json()["id"]
    
    # Agora tenta pagar
    pagamento_resp = client.post(f"/inscricoes/{inscricao_id}/pagar")
    
    assert pagamento_resp.status_code == 200
    dados = pagamento_resp.json()
    assert dados["estado"] == EstadoInscricao.PAGA.value
    assert dados["codigo_checkin"] is not None
    assert dados["codigo_checkin"].startswith("CHK-")

    import uuid
import pytest
from app.schemas.schemas import EventoCreate

def test_rn003_nao_pode_pagar_inscricao_ja_paga(client, usuario_comum, lote_valido):
    """Garante que uma inscrição não pode transicionar de PAGA para PAGA."""
    # 1. Cria e Paga a inscrição
    criacao = client.post("/inscricoes/", json={"usuario_id": str(usuario_comum.id), "lote_id": str(lote_valido.id)})
    inscricao_id = criacao.json()["id"]
    client.post(f"/inscricoes/{inscricao_id}/pagar")
    
    # 2. Tenta pagar de novo (Deve falhar)
    response = client.post(f"/inscricoes/{inscricao_id}/pagar")
    assert response.status_code == 422
    assert response.json()["error"] == "INVALID_STATE_TRANSITION"

def test_pagar_inscricao_inexistente(client):
    """Testa o tratamento de erro 404 para entidades inexistentes."""
    fake_uuid = str(uuid.uuid4())
    response = client.post(f"/inscricoes/{fake_uuid}/pagar")
    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"

def test_criar_inscricao_lote_inexistente(client, usuario_comum):
    """Garante que a inscrição falha se o lote referenciado não existir no banco."""
    fake_uuid = str(uuid.uuid4())
    payload = {"usuario_id": str(usuario_comum.id), "lote_id": fake_uuid}
    response = client.post("/inscricoes/", json=payload)
    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"

def test_listar_inscricoes_paginacao(client, usuario_comum, lote_valido):
    """Valida se o endpoint de listagem respeita o limite (limit) da paginação."""
    # Cria 2 inscrições
    client.post("/inscricoes/", json={"usuario_id": str(usuario_comum.id), "lote_id": str(lote_valido.id)})
    client.post("/inscricoes/", json={"usuario_id": str(usuario_comum.id), "lote_id": str(lote_valido.id)})
    
    # Pede apenas 1 item
    response = client.get("/inscricoes/?limit=1&offset=0")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_listar_inscricoes_filtro_estado(client, usuario_comum, lote_valido):
    """Valida se o filtro de query parameter por 'estado' está funcionando."""
    # Cria uma inscrição e a transforma em PAGA
    criacao = client.post("/inscricoes/", json={"usuario_id": str(usuario_comum.id), "lote_id": str(lote_valido.id)})
    inscricao_id = criacao.json()["id"]
    client.post(f"/inscricoes/{inscricao_id}/pagar")
    
    # Busca por inscrições PENDENTES (Não deve retornar nenhuma)
    response = client.get(f"/inscricoes/?estado={EstadoInscricao.PENDENTE.value}")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_rn005_validacao_evento_data_passada():
    """Valida o Pydantic (RN-005): Impede instanciar eventos no passado."""
    data_passada = datetime.now(timezone.utc) - timedelta(days=5)
    
    with pytest.raises(ValueError) as exc:
        EventoCreate(
            organizador_id=uuid.uuid4(),
            titulo="Evento Antigo",
            data_hora=data_passada
        )
    assert "A data do evento não pode ser no passado" in str(exc.value)