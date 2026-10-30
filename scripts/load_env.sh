# Carga un archivo KEY=VALUE (escenario.env) SIN pisar variables que ya vengan
# del entorno. Asi se puede hacer p.ej.:  TIME_LIMIT=2 ./target-runner ...
# Acepta comentarios de linea completa y al final ("KEY=valor   # comentario").
load_env() {
    local file="$1" key value
    [ -f "${file}" ] || return 0
    while IFS= read -r line || [ -n "${line}" ]; do
        line="${line%$'\r'}"
        case "${line}" in ''|\#*) continue ;; esac
        key="${line%%=*}"
        value="${line#*=}"
        value="${value%%[[:space:]]#*}"
        value="${value%"${value##*[![:space:]]}"}"
        value="${value#\"}"; value="${value%\"}"
        key="$(printf '%s' "${key}" | tr -d '[:space:]')"
        case "${key}" in *[!A-Za-z0-9_]*|'') continue ;; esac
        if [ -z "$(eval "printf '%s' \"\${${key}:-}\"")" ]; then
            export "${key}=${value}"
        fi
    done < "${file}"
}
