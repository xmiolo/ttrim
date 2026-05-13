#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  install.sh — instala o token-trim na máquina
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${TOKEN_TRIM_HOME:-$HOME/.token-trim}"
BIN_DIR="$HOME/.local/bin"
SHELL_RC=""

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC}  $*"; }
info() { echo -e "  ${CYAN}→${NC}  $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $*"; }
err()  { echo -e "  ${RED}✗${NC}  $*"; exit 1; }

echo ""
echo -e "${BOLD}  token-trim installer${NC}"
echo "  ────────────────────────────────────"
echo ""

# ── pré-requisitos ────────────────────────────────────────────────────────────

info "verificando pré-requisitos..."

command -v python3 &>/dev/null || err "python3 não encontrado."
ok "python3: $(python3 --version)"

command -v pip3 &>/dev/null || command -v pip &>/dev/null || warn "pip não encontrado — instale manualmente: pip install git+https://github.com/toon-format/toon-python.git"

command -v claude &>/dev/null \
  && ok "claude: $(claude --version 2>/dev/null | head -1 || echo 'ok')" \
  || warn "claude CLI não encontrado. Instale o Claude Code antes de usar o 'ttrim'."

# ── detettrima shell ─────────────────────────────────────────────────────────────

if [[ "$SHELL" == */zsh ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    SHELL_RC="${HOME}/.bash_profile"
    [[ -f "$HOME/.bashrc" && ! -f "$HOME/.bash_profile" ]] && SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi
info "shell rc: $SHELL_RC"

# ── instala lib oficial toon-python ──────────────────────────────────────────

info "instalando lib oficial toon-python..."
PIP_CMD=""
command -v pip3 &>/dev/null && PIP_CMD="pip3"
command -v pip  &>/dev/null && PIP_CMD="pip"

if [[ -n "$PIP_CMD" ]]; then
    DEPS="git+https://github.com/toon-format/toon-python.git tiktoken"
    if $PIP_CMD install $DEPS --break-system-packages -q 2>/dev/null; then
        ok "toon-python + tiktoken instalados"
    elif python3 -m pip install $DEPS --break-system-packages -q 2>/dev/null; then
        ok "toon-python + tiktoken instalados (via python3 -m pip)"
    else
        warn "falha ao instalar dependências — rode manualmente:"
        warn "  pip install git+https://github.com/toon-format/toon-python.git tiktoken --break-system-packages"
    fi
else
    warn "pip não encontrado — instale manualmente: pip install git+https://github.com/toon-format/toon-python.git"
fi

# ── copia arquivos ────────────────────────────────────────────────────────────

info "instalando em $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR/src"
cp -r "$REPO_DIR/src/"* "$INSTALL_DIR/src/"
ok "conversor copiado"

mkdir -p "$BIN_DIR"
cp "$REPO_DIR/bin/ttrim" "$BIN_DIR/ttrim"
chmod +x "$BIN_DIR/ttrim"
ok "binário instalado em $BIN_DIR/ttrim"

# ── variáveis de ambiente e PATH ──────────────────────────────────────────────

ENV_LINE="export TOKEN_TRIM_HOME=\"$INSTALL_DIR\""
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

grep -q 'TOKEN_TRIM_HOME' "$SHELL_RC" 2>/dev/null || {
    echo "" >> "$SHELL_RC"
    echo "# token-trim" >> "$SHELL_RC"
    echo "$ENV_LINE" >> "$SHELL_RC"
    ok "TOKEN_TRIM_HOME adicionado ao $SHELL_RC"
}

grep -q '\.local/bin' "$SHELL_RC" 2>/dev/null || {
    echo "$PATH_LINE" >> "$SHELL_RC"
    ok "\$HOME/.local/bin adicionado ao PATH"
}

# ── slash commands do Claude Code ─────────────────────────────────────────────

CLAUDE_COMMANDS_DIR="$HOME/.claude/commands"
if [[ -d "$HOME/.claude" ]]; then
    mkdir -p "$CLAUDE_COMMANDS_DIR"
    cp "$REPO_DIR/claude-commands/"*.md "$CLAUDE_COMMANDS_DIR/" 2>/dev/null \
      && ok "slash commands instalados em $CLAUDE_COMMANDS_DIR" \
      || true
fi

# ── hooks do Claude Code ──────────────────────────────────────────────────────

info "configurando hooks do Claude Code..."

chmod +x "$REPO_DIR/.claude/hooks/compress_md.py" 2>/dev/null || true
chmod +x "$REPO_DIR/.claude/hooks/detect_flags.sh" 2>/dev/null || true
ok "hooks configurados (.claude/settings.json)"

# jq melhora a detecção de flags — instala se ausente
if ! command -v jq &>/dev/null; then
    warn "jq não encontrado — detecção de flags usará fallback Python (funcional, mas mais lento)"
    warn "  instale com: sudo apt install jq  ou  brew install jq"
else
    ok "jq: $(jq --version)"
fi

# ── testa a instalação ────────────────────────────────────────────────────────

info "testando conversor..."

# Teste 1: compressão de prompt
RESULT=$(python3 "$INSTALL_DIR/src/converter.py" prompt "por favor poderia me ajudar a implementar esse repositório" 2>/dev/null)
[[ -n "$RESULT" ]] && ok "prompt compress OK → \"$RESULT\"" || warn "compressor retornou vazio"

# Teste 2: JSON → TOON via lib oficial
TOON_RESULT=$(python3 "$INSTALL_DIR/src/converter.py" json '{"users":[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]}' 2>/dev/null)
[[ "$TOON_RESULT" == *"users"* ]] && ok "JSON→TOON OK" || warn "conversão TOON retornou resultado inesperado"

# ── uninstall helper ──────────────────────────────────────────────────────────

cat > "$INSTALL_DIR/uninstall.sh" << 'UNINSTALL'
#!/usr/bin/env bash
echo "  removendo token-trim..."
rm -f "$HOME/.local/bin/ttrim"
rm -rf "${TOKEN_TRIM_HOME:-$HOME/.token-trim}"
echo "  ✓ removido. Limpe manualmente as linhas 'token-trim' do seu shell rc."
UNINSTALL
chmod +x "$INSTALL_DIR/uninstall.sh"

# ── resumo ────────────────────────────────────────────────────────────────────

echo ""
echo "  ────────────────────────────────────"
echo -e "  ${BOLD}${GREEN}instalação concluída!${NC}"
echo "  ────────────────────────────────────"
echo ""
echo -e "  Recarregue o shell:  ${CYAN}source $SHELL_RC${NC}"
echo ""
echo -e "  Uso básico:"
echo -e "    ${CYAN}ttrim \"explica esse service\" --file UserService.java${NC}"
echo -e "    ${CYAN}ttrim \"review\" --diff${NC}"
echo -e "    ${CYAN}ttrim_DRY_RUN=1 ttrim \"teste\" --file algo.ts${NC}"
echo ""
echo -e "  Para desinstalar:  ${CYAN}$INSTALL_DIR/uninstall.sh${NC}"
echo ""