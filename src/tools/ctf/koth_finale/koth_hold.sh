#!/usr/bin/env bash
# =============================================================================
# Alias historique : `koth_hold.sh` = `koth_run.sh`.
# La commande a lancer est desormais :  bash koth_run.sh start
# =============================================================================
set -u
cd "$(dirname "$0")"
exec bash ./koth_run.sh "$@"
