# The index format (`NUCLEOIX`)

The index is **a signed file, not a service and not a stream of facts**.
The CI publishes it; `pkg.refresh` downloads it and keeps it at
`packages/index.nki` on the system volume; `pkg.search` reads it;
`pkg.fetch` finds the server path and the SHA-256 to check arriving
bytes against.

It is data with a signature and an expiry, not state. That is why it is
a file and not a series of facts, and why it is **replaced whole or not
touched at all**.

> This document describes what the running system already reads
> (`nucleo-core/src/pacchetto/indice/`). It is written down here so the
> publisher can be built against a spec instead of against the reader's
> source.

## Layout

All integers are little-endian. Every reserved field is zero **and is
checked**: a reader that skipped them would accept a file a future
version means differently.

### Header — 96 bytes

| offset | size | field | notes |
|---:|---:|---|---|
| 0 | 8 | magic | `NUCLEOIX` |
| 8 | 2 | format version | |
| 10 | 2 | reserved | zero |
| 12 | 4 | entry count | |
| 16 | 8 | `valid_until` | Unix seconds |
| 24 | 64 | host | NUL-padded: where to download from |
| 88 | 2 | port | |
| 90 | 4 | ip | zero = ask `net.resolve` |
| 94 | 2 | reserved | zero |

### Entry — 160 bytes, repeated

| offset | size | field | notes |
|---:|---:|---|---|
| 0 | 32 | name | NUL-padded, and a valid filesystem name |
| 32 | 6 | version | three `u16`: major, minor, patch |
| 38 | 2 | machine | see below |
| 40 | 2 | proposed powers | bit mask, see below |
| 42 | 1 | outcome | 1 = green in CI |
| 43 | 1 | reserved | zero |
| 44 | 8 | pack size | |
| 52 | 32 | pack sha256 | |
| 84 | 64 | server path | NUL-padded, starts with `/` |
| 148 | 12 | reserved | zero |

### Tail

64 bytes: the ECDSA P-256 signature over everything that precedes it.

## Machine

| value | meaning |
|---:|---|
| 1 | `x86_64-unknown-none` — a native NucleoOS ring-3 program |
| 2 | `linux-x86_64` — a static Linux binary, run as a **guest** of `linuxd` |

A guest package is a package like any other: it is signed, installed,
listed and removed the same way. `start` hands it to the tutor instead
of loading it.

## Powers

A bit mask. They are **deliberately coarse**: a fine-grained list —
"this disk", "this port" — would describe a capability, and a capability
is not described, it is handed over. The index says only what *kind* of
thing a program will need, because it is read by a person who has two
seconds to decide; the system remains the one who hands anything over.

| bit | power |
|---:|---|
| 0 | disk — reads and writes a volume |
| 1 | network |
| 2 | audio |
| 3 | screen — draws a window |
| 4 | facts — reads the system's journal |
| 5 | intents — talks to other programs over the intent bus |

## What the reader refuses

The reader **refuses rather than trusts**, and refuses the *whole file*:

- wrong magic, unknown format version, a non-zero reserved field;
- an entry whose name is not a valid filesystem name;
- a truncated file, or a count that does not match the size;
- a signature that does not verify;
- `valid_until` in the past, **against the system clock** — and a clock
  that is behind is itself a refusal, not a yes.

An index with one unreadable entry is an unreadable index: it is signed
as a whole, and whoever signed it should not have published it.

## Why an expiry

Hash and signature make the transport irrelevant, but they do not stop a
mirror from serving an **old, correctly signed** index forever — the
rollback that hides a fixed vulnerability behind a version you already
had. `valid_until` closes it, the way Debian's `Valid-Until` and TUF's
timestamp role do. The CI sets it seven days out.
