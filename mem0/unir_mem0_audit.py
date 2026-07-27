#!/usr/bin/env python3
"""Auditoria de factos UNIR na mem0: staleness, contradições, frescura.

Regras temporais:
  - Q atual (últimos 3 meses): 🟢 FRESCO
  - Q anterior (3-6 meses): 🟡 REVER
  - >6 meses: 🔴 OBSOLETO

Uso:
  python3 unir_mem0_audit.py
  python3 unir_mem0_audit.py --entity PS
  python3 unir_mem0_audit.py --stale-only
"""

import os, sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter

os.environ["MEM0_TELEMETRY"] = "false"
from mem0 import MemoryClient

API_KEY="REDACTED"
USER_ID = "unir-agent"

def classify_staleness(verified_date):
    """Classifica um facto por frescura temporal."""
    if not verified_date or verified_date == "?":
        return "⚪ SEM DATA", -1
    
    try:
        date = datetime.strptime(verified_date, "%Y-%m-%d")
    except ValueError:
        return "⚪ DATA INVÁLIDA", -1
    
    now = datetime.now()
    months = (now.year - date.year) * 12 + (now.month - date.month)
    
    if months <= 3:
        return "🟢 FRESCO (Q atual)", months
    elif months <= 6:
        return "🟡 REVER (Q anterior)", months
    else:
        return "🔴 OBSOLETO", months

def find_contradictions(client):
    """Deteta entidades com múltiplos factos contraditórios."""
    all_facts = client.get_all(filters={"user_id": USER_ID})
    facts = all_facts.get("results", all_facts) if isinstance(all_facts, dict) else all_facts
    
    # Agrupar por entidade
    by_entity = defaultdict(list)
    for f in facts:
        entity = f.get("metadata", {}).get("entity", "?")
        by_entity[entity].append(f)
    
    contradictions = []
    for entity, items in by_entity.items():
        if len(items) <= 1:
            continue
        # Procurar nomes próprios diferentes (indicador de liderança trocada)
        names = set()
        for item in items:
            mem = item["memory"]
            # Extrair nomes capitalizados
            import re
            found = set(re.findall(r'\b[A-ZÀ-Ú][a-zà-ú]+\s[A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)?\b', mem))
            names.update(found)
        
        # Se há mais de 2 nomes próprios, pode ser contradição
        if len(names) > 2:
            contradictions.append((entity, len(items), names))
    
    return contradictions

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auditar factos UNIR na mem0")
    parser.add_argument("--entity", help="Filtrar por entidade específica")
    parser.add_argument("--stale-only", action="store_true", help="Mostrar apenas factos obsoletos")
    args = parser.parse_args()

    client = MemoryClient(api_key=API_KEY)
    
    all_raw = client.get_all(filters={"user_id": USER_ID})
    all_facts = all_raw.get("results", all_raw) if isinstance(all_raw, dict) else all_raw
    
    # Filtrar por entidade
    if args.entity:
        all_facts = [f for f in all_facts if f.get("metadata", {}).get("entity") == args.entity]
        if not all_facts:
            print(f"❌ Nenhum facto encontrado para entidade '{args.entity}'")
            return
    
    print("=" * 60)
    print("AUDITORIA UNIR — STALENESS")
    print("=" * 60)
    
    stats = Counter()
    for fact in all_facts:
        date = fact.get("metadata", {}).get("verified_date", "?")
        entity = fact.get("metadata", {}).get("entity", "?")
        category = fact.get("metadata", {}).get("category", "?")
        fiab = fact.get("metadata", {}).get("fiabilidade", "⚪")
        label, months = classify_staleness(date)
        stats[label] += 1
        
        if args.stale_only and months <= 6:
            continue
        
        mem = fact["memory"][:100]
        print(f"  {fiab} {label:30s} [{entity:8s}] [{category:15s}] {date} | {mem}")
    
    print(f"\n📊 Distribuição: {dict(stats)}")
    
    # Contradições
    print("\n" + "=" * 60)
    print("AUDITORIA UNIR — CONTRADIÇÕES")
    print("=" * 60)
    contradictions = find_contradictions(client)
    if contradictions:
        for entity, count, names in contradictions:
            print(f"  ⚠️  [{entity}] {count} factos, {len(names)} nomes diferentes")
            print(f"     Nomes: {', '.join(sorted(names))}")
    else:
        print("  ✅ Nenhuma contradição detetada")
    
    print("\n✅ Auditoria concluída")

if __name__ == "__main__":
    main()
