from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID
from app.models.models import EstadoInscricao

# --- USUARIO ---
class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

# --- EVENTO ---
class EventoCreate(BaseModel):
    organizador_id: UUID
    titulo: str = Field(..., min_length=3, max_length=100)
    descricao: Optional[str] = None
    data_hora: datetime

    @model_validator(mode='after')
    def validar_data_futura(self) -> 'EventoCreate':
        # Garante que a data do evento seja no futuro no momento da criação
        if self.data_hora.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError('A data do evento não pode ser no passado.')
        return self

class EventoResponse(BaseModel):
    id: UUID
    organizador_id: UUID
    titulo: str
    descricao: Optional[str]
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)

# --- LOTE INGRESSO ---
class LoteIngressoCreate(BaseModel):
    evento_id: UUID
    nome: str = Field(..., min_length=2)
    preco: float = Field(..., ge=0)
    capacidade_total: int = Field(..., gt=0)

class LoteIngressoResponse(BaseModel):
    id: UUID
    evento_id: UUID
    nome: str
    preco: float
    capacidade_total: int

    model_config = ConfigDict(from_attributes=True)

# --- INSCRICAO ---
class InscricaoCreate(BaseModel):
    usuario_id: UUID
    lote_id: UUID

class InscricaoResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    lote_id: UUID
    estado: EstadoInscricao
    codigo_checkin: Optional[str]
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)