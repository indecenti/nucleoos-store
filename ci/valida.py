#!/usr/bin/env python3
"""Catalogue entries parse, or they do not get in.

The README promises that CI refuses an entry with no URL. While that
stays a sentence it is only a sentence: here it becomes a check that
runs on every push.

**Two different kinds of no, and they do not blur.** A *malformed* entry
is the author's mistake -- a 42-character `sha256`, a missing proof --
and goes red at once. An *incomplete* entry is an honest one that is not
ready: it says so with `bozza = true`, validation lets it through, and
the index builder **skips it**. A check that goes red while you are
working correctly teaches people to ignore red.
"""

import sys
import tomllib
from pathlib import Path

CAMPI = ("nome", "versione", "origine", "url", "sha256", "prova", "poteri")


def guai(voce: dict, via: str) -> list[str]:
    """What does not add up in this entry. Empty list = it is fine."""
    out = []
    bozza = voce.get("bozza", False)
    if not isinstance(bozza, bool):
        out.append("`bozza` is not a boolean")

    for campo in CAMPI:
        if campo not in voce:
            out.append(f"missing `{campo}`")

    nome = voce.get("nome", "")
    if isinstance(nome, str) and nome:
        atteso = Path(via).stem
        # The name in the file and the name of the file must agree: a
        # catalogue where `busybox.toml` declares `rg` is a catalogue
        # that installs one thing for another.
        if nome != atteso and atteso != "":
            out.append(f"`nome` is « {nome} » but the file is called « {atteso} »")

    sha = voce.get("sha256", "")
    if isinstance(sha, str) and sha:
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            out.append("`sha256` is not 64 lowercase hex digits")
    elif not bozza:
        out.append("`sha256` empty, and the entry does not declare itself a draft")

    url = voce.get("url", "")
    if isinstance(url, str) and url:
        if not url.startswith("https://"):
            # The source is fetched in CI, where HTTPS is free. Plain
            # transport is the **client's** choice, defended by signature
            # and expiry; not ours.
            out.append("`url` is not https")
    elif not bozza:
        out.append("`url` empty, and the entry does not declare itself a draft")

    prova = voce.get("prova")
    if isinstance(prova, dict):
        if "uscita" not in prova:
            out.append("`prova` without `uscita`: « it started » is not a criterion")
        if not isinstance(prova.get("args"), list):
            out.append("`prova.args` is not a list")
    elif prova is not None:
        out.append("`prova` is not a table")

    poteri = voce.get("poteri")
    if isinstance(poteri, dict):
        if not isinstance(poteri.get("radici"), list):
            out.append("`poteri.radici` is not a list")
        pagine = poteri.get("pagine")
        if not isinstance(pagine, int) or pagine <= 0:
            out.append("`poteri.pagine` is not a page count")
    elif poteri is not None:
        out.append("`poteri` is not a table")

    return out


def main(radice: str = "sorgenti") -> int:
    vie = sorted(Path(radice).glob("*.toml"))
    if not vie:
        print(f"no entries in {radice}/")
        return 1
    rotte = 0
    bozze = 0
    for via in vie:
        try:
            voce = tomllib.loads(via.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as e:
            print(f"{via}: not TOML: {e}")
            rotte += 1
            continue
        g = guai(voce, str(via))
        if g:
            rotte += 1
            for riga in g:
                print(f"{via}: {riga}")
        elif voce.get("bozza"):
            bozze += 1
            print(f"{via}: draft -- stays out of the index")
        else:
            print(f"{via}: ok")
    print(f"\n{len(vie)} entries, {rotte} to fix, {bozze} drafts")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
