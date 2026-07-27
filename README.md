# UNIR Agent — Documentacao Tecnica

**Versao:** 2.0.0 (27 Jul 2026)
**Repositorio:** [portugal-political-intelligence](https://github.com/rafatocantins/portugal-political-intelligence)

---

## Visao Geral

O UNIR Agent e um agente especializado em auditoria documental e inteligencia
politica para o projeto UNIR. Opera dentro do Hermes Agent, usando skills
dedicadas e um sistema de memoria em duas camadas.

## Arquitetura

```
┌─────────────────────────────────────────┐
│              HERMES AGENT               │
│  (deepseek-v4-pro, ferramentas, cron)   │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │   SKILLS     │  │     MEMORIA      │  │
│  │              │  │                  │  │
│  │ auditoria    │  │ CAMADA 1: mem0   │  │
│  │ red-team     │  │ (cloud, dinamica)│  │
│  │ unir-mem0    │  │                  │  │
│  │              │  │ CAMADA 2: blocos │  │
│  │              │  │ (.md, estatica)  │  │
│  └─────────────┘  └──────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │         GOOGLE DRIVE              │   │
│  │  Docs publicados + Auditorias     │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Skills

| Skill | Funcao | Gatilho |
|-------|--------|---------|
| `unir-auditoria-completa` | Pipeline 4 Caminhos (A/B/C/D) | "audita o documento X" |
| `unir-red-team` | 3 vetores de ataque, score /30 | Automatico no Passo 9 |
| `unir-mem0` | Memoria verificada com fallback temporal | Passos 0, 3.1, 9.0 |
| `unir-documento-setorial-workflow` | Criar novos docs setoriais | "cria documento sobre X" |
| `google-docs-formatting` | Formatar e publicar Google Docs | Publicacao |

## Sistema de Memoria (Duas Camadas)

### Camada 1: mem0 (Dinamica, Cloud)

- **Onde:** api.mem0.ai (user: `unir-agent`)
- **O que guarda:** Factos verificados com metadados (entidade, fonte, data, fiabilidade)
- **Regras temporais:** 🟢 FRESCO (<3m) → 🟡 REVER (3-6m) → 🔴 MELHOR DISPONIVEL
- **Fallback:** Nunca retorna vazio. Se nao ha dados recentes, usa o mais proximo.
- **Scripts:** `unir_mem0_add.py`, `unir_mem0_audit.py`, `unir_mem0_search.py`

### Camada 2: Blocos .md (Estatica, Local)

- **Onde:** `/root/.hermes/memories/blocks/projetos/unir/`
- **O que guarda:** Estado dos projetos, pipeline, referencias, mapa de poder
- **Blocos ativos:** `estado.md`, `auditoria-pipeline.md`, `mapa-poder-portugal.md`, `ambiente.md`, `ambiente-faq.md`
- **Sincronizacao:** `sync_affinities.py` diario as 03:00

## Pipeline de Auditoria com mem0

```
PASSO 0: PREPARACAO
  ├── 0.1: unir_mem0_audit.py --stale-only  → factos obsoletos
  └── 0.2: unir_mem0_search.py              → dados mais recentes (com fallback)

PASSOS 1-3: EXTRACAO, VERIFICACAO, CLASSIFICACAO
  └── 3.1: unir_mem0_add.py                 → guardar factos verificados

PASSOS 4-8: TABELA, CORRECOES, REFERENCIAS, PUBLICAR

PASSO 9: RED TEAM
  └── 9.0: unir_mem0_audit.py               → detetar contradicoes
```

## Regras Absolutas

1. **Fontes primarias sempre** — INE, Eurostat, OCDE, PORDATA, .gov.pt
2. **Loop de validacao** — maximo 3 iteracoes, score minimo 18/30
3. **Fallback temporal** — 🟢→🟡→🔴, nunca vazio
4. **Output Pt-PT natural** — zero travesoes, zero AI-isms
5. **Nao alterar corpo sem autorizacao** — notas de auditoria no final
6. **Red Team obrigatorio** — nenhum doc sai sem score

## Estrutura de Entidades mem0

| Entidade | Categoria | Exemplos |
|----------|-----------|----------|
| PS, PSD, BE, CH, IL, PCP, CDS-PP, PAN, L | leadership | Lideres atuais, historico |
| AR | composition | Deputados, legislatura |
| PR | leadership | Presidente da Republica |
| (setor) | audit | Claims verificadas de cada doc |

## Comandos Rapidos

```bash
# Auditar documento
python3 /root/.hermes/skills/unir-mem0/scripts/unir_mem0_audit.py --stale-only

# Pesquisar com fallback
python3 /root/.hermes/skills/unir-mem0/scripts/unir_mem0_search.py "lider do PS"

# Adicionar facto verificado
python3 /root/.hermes/skills/unir-mem0/scripts/unir_mem0_add.py \
  --fact "texto do facto" --entity PS --category audit --source "INE" --date 2026-07-27
```
