from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.dependencies import get_db
from app.schemas.schemas import InscricaoCreate, InscricaoResponse
from app.services import inscricao_service
from app.models.models import Inscricao, EstadoInscricao

router = APIRouter(prefix="/inscricoes", tags=["Inscrições"])

@router.post("/", response_model=InscricaoResponse, status_code=201)
def criar_inscricao(dados: InscricaoCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova inscrição (Rascunho/Pendente).
    A regra de negócio e validação ficam isoladas na camada de serviço.
    """
    return inscricao_service.realizar_inscricao(db, dados)

@router.post("/{inscricao_id}/pagar", response_model=InscricaoResponse)
def pagar_inscricao(inscricao_id: UUID, db: Session = Depends(get_db)):
    """
    Realiza a transição de estado de uma inscrição para PAGA.
    """
    return inscricao_service.transicionar_para_paga(db, inscricao_id)

@router.get("/", response_model=List[InscricaoResponse])
def listar_inscricoes(
    estado: Optional[EstadoInscricao] = Query(None, description="Filtro opcional por estado da inscrição"),
    limit: int = Query(10, ge=1, le=100, description="Paginação: quantidade máxima de itens retornados"),
    offset: int = Query(0, ge=0, description="Paginação: quantidade de itens a serem ignorados (pulo)"),
    db: Session = Depends(get_db)
):
    """
    Lista inscrições utilizando paginação e filtros opcionais via Query Params.
    """
    query = db.query(Inscricao)
    
    if estado:
        query = query.filter(Inscricao.estado == estado)
        
    return query.offset(offset).limit(limit).all()