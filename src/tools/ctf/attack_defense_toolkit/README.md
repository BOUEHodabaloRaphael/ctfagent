# Toolkit Attack-Defense

Toolkit générique réutilisable pour n'importe quel CTF A/D (ICC, HackTheBox
A/D events, Kaspersky SAS-style, etc.). 4 outils indépendants à lancer dans
4 terminaux/panes tmux séparés pendant le match.

## Avant le match

1. Remplir `config.py` : IP des équipes (`TEAMS`), regex de flag
   (`FLAG_REGEX`), endpoint/méthode de soumission (`SUBMIT_URL` ou
   `SUBMIT_TCP_HOST`/`PORT`), durée du tick (`TICK_SECONDS`), et tes propres
   services (`SERVICES`) pour le monitoring.
2. `pip3 install --user --break-system-packages requests pwntools` si pas
   déjà fait (pwntools déjà installé sur cette machine, voir mémoire env).

## Pendant le match

**Pane 1 — reverse/patch** : analyse le service fourni, trouve la vuln,
écris `exploits/<service>.py` à partir de `exploits/template.py`. Teste
d'abord en solo :
```
python3 exploit_runner.py exploits/gatekeeper.py --once --targets 127.0.0.1
```
Une fois confirmé qu'il sort bien un flag sur ta propre instance (ou une
instance de test fournie par l'orga), lance-le en boucle sur toutes les
équipes :
```
python3 exploit_runner.py exploits/gatekeeper.py
```
Un process par exploit/service — un tab tmux par service actif.

**Pane 2 — SLA** : pendant que tu patches, surveille que tu ne casses pas
ton propre service :
```
python3 sla_monitor.py --interval 15
```

**Pane 3 — recon défensif** : repère ce que les autres essaient contre toi
pour patcher/bloquer en conséquence :
```
sudo python3 pcap_watch.py --iface tun0 --ports 8080,1337
```
(adapter l'interface — `tun0` si connecté en WireGuard, `eth0` en filaire.)

**Pane 4 — libre** : ad-hoc (curl manuel, gdb sur le binaire, etc.)

## Workflow recommandé

1. Premières ~15-20 min : reverse le(s) service(s), pas de patch précipité
   (patcher trop vite/mal = service down = perte de points SLA garantie).
2. Dès qu'un exploit marche en solo → le lancer en boucle (`exploit_runner.py`
   sans `--once`) le plus tôt possible, avant que les autres équipes patchent.
3. Patcher seulement après avoir un exploit qui marche (sinon tu perds le
   volet attaque pendant que tu défends).
4. Utiliser `pcap_watch.py` pour copier/comprendre les payloads adverses —
   souvent le patch le plus rapide est un blocage regex ciblé plutôt qu'un
   vrai fix de code.
5. Ne jamais couper `sla_monitor.py` — c'est ton seul signal fiable que ton
   patch n'a pas cassé le service.

## Fichiers

- `config.py` — toute la config du match (à remplir en premier)
- `submitter.py` — soumission de flags (HTTP JSON ou TCP texte), dédup
  automatique via `submitted_flags.txt`
- `exploit_runner.py` — boucle d'exploitation multi-cibles au rythme du tick
- `exploits/template.py` — squelette à copier pour chaque nouveau service
- `sla_monitor.py` — health check de tes propres services
- `pcap_watch.py` — détection de payloads suspects en direct sur tes ports
