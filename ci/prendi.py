#!/usr/bin/env python3
"""Scaricare una voce, e **rifiutarla** se non e' quella dichiarata.

E' la prima meta' del CI vero (`plans/APP-DI-TERZI.md` §7.2): prendere
l'asset dall'upstream e confrontarlo con l'impronta che la voce dichiara.
La seconda meta' -- avviare NucleoOS in QEMU e far girare il binario
sotto `linuxd` -- vuole la repo di NucleoOS per costruire le immagini.

**L'impronta si calcola mentre i byte arrivano**, non dopo: un asset da
centinaia di mebibyte non si tiene tutto in memoria per poi guardarlo, e
tenerlo su disco prima di sapere se e' quello giusto vuol dire scrivere
byte di cui non si sa niente.

**E il confronto e' contro cio' che la voce dichiara**, che viene
dall'upstream. Prendere l'impronta di cio' che e' arrivato e chiamarla
verifica controlla che il byte non si sia rotto in volo -- non che sia il
byte giusto.
"""

import hashlib
import sys
import tomllib
from pathlib import Path
from urllib.request import urlopen

# Quanto si legge per volta. Un mebibyte: abbastanza da non fare una
# chiamata per pacchetto TCP, poco da non tenere niente di serio in RAM.
FETTA = 1024 * 1024


class NonPresa(Exception):
    """Con il motivo, che e' l'unica cosa che serve a chi legge il log."""


def impronta(pezzi) -> str:
    """Lo SHA-256 di una sequenza di fette, in esadecimale minuscolo.

    Sta da sola perche' e' l'unica parte che si puo' provare senza rete:
    chi la chiama le passa dei byte, e non le importa da dove vengono.
    """
    h = hashlib.sha256()
    for p in pezzi:
        h.update(p)
    return h.hexdigest()


def fette(f, quanto: int = FETTA):
    """Le fette di un flusso, finche' ce n'e'."""
    while True:
        p = f.read(quanto)
        if not p:
            return
        yield p


def prendi(voce: dict, dove: Path) -> int:
    """Scarica la voce in `dove`. Rende quanti byte, o alza `NonPresa`.

    Il file si scrive **mentre** si calcola, e si **cancella** se
    l'impronta non torna: lasciare in giro un file che non e' quello che
    dice di essere e' il modo in cui qualcuno lo usa lo stesso.
    """
    if voce.get("bozza"):
        raise NonPresa(f"{voce.get('nome')}: e' una bozza, non si scarica")
    url = voce.get("url") or ""
    atteso = voce.get("sha256") or ""
    if not url or not atteso:
        raise NonPresa(f"{voce.get('nome')}: senza url o senza sha256")

    h = hashlib.sha256()
    n = 0
    dove.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(url, timeout=60) as r, dove.open("wb") as out:
            for p in fette(r):
                h.update(p)
                out.write(p)
                n += len(p)
    except NonPresa:
        raise
    except Exception as e:  # rete, DNS, 404: un motivo solo, e si vede
        dove.unlink(missing_ok=True)
        raise NonPresa(f"{voce.get('nome')}: non arrivato: {e}") from e

    avuto = h.hexdigest()
    if avuto != atteso:
        dove.unlink(missing_ok=True)
        raise NonPresa(
            f"{voce.get('nome')}: l'impronta non torna\n"
            f"  dichiarata {atteso}\n"
            f"  arrivata   {avuto}\n"
            f"  ({n} byte da {url})"
        )
    return n


def main(radice: str = "sorgenti", scarico: str = "scarico") -> int:
    vie = sorted(Path(radice).glob("*.toml"))
    prese = saltate = rotte = 0
    for via in vie:
        voce = tomllib.loads(via.read_text(encoding="utf-8"))
        nome = voce.get("nome", via.stem)
        if voce.get("bozza"):
            print(f"{nome}: bozza -- saltata")
            saltate += 1
            continue
        try:
            n = prendi(voce, Path(scarico) / nome)
            print(f"{nome}: {n} byte, impronta giusta")
            prese += 1
        except NonPresa as e:
            print(f"{e}")
            rotte += 1
    print(f"\n{len(vie)} voci: {prese} prese, {saltate} bozze, {rotte} rifiutate")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
