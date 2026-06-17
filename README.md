# API - Plataforma de Eventos (EventPass)

Esta é uma API RESTful completa desenvolvida em FastAPI para a gestão de eventos com capacidade limitada. O sistema foi projetado com foco estrito em **Domain-Driven Design (DDD)**, isolamento de regras de negócio, e tolerância a falhas, garantindo a integridade dos dados mesmo em cenários de alta concorrência.

## 1. Visão Geral do Domínio e Diagrama ER

O domínio modela uma plataforma onde Usuários podem organizar Eventos. Cada Evento possui Lotes de Ingressos (com preços e capacidades distintas). Os Usuários podem realizar Inscrições (reservas) nestes lotes, que passam por uma máquina de estados rigorosa.

`````````text
+----------------+       +-------------------+       +-----------------------+
|    USUARIO     |       |      EVENTO       |       |    LOTE_INGRESSO      |
+----------------+       +-------------------+       +-----------------------+
| id (UUID) [PK] |<----1-| organizador_id    |     1 | id (UUID) [PK]        |
| nome           |     N | id (UUID) [PK]    |---N-->| evento_id             |
| email          |       | titulo            |       | capacidade_total      |
| criado_em      |       | data_hora         |       | preco                 |
+----------------+       +-------------------+       +-----------------------+
^  ^                                                      ^
|  |                                                      |
|  |               +-------------------+                  |
|  +-------------1-|    INSCRICAO      |-N----------------+
+----------------N-| id (UUID) [PK]    |
| usuario_id        |
| lote_id           |
| estado (Enum)     |
| codigo_checkin    |
| criado_em         |
+-------------------+
`````````

## 2. Como Rodar Localmente e Testar

Toda a aplicação e dependências (PostgreSQL) estão conteinerizadas.

Clone o repositório.

Crie um arquivo .env baseado no .env.example.

Suba a infraestrutura:
`````````bash
docker compose up --build
`````````

Em outro terminal, aplique as migrações (Alembic) para criar as tabelas:
`````````bash
docker compose exec api alembic upgrade head
`````````

Acesse a documentação Swagger interativa: ```http://localhost:8000/docs```

Para rodar a suíte de testes unitários isolados (10 testes):
`````````bash
docker compose run api pytest
`````````

## 3. Regras de Negócio Implementadas

| ID | Nome | Ação e Violação Esperada |
| ----- | ----- | ----- |
| **RN-001** | Bloqueio de Overbooking | Valida a capacidade do lote antes de criar a inscrição. Calcula dinamicamente as vagas restantes. Violação: ```409 CAPACITY_EXCEEDED```. |
| **RN-002** | Organizador Restrito | Impede que o organizador do evento se inscreva no próprio evento. Violação: ```403 ORGANIZER_CANNOT_PARTICIPATE```. |
| **RN-003** | Transição de Pagamento | Inscrições só podem transicionar para ```PAGA``` se o estado atual for estritamente ```PENDENTE```. Violação: ```422 INVALID_STATE_TRANSITION```. |
| **RN-004** | Cancelamento Tardio | Impede a transição para ```CANCELADA``` se a data do evento já passou. Violação: ```400 CANCELLATION_TIMEOUT```. |
| **RN-005** | Evento Expirado | Bloqueia novas inscrições para eventos cujas datas já estão no passado. Violação: ```400 EVENT_ALREADY_HAPPENED```. 


## 4. Decisões de Design Justificadas (Seção 5.1)

Nesta seção, respondo às questões de design arquitetural e escolhas técnicas exigidas pela avaliação:

**Por que modelou os relacionamentos dessa forma e não de outra?**
O modelo reflete a realidade de uma plataforma de bilheteria. O ```Evento``` foi separado do ```LoteIngresso``` porque um mesmo evento frequentemente possui setores diferentes (ex: Pista, Camarote) com capacidades e preços diferentes. Relacionar a ```Inscricao``` diretamente ao ```LoteIngresso``` (e não ao Evento genérico) garante o cálculo de capacidade exato por setor e facilita a auditoria financeira.

