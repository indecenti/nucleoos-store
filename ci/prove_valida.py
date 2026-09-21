#!/usr/bin/env python3
"""Le prove del controllo, perche' un controllo che non si prova non e' un
controllo: passerebbe verde anche se non guardasse niente."""

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
    ("una voce piena va bene", BUONA, []),
    ("senza url e senza bozza e' rossa", con(url=""), ["`url` vuoto"]),
    ("senza url ma dichiarata bozza passa", con(url="", bozza=True), []),
    ("senza sha e senza bozza e' rossa", con(sha256=""), ["`sha256` vuoto"]),
    ("uno sha corto e' rosso anche in bozza", con(sha256="abc", bozza=True), ["esadecimali"]),
    ("un url http non basta", con(url="http://x/y"), ["non e' https"]),
    ("il nome deve essere quello del file", con(nome="rg"), ["si chiama"]),
    ("una prova senza uscita e' rossa", con(prova={"args": []}), ["`uscita`"]),
    ("poteri senza pagine sono rossi", con(poteri={"radici": []}), ["pagine"]),
    ("pagine a zero non sono pagine", con(poteri={"radici": [], "pagine": 0}), ["pagine"]),
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
                print(f"       non ha detto: {manca}")
            if troppo:
                print(f"       ha detto in piu': {troppo}")
        else:
            print(f"ok     {nome}")
    print(f"\n{len(PROVE)} prove, {rotte} rosse")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main())
