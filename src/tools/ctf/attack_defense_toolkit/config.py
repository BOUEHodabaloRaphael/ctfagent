"""
Config centrale du toolkit A/D. A remplir au début de chaque compétition
(l'orga donne généralement : liste des IP équipes, format de flag, endpoint
de soumission, durée du tick) puis laisser tel quel pendant tout le match.
"""

# --- Cibles -----------------------------------------------------------
# IP/hostname de toutes les équipes adverses (PAS la tienne). Rempli à
# partir du scoreboard ou de l'annonce de l'orga en début de match.
TEAMS = [
    # "10.10.1.2",
    # "10.10.1.3",
]

# Ton IP à toi, pour les checks SLA sur tes propres services.
OWN_IP = "127.0.0.1"

# --- Timing -------------------------------------------------------------
# Durée d'un tick (généralement annoncée par l'orga, souvent 90-120s).
TICK_SECONDS = 100

# --- Flags ----------------------------------------------------------------
# NCTF26 (National CTF du Togo) : format confirmé sur ctf.tg = NCTF{...}.
# Garder ce flag_regex par defaut pour ce CTF ; si la finale A/D de Lomé
# utilise un format différent (annoncé sur place), changer uniquement
# cette ligne avant le début du match.
FLAG_REGEX = r"NCTF\{[^}]+\}"
# FLAG_REGEX = r"[A-Za-z0-9]{31}="          # format A/D historique (ictf-like)
# FLAG_REGEX = r"FLAG\{[^}]+\}"
# FLAG_REGEX = r"[a-z0-9_]+\{[^}]+\}"

# --- Soumission -----------------------------------------------------------
# A remplir avec l'endpoint réel de arena.ctf.tg une fois l'API de
# soumission A/D de la finale annoncée (pas encore connue avant le 19 nov).
SUBMIT_URL = "http://scoreboard.example/api/submit"
SUBMIT_METHOD = "POST"            # POST le plus courant, parfois flag brut sur un socket TCP
SUBMIT_JSON_KEY = "flag"          # nom du champ JSON attendu par la plateforme
SUBMIT_HEADERS = {
    # "Authorization": "Bearer <team_token>",
}
SUBMIT_TIMEOUT = 5

# Certaines plateformes A/D soumettent via un simple socket TCP texte
# (une ligne par flag, une ligne de réponse). Si c'est le cas, laisser
# SUBMIT_URL à None et remplir ceci à la place.
SUBMIT_TCP_HOST = None
SUBMIT_TCP_PORT = None

# --- Services à toi (pour sla_monitor.py) ----------------------------------
# (nom, host, port, type) — type = "tcp" ou "http"
SERVICES = [
    # ("gatekeeper", OWN_IP, 8080, "http"),
    # ("onlychess", OWN_IP, 1337, "tcp"),
]
