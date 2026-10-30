#!/bin/bash
###############################################################################
# Deja listo el escenario <NOMBRE>: compila / instala el algoritmo y prueba el
# target-runner con una instancia.
#
#   bash escenarios/<NOMBRE>/setup.sh
###############################################################################
set -eu

ESCENARIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ESCENARIO_DIR}"

# TODO: compilar o instalar el algoritmo. Ejemplos:
#   make -C src/<ALGORITMO>
#   uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt

echo "-- prueba del target-runner:"
# TODO: una instancia real y una configuracion valida
./target-runner 1 1 42 "${ESCENARIO_DIR}/instancias/<x>/<instancia>" --alpha 1.0 --ants 10 --a
echo "Listo."
