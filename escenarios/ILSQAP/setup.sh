#!/bin/bash
###############################################################################
# Compila ILS-QAP y prueba el target-runner con una instancia.
#
#   bash escenarios/ILSQAP/setup.sh
###############################################################################
set -eu

ESCENARIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ESCENARIO_DIR}"

make -C src/ils-qap

echo "-- prueba del target-runner (2 s):"
INST="$(head -n 1 instancias/listas/trainQAP.txt)"
cd "$(mktemp -d)"
TIME_LIMIT=2 "${ESCENARIO_DIR}/target-runner" 1 1 42 "${ESCENARIO_DIR}/${INST}" \
    --localsearch 2 --perturbation 2 --acceptance 7 --alpha 0.83
echo "Listo."
