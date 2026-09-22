# The publishing pipeline

What exists today is the **first step**: entries are validated and can
be fetched and checked. This describes the rest, so it can be built
against a plan rather than improvised.

## What runs today

| stage | where | state |
|---|---|---|
| validate entry shape | `ci/valida.py`, 10 tests | **done** |
| fetch + verify sha256 | `ci/prendi.py`, 8 tests | **done** |
| the two generated tables | `ci/tabelle.py`, 4 tests | **done** |
| run each binary under `linuxd` in QEMU | `run.sh giudica` in the NucleoOS repo | **done** |
| build and sign the index | `tools/indice` in the NucleoOS repo | **done** |
| publish to a mirror | GitHub Pages, `.github/workflows/pubblica.yml` | **wired, never run** |

What is missing is not code any more, and it is not entries either:
it is the **two secrets** (`NUCLEO_REPO_TOKEN`, `NUCLEO_STORE_KEY`).
Both entries were rewritten on 2026-09-22 from their origin down — the
upstream file fetched, hashed and **proven under `linuxd`** — so the
first index this pipeline publishes will carry two greens.

## Python writes tables, Rust reads them

The entries are TOML and Python validates them. The judge and the index
builder are Rust. Between them there are **two generated tables**, one
line per entry, and no second parser of anything:

```
sorgenti/*.toml ──ci/tabelle.py voci──► voci.txt ──► run.sh giudica
                                                         │
                                                    verdetti.txt
                                                         │
sorgenti/*.toml ──ci/tabelle.py indice──► indice.txt ──► tools/indice ──► index.nki
```

Two parsers of one format is how two programs stop agreeing about what
was written.

## How the judge decides

Not from the console. The tutor prints the guest's exit code for whoever
is watching, and the CI is not watching: it reads the **facts** written
on the disk — `GuestCreated` and `GuestExited` — with the same decoder
the kernel uses. A log line can be lost; a fact cannot.

`GuestExited` carries the code the guest passed to `exit_group`, and
**zero is not the same as silence**: a guest killed by its quota, or
stopped by the tutor, leaves no such fact, and an entry that leaves no
fact is red rather than green for lack of evidence.

## The missing middle: proving a binary

This is the stage that makes this catalogue different from a mirror, so
it is worth being exact about what it does.

1. Build NucleoOS images (the NucleoOS repo already does this; its own
   CI runs `qemu-system-x86` with `ovmf` on `ubuntu-24.04`).
2. Put the fetched binaries on a disk image as `--dato` entries.
3. Boot, and for each entry run it under the tutor with the `prova`
   the entry declares — `args`, and the `uscita` demanded.
4. Read the outcome from the serial line with `nucleo-facts`: the
   guest's exit code and its footprint.
5. Mark the entry green or red **with the reason**.

**Only green is published.** An entry enters the index because the
binary *started and did what it said*, not because a build succeeded
somewhere else.

### The side effect that is worth as much

A guest that hits a syscall we do not serve leaves a note with the
number. Summed per entry, that gives **the queue of missing syscalls
ordered by how many catalogue entries each one would unblock**. Nobody
has to guess whether `epoll` matters more than signals: the count says
so.

The same goes for `GuestDenied` on paths: an entry that is refused a
folder proposes the manifest it would need.

## Signing

`pkgbuild` signs with ECDSA P-256. The CI needs the private key as a
repository secret.

**This is the trust root of the whole chain.** Whoever holds that key
decides what NucleoOS will agree to install. Two consequences worth
stating before, not after:

- the key in CI is **rotatable**: if it is ever mishandled, generate
  another and republish the index. Nothing is permanently lost;
- the key that one day signs for people who are not the authors is a
  different key, and a different decision. Today they can be the same
  because the repository is private and the users are us. The moment
  that stops being true is easy to miss, which is why it is written
  here.

## The mirror

The client speaks **plain HTTP by design**: hash, signature and expiry
make the transport untrusted, the way Debian has worked for twenty
years. The exposure that remains is *which packages you install*, and
that is stated rather than hidden.

GitHub is therefore the **source of the CI, not of the client**: it is
HTTPS with a 302 to another host, and a redirect is a second connection
with a different name.

Two ways out, neither chosen yet:

**Chosen, and measured** (2026-09-22): the second. GitHub Pages, and
`pkgd` speaks TLS.

What the measurements said, before the choice rather than after:

- plain HTTP on Pages **does not exist**: `http://` answers `301` to
  `https://` on the *same* host, so the redirect is not the cross-host
  one that Releases do — the wall is only the scheme;
- a static file arrives with `Content-Length` and no
  `Transfer-Encoding`, which is the only shape `pkgd`'s reader knows;
- the certificate chain of `*.github.io` is **RSA from leaf to root**
  (Let's Encrypt, anchored at ISRG Root X1). Asking GitHub for an
  ECDSA-only chain fails the handshake: that certificate does not
  exist. So `tlsd` turned on RSA verification, and two of its ceilings
  had to grow — the chain does not fit in 2 048 bytes, and neither do
  its record buffers.

Pages serves a project under the repository's name, not at the root of
the site, so the index lives at `/nucleoos-store/index.nki` and every
pack path in the index carries that prefix.

## Provenance is not adjusted, it is redone

Both entries used to carry the hash of a local copy that did not come
from the origin they named: busybox's was Ubuntu's build (glibc, twice
the size) under a `busybox.net` origin, and ripgrep's was a file that is
not in the published tarball — same version, same target, different
bytes.

Neither was patched. The origin became the truth: fetch what upstream
publishes, run **that** under `linuxd`, and write what came out. An
entry whose provenance and whose proof are about two different files is
worse than no entry, because it looks like one.

## What the catalogue will contain at first

Only what the boundary can run. Today that is busybox and ripgrep. Go
binaries get much further since the guest quota became a fraction of the
machine rather than a borrowed constant, but are not yet proven
end-to-end; `epoll` and `eventfd` are unserved.

The catalogue grows as the boundary grows, and the queue above says in
what order.
