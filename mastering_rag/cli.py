from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings
from .database import Database
from .generation import generate_answer, validate_answer
from .ingest import ingest_pdf
from .ollama import OllamaClient
from .retrieval import Retriever


def dependencies() -> tuple[Settings, Database, OllamaClient]:
    settings = Settings()
    return settings, Database(settings.database_url), OllamaClient(
        settings.ollama_base_url, settings.chat_model, settings.embed_model
    )


def cmd_ingest(args: argparse.Namespace) -> None:
    _, db, client = dependencies()
    paths = sorted(Path(args.path).glob("*.pdf")) if Path(args.path).is_dir() else [Path(args.path)]
    if not paths:
        raise SystemExit(f"No PDFs found at {args.path}")
    for path in paths:
        document_id, count = ingest_pdf(path, db, client, args.contextualize)
        print(f"Indexed {path.name}: document={document_id}, chunks={count}")


def cmd_search(args: argparse.Namespace) -> None:
    _, db, client = dependencies()
    retriever = Retriever(db, client)
    results = getattr(retriever, args.mode)(args.query, args.top_k)
    for rank, result in enumerate(results, start=1):
        print(f"{rank}. score={result.score:.4f} source={result.citation}\n   {result.content[:220]}\n")


def cmd_ask(args: argparse.Namespace) -> None:
    _, db, client = dependencies()
    retriever = Retriever(db, client)
    results = getattr(retriever, args.mode)(args.query, args.top_k)
    answer = generate_answer(client, args.query, results)
    print(answer)
    if args.validate:
        print("\nValidation:\n" + json.dumps(validate_answer(client, args.query, answer, results), indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local RAG examples with Ollama and pgvector")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="Index a PDF or directory of PDFs")
    ingest.add_argument("path")
    ingest.add_argument("--contextualize", action="store_true")
    ingest.set_defaults(func=cmd_ingest)
    for name, function in (("search", cmd_search), ("ask", cmd_ask)):
        command = commands.add_parser(name)
        command.add_argument("query")
        command.add_argument("--mode", choices=("vector", "hybrid", "long_context"), default="hybrid")
        command.add_argument("--top-k", type=int, default=5)
        if name == "ask":
            command.add_argument("--validate", action="store_true")
        command.set_defaults(func=function)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
