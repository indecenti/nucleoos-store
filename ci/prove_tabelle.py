"""The tables' own tests. Run: python3 ci/prove_tabelle.py"""

import sys
import tempfile
from pathlib import Path

import tabelle

VOCE = """\
nome     = "rg"
versione = "14.1.0"
origine  = "github.com/BurntSushi/ripgrep"
url      = "https://example.invalid/rg"
sha256   = "00"
prova    = {{ args = ["-j4", "nucleo", "/dati"], uscita = {uscita} }}
poteri   = {{ radici = [], pagine = 8192 }}
"""

BOZZA = """\
bozza    = true
nome     = "hugo"
versione = "0.128.0"
origine  = "github.com/gohugoio/hugo"
url      = ""
sha256   = "00"
prova    = { args = ["version"], uscita = 0 }
poteri   = { radici = [], pagine = 8192 }
"""


def prepara(d: Path):
    (d / "sorgenti").mkdir()
    (d / "binari").mkdir()
    (d / "packs").mkdir()
    (d / "sorgenti" / "rg.toml").write_text(VOCE.format(uscita=1), encoding="utf-8")
    (d / "sorgenti" / "hugo.toml").write_text(BOZZA, encoding="utf-8")
    return d


def prova_una_bozza_non_entra_nelle_voci():
    with tempfile.TemporaryDirectory() as t:
        d = prepara(Path(t))
        (d / "binari" / "rg").write_bytes(b"\x7fELF")
        fuori = tabelle.voci(d / "sorgenti", d / "binari")
        assert "rg linux-rg -j4,nucleo,/dati 1" in fuori, fuori
        assert "hugo" not in fuori, "una bozza non si prova"


def prova_senza_binario_la_voce_resta_fuori():
    with tempfile.TemporaryDirectory() as t:
        d = prepara(Path(t))
        fuori = tabelle.voci(d / "sorgenti", d / "binari")
        # Una riga che comincia col nome, non il nome ovunque: « args »
        # contiene « rg », e una prova che cercava la sottostringa passava
        # per la ragione sbagliata.
        righe = [r for r in fuori.splitlines() if r.startswith("rg ")]
        assert not righe, f"un binario che non c'e' non si e' provato: {righe}"


def prova_chi_il_giudice_non_ha_visto_e_rosso():
    with tempfile.TemporaryDirectory() as t:
        d = prepara(Path(t))
        (d / "packs" / "rg-14.1.0.nkp").write_bytes(b"pack")
        v = d / "verdetti.txt"
        v.write_text("# nome esito motivo\n", encoding="utf-8")
        fuori = tabelle.indice(d / "sorgenti", v, d / "packs")
        assert fuori.strip().endswith("rosso"), fuori
        assert "/nucleoos-store/packs/rg-14.1.0.nkp" in fuori, "il percorso porta il prefisso di Pages"


def prova_verde_solo_col_pack_e_col_verdetto():
    with tempfile.TemporaryDirectory() as t:
        d = prepara(Path(t))
        v = d / "verdetti.txt"
        v.write_text("rg verde uscito 1\n", encoding="utf-8")
        # Il verdetto c'e' ma il pack no: non si pubblica un percorso
        # che sul server non avrebbe niente dietro.
        assert tabelle.indice(d / "sorgenti", v, d / "packs").strip().endswith("rosso")
        (d / "packs" / "rg-14.1.0.nkp").write_bytes(b"pack")
        assert tabelle.indice(d / "sorgenti", v, d / "packs").strip().endswith("verde")


def main() -> int:
    quante = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("prova_"):
            f()
            quante += 1
    print(f"tabelle: {quante} prove, tutte passate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
