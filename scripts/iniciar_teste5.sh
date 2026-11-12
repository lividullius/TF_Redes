#!/bin/sh
# Inicia os 5 roteadores da topologia de teste, cada um em um terminal.
# macOS: abre janelas do Terminal. Outros sistemas: mostra os comandos.
# Uso: sh scripts/iniciar_teste5.sh [pasta de configs]   (padrão: configs/teste5)

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PASTA="${1:-configs/teste5}"

for conf in "$RAIZ/$PASTA"/r*.conf; do
    cmd="cd '$RAIZ' && python3 roteador.py '$PASTA/$(basename "$conf")'"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "tell application \"Terminal\" to do script \"$cmd\"" >/dev/null
    else
        echo "$cmd"
    fi
done

command -v osascript >/dev/null 2>&1 || \
    echo "Rode cada linha acima em um terminal separado."
