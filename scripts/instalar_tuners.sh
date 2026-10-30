#!/bin/bash
###############################################################################
# Instala irace y/o las ramas de h-irace, cada una en su propia biblioteca de R:
#   tuners/<tuner>/irace
# Todas las variantes se llaman "irace" como paquete de R, por eso no pueden
# convivir en la misma biblioteca. Ejecutor.py elige cual usar con IRACE_R_LIB.
#
#   bash scripts/instalar_tuners.sh                      # irace + h-irace
#   bash scripts/instalar_tuners.sh h-irace-AC-1 h-irace-WAC-1
#   bash scripts/instalar_tuners.sh todos                # irace + las 7 ramas
#
# Ramas de https://github.com/dianagils/h-irace:
#   h-irace, h-irace-AC-1, h-irace-AC-2, h-irace-AC-3,
#   h-irace-WAC-1, h-irace-WAC-2, h-irace-WAC-3
###############################################################################
set -eu

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUNERS="$(cd "${SCRIPTS}/.." && pwd)/tuners"
HIRACE_URL="${HIRACE_URL:-https://github.com/dianagils/h-irace}"
CRAN="${CRAN:-https://cloud.r-project.org}"
DEPS='c("matrixStats", "R6", "withr")'   # Imports del DESCRIPTION de h-irace

TODOS="irace h-irace h-irace-AC-1 h-irace-AC-2 h-irace-AC-3 h-irace-WAC-1 h-irace-WAC-2 h-irace-WAC-3"
if [ $# -eq 0 ]; then
    set -- irace h-irace
elif [ "$1" = "todos" ]; then
    set -- ${TODOS}
fi

command -v Rscript > /dev/null 2>&1 || { echo "ERROR: Rscript no esta en el PATH" >&2; exit 1; }
mkdir -p "${TUNERS}/src"

for tuner in "$@"; do
    lib="${TUNERS}/${tuner}"
    echo "== ${tuner} -> ${lib}"
    mkdir -p "${lib}"
    if [ "${tuner}" = "irace" ]; then
        Rscript -e "install.packages('irace', lib = '${lib}', repos = '${CRAN}')"
    else
        src="${TUNERS}/src/${tuner}"
        if [ -d "${src}/.git" ]; then
            git -C "${src}" pull --ff-only
        else
            git clone --depth 1 -b "${tuner}" "${HIRACE_URL}" "${src}"
        fi
        # Dependencias que falten (se instalan en la misma biblioteca)
        Rscript -e ".libPaths(c('${lib}', .libPaths())); d <- ${DEPS}; d <- d[!sapply(d, requireNamespace, quietly = TRUE)]; if (length(d)) install.packages(d, lib = '${lib}', repos = '${CRAN}')"
        R CMD INSTALL --no-test-load --library="${lib}" "${src}"
    fi
    Rscript -e ".libPaths(c('${lib}', .libPaths())); library(irace); cat('OK', '${tuner}', as.character(packageVersion('irace')), find.package('irace'), '\n')"
done
