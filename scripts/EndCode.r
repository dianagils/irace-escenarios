## Extrae las elites finales (hasta 3) de un irace.Rdata y las guarda como
##   Subset_<key>/Config<ID>.txt
## Cada Config<ID>.txt tiene 2 lineas separadas por tab:
##   ps  gs  ne  nc  xi        <- nombres de los parametros
##   25  40  0.1 0.1 0.4       <- valores
##
## Funciona con irace normal (todas las elites quedan en Subset_ALL) y con
## h-irace (allElites tiene una entrada por subset -> Subset_<key>).
## Lo invoca scripts/configs.sh dentro de cada corrida:  Rscript EndCode.r

lib_extra <- Sys.getenv("IRACE_R_LIB")
if (nzchar(lib_extra)) {
    .libPaths(c(unlist(strsplit(lib_extra, ":", fixed = TRUE)), .libPaths()))
}

suppressPackageStartupMessages(library("irace"))

logfile <- "irace.Rdata"
if (exists("read_logfile")) {
    iraceResults <- read_logfile(logfile)
} else {                       # irace < 3.5
    load(logfile)
}

# Nombres de los parametros (irace 4.x: scenario$parameters, irace 3.x: parameters)
E <- iraceResults$allConfigurations
param_names <- iraceResults$scenario$parameters$names
if (is.null(param_names)) param_names <- iraceResults$parameters$names
if (is.null(param_names)) param_names <- names(E)[!startsWith(names(E), ".")]

# Function to save configurations to a folder
save_configs <- function(ids, elites, folder_name) {
  if (!dir.exists(folder_name)) {
    dir.create(folder_name)
  }

  nElites <- min(length(ids), 3)
  selected_ids <- ids[1:nElites]
  A <- elites[elites$.ID. %in% selected_ids, ]
  # Se respeta el orden de irace (la primera es la mejor)
  A <- A[match(selected_ids, A$.ID.), ]

  for (i in seq_len(nrow(A))) {
    filename <- file.path(folder_name, paste0("Config", A$.ID.[i], ".txt"))
    valores <- as.character(unlist(A[i, param_names]))
    valores[is.na(valores)] <- "NA"
    writeLines(c(paste(param_names, collapse = "\t"),
                 paste(valores, collapse = "\t")), filename)
  }
}

# Se limpian extracciones anteriores
unlink(Sys.glob("Subset_*"), recursive = TRUE)

final_elites <- iraceResults$allElites
es_hirace <- !is.null(names(final_elites)) && length(final_elites) > 0 &&
              is.list(final_elites[[1]])

if (es_hirace) {
  # h-irace: una lista de iteraciones por subset
  for (key in names(final_elites)) {
    elites <- final_elites[[key]]
    last_iteration_ids <- elites[[length(elites)]]
    save_configs(last_iteration_ids, E, paste0("Subset_", key))
  }
} else {
  # irace normal: una lista de IDs por iteracion
  last_iteration_ids <- final_elites[[length(final_elites)]]
  save_configs(last_iteration_ids, E, "Subset_ALL")
}
