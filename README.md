# nucleoos-store

Il catalogo dei pacchetti di [NucleoOS](https://github.com/indecenti/NucleoOs).

**Qui non si scrive software.** Si prendono binari Linux statici che
esistono già — busybox, ripgrep, le CLI in Rust e in Go — li si prova
sotto `linuxd` dentro NucleoOS, e si pubblica **solo quello che passa**.

## La catena

```
upstream (busybox.net, GitHub Releases, aqua-registry)
   │  sha256 dichiarato dalla fonte
   ▼
CI: scarica, verifica, mette i binari su un disco,
    avvia NucleoOS in QEMU e fa girare ognuno sotto `linuxd`
   │  verde o rosso, col motivo
   ▼
indice firmato (ECDSA P-256, con scadenza)
   │
   ▼
mirror in HTTP  ──►  `pkg.refresh` / `pkg.search` / `pkg.fetch` / `install`
```

Tre cose la distinguono da un mirror qualunque:

- **si pubblica solo il verde.** Una voce entra nell'indice se il binario
  è **partito davvero** sotto il tutore, non se la build è riuscita da
  qualche altra parte;
- **l'indice porta i poteri.** Un pacchetto dichiara quali cartelle
  vuole e quanta memoria, e il manifesto **limita**: non è una promessa
  nel README, è ciò che il sistema concede;
- **il nastro non è fidato.** Hash, firma e scadenza rendono il
  trasporto irrilevante, come Debian per vent'anni. La scadenza chiude
  il rollback: un mirror non può servire per sempre un indice vecchio e
  firmato.

## Che cosa non fa, oggi

- **Non legge i repository altrui.** Alpine (`APKINDEX`), Debian e i
  loro formati di firma vogliono il loro codice, e serve prima il
  caricatore dinamico (`ld-musl`).
- **Non tutto gira.** Go muore sulla memoria dell'ospite (il BSS
  dichiarato si paga per intero); `epoll` e `eventfd` non sono servite.
  Il catalogo cresce quando cresce ciò che regge il confine, e il CI
  **conta le chiamate mancanti per voce**: la coda si ordina da sola,
  per quante voci sbloccherebbe.

## La struttura

| dove | che cosa |
|---|---|
| `sorgenti/` | una voce per file: da dove viene, che impronta ha, come si prova |
| `.github/workflows/indice.yml` | la Action che prova e pubblica |

Il formato di una voce sta in [`sorgenti/README.md`](sorgenti/README.md).
