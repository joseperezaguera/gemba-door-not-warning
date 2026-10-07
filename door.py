#!/usr/bin/env python3
"""door.py — una PUERTA, no un aviso.

Hook PreToolUse de Claude Code para la herramienta Bash. Si el comando es un
`git commit` cuyo mensaje contiene una palabra clave de cierre de GitHub
("Closes #12", "fixes #3", "resolved #7"...), el hook BLOQUEA el comando.
No avisa, no sugiere: devuelve `deny`, y la acción no ocurre.

Por qué existe: GitHub cierra un issue cuando una de esas frases llega a la
rama principal en CUALQUIER commit, aunque vaya dentro de una cita. Un commit
de documentación que solo mencionaba "Closes #451" cerró un issue vivo.

Tres propiedades que lo hacen puerta y no adorno (ver README y tests):
  1. Se mide por EFECTO (test_effect.py): un fichero centinela que no aparece.
  2. Sigue cerrando con `--permission-mode bypassPermissions`.
  3. Declara lo que NO ve (lista al final de este fichero).

Sin dependencias. Python 3.9+.
"""
import json
import re
import shlex
import sys

CLOSING = re.compile(
    r"\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#\d+\b", re.IGNORECASE
)


def commit_messages(command: str) -> list[str]:
    """Devuelve los mensajes `-m` de cada `git commit` del comando, o [] si no hay."""
    try:
        tokens = shlex.split(command)
    except ValueError:  # comilla sin cerrar: no se puede saber qué es, no se bloquea
        return []
    messages: list[str] = []
    for segment in _split_on_operators(tokens):
        if "git" in segment and "commit" in segment:
            gi, ci = segment.index("git"), segment.index("commit")
            if gi < ci:
                messages.extend(_messages_after(segment[ci + 1 :]))
    return messages


def _split_on_operators(tokens: list[str]) -> list[list[str]]:
    segments, current = [], []
    for tok in tokens:
        if tok in ("&&", "||", ";", "|"):
            segments.append(current)
            current = []
        else:
            current.append(tok)
    segments.append(current)
    return segments


def _messages_after(args: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(args):
        a = args[i]
        takes_next = a in ("-m", "--message") or (
            a.startswith("-") and not a.startswith("--") and a.endswith("m") and len(a) > 1
        )  # `-m`, `--message` o un grupo corto que termina en m: `-am`, `-qm`
        if takes_next and i + 1 < len(args):
            out.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--message="):
            out.append(a.split("=", 1)[1])
        elif a.startswith("-m") and len(a) > 2:
            out.append(a[2:])
        i += 1
    return out


def decide(command: str) -> tuple[str, str]:
    """Función PURA: ('allow'|'deny', razón). No toca disco ni red."""
    for msg in commit_messages(command):
        hit = CLOSING.search(msg)
        if hit:
            return (
                "deny",
                f'El mensaje del commit contiene "{hit.group(0)}": GitHub cerraría ese issue '
                "al llegar a la rama principal. Quita la palabra clave del mensaje y pon el "
                "cierre en el CUERPO del pull request.",
            )
    return ("allow", "")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # sin JSON no se sabe qué comando es: no se bloquea a ciegas
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return
    decision, reason = decide(command)
    if decision == "deny":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))


if __name__ == "__main__":
    main()

# LO QUE NO VE (medido, no supuesto):
# - Lo que una persona teclea en su terminal, o con el prefijo `!` de Claude Code:
#   nunca pasa por la herramienta Bash, así que ningún PreToolUse lo ve.
# - `git commit` sin `-m` (abre el editor), `-F fichero`, `--amend --no-edit`.
# - Comandos envueltos: `eval "..."`, `bash -c "..."`, `sudo git commit`, `env X=1 git commit`.
# - Mensajes construidos con variables o heredocs: $MSG, $(cat f), <<EOF.
