# Perfil Go del workflow SDD + IA (ADR-0002). BORRADOR v0.11.
#
# Uso: añade al final de ~/.bashrc la línea
#   source ~/proyectos/sdd-workflow/entorno/claude-go.sh
# y abre la sesión con `claude-go` (modelo ligero) o `claude-go minimax-m3`.
#
# - Solo sirven los modelos de OpenCode Go con API compatible con Anthropic
#   (en su web, paquete `@ai-sdk/anthropic`): hoy qwen3.8-flash, qwen3.8-max,
#   qwen3.7-plus, minimax-m3 y claude-haiku-5-5. DeepSeek V4.1 Flash NO lo es.
# - Nunca uses un modelo "Contributor".
# - Remote Control no funciona en esta sesión (exige la API de Anthropic):
#   el perfil Go se usa solo desde el PC.
# - La clave vive en ~/.config/opencode-go/api-key (chmod 600). El sandbox
#   y las reglas de permisos impiden que el agente la lea.
# - PENDIENTE DE VERIFICAR en la fase C: la URL base. La documentación de Go
#   publica el endpoint https://opencode.ai/inference/go/anthropic/v1/messages;
#   una guía de junio de 2026 usaba https://opencode.ai/zen/go/.

claude-go() {
  local modelo="qwen3.8-flash"
  if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then modelo="$1"; shift; fi
  local clave_fichero="$HOME/.config/opencode-go/api-key"
  if [ ! -r "$clave_fichero" ]; then
    echo "Falta $clave_fichero (crea la clave en https://opencode.ai/console)." >&2
    return 1
  fi
  ANTHROPIC_BASE_URL="https://opencode.ai/inference/go/anthropic" \
  ANTHROPIC_AUTH_TOKEN="" \
  ANTHROPIC_API_KEY="$(cat "$clave_fichero")" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="$modelo" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="$modelo" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="$modelo" \
  CLAUDE_CODE_SUBAGENT_MODEL="$modelo" \
  claude "$@"
}
