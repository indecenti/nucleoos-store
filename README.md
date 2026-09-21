# nucleoos-store

The package catalogue for [NucleoOS](https://github.com/indecenti/NucleoOs).

**No software is written here.** We take static Linux binaries that
already exist — busybox, ripgrep, the Rust and Go CLIs — run each one
under `linuxd` inside NucleoOS, and publish **only what passes**.

## The chain

```
upstream (busybox.net, GitHub Releases, aqua-registry)
   │  sha256 as declared by the source
   ▼
CI: download, verify, put the binaries on a disk,
    boot NucleoOS in QEMU and run each one under `linuxd`
   │  green or red, with the reason
   ▼
signed index (ECDSA P-256, with an expiry)
   │
   ▼
plain-HTTP mirror ──► `pkg.refresh` / `pkg.search` / `pkg.fetch` / `install`
```

Three things set this apart from an ordinary mirror:

- **only green gets published.** An entry enters the index if the binary
  **actually started** under the tutor — not if a build succeeded
  somewhere else;
- **the index carries the powers.** A package declares which folders it
  wants and how much memory, and the manifest **is the limit**: not a
  promise in a README, but what the system grants;
- **the transport is not trusted.** Hash, signature and expiry make it
  irrelevant, the way Debian has worked for twenty years. The expiry
  closes rollback: a mirror cannot serve an old signed index forever.

## What it does not do, today

- **It does not read other people's repositories.** Alpine
  (`APKINDEX`), Debian and their signature formats need their own code,
  and that needs the dynamic loader (`ld-musl`) first.
- **Not everything runs.** Go dies on guest memory (declared BSS is
  charged in full); `epoll` and `eventfd` are not served. The catalogue
  grows as the boundary grows, and CI **counts the missing syscalls per
  entry**: the queue sorts itself, by how many entries each one would
  unblock.

## Layout

| where | what |
|---|---|
| `sorgenti/` | one entry per file: where it comes from, what it hashes to, how it is proven |
| `ci/` | the checks, each with its own tests |
| `.github/workflows/sorgenti.yml` | the Action that validates and fetches |
| `docs/INDEX-FORMAT.md` | the signed index, byte by byte |
| `docs/CI.md` | the publishing pipeline: what runs, what does not, and why |

The entry format is in [`sorgenti/README.md`](sorgenti/README.md).

## A note on the language

NucleoOS itself is written and documented in Italian by design, and this
repository keeps the **field names** of that vocabulary — `nome`,
`origine`, `prova`, `poteri` — because they are the same words the
system uses for the same things. One name for one concept beats a
translation layer that drifts. The prose here is English because this is
the outward-facing side.
