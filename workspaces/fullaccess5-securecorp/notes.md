# fullaccess5--securecorp-incident-reseau-invite (forensics, 200pts) — formatage flag bloque

## Faits confirmes (analyse pcap traffic-04.cap, 11MB, 802.11)
- SSID: `Wifi-Test` (hex 576966692d54657374, decode confirme)
- BSSID: `EA:2A:EA:1E:A0:5A` (seul BSSID emettant des beacons dans le pcap)
- Attaque: Deauthentication (196258 frames subtype 0x0c -- deauth massif confirme)
- 1ere trame EAPOL (msg1, AP->client ea:2a:ea:1e:a0:5a -> e8:fb:1c:bc:8c:1d):
  epoch 1780925091.624999 -> `date -u -d @1780925091` = **2026-06-08 13:24:51 UTC**
  (coherent avec "vers 13 heures" du recit -- verifie avec `date` pas juste tshark)
- Mot de passe WPA2 (aircrack-ng -w rockyou.txt): **30secondstomars** (KEY FOUND confirme)
- MITRE ATT&CK Initial Access: **T1669** "Wi-Fi Networks" (verifie via web search,
  page officielle attack.mitre.org/techniques/T1669/, v1.0 fev 2025)

## 6 tentatives rejetees (formatage uniquement, pas les valeurs factuelles)
1. `NCTF{Wifi-Test_EA:2A:EA:1E:A0:5A_Deauthentication_13:24:51_30secondstomars_T1669}`
2. `NCTF{Wifi-Test_ea:2a:ea:1e:a0:5a_Deauthentication_09:24:51_30secondstomars_T1669}` (heure locale)
3. `NCTF{Wifi-Test_EA:2A:EA:1E:A0:5A_Desauthentification_13:24:51_30secondstomars_T1669}` (FR)
4. `NCTF{Wifi-Test_EA2AEA1EA05A_Deauthentication_13:24:51_30secondstomars_T1669}` (bssid sans :)
5. `NCTF{Wifi-Test_ea:2a:ea:1e:a0:5a_Deauthentication_13:24:51_30secondstomars_T1669}` (bssid minuscule)

## Pistes non testees (si repris)
- Nom d'attaque alternatif: "Deauth", "Deauth Attack", "Disassociation" (verifier
  subtype exact -- 0x0c = Deauthentication, 0x0a = Disassociation, deja confirme 0x0c)
- SSID avec casse differente ou underscore au lieu du tiret: "Wifi_Test"
- BSSID avec tirets au lieu de deux-points: "EA-2A-EA-1E-A0-5A"
- MITRE ID alternatif: T1078 (Valid Accounts) si T1669 pas reconnu par le grader
- Heure avec millisecondes ou format different

Statut: blackbox-exhausted sur le FORMAT (valeurs factuelles solides, verifiees
par outils independants: tshark, aircrack-ng, date, recherche web officielle
MITRE). Pas de flag soumis avec succes.