**Por que escolheu colocar determinada regra no validator do Pydantic versus na camada de serviço?**
Adotei a estratégia de !Fail Fast!. Regras estáticas (como "data_hora não pode ser no passado" - RN-005) estão no ```@model_validator``` do Pydantic para invalidar a requisição logo na entrada, poupando processamento. Regras que dependem do contexto do banco (como capacidade do lote - RN-001) foram alocadas exclusivamente na camada de ```services``` (Regra de Negócio).

**Por que a migration 2 foi necessária? O que mudou no entendimento do domínio?**
Durante o desenvolvimento, percebeu-se a necessidade do mundo físico: a portaria do evento. Foi adicionada a coluna ```codigo_checkin``` na Inscrição (com índice para busca rápida), gerado apenas quando a inscrição transiciona para ```PAGA```.

**Qual seria o comportamento correto se dois usuários tentassem modificar o mesmo recurso simultaneamente? (Race condition)**
Se duas pessoas tentarem criar a última inscrição disponível no exato mesmo milissegundo, o comportamento correto é que a primeira requisição que chegar ao banco trave a linha correspondente, e a segunda aguarde e falhe. Atualmente, mitigamos isso via transações puras (```db.commit()```), mas a implementação ideal em um cenário real seria o uso de **Pessimistic Locking** (```with_for_update()``` no SQLAlchemy), que faria o PostgreSQL aplicar um lock a nível de linha no Lote.

**Quais estados são terminais? Por que não faz sentido retornar de um estado terminal?**
Os estados ```CONFIRMADA``` (check-in realizado) e ```CANCELADA``` são terminais. Não faz sentido, por exemplo, retornar uma inscrição de ```CANCELADA``` para ```PENDENTE``` porque, no momento do cancelamento, a vaga foi devolvida à "pool" de capacidade e pode ter sido comprada por outro utilizador. Retornar de um estado terminal geraria overbooking (vender a mesma cadeira duas vezes) e inconsistência de caixa.

## 5. Consistência em Cenários de Borda (Seção 5.2)

Foram identificados, mapeados e tratados os seguintes !edge cases! (cenários de borda) no domínio da aplicação:

**1. O que acontece quando um recurso limitado (vagas) chega a zero?**

**Decisão:** O sistema bloqueia a transação e retorna um HTTP 409 com o código interno ```CAPACITY_EXCEEDED```.

**Tratamento Específico (Bug Descoberto):** Durante a criação dos testes (```pytest```), percebemos que o cálculo derivado contava apenas inscrições "Pagas". Isso causaria um "Overbooking Fantasma", onde utilizadores gerariam reservas (Pendente) excedendo o local. O sistema foi ajustado para que o cálculo abata vagas também de inscrições ```PENDENTES```.

**2. O que acontece quando se tenta modificar uma entidade em estado terminal?**

**Decisão:** O sistema recusa a modificação e retorna HTTP 422 com código ```INVALID_STATE_TRANSITION```.

**Justificativa:** Se um utilizador atualizar a página repetidas vezes ou houver duplo clique, o serviço verifica o estado atual. Apenas inscrições estritamente ```PENDENTES``` sofrem transição para pagamento, mantendo a operação segura e idempotente.

**3. O que acontece quando uma entidade pai é deletada e possui filhos ativos?**

**Decisão:** Não foi implementado !Cascade Delete! (deleção em cascata). O sistema bloqueará a exclusão na camada do banco de dados (PostgreSQL lança erro de Foreign Key).

**Justificativa:** Numa plataforma financeira, deletar um ```Evento``` que já possui inscrições ativas corromperia a prestação de contas. A consistência referencial do banco de dados funciona como a última barreira de proteção, exigindo que as inscrições sejam canceladas/estornadas antes de qualquer deleção de lotes ou eventos.