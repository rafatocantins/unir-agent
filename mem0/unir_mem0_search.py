#!/usr/bin/env python3
"""Pesquisa factos UNIR na mem0 com fallback temporal progressivo.

Regra de fallback:
  1. Tenta 🟢 FRESCO (ultimos 3 meses)
  2. Se nao encontra → 🟡 REVER (3-6 meses)
  3. Se nao encontra → 🔴 MELHOR DISPONIVEL (dado mais recente, com aviso)
  4. NUNCA retorna vazio se existe algum dado sobre a entidade

Uso:
  python3 unir_mem0_search.py "lider do PS"
  python3 unir_mem0_search.py "composicao AR"
  python3 unir_mem0_search.py "Bloco de Esquerda" --entity BE
"""

import os
from datetime import datetime, timedelta

os.environ["MEM0_TELEMETRY"] = "false"
from mem0 import MemoryClient

API_KEY = os.environ.get("MEM0_API_KEY", "REDACTED")
USER_ID = "unir-agent"

# Thresholds: Q atual = ultimos 90 dias, Q anterior = 90-180 dias
NOW = datetime.now()
Q_ATUAL = (NOW - timedelta(days=90)).strftime("%Y-%m-%d")
Q_ANTERIOR = (NOW - timedelta(days=180)).strftime("%Y-%m-%d")


def classify(date_str):
    """Classifica frescura: 🟢 🟡 🔴"""
    if not date_str or date_str == "?":
        return "⚪ SEM DATA"
    if date_str >= Q_ATUAL:
        return "🟢 FRESCO"
    elif date_str >= Q_ANTERIOR:
        return "🟡 REVER"
    else:
        return "🔴 OBSOLETO"


def search_with_fallback(client, query, entity=None):
    """Pesquisa com fallback progressivo: 🟢 → 🟡 → 🔴 (melhor disponivel)."""
    filters = {"user_id": USER_ID}
    if entity:
        filters["metadata"] = {"entity": entity}

    raw = client.search(query, filters=filters)
    results = raw.get("results", raw) if isinstance(raw, dict) else raw

    if not results:
        return None, []

    # Ordenar por data (mais recente primeiro)
    results.sort(key=lambda r: r.get("metadata", {}).get("verified_date", "0"), reverse=True)

    # Tentar 🟢
    fresh = [r for r in results if r.get("metadata", {}).get("verified_date", "0") >= Q_ATUAL]
    if fresh:
        return "🟢 FRESCO (ultimos 3 meses)", fresh

    # Tentar 🟡
    recent = [r for r in results if r.get("metadata", {}).get("verified_date", "0") >= Q_ANTERIOR]
    if recent:
        return "🟡 REVER (3-6 meses) — verificar antes de usar", recent

    # Fallback: melhor disponivel
    best = results[:3]
    best_date = best[0].get("metadata", {}).get("verified_date", "?")
    return f"🔴 MELHOR DISPONIVEL (dado de {best_date}) — requer nova verificacao", best


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pesquisar factos UNIR na mem0 com fallback temporal")
    parser.add_argument("query", help="Termo de pesquisa")
    parser.add_argument("--entity", help="Filtrar por entidade (PS, BE, PR, AR...)")
    parser.add_argument("--limit", type=int, default=5, help="Maximo de resultados")
    args = parser.parse_args()

    client = MemoryClient(api_key=API_KEY)
    status, results = search_with_fallback(client, args.query, args.entity)

    if not results:
        print("Nenhum resultado encontrado para esta entidade/topico.")
        print("Sugestao: usar unir_mem0_add.py para registar o dado em falta.")
        return

    print(f"'{args.query}' — {status}")
    print(f"{len(results)} resultados\n")

    for r in results[:args.limit]:
        date = r.get("metadata", {}).get("verified_date", "?")
        ent = r.get("metadata", {}).get("entity", "?")
        fiab = r.get("metadata", {}).get("fiabilidade", "⚪")
        source = r.get("metadata", {}).get("source", "?")
        mem = r["memory"]
        age_icon = classify(date)[:2]

        print(f"  {fiab} {age_icon} [{ent}] [{date}] {mem[:150]}")
        print(f"     Fonte: {source}")
        print()


if __name__ == "__main__":
    main()
