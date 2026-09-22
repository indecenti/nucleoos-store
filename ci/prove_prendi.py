#!/usr/bin/env python3
"""The fetch tests, **without a network**.

`urlopen` speaks `file://` too, so the whole round -- fetch, hash as it
arrives, compare, delete on mismatch -- is tested with a real file and
no connection. A test that needed the network would go red the day CI
has none, and then people stop believing it.
"""

import hashlib
import io
import tarfile
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

    def archivio(d: Path, membro: str = "dentro/rg", corpo: bytes = b"abc") -> Path:
        """A .tar.gz with one member, like every Rust release."""
        via = d / "roba.tar.gz"
        with tarfile.open(via, "w:gz") as t:
            info = tarfile.TarInfo(membro)
            info.size = len(corpo)
            t.addfile(info, io.BytesIO(corpo))
        return via

    def da_un_archivio():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            out = d / "out"
            # `sha256` is the hash of the **binary**, never the
            # archive's: it is the file that runs.
            n = prendi({"nome": "x", "url": via_file(archivio(d)), "sha256": ABC, "dentro": "dentro/rg"}, out)
            return n == 3 and out.read_bytes() == b"abc"

    yield "an archive gives up the member it was asked for", da_un_archivio

    def membro_che_non_ce():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            out = d / "out"
            try:
                prendi({"nome": "x", "url": via_file(archivio(d)), "sha256": ABC, "dentro": "altro"}, out)
                return False
            except NonPresa as e:
                return "not in the archive" in str(e) and not out.exists()

    yield "a member that is not there is a no with its name", membro_che_non_ce

    def archivio_che_non_e_un_archivio():
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            src = d / "fonte"
            src.write_bytes(b"abc")
            out = d / "out"
            try:
                prendi({"nome": "x", "url": via_file(src), "sha256": ABC, "dentro": "rg"}, out)
                return False
            except NonPresa as e:
                return "not an archive" in str(e) and not out.exists()

    yield "asking inside something that is not an archive is refused", archivio_che_non_e_un_archivio


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
