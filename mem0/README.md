---
name: unir-mem0
description: Memoria verificada para o projeto UNIR usando mem0 cloud. Armazena factos politicos com metadados de verificacao, detecta staleness e contradicoes.
category: productivity
version: 1.0.0
created: 2026-07-27
---

# UNIR mem0 — Memoria Verificada

Sistema de memoria para o projeto UNIR baseado em mem0 cloud. Substitui a necessidade de procuras manuais por factos — o agente consulta a memoria e recebe resultados com indicacao de frescura.

## Estrutura de Dados

Cada facto armazenado tem:

| Campo | Descricao |
|-------|-----------|
| `memory` | Texto do facto |
| `user_id` | Sempre "unir-agent" |
| `metadata.entity` | Entidade: PS, BE, PSD, PR, AR, IL, CH, PCP, CDS-PP, PAN, L |
| `metadata.category` | Categoria: leadership, parliamentary, composition, audit |
| `metadata.verified` | True/False |
| `metadata.source` | Fonte: Wikipedia, SGMAI, INE, etc. |
| `metadata.verified_date` | Data de verificacao (YYYY-MM-DD) |

## Regras Temporais

Regras temporais com fallback progressivo:
  - Q atual (ultimos 3 meses): 🟢 FRESCO — confiavel
  - Q anterior (3-6 meses): 🟡 REVER — verificar antes de usar
  - >6 meses: 🔴 MELHOR DISPONIVEL — usar com aviso, requer nova verificacao
  - NUNCA retornar vazio se existe algum dado sobre a entidade. O fallback e sempre para o dado mais recente disponivel.
```

## Scripts

### `unir_mem0_add.py` — Adicionar factos

```bash
# Facto individual
python3 scripts/unir_mem0_add.py \
  --fact "Jose Luis Carneiro e o Secretario-Geral do PS desde 2025" \
  --entity PS --category leadership --source Wikipedia --date 2026-07-27

# Em lote (JSON)
python3 scripts/unir_mem0_add.py --batch novos_factos.json
```

### `unir_mem0_audit.py` — Auditar staleness e contradicoes

```bash
# Auditoria completa
python3 scripts/unir_mem0_audit.py

# Apenas factos obsoletos
python3 scripts/unir_mem0_audit.py --stale-only

# Entidade especifica
python3 scripts/unir_mem0_audit.py --entity PS
```

### `unir_mem0_search.py` — Pesquisar com frescura

```bash
# Pesquisa normal
python3 scripts/unir_mem0_search.py "lider do PS"

# Apenas factos recentes
python3 scripts/unir_mem0_search.py "composicao AR" --fresh-only

# Filtrar por entidade
python3 scripts/unir_mem0_search.py "deputados" --entity BE
```

## Workflow com Agente UNIR

1. **Antes de auditoria**: `unir_mem0_audit.py --stale-only` → lista factos a reverificar
2. **Durante auditoria**: `unir_mem0_search.py "<claim>" --fresh-only` → factos recentes para cruzar
3. **Apos verificacao**: `unir_mem0_add.py` → armazenar factos novos com `verified: True`
4. **Trimestralmente**: `unir_mem0_audit.py` → relatorio de staleness

## Setup

```bash
# Instalar o SDK
uv pip install --python /root/.hermes/hermes-agent/venv/bin/python mem0ai
```

Usar SEMPRE `MemoryClient` (cloud) para o UNIR, nunca `Memory.from_config()` (local). A abordagem cloud resolve LLM + embeddings sem depender de OpenAI key.

```python
from mem0 import MemoryClient
client = MemoryClient(api_key="m0-...")
```

## Pitfalls

### API: search() e get_all() devolvem `dict`, nao `list`

```python
# ❌ ERRADO
results = client.search("query", filters={...})
first = results[0]  # KeyError!

# ✅ CORRETO
raw = client.search("query", filters={...})
results = raw.get("results", raw) if isinstance(raw, dict) else raw
first = results[0] if results else None
```

### API: filtros usam `categories` (plural), nao `category`

```python
# ❌ ERRADO
filters={"category": "leadership"}  # Unknown filter key

# ✅ CORRETO
filters={"user_id": "unir-agent"}  # user_id e valido
# categories so funciona como filtro pre-definido, nao como metadata custom
```

### API: `MemoryClient` vs `Memory`

- `MemoryClient(api_key=...)` — cloud platform. LLM e embeddings geridos pela mem0.
- `Memory.from_config({...})` — local/self-hosted. Requer OpenAI key para LLM + embeddings.
- O UNIR usa `MemoryClient` com API key fornecida pelo Rafael.

### Contradicao detection funciona com semantic search

O search semantico retorna TODOS os factos relevantes, incluindo historicos. Isto e uma feature: se ha 2 nomes diferentes para a mesma entidade (ex: "Jose Luis Carneiro" e "Pedro Nuno Santos" para PS), o search revela a contradicao automaticamente.

- Factos historicos (ex: "Pedro Nuno Santos era lider do PS em 2024") devem ter `verified_date` antiga para aparecerem como 🔴 OBSOLETO
- NUNCA apagar factos antigos — adicionar novos com `verified_date` atual. O sistema de staleness distingue automaticamente.
- API key hardcoded nos scripts — em producao, usar variavel de ambiente
