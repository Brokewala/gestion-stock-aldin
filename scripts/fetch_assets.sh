#!/usr/bin/env bash
set -euo pipefail

ASSETS_DIR="dynamic_shop/static/img"
mkdir -p "$ASSETS_DIR"

curl -L "https://images.unsplash.com/photo-1573878735868-80d17752b5d7?auto=format&fit=crop&w=800&q=80" -o "$ASSETS_DIR/dynamic-cans.jpg"

echo "Assets téléchargés dans $ASSETS_DIR. Utilisez-les librement pour vos maquettes locales." 
