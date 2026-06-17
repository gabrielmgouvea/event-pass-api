from fastapi import FastAPI
from app.core.config import settings
from app.core.exceptions import DomainException, domain_exception_handler
from app.routers import inscricoes

app = FastAPI(
    title="API - Plataforma de Eventos",
    description="API para gestão de eventos com capacidade limitada e regras de negócio complexas."
)

# Registrando o handler global de exceções
app.add_exception_handler(DomainException, domain_exception_handler)

# Registrando as rotas
app.include_router(inscricoes.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "API da Plataforma de Eventos rodando perfeitamente!"
    }