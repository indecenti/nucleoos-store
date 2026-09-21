#!/usr/bin/env python3
"""Le voci del catalogo si leggono, o non entrano.

Il README promette che una voce senza URL il CI la rifiuta. Finche' resta
una frase, e' una frase: qui diventa un controllo che gira a ogni push.

**Due no diversi, e non si confondono.** Una voce *malformata* e' un
errore di chi l'ha scritta -- un `sha256` di quarantadue caratteri, una
prova che manca -- e va rossa subito. Una voce *incompleta* e' una voce
onesta che non e' ancora pronta: lo dichiara con `bozza = true`, il
controllo la lascia passare, e il costruttore dell'indice **la salta**.
Un controllo rosso mentre si lavora bene insegna a ignorare il rosso.
"""

import sys
import tomllib
from pathlib import Path

CAMPI = ("nome", "versione", "origine", "url", "sha256", "prova", "poteri")


def guai(voce: dict, via: str) -> list[str]:
    """Che cosa non torna in questa voce. Lista vuota = va bene."""
    out = []
    bozza = voce.get("bozza", False)
    if not isinstance(bozza, bool):
        out.append("`bozza` non e' un booleano")

    for campo in CAMPI:
        if campo not in voce:
            out.append(f"manca `{campo}`")

    nome = voce.get("nome", "")
    if isinstance(nome, str) and nome:
        atteso = Path(via).stem
        # Il nome nel file e il nome del file devono coincidere: un
        # catalogo in cui `busybox.toml` dichiara `rg` e' un catalogo che
        # installa una cosa per un'altra.
        if nome != atteso and atteso != "":
            out.append(f"`nome` e' « {nome} » ma il file si chiama « {atteso} »")

    sha = voce.get("sha256", "")
    if isinstance(sha, str) and sha:
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            out.append("`sha256` non e' sessantaquattro cifre esadecimali minuscole")
    elif not bozza:
        out.append("`sha256` vuoto, e la voce non si dichiara bozza")

    url = voce.get("url", "")
    if isinstance(url, str) and url:
        if not url.startswith("https://"):
            # L'origine si scarica in CI, dove HTTPS c'e' e costa zero.
            # Il trasporto senza TLS e' una scelta del **client**, che ha
            # firma e scadenza a difenderlo; qui no.
            out.append("`url` non e' https")
    elif not bozza:
        out.append("`url` vuoto, e la voce non si dichiara bozza")

    prova = voce.get("prova")
    if isinstance(prova, dict):
        if "uscita" not in prova:
            out.append("`prova` senza `uscita`: « e' partito » non e' un criterio")
        if not isinstance(prova.get("args"), list):
            out.append("`prova.args` non e' una lista")
    elif prova is not None:
        out.append("`prova` non e' una tabella")

    poteri = voce.get("poteri")
    if isinstance(poteri, dict):
        if not isinstance(poteri.get("radici"), list):
            out.append("`poteri.radici` non e' una lista")
        pagine = poteri.get("pagine")
        if not isinstance(pagine, int) or pagine <= 0:
            out.append("`poteri.pagine` non e' un numero di pagine")
    elif poteri is not None:
        out.append("`poteri` non e' una tabella")

    return out


def main(radice: str = "sorgenti") -> int:
    vie = sorted(Path(radice).glob("*.toml"))
    if not vie:
        print(f"nessuna voce in {radice}/")
        return 1
    rotte = 0
    bozze = 0
    for via in vie:
        try:
            voce = tomllib.loads(via.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as e:
            print(f"{via}: non e' TOML: {e}")
            rotte += 1
            continue
        g = guai(voce, str(via))
        if g:
            rotte += 1
            for riga in g:
                print(f"{via}: {riga}")
        elif voce.get("bozza"):
            bozze += 1
            print(f"{via}: bozza -- non entra nell'indice")
        else:
            print(f"{via}: a posto")
    print(f"\n{len(vie)} voci, {rotte} da sistemare, {bozze} bozze")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
