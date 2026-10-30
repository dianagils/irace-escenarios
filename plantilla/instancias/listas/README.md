# Listas de instancias

- `TRAIN.txt`: entrenamiento (irace / h-irace). Una ruta por línea, relativa a la carpeta del escenario.
- `TRAIN_SUBSETS.txt`: las mismas líneas que `TRAIN.txt`, en el mismo orden, con `:<subset>` al final. Solo la usa h-irace.
- `TEST.txt`: test (`scripts/EjecutorColaAll.py`), con instancias que no aparecen en el entrenamiento.

Ejemplo:

```
instancias/x/a1.txt          (TRAIN.txt)
instancias/x/a1.txt:1        (TRAIN_SUBSETS.txt)
```
