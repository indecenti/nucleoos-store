#!/usr/bin/env python3
"""The fetch tests, **without a network**.

`urlopen` speaks `file://` too, so the whole round -- fetch, hash as it
arrives, compare, delete on mismatch -- is tested with a real file and
no connection. A test that needed the network would go red the day CI
has none, and then people stop believing it.
"""

import hashlib
import sys
import tempfile
from pathlib import Path

from prendi import NonPresa, impronta, prendi

# The SHA-256 vectors everyone knows: if these do not match, it is not
# our code that is broken, and it is good to know at once.
VUOTO = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def via_file(p: Path) -> str:
    return p.resolve().as_uri()


def prove():
    yield "the empty input hashes to the empty hash", lambda: impronta([b""]) == VUOTO
    yield "abc in one chunk", lambda: impronta([b"abc"]) == ABC
    # **Chunking does not change the hash**: this is the property the
    # arrive-as-you-hash design rests on, and if it broke nobody would
    # notice until a large asset failed.
    yield "abc in three chunks", lambda: impronta([b"a", b"b", b"c"]) == ABC

    def bozza_non_si_scarica():
        try:
            prendi({"nome": "x", "bozza": True, "url": "https://x", "sha256": "d" * 64}, Path("/tmp/x"))
            return False
        except NonPresa as e:
            return "draft" in str(e)

    yield "a draft is not fetched", bozza_non_si_scarica

    def senza_url():
        try:
            prendi({"nome": "x", "url": "", "sha256": "d" * 64}, Path("/tmp/x"))
            return False
        except NonPresa as e:
            return "no url" in str(e)

    yield "no url is refused", senza_url

    def giro_giusto():
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "fonte"
            src.write_bytes(b"abc")
            out = Path(d) / "out"
            n = prendi({"nome": "x", "url": via_file(src), "sha256": ABC}, out)
            return n == 3 and out.read_bytes() == b"abc"

    yield "a matching hash leaves the file", giro_giusto

    def sbagliata_cancella():
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "fonte"
            src.write_bytes(b"abc")
            out = Path(d) / "out"
            try:
                prendi({"nome": "x", "url": via_file(src), "sha256": "d" * 64}, out)
                return False
            except NonPresa as e:
                # **The file must not survive**: one that is not what it
                # claims to be, left lying around, gets used anyway.
                return "mismatch" in str(e) and not out.exists()

    yield "a mismatching hash deletes the file", sbagliata_cancella

    def manca_la_fonte():
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            try:
                prendi({"nome": "x", "url": via_file(Path(d) / "niente"), "sha256": ABC}, out)
                return False
            except NonPresa as e:
                return "did not arrive" in str(e) and not out.exists()

    yield "a missing source is a no with a reason", manca_la_fonte


def main() -> int:
    rotte = 0
    for nome, f in prove():
        try:
            ok = f()
        except Exception as e:  # a test that explodes is a red test
            ok, nome = False, f"{nome} (ha alzato {e!r})"
        print(("ok     " if ok else "ROSSO  ") + nome)
        rotte += not ok
    print(f"\n{rotte} red")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main())
