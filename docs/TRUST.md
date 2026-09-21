# What this catalogue protects, and what it does not

A package manager that oversells its guarantees is worse than one that
states them, because people act on the difference. This is the honest
version.

## What there is to protect

Someone runs `install rg` on a machine they own. Between the upstream
author and that machine there are: a build, a CI, an index, a mirror, a
network, and a signature. What must be true at the end is that the
bytes that run are the bytes the author published, and that what the
program is allowed to touch is what the person agreed to.

## What is actually defended

**Tampering in transit.** The index is signed (ECDSA P-256) and each
pack carries a SHA-256 that is checked **as the bytes arrive**, before
anything is written to the volume. The mirror is a tape that carries
bytes; corrupting it changes nothing it can get away with. This is why
plain HTTP is a deliberate choice and not a gap.

**Rollback.** A correctly signed old index — the one hiding a fix you
already had — is refused by `valid_until`, checked against the system
clock. A clock that is behind is itself a refusal, not a yes.

**A malformed index.** The reader refuses the *whole file* if any part
of it does not read: reserved bytes must be zero, names must be valid,
the count must match the size. It is signed as a whole, so a
half-readable index is one its signer should not have published.

**Untested software.** An entry is in the index because the binary
**started and did what its `prova` said**, inside NucleoOS, under the
tutor. This is the part no ordinary mirror does.

**Unbounded reach.** A package declares the *kind* of things it needs —
disk, network, audio, screen, facts, intents — and the manifest limits
it. The system hands over capabilities; the index only says what will
be asked for, so a person can decide in two seconds.

## What is not defended, and is not pretended to be

**A malicious upstream.** If the author of a tool publishes something
harmful, we will fetch it, verify it matches what they published, run
its smoke test, and sign it. The signature says *this is what upstream
published and it started under our tutor*. It does not say the program
is benign. No catalogue can say that, and this one does not pretend to.

**A compromised signing key.** Whoever holds it decides what NucleoOS
will install. There is no threshold, no second signer, no transparency
log. While the repository is private and the users are its authors,
this is a stated limitation rather than a hole; the day it signs for
strangers, it needs more than one person's key.

**Upstream without a checksum.** Some projects publish no `SHA256SUMS`.
Those entries declare `origine_senza_checksum = true` and go into the
index **marked**: trust stops at whoever hosts the asset. We record
that rather than hiding it behind our own signature, which would
launder it.

**What a program does with what it was given.** A package that asks for
disk gets a folder, and inside that folder it can do what it likes. The
powers bound the *reach*, not the behaviour.

**Who is watching.** Plain HTTP exposes *which packages you install* to
anyone on the path. That is a real cost of the choice, and the mitigation
is not encryption of the tape — it is that the list is not secret in the
first place. If it needs to be, the client must speak TLS.

**The build.** We do not build most of what we ship; we repackage
published binaries. Where the CI does build (from crates.io, from Go
modules), it signs what **it** built, and says whether the build was
reproducible. Those are different claims and the index keeps them apart.

## The decision this document exists for

Before the first public index, one thing must be chosen deliberately:
**who holds the key, and what it means when it signs.**

Today the CI key and the publisher key can be the same, because the
repository is private and the audience is its authors. The moment
someone who is not an author installs from this catalogue, the
signature stops meaning "we tested this" and starts meaning "trust us".
That transition is easy to miss because nothing breaks when it happens.

It is written here so that it is a decision and not a drift.
