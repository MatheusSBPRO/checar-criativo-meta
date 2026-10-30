#!/usr/bin/env bash
# Instala a checagem de criativo (política de publicidade da Meta).
#
#   ./instalar.sh            confere o ambiente. A skill já vale quando você roda `claude`
#                            (ou `codex`) dentro desta pasta.
#   ./instalar.sh --global   copia a skill, com o script e a lista de termos, para ~/.claude/skills
#                            e, se existir, para ~/.codex/skills. Vale em qualquer pasta.
#                            Uma skill com o mesmo nome vira backup (.bak-AAAAMMDD) antes de ser trocada.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")" && pwd)"
SKILL="checar-criativo"
GLOBAL=0
[ "${1:-}" = "--global" ] && GLOBAL=1

ok()    { printf '  \033[32m✓\033[0m %s\n' "$1"; }
aviso() { printf '  \033[33m!\033[0m %s\n' "$1"; }

echo "Checar criativo · instalação"
echo

echo "1. Ambiente"
if command -v python3 >/dev/null 2>&1; then
  ok "python3 $(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
else
  aviso "python3 não encontrado. Instale o Python 3.9+ (python.org)."
fi
if command -v mlx_whisper >/dev/null 2>&1 || python3 -c 'import mlx_whisper' >/dev/null 2>&1; then
  ok "whisper (mlx-whisper) para transcrever vídeo"
elif command -v whisper >/dev/null 2>&1; then
  ok "whisper (openai-whisper) para transcrever vídeo"
else
  aviso "whisper não encontrado. Para ler a fala do vídeo: pip install mlx-whisper (Mac M1+) ou pip install openai-whisper."
  aviso "Sem ele, deixe a transcrição em <nome>.txt ao lado de cada vídeo."
fi
command -v claude >/dev/null 2>&1 && ok "Claude Code instalado"
command -v codex  >/dev/null 2>&1 && ok "Codex instalado"

copiar_skill() {
  local base="$1" destino="$1/$SKILL" hoje
  hoje="$(date +%Y%m%d)"
  mkdir -p "$base"
  if [ -e "$destino" ]; then
    rm -rf "$destino.bak-$hoje"
    mv "$destino" "$destino.bak-$hoje"
  fi
  mkdir -p "$destino"
  cp "$RAIZ/.claude/skills/$SKILL/SKILL.md" "$destino/"
  cp -R "$RAIZ/scripts" "$RAIZ/referencias" "$destino/"
  ok "skill copiada para $destino"
}

if [ "$GLOBAL" = 1 ]; then
  echo
  echo "2. Instalação global"
  copiar_skill "$HOME/.claude/skills"
  if [ -d "$HOME/.codex" ]; then
    copiar_skill "$HOME/.codex/skills"
  fi
fi

echo
echo "Teste rápido:"
python3 "$RAIZ/scripts/checar_criativo.py" --texto "Ganhe R\$ 300 por dia, sem esforço" || true

echo
echo "Pronto. Abra o Claude Code ou o Codex e peça:"
echo "  \"checa esses criativos antes de subir: <pasta>, copy em <arquivo>, página <link>\""
