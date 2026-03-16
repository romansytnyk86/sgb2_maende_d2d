#!/usr/bin/env bash
# ============================================================
#  SGB II MaEnde - Deployment Launcher (Linux / macOS)
# ============================================================

set -euo pipefail

usage() {
    echo ""
    echo "Usage:"
    echo "  ./run.sh ohne-backup"
    echo "  ./run.sh mit-backup <YYYYMM>"
    echo ""
    echo "Examples:"
    echo "  ./run.sh ohne-backup"
    echo "  ./run.sh mit-backup 202512"
    echo ""
    exit 1
}

if [[ $# -lt 1 ]]; then usage; fi

case "$1" in
    ohne-backup)
        echo "Running: ohne-backup workflow"
        python main.py ohne-backup
        ;;
    mit-backup)
        if [[ $# -lt 2 ]]; then
            read -rp "Bitte Monat fuer das Backup-Projekt angeben (z.B. 202512): " MONTH
        else
            MONTH="$2"
        fi
        echo "Running: mit-backup workflow [backup-month: ${MONTH}]"
        python main.py mit-backup --backup-month "${MONTH}"
        ;;
    *)
        usage
        ;;
esac
