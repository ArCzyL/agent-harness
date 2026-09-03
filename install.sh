#!/usr/bin/env bash
# ==============================================================================
# agent-harness Universal Installer
# One-line install script for AI Agent Anti-Drift Framework & Codebase Memory
# Supports: macOS (Intel & Apple Silicon), Linux (x86_64 & arm64)
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
   ___                    __     __ __                                 
  / _ | ___ ____ ___  __ / /_   / // /___ _ ____ ___  ___  ___ ___    
 / __ |/ _ `/ -_) _ \/ // / -_) / _  // _ `// __// _ \/ -_)(_-<(_-<   
/_/ |_|\_, /\__/_//_/\_,_/\__/ /_//_/ \_,_//_/  /_//_/\__//___/___/   
      /___/                                                            
       Universal Anti-Drift & Codebase Memory Harness for AI Agents
EOF
echo -e "${NC}"

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "${INSTALL_DIR}"

# 1. Detect OS & Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

echo -e "🔍 Detecting platform: ${YELLOW}${OS} (${ARCH})${NC}..."

CBM_TAR=""
case "${OS}" in
    Darwin)
        if [ "${ARCH}" = "arm64" ]; then
            CBM_TAR="codebase-memory-mcp-darwin-arm64.tar.gz"
        else
            CBM_TAR="codebase-memory-mcp-darwin-amd64.tar.gz"
        fi
        ;;
    Linux)
        if [ "${ARCH}" = "aarch64" ] || [ "${ARCH}" = "arm64" ]; then
            CBM_TAR="codebase-memory-mcp-linux-arm64-portable.tar.gz"
        else
            CBM_TAR="codebase-memory-mcp-linux-amd64-portable.tar.gz"
        fi
        ;;
    *)
        echo -e "${RED}❌ Unsupported operating system: ${OS}${NC}"
        exit 1
        ;;
esac

# 2. Check / Install codebase-memory-mcp
CBM_BIN="${INSTALL_DIR}/codebase-memory-mcp"
CBM_VERSION="v0.10.8"

if [ ! -f "${CBM_BIN}" ]; then
    echo -e "⬇️  Downloading codebase-memory-mcp engine (${CBM_VERSION})..."
    DOWNLOAD_URL="https://github.com/DeusData/codebase-memory-mcp/releases/download/${CBM_VERSION}/${CBM_TAR}"
    TMP_DIR="$(mktemp -d)"
    curl -sL "${DOWNLOAD_URL}" -o "${TMP_DIR}/${CBM_TAR}"
    tar -xzf "${TMP_DIR}/${CBM_TAR}" -C "${TMP_DIR}"
    cp "${TMP_DIR}/codebase-memory-mcp" "${CBM_BIN}"
    chmod +x "${CBM_BIN}"
    rm -rf "${TMP_DIR}"
    echo -e "✅ Installed codebase-memory-mcp engine to ${CBM_BIN}"
else
    echo -e "✅ Found existing codebase-memory-mcp at ${CBM_BIN}"
fi

# 3. Install agent-harness CLI
echo -e "📦 Installing agent-harness CLI..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${SCRIPT_DIR}/bin/agent-harness" ]; then
    cp "${SCRIPT_DIR}/bin/agent-harness" "${INSTALL_DIR}/agent-harness"
else
    # Remote curl install fallback
    curl -sL "https://raw.githubusercontent.com/ArCzyL/agent-harness/main/bin/agent-harness" -o "${INSTALL_DIR}/agent-harness" || \
    curl -sL "https://github.com/ArCzyL/agent-harness/raw/main/bin/agent-harness" -o "${INSTALL_DIR}/agent-harness"
fi
chmod +x "${INSTALL_DIR}/agent-harness"
ln -sf "${INSTALL_DIR}/agent-harness" "${INSTALL_DIR}/cbm-init"

# 4. Ensure ~/.local/bin in PATH
SHELL_RC=""
if [ -n "${ZSH_VERSION}" ] || [ -n "${ZSH_NAME}" ] || [ -f "${HOME}/.zshrc" ]; then
    SHELL_RC="${HOME}/.zshrc"
elif [ -f "${HOME}/.bashrc" ]; then
    SHELL_RC="${HOME}/.bashrc"
fi

if [ -n "${SHELL_RC}" ]; then
    if ! grep -q "export PATH=\"${INSTALL_DIR}:\$PATH\"" "${SHELL_RC}" && ! echo "$PATH" | grep -q "${INSTALL_DIR}"; then
        echo -e "\n# agent-harness\nexport PATH=\"${INSTALL_DIR}:\$PATH\"" >> "${SHELL_RC}"
        echo -e "✅ Added ${INSTALL_DIR} to PATH in ${SHELL_RC}"
    fi
fi

# 5. Run auto-configuration across installed IDEs
"${INSTALL_DIR}/agent-harness" setup

# 6. Start daemon if not running
echo -e "⚡ Starting codebase memory warm daemon..."
"${CBM_BIN}" daemon start >/dev/null 2>&1 || true

echo -e "${GREEN}"
echo "=================================================================="
echo "🎉 agent-harness successfully installed!"
echo "=================================================================="
echo -e "${NC}"
echo "How to use:"
echo "  1. cd /path/to/any/project"
echo "  2. agent-harness init ."
echo "  3. Open project in TRAE, Cursor, Claude Code, or Antigravity and start coding!"
echo ""
echo "Or in AI chat, simply say: '为当前项目建图并初始化开发规范'"
echo ""
