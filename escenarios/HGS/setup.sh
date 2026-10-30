#!/bin/bash
###############################################################################
# Deja listo el escenario HGS: crea .venv (Python 3.11 + pyVRP 0.5.0) en esta
# carpeta y prueba el target-runner con una instancia.
#
#   bash escenarios/HGS/setup.sh
#
# Si ya tienes un Python con pyvrp==0.5.0, puedes saltarte esto y poner
# PYTHON_BIN=/ruta/a/python en escenario.env.
###############################################################################
set -eu

ESCENARIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ESCENARIO_DIR}"

if [ ! -x .venv/bin/python ]; then
    if ! command -v uv > /dev/null 2>&1; then
        echo "-- instalando uv en ~/.local/bin"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="${HOME}/.local/bin:${PATH}"
    fi
    # pyvrp 0.5.0 solo tiene wheels hasta Python 3.11
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python -r requirements.txt
else
    echo "-- .venv ya existe, se omite"
fi

echo "-- prueba del target-runner (5 s):"
TIME_LIMIT=5 ./target-runner 1 1 42 "${ESCENARIO_DIR}/instancias/solomon/C101.txt" \
    -ps 25 -gs 40 -ne 0.1 -nc 0.1 -xi 0.4
echo "Listo."
