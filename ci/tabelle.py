"""The two tables that join Python to Rust.

The catalogue's entries are TOML, and Python validates them
(`ci/valida.py`). The judge and the index builder are Rust, inside
NucleoOS's own repository, and they read **generated tables**: one line
per entry, fields separated by spaces.

Two parsers of one format is how two programs stop agreeing about what
was written. A generated table has one writer and one reader, and
neither has to guess the other.

    tabelle.py voci    sorgenti/ binari/ > voci.txt
    tabelle.py indice  sorgenti/ verdetti.txt packs/ [prefisso] > indice.txt

`voci.txt` is what the judge runs: name, the name the binary has inside
the pack, the arguments, and the exit code the entry promises.
`indice.txt` is what the index builder publishes: name, path on the
server, pack file, and the verdict the judge actually gave.
"""

import sys
import tomllib
from pathlib import Path


def entries(cartella: Path):
    """Every entry that is not a draft, by name."""
    fuori = {}
    for f in sorted(Path(cartella).glob("*.toml")):
        with f.open("rb") as fh:
            v = tomllib.load(fh)
        if v.get("bozza"):
            continue
        fuori[v["nome"]] = v
    return fuori


def voci(sorgenti: Path, binari: Path) -> str:
    """The judge's input.

    The binary is in the image as `linux-<name>`: that is the name
    `imgbuild --dato` gives it and the name `start linuxd elf=` asks
    for. An entry whose binary was not fetched is left out rather than
    declared red — it was never run, and a verdict nobody produced is
    not a verdict.
    """
    righe = ["# nome dato args uscita"]
    for nome, v in entries(sorgenti).items():
        if not (Path(binari) / nome).exists():
            print(f"tabelle: {nome}: il binario non c'e' in {binari}, resta fuori", file=sys.stderr)
            continue
        prova = v["prova"]
        args = ",".join(prova["args"])
        righe.append(f"{nome} linux-{nome} {args} {prova['uscita']}")
    return "\n".join(righe) + "\n"


def verdetti(file: Path) -> dict:
    """The judge's output: name -> green?"""
    fuori = {}
    for riga in Path(file).read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#"):
            continue
        campi = riga.split(maxsplit=2)
        if len(campi) < 2:
            continue
        fuori[campi[0]] = campi[1] == "verde"
    return fuori


def indice(sorgenti: Path, file_verdetti: Path, packs: Path, prefisso: str = "/nucleoos-store") -> str:
    """What the index builder publishes.

    An entry the judge never saw is **red**, not missing: the index
    counts greens, and a number that can drop because something quietly
    stopped being run is a number that answers nothing.
    """
    dati = entries(sorgenti)
    dei_verdetti = verdetti(file_verdetti)
    righe = ["# nome percorso file esito"]
    for nome, v in dati.items():
        pack = f"{nome}-{v['versione']}.nkp"
        # Il prefisso non e' un vezzo: GitHub Pages serve un progetto
        # sotto il nome della repository, non alla radice del sito, e il
        # percorso che finisce nell'indice e' quello che `pkgd` chiedera'.
        percorso = f"{prefisso}/packs/{pack}"
        verde = dei_verdetti.get(nome, False) and (Path(packs) / pack).exists()
        righe.append(f"{nome} {percorso} {Path(packs) / pack} {'verde' if verde else 'rosso'}")
    return "\n".join(righe) + "\n"


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    quale = argv[1]
    if quale == "voci" and len(argv) == 4:
        sys.stdout.write(voci(Path(argv[2]), Path(argv[3])))
        return 0
    if quale == "indice" and len(argv) in (5, 6):
        prefisso = argv[5] if len(argv) == 6 else "/nucleoos-store"
        sys.stdout.write(indice(Path(argv[2]), Path(argv[3]), Path(argv[4]), prefisso))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
