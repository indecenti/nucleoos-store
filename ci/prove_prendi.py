#!/usr/bin/env python3
"""Le prove dello scaricamento, **senza rete**.

`urlopen` parla anche `file://`, quindi il giro intero -- scarica,
calcola mentre arriva, confronta, cancella se non torna -- si prova con
un file vero e nessuna connessione. Una prova che chiedesse la rete
sarebbe rossa il giorno che il CI non ce l'ha, e allora si smette di
crederle.
"""

import hashlib
import sys
import tempfile
from pathlib import Path

from prendi import NonPresa, impronta, prendi

# I vettori di SHA-256 che tutti conoscono: se questi non tornano, non e'
# il nostro codice a essere rotto, ed e' bene saperlo subito.
VUOTO = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def via_file(p: Path) -> str:
    return p.resolve().as_uri()


def prove():
    yield "il vuoto ha l'impronta del vuoto", lambda: impronta([b""]) == VUOTO
    yield "abc in un pezzo", lambda: impronta([b"abc"]) == ABC
    # **Il taglio non cambia l'impronta**: e' la proprieta' su cui si regge
    # il calcolo mentre i byte arrivano, e se saltasse non se ne
    # accorgerebbe nessuno finche' un asset grosso non fallisse.
    yield "abc in tre pezzi", lambda: impronta([b"a", b"b", b"c"]) == ABC

    def bozza_non_si_scarica():
        try:
            prendi({"nome": "x", "bozza": True, "url": "https://x", "sha256": "d" * 64}, Path("/tmp/x"))
            return False
        except NonPresa as e:
            return "bozza" in str(e)

    yield "una bozza non si scarica", bozza_non_si_scarica

    def senza_url():
        try:
            prendi({"nome": "x", "url": "", "sha256": "d" * 64}, Path("/tmp/x"))
            return False
        except NonPresa as e:
            return "senza url" in str(e)

    yield "senza url si rifiuta", senza_url

    def giro_giusto():
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "fonte"
            src.write_bytes(b"abc")
            out = Path(d) / "out"
            n = prendi({"nome": "x", "url": via_file(src), "sha256": ABC}, out)
            return n == 3 and out.read_bytes() == b"abc"

    yield "l'impronta giusta lascia il file", giro_giusto

    def sbagliata_cancella():
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "fonte"
            src.write_bytes(b"abc")
            out = Path(d) / "out"
            try:
                prendi({"nome": "x", "url": via_file(src), "sha256": "d" * 64}, out)
                return False
            except NonPresa as e:
                # **Il file non deve restare**: uno che non e' quello che
                # dice di essere, lasciato li', prima o poi lo usa qualcuno.
                return "non torna" in str(e) and not out.exists()

    yield "l'impronta sbagliata cancella il file", sbagliata_cancella

    def manca_la_fonte():
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            try:
                prendi({"nome": "x", "url": via_file(Path(d) / "niente"), "sha256": ABC}, out)
                return False
            except NonPresa as e:
                return "non arrivato" in str(e) and not out.exists()

    yield "una fonte che non c'e' e' un no col motivo", manca_la_fonte


def main() -> int:
    rotte = 0
    for nome, f in prove():
        try:
            ok = f()
        except Exception as e:  # una prova che esplode e' una prova rossa
            ok, nome = False, f"{nome} (ha alzato {e!r})"
        print(("ok     " if ok else "ROSSO  ") + nome)
        rotte += not ok
    print(f"\n{rotte} rosse")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main())
