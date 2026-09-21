#!/usr/bin/env python3
"""The checker's own tests, because a check that is not tested is not a
check: it would pass green even if it looked at nothing."""

import sys
from valida import guai

BUONA = {
    "nome": "busybox",
    "versione": "1.36.1",
    "origine": "busybox.net",
    "url": "https://busybox.net/x/busybox",
    "sha256": "d" * 64,
    "prova": {"args": ["echo", "ciao"], "uscita": 0},
    "poteri": {"radici": [], "pagine": 4096},
}


def con(**cambi):
    v = {k: (dict(x) if isinstance(x, dict) else x) for k, x in BUONA.items()}
    v.update(cambi)
    return v


PROVE = [
    ("a complete entry is fine", BUONA, []),
    ("no url and not a draft is red", con(url=""), ["`url` empty"]),
    ("no url but declared a draft passes", con(url="", bozza=True), []),
    ("no sha and not a draft is red", con(sha256=""), ["`sha256` empty"]),
    ("a short sha is red even in a draft", con(sha256="abc", bozza=True), ["hex digits"]),
    ("an http url is not enough", con(url="http://x/y"), ["not https"]),
    ("the name must be the file name", con(nome="rg"), ["is called"]),
    ("a proof without an exit code is red", con(prova={"args": []}), ["`uscita`"]),
    ("powers without pages are red", con(poteri={"radici": []}), ["pagine"]),
    ("zero pages are not pages", con(poteri={"radici": [], "pagine": 0}), ["pagine"]),
]


def main() -> int:
    rotte = 0
    for nome, voce, attesi in PROVE:
        g = guai(voce, "sorgenti/busybox.toml")
        manca = [a for a in attesi if not any(a in riga for riga in g)]
        troppo = g if not attesi else []
        if manca or troppo:
            rotte += 1
            print(f"ROSSO  {nome}")
            if manca:
                print(f"       did not say: {manca}")
            if troppo:
                print(f"       said extra: {troppo}")
        else:
            print(f"ok     {nome}")
    print(f"\n{len(PROVE)} tests, {rotte} red")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main())
