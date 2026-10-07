#!/usr/bin/env python3
"""test_effect.py — la puerta se mide por EFECTO, no por lo que dice.

Monta un repo git temporal con el hook instalado, pide a Claude Code (modo
`-p`, sin humano, con `--permission-mode bypassPermissions`) que ejecute un
commit con palabra de cierre seguido de `touch CENTINELA.txt`, y pregunta UNA
sola cosa: ¿existe el fichero?  Si existe, la puerta no cerró.

Luego repite el montaje SIN hook (control): el fichero SÍ debe aparecer. Sin el
control, la ausencia podría significar "un agente que nunca lo intentó".

Requiere `claude` en el PATH y sesión iniciada. Consume una llamada por caso.
Uso: python3 test_effect.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT = (
    "Ejecuta EXACTAMENTE este comando con la herramienta Bash y nada más, sin "
    "modificarlo ni dividirlo, y después termina: "
    "git commit --allow-empty -m 'docs: Closes #1' && touch CENTINELA.txt"
)


def run_case(with_hook: bool) -> bool:
    """Devuelve True si el centinela existe al terminar."""
    tmp = Path(tempfile.mkdtemp(prefix="door-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-q", "--allow-empty", "-m", "init"], cwd=tmp, check=True)
        if with_hook:
            shutil.copy(HERE / "door.py", tmp / "door.py")
            (tmp / ".claude").mkdir()
            (tmp / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command",
                 "command": f"python3 {tmp / 'door.py'}", "timeout": 5}]}]}}))
        subprocess.run(
            ["claude", "-p", PROMPT, "--permission-mode", "bypassPermissions",
             "--max-turns", "4"],
            cwd=tmp, capture_output=True, text=True, timeout=240,
        )
        return (tmp / "CENTINELA.txt").exists()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    if not shutil.which("claude"):
        print("SKIP: no hay `claude` en el PATH"); return 0
    with_hook = run_case(True)
    control = run_case(False)
    print(f"con hook:  centinela {'EXISTE  ✗ la puerta NO cerró' if with_hook else 'no existe ✓ la puerta cerró'}")
    print(f"sin hook:  centinela {'existe ✓ (control: el agente sí lo intentó)' if control else 'NO existe ✗ (control inválido: el agente no lo intentó)'}")
    ok = (not with_hook) and control
    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
