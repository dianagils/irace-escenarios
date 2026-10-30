# Testea las configuraciones encontradas por irace / h-irace sobre las
# instancias de test, con varias semillas, usando el target-runner del escenario.
# Las configuraciones se extraen antes con:  bash scripts/configs.sh <experimento>
#
#   python3 scripts/EjecutorColaAll.py <escenario> <carpeta Subset_*> [opciones]
#
#   python3 scripts/EjecutorColaAll.py HGS corridas/HGS/irace_both_TRAIN/Subset_ALL
#   python3 scripts/EjecutorColaAll.py HGS corridas/HGS/h-irace_both_TRAIN/Subset_1 \
#                                       --test instancias/listas/both_TEST_solomon.txt
#
#   <Subset>/<corrida>/Config<ID>.txt
#     -> <experimento>/Test_<Subset>_<lista test>/<corrida>_Config<ID>/<instancia>.txt
#
# Cada <instancia>.txt tiene un costo por linea (una linea por semilla, en orden).
# Si se corta, se puede volver a lanzar: se omiten las instancias ya terminadas.

import argparse
import concurrent.futures
import os
import re
import subprocess
import threading

import comun

parser = argparse.ArgumentParser(description="Testea las configuraciones finales de irace / h-irace")
parser.add_argument("escenario", help="carpeta dentro de escenarios/ (ej: HGS)")
parser.add_argument("configs", help="carpeta Subset_* creada por scripts/configs.sh")
parser.add_argument("--test", help="lista de instancias de test (def: TEST de escenario.env)")
parser.add_argument("--semillas", type=int, help="semillas 1..N por instancia (def: SEMILLAS_TEST)")
parser.add_argument("--k", type=int, help="ejecuciones simultaneas (def: K)")
args = parser.parse_args()

esc_dir, cfg = comun.escenario(args.escenario)
ConfigsDir = os.path.abspath(args.configs)
instancesFile = args.test or cfg.get("TEST") or comun.error("falta --test o TEST en escenario.env")
totalSeeds = args.semillas or int(cfg.get("SEMILLAS_TEST", "20"))
K = args.k or int(cfg.get("K", "20"))   # Cantidad de ejecuciones simultaneas

if not os.path.isdir(ConfigsDir):
    comun.error("no existe " + ConfigsDir + " (corre antes scripts/configs.sh)")

targetRunner = os.path.join(esc_dir, 'target-runner')
paramFile = os.path.join(esc_dir, 'parameters.txt')
testDir = os.path.join(os.path.dirname(ConfigsDir), 'Test_{}_{}'.format(
    os.path.basename(ConfigsDir), comun.nombre_lista(instancesFile)))
errorLog = os.path.join(testDir, 'errors.log')
Seeds = list(range(1, totalSeeds + 1))
entorno = comun.entorno(esc_dir, cfg)

lock = threading.Lock()
resultados = {}   # (pathToRun, iName) -> {seed: cost}
fallidos = set()  # (pathToRun, iName) con alguna ejecucion fallida


def error(message):
    print("error: " + message)
    with lock:
        with open(errorLog, 'a') as f:
            f.write(message + '\n')


def readSwitches(file):
    # nombre -> switch, desde parameters.txt de irace:  ps  "-ps "  o  (...)
    switches = {}
    with open(file) as fh:
        for line in fh:
            if line.strip().startswith('['):   # [forbidden], [global]: fin de los parametros
                break
            m = re.match(r'^\s*([^#\s]\S*)\s+"([^"]*)"', line)
            if m:
                switches[m.group(1)] = m.group(2)
    return switches


def readParams(file):
    # Config<ID>.txt: linea 1 nombres, linea 2 valores (separados por tab)
    with open(file) as paramFile:
        lines = [line.rstrip('\n').split('\t') for line in paramFile if line.strip()]
    return dict(zip(lines[0], lines[1]))


def instanceName(inst):
    return os.path.splitext(os.path.basename(inst))[0]


