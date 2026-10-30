# Escenario `ILSQAP`

- **Algoritmo:** ILS-QAP, *Configurable Iterated Local Search for QAP* V0.9, de Thomas Stützle (`src/ils-qap`, en C). El código fuente no trae archivo de licencia.
- **Problema:** QAP (asignación cuadrática).
- **Instancias:** QAP de 60 facilidades, 30 de train y 30 de test, sin instancias en común. `instancias/InstancesQAP/` también trae las de 80 y 100 facilidades, por si se quieren usar.
- **Objetivo que se minimiza:** costo de la mejor solución, es decir la última línea `best <costo>` de `ilsqap`.
- **Tiempo por ejecución:** `TIME_LIMIT` segundos, 10 por defecto (`--trials 1 --time 10`).
- **Presupuesto:** los experimentos usaron 1.000 y 5.000 evaluaciones por corrida. En las carpetas de resultados aparecen como "1M" y "5M", aunque son miles y no millones. `MAX_EXPERIMENTS=1000` es el valor por defecto; para 5.000 se usa `--budget 5000`.

## Subsets (h-irace)

| subset | tipo | carpeta | train | test |
|---|---|---|---|---|
| `:1` | Euclidean Structured | `60-0.90/ES/0.90` | 15 | 15 (`testQAP_S1.txt`) |
| `:2` | tai-like random | `60rr/tailike/0.00` | 15 | 15 (`testQAP_S2.txt`) |

`trainQAP.txt` contiene las 30 instancias de train y `trainQAP_SUBSETS.txt` las mismas en el mismo orden, con la etiqueta de subset. `testQAP.txt` junta los dos tests.

`instancias/optimsQAP.txt` trae los óptimos o mejores conocidos de las instancias de test (`<id>_n60:<costo>`), para calcular el RPD en el análisis.

## Parámetros (`parameters.txt`)

| nombre | dominio | qué es |
|---|---|---|
| `localsearch` | 0, 1, 2 | 0: first improvement + don't look bits, 1: first improvement, 2: best improvement |
| `perturbation` | 0–9 | tamaño n/16, n/8, n/4, n/2, 3n/4; de 0 a 4 fijo, de 5 a 9 variable |
| `acceptance` | 0–7 | 0–3: temperatura constante (0, 0.25, 1, ∞), 4–6: restart (1n, 3n, 5n), 7: LSMC |
| `alpha` | [0.01, 1] | factor de enfriamiento geométrico |

## Preparar

```bash
bash escenarios/ILSQAP/setup.sh   # compila src/ils-qap (gcc, make) y lo prueba
```

## Correr

```bash
python3 scripts/Ejecutor.py ILSQAP irace
python3 scripts/Ejecutor.py ILSQAP h-irace                                   # 1.000 evaluaciones
python3 scripts/Ejecutor.py ILSQAP h-irace --budget 5000 --nombre h-irace_5K # 5.000 evaluaciones
bash scripts/configs.sh corridas/ILSQAP/h-irace_trainQAP
python3 scripts/EjecutorColaAll.py ILSQAP corridas/ILSQAP/h-irace_trainQAP/Subset_1 \
        --test instancias/listas/testQAP_S1.txt
python3 scripts/EjecutorColaAll.py ILSQAP corridas/ILSQAP/h-irace_trainQAP/Subset_2 \
        --test instancias/listas/testQAP_S2.txt
```
