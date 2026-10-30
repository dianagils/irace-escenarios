#!/bin/bash
###############################################################################
# Extrae las elites finales (hasta 3) de cada corrida de un experimento y las
# junta en:
#   <experimento>/Subset_<k>/<corrida>/Config<ID>.txt
# (Subset_ALL con irace normal, Subset_<key> por subset con h-irace)
#
#   bash scripts/configs.sh corridas/<escenario>/<experimento>
#   ej: bash scripts/configs.sh corridas/HGS/irace_both_TRAIN
###############################################################################
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPTS}/.." && pwd)"

expDir="${1:?uso: bash scripts/configs.sh corridas/<escenario>/<experimento>}"
cd "${expDir}" || exit 1

# Se lee el irace.Rdata con el mismo tuner que lo genero (lo deja Ejecutor.py)
tuner="$(cat tuner.txt 2> /dev/null || echo irace)"
if [ -d "${REPO}/tuners/${tuner}" ]; then
    export IRACE_R_LIB="${REPO}/tuners/${tuner}"
fi
# R fuera del PATH (p.ej. micromamba)
if [ -n "${IRACE_R_PATH:-}" ] && [ -d "${IRACE_R_PATH}" ]; then
    export PATH="${IRACE_R_PATH}:${PATH}"
fi

shopt -s nullglob
rm -rf Subset_*
i=0

for foldTun in *_s_*/ ; do
    run="${foldTun%/}"
    (
        cd "${run}" || exit 1
        if [ ! -f irace.Rdata ]; then
            echo "AVISO: ${run} no tiene irace.Rdata (irace no termino?), se omite"
            exit 0
        fi
        rm -rf Subset_* Config*
        Rscript "${SCRIPTS}/EndCode.r" || { echo "ERROR: EndCode.r fallo en ${run}" >&2; exit 1; }

        # Move each subset to the new structure
        for subset in Subset_* ; do
            subsetDirName=$(basename "$subset")

            mkdir -p "../${subsetDirName}/${run}"

            configFiles=( "${subset}"/Config* )
            if [ ${#configFiles[@]} -gt 0 ]; then
                cp "${configFiles[@]}" "../${subsetDirName}/${run}/"
            else
                echo "No Config* files found in ${run}/${subset}"
            fi
        done
    )
    i=$((i+1))
done

echo "${i} corridas procesadas (tuner: ${tuner})"
for s in Subset_*/ ; do
    echo "  ${expDir%/}/${s%/}: $(ls "${s}"*/Config* 2> /dev/null | wc -l) configuraciones"
done
echo "Siguiente paso:  python3 scripts/EjecutorColaAll.py <escenario> ${expDir%/}/Subset_ALL"
