import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class EstadoInscricao(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PAGA = "PAGA"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    eventos_organizados = relationship("Evento", back_populates="organizador")
    inscricoes = relationship("Inscricao", back_populates="usuario")

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizador_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(100), nullable=False)
    descricao = Column(String, nullable=True)
    data_hora = Column(DateTime, nullable=False)

    organizador = relationship("Usuario", back_populates="eventos_organizados")
    lotes = relationship("LoteIngresso", back_populates="evento")

class LoteIngresso(Base):
    __tablename__ = "lotes_ingresso"

    __table_args__ = (
        CheckConstraint('capacidade_total > 0', name='chk_capacidade_positiva'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"), nullable=False)
    nome = Column(String, nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    capacidade_total = Column(Integer, nullable=False)

    evento = relationship("Evento", back_populates="lotes")
    inscricoes = relationship("Inscricao", back_populates="lote")

class Inscricao(Base):
    __tablename__ = "inscricoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes_ingresso.id"), nullable=False)
    codigo_checkin = Column(String(50), unique=True, index=True, nullable=True)
    estado = Column(SQLEnum(EstadoInscricao), default=EstadoInscricao.PENDENTE, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="inscricoes")
    lote = relationship("LoteIngresso", back_populates="inscricoes")