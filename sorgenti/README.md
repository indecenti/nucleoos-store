# Catalogue entries

One entry per file, and **nothing for CI to guess**.

```toml
nome     = "busybox"          # the name it installs and starts as
versione = "1.36.1"
origine  = "busybox.net"      # who publishes it, for whoever reads the index
url      = "https://..."      # the static x86_64 asset, from upstream
sha256   = "dbac...ac14"      # what upstream declares, not what arrives

# How it is proven to work. CI starts it under `linuxd` and demands this
# exit code: a binary that loads but does nothing is not a binary that
# works.
prova    = { args = ["echo", "ciao"], uscita = 0 }

# The powers it asks for. Empty = it touches nothing outside itself.
# `radici` are the handed-over folders; without them it sees no files.
poteri   = { radici = [], pagine = 4096 }
```

## The fields

| field | meaning |
|---|---|
| `nome` | the package name; **must match the file name** |
| `versione` | upstream's version string |
| `origine` | who publishes it |
| `url` | the exact asset, over `https` |
| `sha256` | 64 lowercase hex digits, **from the source** |
| `prova` | `args` handed to the binary, and the `uscita` (exit code) demanded |
| `poteri` | `radici` (folders) and `pagine` (4 KiB pages of memory) |
| `bozza` | `true` = a draft: it validates, but stays out of the index |

## Two rules worth the words

**`sha256` comes from the source, not from the downloaded file.**
Hashing what arrived and calling it verification checks that the bytes
did not rot in flight — not that they are the right bytes. If upstream
publishes no checksum, the entry says so
(`origine_senza_checksum = true`) and goes into the index **marked**, so
whoever installs knows trust stops at GitHub.

**`prova` is not optional.** The criterion of this catalogue is "it
actually started", and without a proof an entry cannot be green.

## Drafts

An entry with no `url` yet is not an error — it is honest. Mark it
`bozza = true`: validation passes, and the index builder skips it. A
check that goes red while you are working correctly teaches people to
ignore red.
