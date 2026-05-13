"""Slash command parsing for the unified AI chat endpoint."""

from __future__ import annotations

from dataclasses import dataclass

from route_examples import ROUTE_DOCS, ROUTE_SQL

ROUTE_SOURCE_SLASH = "slash_command"
ROUTE_SOURCE_SEMANTIC = "semantic_router"
SUPPORTED_COMMANDS = {
    "/sql": ROUTE_SQL,
    "/docs": ROUTE_DOCS,
}


class SlashCommandError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.allowed_commands = sorted(SUPPORTED_COMMANDS)


@dataclass(frozen=True)
class SlashParseResult:
    question: str
    forced_route: str | None
    command: str | None


def parse_slash_command(raw_question: str) -> SlashParseResult:
    text = raw_question.strip()
    if not text.startswith("/"):
        return SlashParseResult(question=text, forced_route=None, command=None)

    command, _, rest = text.partition(" ")
    command = command.lower()
    if command not in SUPPORTED_COMMANDS:
        raise SlashCommandError(
            f"Desteklenmeyen komut: {command}. Izinli komutlar: /sql, /docs."
        )

    question = rest.strip()
    if len(question) < 2:
        raise SlashCommandError("Komuttan sonra en az 2 karakterlik soru yazin.")

    return SlashParseResult(
        question=question,
        forced_route=SUPPORTED_COMMANDS[command],
        command=command,
    )
