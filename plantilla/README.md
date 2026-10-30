# Escenario `<NOMBRE>`

- **Algoritmo:** `<algoritmo>`, versión y autor. Origen: `<url>`. Licencia: `<licencia>`.
- **Problema:** `<problema>`.
- **Instancias:** `<conjunto>`, origen: `<url/paper>`. Train: `<n>`, test: `<n>`.
- **Subsets para h-irace:** cómo se definen los subsets (`:1`, `:2`, …).
- **Objetivo que se minimiza:** qué número imprime el target-runner (costo, RPD, …).
- **Presupuesto y tiempo:** `MAX_EXPERIMENTS`, tiempo por ejecución, etc.

## Preparar

```bash
bash escenarios/<NOMBRE>/setup.sh
```

## Correr

```bash
python3 scripts/Ejecutor.py <NOMBRE> irace
bash scripts/configs.sh corridas/<NOMBRE>/irace_TRAIN
python3 scripts/EjecutorColaAll.py <NOMBRE> corridas/<NOMBRE>/irace_TRAIN/Subset_ALL
```

## Notas

Detalles que alguien necesite para reproducir los experimentos.
