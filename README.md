# spedy-api

SDK Python para a [API Spedy](https://api.spedy.com.br/v1) — plataforma SaaS de automação fiscal para emissão de NF-e e NFS-e.

## Instalação

```bash
pip install spedy-api
```

Para instalar em modo de desenvolvimento com dependências de teste:

```bash
pip install -e ".[dev]"
```

## Configuração

```python
from spedy_api import SpedyClient

# Produção
client = SpedyClient(api_key="SUA_CHAVE")

# Sandbox (requer registro separado e chave própria)
client = SpedyClient(api_key="SUA_CHAVE_SANDBOX", environment="sandbox")
```

A chave de API é por empresa (CNPJ) e enviada automaticamente no header `X-Api-Key` em todas as requisições.

## Recursos disponíveis

### Empresas (`client.companies`)

```python
# Criar empresa
client.companies.create({...})

# Listar empresas
client.companies.list(page=1, page_size=20)

# Buscar empresa por ID
client.companies.get("id-da-empresa")

# Atualizar empresa
client.companies.update("id-da-empresa", {...})

# Remover empresa
client.companies.delete("id-da-empresa")

# Upload de certificado A1 (.pfx)
client.companies.upload_certificate("id-da-empresa", "certificado.pfx", "senha")

# Atualizar configurações da empresa
client.companies.update_settings("id-da-empresa", {...})
```

### NFS-e — Nota Fiscal de Serviços (`client.service_invoices`)

```python
from spedy_api.models import (
    ServiceInvoice, ServiceInvoiceTotals,
    Receiver, Address, City,
)

nota = ServiceInvoice(
    integration_id="pedido-123",       # idempotência (máx. 36 chars)
    effective_date="2026-04-22",
    description="Desenvolvimento de software",
    federal_service_code="01.07",
    city_service_code="7319",
    taxation_type="taxationInMunicipality",
    receiver=Receiver(
        name="Empresa Tomadora Ltda",
        federal_tax_number="12345678000195",
        email="financeiro@tomadora.com.br",
        address=Address(
            street="Av. Paulista",
            number="1000",
            district="Bela Vista",
            postal_code="01310100",
            city=City(code="3550308"),  # código IBGE preferível a nome+estado
        ),
    ),
    total=ServiceInvoiceTotals(
        invoice_amount=1500.00,
        iss_rate=5.0,
        iss_amount=75.00,
        iss_withheld=False,
    ),
)

# Emitir nota
response = client.service_invoices.create(nota.to_dict())

# Listar notas (com filtros opcionais de data)
client.service_invoices.list(
    page=1,
    effective_date_start="2026-01-01",
    effective_date_end="2026-04-30",
)

# Buscar nota por ID
client.service_invoices.get("id-da-nota")

# Cancelar nota
client.service_invoices.cancel("id-da-nota", justification="Erro no valor informado")

# Reemitir nota manualmente
client.service_invoices.issue("id-da-nota")

# Verificar status no SEFAZ/município
client.service_invoices.check_status("id-da-nota")

# Reenviar e-mail ao tomador
client.service_invoices.resend_email("id-da-nota")

# Baixar XML e PDF
xml_bytes = client.service_invoices.get_xml("id-da-nota")
pdf_bytes = client.service_invoices.get_pdf("id-da-nota")

# Listar municípios disponíveis
client.service_invoices.list_cities(state="SP")
```

### NF-e — Nota Fiscal de Produto (`client.product_invoices`)

```python
from spedy_api.models import (
    ProductInvoice, ProductInvoiceItem, ProductInvoiceTotals,
    ItemTaxes, IcmsTax, PisCofinsTax, Payment,
    Receiver, Address, City,
)

nota = ProductInvoice(
    integration_id="venda-456",
    effective_date="2026-04-22",
    operation_type="outgoing",
    destination="internal",
    presence_type="internet",
    operation_nature="Venda de mercadoria",
    is_final_customer=True,
    receiver=Receiver(
        name="João da Silva",
        federal_tax_number="98765432100",
        address=Address(
            street="Rua das Flores",
            number="42",
            district="Centro",
            postal_code="01001000",
            city=City(code="3550308"),
        ),
    ),
    items=[
        ProductInvoiceItem(
            code="PROD-001",
            description="Teclado mecânico",
            ncm="84716021",
            cfop=5102,
            unit="UN",
            quantity=1,
            unit_amount=350.00,
            total_amount=350.00,
            taxes=ItemTaxes(
                icms=IcmsTax(origin=0, csosn=400),
                pis=PisCofinsTax(cst=7),
                cofins=PisCofinsTax(cst=7),
            ),
        )
    ],
    payments=[Payment(method="creditCard", amount=350.00)],
    total=ProductInvoiceTotals(invoice_amount=350.00, product_amount=350.00),
)

# Emitir nota
response = client.product_invoices.create(nota.to_dict())

# Listar notas
client.product_invoices.list(page=1, page_size=20)

# Buscar nota por ID
client.product_invoices.get("id-da-nota")

# Cancelar nota
client.product_invoices.cancel("id-da-nota", justification="Devolução solicitada pelo cliente")

# Adicionar carta de correção (CC-e)
client.product_invoices.add_correction("id-da-nota", description="Correção no endereço do destinatário")

# Reemitir, verificar status, reenviar e-mail, baixar XML/PDF
client.product_invoices.issue("id-da-nota")
client.product_invoices.check_status("id-da-nota")
client.product_invoices.resend_email("id-da-nota")
xml_bytes = client.product_invoices.get_xml("id-da-nota")
pdf_bytes = client.product_invoices.get_pdf("id-da-nota")

# Inutilização de numeração
client.product_invoices.list_disablements()
client.product_invoices.create_disablement({...})
```

## Fluxo de emissão

A emissão é **assíncrona**. O retorno imediato do `create` tem `status: "enqueued"`. A Spedy transmite a nota ao SEFAZ ou prefeitura e notifica sua aplicação via webhook quando o resultado estiver disponível (tempo médio inferior a 10 segundos).

```
POST /service-invoices  →  status: enqueued
         ↓  (Spedy transmite à prefeitura)
webhook: invoice.authorized  |  invoice.rejected
```

**Prefira webhooks a polling.** Caso precise verificar manualmente, use `check_status`.

### Webhooks

Spedy envia um `POST` ao endpoint configurado nos seguintes eventos:

| Evento | Descrição |
|---|---|
| `invoice.authorized` | Nota autorizada pelo SEFAZ/prefeitura |
| `invoice.rejected` | Nota rejeitada (verifique `processingDetail.message`) |
| `invoice.canceled` | Nota cancelada com sucesso |
| `invoice.status_changed` | Mudança de status genérica |

Payload:
```json
{
  "id": "<uuid-do-evento>",
  "event": "invoice.authorized",
  "data": { ... }
}
```

## Tratamento de erros

```python
from spedy_api.exceptions import (
    ValidationError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SpedyServerError,
)

try:
    response = client.service_invoices.create(nota.to_dict())
except ValidationError as e:
    print("Erros de validação:", e.errors)
except AuthenticationError:
    print("Chave de API inválida ou sem permissão")
except NotFoundError:
    print("Recurso não encontrado")
except RateLimitError as e:
    print(f"Limite de requisições atingido. Reset em: {e.reset}")
except SpedyServerError as e:
    print(f"Erro no servidor Spedy: {e.status_code}")
```

### Limites de taxa

60 requisições/minuto e 5 requisições/segundo por chave de API. Os headers `x-rate-limit-remaining` e `x-rate-limit-reset` são retornados em todas as respostas.

## idempotência com `integration_id`

Recomenda-se fortemente informar o `integration_id` (máx. 36 caracteres) em todas as emissões. Ele funciona como chave de idempotência: reenviar uma requisição com o mesmo `integration_id` atualiza a nota existente em vez de criar uma duplicata. Use o ID natural do seu sistema (ID do pedido, transação etc.).

## Validação local

Os modelos `ServiceInvoice` e `ProductInvoice` expõem o método `is_valid()` para checar campos obrigatórios antes de fazer a requisição:

```python
if not nota.is_valid():
    raise ValueError("Nota inválida — verifique os campos obrigatórios")
```

## Testes

```bash
pytest
pytest --cov=spedy_api
```

Os testes usam a biblioteca `responses` para interceptar chamadas HTTP sem tocar na API real.

## Licença

Consulte o arquivo [LICENSE](LICENSE).
