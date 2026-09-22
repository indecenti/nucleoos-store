#!/usr/bin/env python3
"""Fetch an entry, and **refuse it** if it is not the one declared.

This is the first half of the real CI (`plans/APP-DI-TERZI.md` §7.2):
take the asset from upstream and compare it against the hash the entry
declares. The second half -- boot NucleoOS in QEMU and run the binary
under `linuxd` -- needs the NucleoOS repository to build the images.

**The hash is computed as the bytes arrive**, not afterwards: an asset
of hundreds of megabytes is not held in memory to be looked at later,
and putting it on disk before knowing whether it is the right one means
writing bytes nobody knows anything about.

**And the comparison is against what the entry declares**, which comes
from upstream. Hashing what arrived and calling it verification checks
that the bytes did not rot in flight -- not that they are the right
bytes.
"""

import hashlib
import tarfile
import zipfile
import sys
import tomllib
from pathlib import Path
from urllib.request import urlopen

# How much is read at a time. One mebibyte: enough not to make a call per
# TCP packet, little enough to hold nothing serious in RAM.
FETTA = 1024 * 1024


class NonPresa(Exception):
    """With the reason, which is the only thing a log reader needs."""


def impronta(pezzi) -> str:
    """The SHA-256 of a sequence of chunks, as lowercase hex.

    It stands alone because it is the only part that can be tested
    without a network: the caller hands it bytes, and it does not care
    where they came from.
    """
    h = hashlib.sha256()
    for p in pezzi:
        h.update(p)
    return h.hexdigest()


def fette(f, quanto: int = FETTA):
    """The chunks of a stream, while there are any."""
    while True:
        p = f.read(quanto)
        if not p:
            return
        yield p


def estrai(via: Path, dentro: str) -> int:
    """Replace the archive at `via` with the member `dentro`.

    **The kind is read from the bytes, not from the name.** The file we
    downloaded is named by us, not by upstream: it has no extension to
    read, and a URL can redirect to something that does not carry one
    either. `tarfile` and `zipfile` both know how to recognise their own.

    A member that is not a plain file — a symlink, a device, a directory
    — is refused rather than written: an archive is somebody else's
    bytes, and the first thing it can try is to write something we did
    not ask for.
    """
    fuori = via.with_name(via.name + ".estratto")
    if zipfile.is_zipfile(via):
        with zipfile.ZipFile(via) as z:
            try:
                info = z.getinfo(dentro)
            except KeyError as e:
                raise NonPresa(f"`{dentro}` is not in the archive") from e
            if info.is_dir():
                raise NonPresa(f"`{dentro}` is a directory")
            with z.open(info) as f, fuori.open("wb") as out:
                for p in fette(f):
                    out.write(p)
    else:
        try:
            t = tarfile.open(via, "r:*")
        except tarfile.TarError as e:
            raise NonPresa(f"not an archive this knows: {e}") from e
        with t:
            try:
                m = t.getmember(dentro)
            except KeyError as e:
                raise NonPresa(f"`{dentro}` is not in the archive") from e
            if not m.isfile():
                raise NonPresa(f"`{dentro}` is not a plain file")
            f = t.extractfile(m)
            if f is None:
                raise NonPresa(f"`{dentro}` has no content")
            with f, fuori.open("wb") as out:
                for p in fette(f):
                    out.write(p)
    via.unlink()
    fuori.replace(via)
    return via.stat().st_size


def prendi(voce: dict, dove: Path) -> int:
    """Fetch the entry into `dove`. Returns the byte count, or raises.

    The file is written **while** the hash is computed, and **deleted**
    if it does not match: leaving a file that is not what it claims to
    be is how somebody ends up using it anyway.
    """
    if voce.get("bozza"):
        raise NonPresa(f"{voce.get('nome')}: it is a draft, not fetched")
    url = voce.get("url") or ""
    atteso = voce.get("sha256") or ""
    dentro = voce.get("dentro") or ""
    if not url or not atteso:
        raise NonPresa(f"{voce.get('nome')}: no url or no sha256")

    n = 0
    dove.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(url, timeout=60) as r, dove.open("wb") as out:
            for p in fette(r):
                out.write(p)
                n += len(p)
    except NonPresa:
        raise
    except Exception as e:  # network, DNS, 404: one reason, and visible
        dove.unlink(missing_ok=True)
        raise NonPresa(f"{voce.get('nome')}: did not arrive: {e}") from e

    # **Almost nothing upstream ships a bare binary.** Rust and Go
    # releases are `.tar.gz`, and an entry that could only name a plain
    # file would leave most of the catalogue unreachable. So an entry may
    # say `dentro`: then `url` is an archive, and that is the member we
    # run.
    #
    # `sha256` stays the hash of **the file that runs**, never the
    # archive's: it is the thing the judge boots and the thing the pack
    # carries, and pinning anything else would pin something nobody
    # executes.
    if dentro:
        try:
            n = estrai(dove, dentro)
        except NonPresa:
            dove.unlink(missing_ok=True)
            raise
        except Exception as e:
            dove.unlink(missing_ok=True)
            raise NonPresa(f"{voce.get('nome')}: the archive did not open: {e}") from e

    h = hashlib.sha256()
    with dove.open("rb") as f:
        for p in fette(f):
            h.update(p)
    avuto = h.hexdigest()
    if avuto != atteso:
        dove.unlink(missing_ok=True)
        raise NonPresa(
            f"{voce.get('nome')}: hash mismatch\n"
            f"  declared {atteso}\n"
            f"  arrived  {avuto}\n"
            f"  ({n} bytes from {url})"
        )
    return n


def main(radice: str = "sorgenti", scarico: str = "scarico") -> int:
    vie = sorted(Path(radice).glob("*.toml"))
    prese = saltate = rotte = 0
    for via in vie:
        voce = tomllib.loads(via.read_text(encoding="utf-8"))
        nome = voce.get("nome", via.stem)
        if voce.get("bozza"):
            print(f"{nome}: draft -- skipped")
            saltate += 1
            continue
        try:
            n = prendi(voce, Path(scarico) / nome)
            print(f"{nome}: {n} bytes, hash matches")
            prese += 1
        except NonPresa as e:
            print(f"{e}")
            rotte += 1
    print(f"\n{len(vie)} voci: {prese} prese, {saltate} bozze, {rotte} rifiutate")
    return 1 if rotte else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