def formatParam(params):
    # Igual que irace: switch + valor pegados ("--" + "mmas" -> --mmas,
    # "-ps " + "25" -> -ps 25). Los parametros inactivos (NA) no se pasan.
    args = []
    for name, value in params.items():
        if value == 'NA':
            continue
        args += (switches[name] + value).split()
    return args


def ejecutar(Mat):
    pathToRun, configID, instID, Inst, seed, params = Mat
    iName = instanceName(Inst)
    key = (pathToRun, iName)

    cost = None
    try:
        comando = [targetRunner, configID, str(instID), str(seed), Inst] + formatParam(params)
        r = subprocess.run(comando, cwd=pathToRun, env=entorno, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            try:
                cost = r.stdout.strip().splitlines()[-1].split()[0]
                float(cost)
            except (IndexError, ValueError):
                cost = None
        if cost is None:
            error("{} {} seed {}: codigo {}: {} {}".format(
                pathToRun, iName, seed, r.returncode, r.stdout.strip(), r.stderr.strip()))
    except Exception as e:
        error("{} {} seed {}: {}: {}".format(pathToRun, iName, seed, type(e).__name__, e))

    with lock:
        if cost is None:
            fallidos.add(key)
        resultados.setdefault(key, {})[seed] = cost
        terminado = len(resultados[key]) == len(Seeds)
    # Cuando terminan todas las semillas se escribe el archivo en orden de semilla
    if terminado:
        if key in fallidos:
            error("{} {}: no se escribe (hay semillas fallidas)".format(pathToRun, iName))
        else:
            with open(os.path.join(pathToRun, iName + '.txt'), 'w') as out:
                for s in Seeds:
                    out.write(resultados[key][s] + '\n')
    return pathToRun


def completo(path):
    if not os.path.isfile(path):
        return False
    with open(path) as fh:
        return len([l for l in fh if l.strip()]) == len(Seeds)


switches = readSwitches(paramFile)
Instances = [i for i, _ in comun.leer_lista(esc_dir, instancesFile)]
os.makedirs(testDir, exist_ok=True)

MatPat = []
dirs = sorted(d for d in os.listdir(ConfigsDir) if os.path.isdir(os.path.join(ConfigsDir, d)))
for d in dirs:
    confiles = sorted(f for f in os.listdir(os.path.join(ConfigsDir, d)) if f.startswith('Config'))
    for c in confiles:
        pFile = os.path.join(ConfigsDir, d, c)
        params = readParams(pFile)
        desconocidos = [p for p in params if p not in switches]
        if desconocidos:
            comun.error("{}: parametros que no estan en {}: {}".format(pFile, paramFile, desconocidos))
        configID = os.path.splitext(c)[0][len('Config'):]

        dn = os.path.join(testDir, d + '_' + os.path.splitext(c)[0])
        os.makedirs(dn, exist_ok=True)

        for instID, i in enumerate(Instances, start=1):
            if completo(os.path.join(dn, instanceName(i) + '.txt')):
                continue
            for s in Seeds:
                MatPat.append((dn, configID, instID, i, s, params))

#Cantidad total de procesos
N = len(MatPat)
print("{} instancias en {}, {} semillas, {} parametros en {}".format(
    len(Instances), instancesFile, len(Seeds), len(switches), paramFile))
print("{} ejecuciones, {} simultaneas".format(N, K))
if N == 0:
    print("AVISO: no hay nada que ejecutar (sin configuraciones o todo ya terminado)")

with concurrent.futures.ThreadPoolExecutor(max_workers=K) as executor:
    futures = [executor.submit(ejecutar, m) for m in MatPat]
    for n, future in enumerate(concurrent.futures.as_completed(futures), start=1):
        print("Termino {} ({}/{})".format(os.path.basename(future.result()), n, N))

print("Resultados en " + testDir + ("" if not fallidos else " (hay errores, ver " + errorLog + ")"))
