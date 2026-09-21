# Le voci del catalogo

Una voce per file, e **niente che il CI debba indovinare**.

```toml
nome     = "busybox"          # come si chiamera' installato
versione = "1.36.1"
url      = "https://..."      # l'asset x86_64 statico, dall'upstream
sha256   = "dbac...ac14"      # quello che l'upstream dichiara, non quello che arriva
origine  = "busybox.net"      # chi lo pubblica, per chi legge l'indice

# Come si prova che funziona. Il CI lo avvia sotto `linuxd` e pretende
# questo codice di uscita: un binario che si carica ma non fa niente non
# e' un binario che funziona.
prova    = { args = ["echo", "ciao"], uscita = 0 }

# I poteri che chiede. Vuoti = non tocca niente fuori da se'.
# `radici` sono le cartelle consegnate; senza, non vede nessun file.
poteri   = { radici = [], pagine = 4096 }
```

**`sha256` viene dalla fonte, non dal file scaricato.** Prendere
l'impronta di cio' che e' arrivato e chiamarla verifica e' un giro a
vuoto: verifica che il byte non si sia rotto in volo, non che sia il
byte giusto. Se l'upstream non pubblica un checksum, la voce lo dice
(`origine_senza_checksum = true`) e finisce nell'indice **marcata**,
perche' chi installa sappia che la fiducia si ferma a GitHub.

**`prova` non e' opzionale.** Il criterio di questo catalogo e' « e'
partito davvero », e senza una prova una voce non puo' essere verde.
