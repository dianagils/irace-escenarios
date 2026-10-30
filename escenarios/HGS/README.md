# Escenario `HGS`

- **Algoritmo:** HGS (Hybrid Genetic Search) de [PyVRP](https://github.com/PyVRP/PyVRP) 0.5.0, que se instala con pip (licencia MIT). `src/SolveVRP.py` envuelve el `GeneticAlgorithm` de PyVRP y expone los parámetros de población.
- **Problema:** VRPTW (ruteo de vehículos con ventanas de tiempo).
- **Instancias:** Solomon (56) y Homberger (300), en formato Solomon.
- **Objetivo que se minimiza:** costo de la mejor solución (`res.cost()`). Si es infactible se devuelve `INFEASIBLE_COST`.
- **Tiempo por ejecución:** `TIME_LIMIT` segundos (10 por defecto).

## Parámetros (`parameters.txt`)

| nombre | switch | dominio | qué es |
|---|---|---|---|
| `ps` | `-ps` | 5, 15, 25, 35, 45 | tamaño mínimo de la población (μ) |
| `gs` | `-gs` | 10, 20, 40, 70, 100 | tamaño de la generación (λ) |
| `ne` | `-ne` | 0.1 … 0.8 | elite, como fracción de μ |
| `nc` | `-nc` | 0.1 … 0.8 | vecinos cercanos para la diversidad, como fracción de μ |
| `xi` | `-xi` | 0.1 … 0.8 | diversidad de referencia (±0.1) |

Los niveles son discretos (los mismos que en ParamILS). En `parameters.txt` hay una variante continua comentada.

## Listas de instancias (`instancias/listas/`)

Split 50/50 con semilla 42; detalle por instancia en `split_manifest.csv`.

| Archivo | Uso |
|---|---|
| `<conj>_TRAIN.txt` / `<conj>_TEST.txt` | train y test por conjunto (`solomon`, `Homberger`) |
| `<conj>_TRAIN_SUBSETS.txt` | igual que `_TRAIN`, con subsets por tipo: `:1` Random (R1, R2), `:2` Clustered (C1, C2), `:3` Random-Clustered (RC1, RC2) |
| `<conj>_TEST_{R,C,RC}.txt` | test por tipo |
| `both_TRAIN.txt` / `both_TEST.txt` | Solomon + Homberger, 28 + 28 de cada uno |
| `both_TRAIN_SUBSETS.txt` | subsets por conjunto: `:1` Solomon, `:2` Homberger |
| `both_TEST_{solomon,Homberger}.txt` | test por conjunto |
| `<conj>_ALL.txt`, `<conj>_<familia>.txt` | todas las instancias / por familia |

Por defecto (`escenario.env`) se usa `both_TRAIN`, `both_TRAIN_SUBSETS` y `both_TEST`.

## Preparar

```bash
bash escenarios/HGS/setup.sh     # crea escenarios/HGS/.venv con pyvrp 0.5.0 (usa uv)
```

## Correr

```bash
python3 scripts/Ejecutor.py HGS irace
python3 scripts/Ejecutor.py HGS h-irace
bash scripts/configs.sh corridas/HGS/h-irace_both_TRAIN
python3 scripts/EjecutorColaAll.py HGS corridas/HGS/h-irace_both_TRAIN/Subset_1 \
        --test instancias/listas/both_TEST_solomon.txt
```
