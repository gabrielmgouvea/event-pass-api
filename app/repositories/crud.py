from sqlalchemy.orm import Session
from uuid import UUID
from app.models.models import Evento, LoteIngresso, Inscricao, EstadoInscricao

def get_evento(db: Session, evento_id: UUID):
    return db.query(Evento).filter(Evento.id == evento_id).first()

def get_lote(db: Session, lote_id: UUID):
    return db.query(LoteIngresso).filter(LoteIngresso.id == lote_id).first()

def get_inscricao(db: Session, inscricao_id: UUID):
    return db.query(Inscricao).filter(Inscricao.id == inscricao_id).first()

# Cálculo Derivado exigido no projeto
def contar_inscricoes_ativas_lote(db: Session, lote_id: UUID) -> int:
    return db.query(Inscricao).filter(
        Inscricao.lote_id == lote_id,
        Inscricao.estado.in_([EstadoInscricao.PENDENTE, EstadoInscricao.PAGA, EstadoInscricao.CONFIRMADA])
    ).count()

def criar_inscricao(db: Session, usuario_id: UUID, lote_id: UUID):
    nova_inscricao = Inscricao(
        usuario_id=usuario_id, 
        lote_id=lote_id, 
        estado=EstadoInscricao.PENDENTE
    )
    db.add(nova_inscricao)
    db.commit()
    db.refresh(nova_inscricao)
    return nova_inscricao

def atualizar_estado_inscricao(db: Session, inscricao: Inscricao, novo_estado: EstadoInscricao, codigo_checkin: str = None):
    inscricao.estado = novo_estado
    if codigo_checkin:
        inscricao.codigo_checkin = codigo_checkin
    db.commit()
    db.refresh(inscricao)
    return inscricao