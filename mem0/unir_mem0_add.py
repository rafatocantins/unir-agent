#!/usr/bin/env python3
"""Adiciona factos verificados a mem0 para o projeto UNIR.

Uso:
  python3 unir_mem0_add.py --fact "texto" --entity PS --fiab 🟢 --source INE
  python3 unir_mem0_add.py --batch /path/to/facts.json

Fiabilidade:
  🟢 Fonte oficial (INE, Eurostat, OCDE, DRE, .gov.pt)
  🟡 Imprensa credivel (jornal cita fonte oficial)
  🟠 Fonte privada (estudo, think tank, ONG)
  🔴 Nao verificavel (sem fonte identificada)
"""

import argparse, json, os, sys
os.environ["MEM0_TELEMETRY"] = "false"

from mem0 import MemoryClient

API_KEY = os.environ.get("MEM0_API_KEY", "REDACTED")
USER_ID = "unir-agent"

FIAB_SCORES = {"🟢": "Fonte oficial", "🟡": "Imprensa credivel",
               "🟠": "Fonte privada", "🔴": "Nao verificavel"}


def add_fact(client, fact, metadata):
    """Adiciona um facto a mem0 com metadados UNIR."""
    client.add(fact, user_id=USER_ID, metadata=metadata)
    entity = metadata.get("entity", "?")
    fiab = metadata.get("fiabilidade", "⚪")
    print(f"{fiab} [{entity}] {fact[:80]}...")


def add_batch(client, facts):
    """Adiciona multiplos factos de um ficheiro JSON."""
    for item in facts:
        add_fact(client, item["fact"], item["metadata"])


def main():
    parser = argparse.ArgumentParser(description="Adicionar factos UNIR a mem0")
    parser.add_argument("--fact", help="Texto do facto")
    parser.add_argument("--entity", help="Entidade (PS, BE, PR, AR, EDU, FIN, etc.)")
    parser.add_argument("--fiab", default="🟢",
                        choices=["🟢", "🟡", "🟠", "🔴"],
                        help="Fiabilidade: 🟢 oficial 🟡 imprensa 🟠 privada 🔴 nao ver")
    parser.add_argument("--category", default="fact",
                        help="Categoria (leadership, parliamentary, audit, composition)")
    parser.add_argument("--source", default="manual", help="Fonte do facto")
    parser.add_argument("--date", help="Data de verificacao (YYYY-MM-DD)")
    parser.add_argument("--batch", help="Ficheiro JSON com lista de factos")
    args = parser.parse_args()

    client = MemoryClient(api_key=API_KEY)

    if args.batch:
        with open(args.batch) as f:
            facts = json.load(f)
        add_batch(client, facts)
        print(f"\n{len(facts)} factos adicionados em lote")
    elif args.fact and args.entity:
        meta = {
            "entity": args.entity,
            "category": args.category,
            "fiabilidade": args.fiab,
            "verified": True,
            "source": args.source,
            "verified_date": args.date or "2026-07-27",
        }
        add_fact(client, args.fact, meta)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
