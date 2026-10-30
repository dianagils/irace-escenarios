# Escenarios de irace / h-irace

Escenarios de configuración automática de algoritmos, listos para correr con
[irace](https://cran.r-project.org/package=irace) y con
[h-irace](https://github.com/dianagils/h-irace) (y sus variantes AC / WAC). Incluyen también la fase de testing de las configuraciones encontradas.

Todos los escenarios comparten los mismos scripts. Para agregar uno nuevo basta con copiar `plantilla/` (ver [Agregar un escenario](#agregar-un-escenario)).

| Escenario | Algoritmo | Problema | Instancias | h-irace |
|---|---|---|---|---|
| [`HGS`](escenarios/HGS/README.md) | HGS (PyVRP 0.5.0) | VRPTW | Solomon + Homberger | subsets por tipo y por conjunto |
| [`ILSQAP`](escenarios/ILSQAP/README.md) | ILS-QAP V0.9 | QAP | QAP n=60 (ES + tai-like) | subsets por tipo de instancia |

Pendientes de agregar: MMAS-QAP, PSO-X, SPSO2011.

## Estructura

```
scripts/                     comunes a todos los escenarios
  instalar_tuners.sh         instala irace y las ramas de h-irace en tuners/
  Ejecutor.py                lanza N corridas (semillas) de irace / h-irace
  execute.R                  lo que corre R en cada corrida
  configs.sh + EndCode.r     extraen las elites finales de cada corrida
  EjecutorColaAll.py         testing: config × instancia × semilla
  comun.py, load_env.sh      utilidades
escenarios/<NOMBRE>/
  escenario.env              listas, presupuesto, semillas, paralelismo, opciones del algoritmo
  scenario.txt               opciones de irace propias del escenario
  parameters.txt             espacio de parámetros
  target-runner              evalúa una configuración (última línea = valor a minimizar)
  setup.sh                   compila / instala el algoritmo y lo prueba
  src/                       código fuente del algoritmo
  instancias/                instancias y listas (rutas relativas al escenario)
plantilla/                   escenario vacío para copiar
corridas/                    se genera al correr (no se versiona)
tuners/                      bibliotecas de R con irace / h-irace (no se versiona)
```

## Requisitos

- Linux con `bash`, `python3` (≥ 3.8, sin paquetes extra), `git` y R (≥ 3.6) con `Rscript` en el PATH.
- Lo que pida cada escenario en su `setup.sh` (por ejemplo `gcc`/`make` para ILSQAP, o `uv` para HGS).

## Instalación

```bash
git clone <url de este repo> && cd irace-escenarios

# irace (CRAN) y h-irace, cada uno en su biblioteca dentro de tuners/
bash scripts/instalar_tuners.sh                  # irace + h-irace
bash scripts/instalar_tuners.sh h-irace-AC-1     # otras ramas
bash scripts/instalar_tuners.sh todos            # irace + las 7 ramas de h-irace

# cada escenario que se vaya a usar
bash escenarios/HGS/setup.sh
bash escenarios/ILSQAP/setup.sh
```

h-irace y todas sus ramas se llaman `irace` como paquete de R, así que no pueden convivir en la misma biblioteca. Por eso cada una se instala en `tuners/<rama>/`, y los scripts eligen cuál cargar según el tuner que se pida. Si no existe `tuners/irace/`, se usa el irace que tenga instalado R.

## Flujo completo

```bash
# 1. Tuning: SEMILLAS_TUNING corridas independientes, K a la vez
python3 scripts/Ejecutor.py HGS irace
python3 scripts/Ejecutor.py HGS h-irace
python3 scripts/Ejecutor.py HGS h-irace-WAC-1 --semillas 5 --budget 2000

# 2. Extraer las elites finales (hasta 3 por corrida; por subset con h-irace)
bash scripts/configs.sh corridas/HGS/h-irace_both_TRAIN

# 3. Testing: cada config × cada instancia de test × SEMILLAS_TEST semillas
python3 scripts/EjecutorColaAll.py HGS corridas/HGS/h-irace_both_TRAIN/Subset_1
python3 scripts/EjecutorColaAll.py HGS corridas/HGS/h-irace_both_TRAIN/Subset_2 \
        --test instancias/listas/both_TEST_Homberger.txt
```

Los valores por defecto vienen de `escenarios/<NOMBRE>/escenario.env`. Se pueden cambiar con opciones (`--train`, `--subsets`, `--test`, `--semillas`, `--budget`, `--k`, `--nombre`; ver `--help`) o con variables de entorno, por ejemplo `TIME_LIMIT=2 K=8 python3 scripts/Ejecutor.py HGS irace`.

Los tres pasos se pueden relanzar si se cortan: las corridas terminadas (archivo `FIN`) y las instancias de test completas se omiten. Para dejarlos corriendo en un servidor, usar `nohup … > log 2>&1 &`, y no editar los scripts mientras corren.

### Qué se genera

```
corridas/HGS/h-irace_both_TRAIN/                 <tuner>_<lista train>  (o --nombre)
├── tuner.txt
├── h-irace_both_TRAIN_s_1/                      una corrida por semilla
│   ├── scenario.txt  instances.txt  subsets.txt execute.R
│   ├── Salida                                   log de irace
│   ├── irace.Rdata
│   └── FIN                                      terminó bien
├── Subset_1/h-irace_both_TRAIN_s_1/Config<ID>.txt      (configs.sh)
└── Test_Subset_1_both_TEST/                            (EjecutorColaAll.py)
    ├── h-irace_both_TRAIN_s_1_Config<ID>/
    │   └── <instancia>.txt                      un valor por línea, semillas 1..N en orden
    └── errors.log                               solo si algo falló
```

- **Subsets:** con irace se crea un único `Subset_ALL`. Con h-irace hay un `Subset_<k>` por subset, con las elites finales de ese subset.
- **`Config<ID>.txt`:** tiene dos líneas separadas por tabulador: los nombres de los parámetros y sus valores (`NA` = parámetro inactivo).
- **Instancias con fallos:** si alguna semilla falla, el archivo de esa instancia no se escribe y el motivo queda en `errors.log`.

## Agregar un escenario

1. `cp -r plantilla escenarios/<NOMBRE>`
2. **Código del algoritmo** en `src/`, solo fuentes, sin binarios ni `.o`. En `setup.sh` se compila o instala.
3. **`parameters.txt`** en el formato de irace. El switch se pega al valor igual que lo hace irace: `"--alpha "` + `1.5`, o `"--"` + `mmas`.
4. **`target-runner`**: recibe `<config_id> <instance_id> <seed> <instance> [bound] <parámetros…>` y debe imprimir en la **última línea** un único número, el valor a **minimizar**. Si falla, debe salir con código ≠ 0. Construye las rutas a partir de `ESCENARIO_DIR` y lee sus opciones de `escenario.env`.
5. **Instancias** en `instancias/` y listas en `instancias/listas/`, con rutas **relativas a la carpeta del escenario**:
   - `TRAIN`: una instancia por línea.
   - `TRAIN_SUBSETS` (solo h-irace): las **mismas líneas, en el mismo orden**, con `:<subset>` al final. h-irace asocia cada línea con la instancia de entrenamiento de la misma posición; `Ejecutor.py` lo verifica.
   - `TEST`: instancias que no aparecen en el entrenamiento.
6. **`escenario.env`** con las listas, el presupuesto y las semillas. **`scenario.txt`** solo con las opciones de irace propias del escenario (`digits`, `deterministic`, `configurationsFile`, …). Las rutas, la semilla y el presupuesto los agrega `Ejecutor.py`.
7. **Prueba:** `bash escenarios/<NOMBRE>/setup.sh` y después una corrida corta, por ejemplo `python3 scripts/Ejecutor.py <NOMBRE> irace --semillas 1 --budget 200`.
8. **README.md** del escenario: origen y licencia del algoritmo y de las instancias, qué se minimiza, cómo se definieron los subsets.

## Licencias

Cada algoritmo mantiene su licencia original (ver el README de cada escenario). irace y h-irace son GPL-2.0.
