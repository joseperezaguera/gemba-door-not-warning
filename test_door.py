"""Tests de la función pura `decide`. Ejecutar: python3 -m pytest -q  (o python3 test_door.py)."""
from door import decide, commit_messages

DENY = [
    'git commit -m "docs: Closes #451"',
    "git commit -am 'fix: fixes #3 at last'",
    'git add . && git commit -m "Resolved #7" && touch CENTINELA.txt',
    'git commit --message="chore: close #12"',
    'git commit -m"FIXED #99"',
]
ALLOW = [
    'git commit -m "docs: explain why closing keywords go in the PR body"',
    'git commit -m "fix: #12 was a typo"',          # número sin palabra clave
    'git commit -m "closes the loop"',             # palabra clave sin número
    "git status",
    'echo "Closes #1"',                            # no es un commit
    "git commit",                                  # sin -m: punto ciego declarado
    "git commit -m 'unterminated",                 # comilla rota: no se bloquea a ciegas
]


def test_deny():
    for cmd in DENY:
        assert decide(cmd)[0] == "deny", cmd


def test_allow():
    for cmd in ALLOW:
        assert decide(cmd)[0] == "allow", cmd


def test_messages():
    assert commit_messages('git commit -m "a" && git commit -m "b"') == ["a", "b"]
    assert commit_messages("ls") == []


if __name__ == "__main__":
    test_deny(); test_allow(); test_messages(); print("OK: 3 tests")
