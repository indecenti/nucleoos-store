# The publishing pipeline

What exists today is the **first step**: entries are validated and can
be fetched and checked. This describes the rest, so it can be built
against a plan rather than improvised.

## What runs today

| stage | where | state |
|---|---|---|
| validate entry shape | `ci/valida.py`, 10 tests | **done** |
| fetch + verify sha256 | `ci/prendi.py`, 8 tests | **done** |
| run each binary under `linuxd` in QEMU | — | to build |
| build and sign the index | `tools/indice` in the NucleoOS repo | to build |
| publish to a mirror | — | needs a host |

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

- a static host serving plain HTTP (a free-tier VPS with nginx);
- teach `pkgd` to use `tls.connect` — the system already has TLS 1.3,
  and `fetch` uses it — and publish somewhere that serves HTTPS from a
  stable hostname **without cross-host redirects**. GitHub Pages
  qualifies where Releases do not.

The second costs a small amount of code in `pkgd` and no money. It has
not been verified that Pages behaves as assumed; that check comes before
the choice.

## What the catalogue will contain at first

Only what the boundary can run. Today that is busybox and ripgrep. Go
binaries get much further since the guest quota became a fraction of the
machine rather than a borrowed constant, but are not yet proven
end-to-end; `epoll` and `eventfd` are unserved.

The catalogue grows as the boundary grows, and the queue above says in
what order.
