# Lanza varias corridas de irace / h-irace (una por semilla) sobre un escenario,
# con K corridas en paralelo.
#
#   python3 scripts/Ejecutor.py <escenario> <tuner> [opciones]
#
#   python3 scripts/Ejecutor.py HGS irace
#   python3 scripts/Ejecutor.py HGS h-irace --train instancias/listas/both_TRAIN.txt \
#                                         --subsets instancias/listas/both_TRAIN_SUBSETS.txt
#   python3 scripts/Ejecutor.py HGS h-irace-AC-1 --semillas 5 --budget 2000
#
# <tuner> es "irace" o el nombre de una rama de h-irace (h-irace, h-irace-AC-1,
# ..., h-irace-WAC-3) instalada con scripts/instalar_tuners.sh.
#
# Cada corrida queda en
#   corridas/<escenario>/<nombre>/<nombre>_s_<semilla>/
# con nombre = <tuner>_<lista de train> (o --nombre). Ahi se generan
# scenario.txt, instances.txt (y subsets.txt para h-irace) con rutas absolutas,
# y se ejecuta  R < execute.R --no-save > Salida
# Las corridas que ya tienen irace.Rdata terminado se omiten.

import argparse
import concurrent.futures
import os
import shutil
import subprocess

import comun

parser = argparse.ArgumentParser(description="Lanza corridas de irace / h-irace sobre un escenario")
parser.add_argument("escenario", help="carpeta dentro de escenarios/ (ej: HGS)")
parser.add_argument("tuner", help="irace, h-irace, h-irace-AC-1, ... (ver scripts/instalar_tuners.sh)")
parser.add_argument("--train", help="lista de instancias de entrenamiento (def: TRAIN de escenario.env)")
parser.add_argument("--subsets", help="lista con etiquetas <instancia>:<subset> para h-irace (def: TRAIN_SUBSETS)")
parser.add_argument("--semillas", type=int, help="corre las semillas 1..N (def: SEMILLAS_TUNING)")
parser.add_argument("--budget", help="maxExperiments de cada corrida (def: MAX_EXPERIMENTS)")
parser.add_argument("--k", type=int, help="corridas simultaneas (def: K)")
parser.add_argument("--nombre", help="nombre de la carpeta de este experimento")
args = parser.parse_args()

esc_dir, cfg = comun.escenario(args.escenario)
es_hirace = args.tuner != 'irace'

train = args.train or cfg.get("TRAIN") or comun.error("falta --train o TRAIN en escenario.env")
subsets = args.subsets or cfg.get("TRAIN_SUBSETS")
NumSeeds = args.semillas or int(cfg.get("SEMILLAS_TUNING", "20"))
maxExperiments = args.budget or cfg.get("MAX_EXPERIMENTS")
parallel = cfg.get("IRACE_PARALLEL", "1")
K = args.k or int(cfg.get("K", "20"))
nombre = args.nombre or "{}_{}".format(args.tuner, comun.nombre_lista(train))

instancias = comun.leer_lista(esc_dir, train)
if es_hirace:
    if not subsets:
        comun.error("h-irace necesita --subsets o TRAIN_SUBSETS en escenario.env")
    etiquetadas = comun.leer_lista(esc_dir, subsets)
    # h-irace asocia cada linea del archivo de subsets con la instancia de
    # entrenamiento de la MISMA posicion: ambas listas deben coincidir.
    if [i for i, _ in etiquetadas] != [i for i, _ in instancias]:
        comun.error("{} y {} deben tener las mismas instancias en el mismo orden".format(train, subsets))
    if any(s is None for _, s in etiquetadas):
        comun.error("{}: todas las lineas deben terminar en :<subset>".format(subsets))

entorno = comun.entorno(esc_dir, cfg, args.tuner)
comun.comprobar_irace(entorno)

expDir = os.path.join(comun.CORRIDAS, args.escenario, nombre)
os.makedirs(expDir, exist_ok=True)
# configs.sh usa este archivo para leer los irace.Rdata con el mismo tuner
with open(os.path.join(expDir, 'tuner.txt'), 'w') as fh:
    fh.write(args.tuner + '\n')


def preparar(pathToRun, seed):
    os.makedirs(pathToRun, exist_ok=True)
    shutil.copy2(os.path.join(comun.SCRIPTS, 'execute.R'), pathToRun)
    with open(os.path.join(pathToRun, 'instances.txt'), 'w') as fh:
        fh.writelines(i + '\n' for i, _ in instancias)
    shutil.copy2(os.path.join(esc_dir, 'scenario.txt'), os.path.join(pathToRun, 'scenario.txt'))
    # Lo que va al final de scenario.txt pisa lo que defina el escenario
    lineas = [
        '',
        '## --- agregado por scripts/Ejecutor.py ---',
        'parameterFile = "{}"'.format(os.path.join(esc_dir, 'parameters.txt')),
        'targetRunner = "{}"'.format(os.path.join(esc_dir, 'target-runner')),
        'execDir = "."',
        'logFile = "./irace.Rdata"',
        'trainInstancesDir = ""',
        'trainInstancesFile = "./instances.txt"',
        'seed = {}'.format(seed),
        'parallel = {}'.format(parallel),
    ]
    if maxExperiments:
        lineas.append('maxExperiments = {}'.format(maxExperiments))
    if es_hirace:
        with open(os.path.join(pathToRun, 'subsets.txt'), 'w') as fh:
            fh.writelines('{}:{}\n'.format(i, s) for i, s in etiquetadas)
        lineas.append('instanceSubsetsFile = "./subsets.txt"')
    with open(os.path.join(pathToRun, 'scenario.txt'), 'a') as fh:
        fh.write('\n'.join(lineas) + '\n')


def ejecutar(pathToRun):
    with open(os.path.join(pathToRun, 'Salida'), 'w') as salida:
        subprocess.run('R --no-save < execute.R', shell=True, cwd=pathToRun, env=entorno,
                       stdout=salida, stderr=subprocess.STDOUT)
    return pathToRun


def terminada(pathToRun):
    # execute.R escribe FIN al terminar bien
    return os.path.isfile(os.path.join(pathToRun, 'FIN'))


Paths = []
for seed in range(1, NumSeeds + 1):
    pathdirToExec = os.path.join(expDir, '{}_s_{}'.format(nombre, seed))
    if terminada(pathdirToExec):
        print("Ya termino " + pathdirToExec + ", se omite")
        continue
    preparar(pathdirToExec, seed)
    Paths.append(pathdirToExec)

#Cantidad total de procesos
N = len(Paths)
print("{}: {} corridas de {} ({} instancias de {}), {} simultaneas".format(
    args.escenario, N, args.tuner, len(instancias), train, K))

with concurrent.futures.ThreadPoolExecutor(max_workers=K) as executor:
    futures = [executor.submit(ejecutar, p) for p in Paths]
    for n, future in enumerate(concurrent.futures.as_completed(futures), start=1):
        p = future.result()
        estado = "OK" if terminada(p) else "FALLO (revisa {}/Salida)".format(p)
        print("Termino {} ({}/{}): {}".format(os.path.basename(p), n, N, estado))

fallidas = [p for p in Paths if not terminada(p)]
print("Corridas en " + expDir)
if fallidas:
    print("{} corridas fallaron; se pueden relanzar con el mismo comando".format(len(fallidas)))
else:
    print("Siguiente paso:  bash scripts/configs.sh " + os.path.relpath(expDir, comun.REPO))
