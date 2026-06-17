import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories import crud
from app.schemas.schemas import InscricaoCreate
from app.core.exceptions import DomainException
from app.models.models import EstadoInscricao

def realizar_inscricao(db: Session, dados: InscricaoCreate):
    lote = crud.get_lote(db, dados.lote_id)
    if not lote:
        raise DomainException("NOT_FOUND", "Lote não encontrado.", 404)

    evento = crud.get_evento(db, lote.evento_id)
    if not evento:
        raise DomainException("NOT_FOUND", "Evento não encontrado.", 404)

    # RN-005: Evento Expirado
    if evento.data_hora.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise DomainException("EVENT_ALREADY_HAPPENED", "Não é possível se inscrever em eventos que já começaram.")

    # RN-002: Organizador Restrito
    if dados.usuario_id == evento.organizador_id:
        raise DomainException(
            "ORGANIZER_CANNOT_PARTICIPATE", 
            "O organizador não pode se inscrever no próprio evento.", 
            403
        )

    # RN-001: Bloqueio de Overbooking (Validando Cálculo Derivado)
    inscricoes_ativas = crud.contar_inscricoes_ativas_lote(db, lote.id)
    vagas_disponiveis = lote.capacidade_total - inscricoes_ativas

    if vagas_disponiveis <= 0:
        raise DomainException(
            "CAPACITY_EXCEEDED", 
            "Os ingressos para este lote estão esgotados.", 
            409,
            {"capacidade_total": lote.capacidade_total, "vagas_disponiveis": 0}
        )

    return crud.criar_inscricao(db, dados.usuario_id, dados.lote_id)

def transicionar_para_paga(db: Session, inscricao_id: uuid.UUID):
    inscricao = crud.get_inscricao(db, inscricao_id)
    if not inscricao:
        raise DomainException("NOT_FOUND", "Inscrição não encontrada.", 404)

    # RN-003: Transição de Pagamento (Validação de Máquina de Estados)
    if inscricao.estado != EstadoInscricao.PENDENTE:
        raise DomainException(
            "INVALID_STATE_TRANSITION", 
            "Apenas inscrições pendentes podem ser pagas.", 
            422,
            {"estado_atual": inscricao.estado}
        )

    # Gera o código de checkin na transição (História da Migration 2)
    codigo = f"CHK-{uuid.uuid4().hex[:8].upper()}"
    return crud.atualizar_estado_inscricao(db, inscricao, EstadoInscricao.PAGA, codigo)