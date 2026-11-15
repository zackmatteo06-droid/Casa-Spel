#!/usr/bin/env bash
# Bygger CarDep från källkoden och lägger den färdiga sajten i ../bilkollen (det som publiceras).
#   ./bygg_och_publicera.sh
# Bilder, ikoner, typsnitt och css som inte byggs av bygg.py hämtas först från den publicerade sajten.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p app
cp -R -n ../bilkollen/. app/ 2>/dev/null || true
python3 bygg.py
python3 publicera.py ..
