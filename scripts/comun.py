# Funciones compartidas por Ejecutor.py y EjecutorColaAll.py.
#
# Convenciones del repo (ver README.md):
#   escenarios/<NOMBRE>/escenario.env   configuracion del escenario (KEY=VALUE)
#   escenarios/<NOMBRE>/scenario.txt    opciones de irace propias del escenario
#   escenarios/<NOMBRE>/parameters.txt  espacio de parametros
#   escenarios/<NOMBRE>/target-runner   evalua una configuracion (ultima linea = costo)
#   escenarios/<NOMBRE>/instancias/     instancias y listas (rutas RELATIVAS al escenario)
#   tuners/<TUNER>/                     biblioteca de R con irace o una rama de h-irace
#   corridas/                           todo lo que se genera al correr (no se versiona)

import os
import re
import stat
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO, 'scripts')
CORRIDAS = os.path.join(REPO, 'corridas')
TUNERS = os.path.join(REPO, 'tuners')


def error(message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(1)


def cargar_env(path):
    # KEY=VALUE por linea, # para comentarios. Las variables que ya vienen del
    # entorno tienen prioridad (igual que load_env.sh), asi se puede hacer
    #   TIME_LIMIT=2 python3 scripts/Ejecutor.py HGS irace
    valores = {}
    if not os.path.isfile(path):
        return valores
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.split(' #')[0].strip().strip('"').strip("'")
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
                valores[key] = os.environ.get(key, value)
    return valores


def escenario(nombre):
    # Devuelve (carpeta del escenario, configuracion de escenario.env)
    esc_dir = os.path.join(REPO, 'escenarios', nombre)
    if not os.path.isdir(esc_dir):
        disponibles = sorted(os.listdir(os.path.join(REPO, 'escenarios')))
        error("no existe el escenario '{}'. Disponibles: {}".format(nombre, ', '.join(disponibles)))
    for f in ('scenario.txt', 'parameters.txt', 'target-runner'):
        if not os.path.isfile(os.path.join(esc_dir, f)):
            error("falta {} en {}".format(f, esc_dir))
    # irace y Python ejecutan el target-runner directamente: debe ser ejecutable
    tr = os.path.join(esc_dir, 'target-runner')
    os.chmod(tr, os.stat(tr).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return esc_dir, cargar_env(os.path.join(esc_dir, 'escenario.env'))


def ruta(esc_dir, path):
    # Rutas de listas e instancias: relativas a la carpeta del escenario
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(esc_dir, path))


def leer_lista(esc_dir, lista):
    # Lineas "<instancia>" o "<instancia>:<subset>" -> [(ruta absoluta, subset o None)]
    out = []
    with open(ruta(esc_dir, lista)) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            inst, subset = line, None
            m = re.match(r'^(.*?)\s*:\s*(\d+)$', line)
            if m:
                inst, subset = m.group(1), m.group(2)
            inst = ruta(esc_dir, inst)
            if not os.path.isfile(inst):
                error("{}: no existe la instancia {}".format(lista, inst))
            out.append((inst, subset))
    if not out:
        error("la lista {} esta vacia".format(lista))
    return out


def nombre_lista(lista):
    return os.path.splitext(os.path.basename(lista))[0]


def entorno(esc_dir, cfg, tuner=None):
    # Entorno que ven R/irace y el target-runner
    env = os.environ.copy()
    env.update(cfg)
    env["ESCENARIO_DIR"] = esc_dir
    if tuner is not None:
        lib = os.path.join(TUNERS, tuner)
        if os.path.isdir(lib):
            env["IRACE_R_LIB"] = lib
        elif tuner != 'irace':
            error("no esta instalado el tuner '{}' (falta {}). Instalalo con:\n"
                  "    bash scripts/instalar_tuners.sh {}".format(tuner, lib, tuner))
    if env.get("IRACE_R_PATH") and os.path.isdir(env["IRACE_R_PATH"]):
        env["PATH"] = env["IRACE_R_PATH"] + os.pathsep + env.get("PATH", "")
    # Ni R ni los algoritmos son multihilo, pero BLAS/numpy crean por defecto
    # un pool del tamano del nro de cores: con K corridas a la vez son cientos
    # de hebras ociosas. Se limita a 1 (se puede sobreescribir).
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env.setdefault(v, "1")
    return env


def comprobar_irace(env):
    # Verifica que R encuentre el paquete irace ANTES de crear las carpetas
    prueba = ('lib <- Sys.getenv("IRACE_R_LIB"); '
              'if (nzchar(lib)) .libPaths(c(unlist(strsplit(lib, ":", fixed=TRUE)), .libPaths())); '
              'if (!requireNamespace("irace", quietly=TRUE)) { cat("NO-IRACE\\n"); quit(status=1) }; '
              'cat("IRACE-OK", as.character(packageVersion("irace")), find.package("irace"), "\\n")')
    try:
        r = subprocess.run(["R", "--slave", "--no-save", "--no-restore", "-e", prueba],
                           env=env, capture_output=True, text=True)
    except FileNotFoundError:
        error("no se encontro R en el PATH (o define IRACE_R_PATH en escenario.env)")
    if r.returncode != 0 or "IRACE-OK" not in r.stdout:
        error("R no encuentra el paquete 'irace'.\n" + r.stdout + r.stderr +
              "\nInstalalo con:  bash scripts/instalar_tuners.sh irace")
    print("irace encontrado: " + r.stdout.strip())
