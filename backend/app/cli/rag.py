"""
SecondBrain RAG command line interface.
"""
from __future__ import annotations

import argparse
import asyncio
import json

from app.db.connection import async_session_factory, close_db, init_db
from app.services.rag_service import rag_service


async def _run(args: argparse.Namespace) -> int:
    await init_db()
    await rag_service.initialize()

    try:
        if args.command == "stats":
            result = await rag_service.get_index_stats()
        elif args.command == "index":
            async with async_session_factory() as db:
                note_ids = args.note_id or None
                result = await rag_service.index_notes_batch(
                    db,
                    note_ids=note_ids,
                    force=args.force,
                )
        elif args.command == "query":
            result = await rag_service.query(
                args.query,
                mode=args.mode,
                top_k=args.top_k,
            )
        else:
            raise RuntimeError(f"Unknown command: {args.command}")

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        await rag_service.close()
        await close_db()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="secondbrain-rag")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stats", help="Show RAG readiness and index stats")

    index_parser = subparsers.add_parser("index", help="Index notes for RAG")
    index_parser.add_argument("--note-id", action="append", default=[])
    index_parser.add_argument("--force", action="store_true")

    query_parser = subparsers.add_parser("query", help="Query the RAG index")
    query_parser.add_argument("query")
    query_parser.add_argument("--mode", default="mix")
    query_parser.add_argument("--top-k", type=int, default=5)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
