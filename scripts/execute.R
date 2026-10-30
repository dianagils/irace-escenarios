## Corre irace (o h-irace) con el scenario.txt de la carpeta actual.
## Lo copia y lo invoca scripts/Ejecutor.py:  R --no-save < execute.R > Salida
##   - IRACE_R_LIB: biblioteca de R donde esta el tuner (tuners/<tuner>), para
##     elegir entre irace y las ramas de h-irace (todas se llaman "irace").
##   - al terminar bien escribe el archivo FIN.

lib_extra <- Sys.getenv("IRACE_R_LIB")
if (nzchar(lib_extra)) {
    .libPaths(c(unlist(strsplit(lib_extra, ":", fixed = TRUE)), .libPaths()))
}

library("irace")
cat("# irace cargado desde", find.package("irace"), "\n")
scenario <- readScenario(filename = "scenario.txt", scenario = defaultScenario())
irace(scenario = scenario)

writeLines(format(Sys.time()), "FIN")
