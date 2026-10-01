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

# 2. Install / upgrade codebase-memory-mcp to the latest official release
CBM_BIN="${INSTALL_DIR}/codebase-memory-mcp"
CBM_UPGRADED=""
LATEST_TAG="$(curl -fsSLI -o /dev/null -w '%{url_effective}' https://github.com/DeusData/codebase-memory-mcp/releases/latest 2>/dev/null | sed -n 's#.*/tag/##p')"
INSTALLED_TAG=""
if [ -f "${CBM_BIN}" ]; then
    INSTALLED_TAG="v$("${CBM_BIN}" --version 2>/dev/null | awk '/^codebase-memory-mcp /{print $2; exit}')"
fi

if [ -n "${LATEST_TAG}" ] && [ "${LATEST_TAG}" != "${INSTALLED_TAG}" ]; then
    echo -e "⬇️  Downloading codebase-memory-mcp engine (${LATEST_TAG})..."
    DOWNLOAD_URL="https://github.com/DeusData/codebase-memory-mcp/releases/download/${LATEST_TAG}/${CBM_TAR}"
    TMP_DIR="$(mktemp -d)"
    curl -fsSL "${DOWNLOAD_URL}" -o "${TMP_DIR}/${CBM_TAR}"
    tar -xzf "${TMP_DIR}/${CBM_TAR}" -C "${TMP_DIR}"
    if [ -f "${CBM_BIN}" ]; then
        # A new engine refuses to start while any older engine process is alive
        "${CBM_BIN}" daemon stop >/dev/null 2>&1 || true
        pkill -f "${CBM_BIN}" 2>/dev/null || true
        CBM_UPGRADED="${INSTALLED_TAG} -> ${LATEST_TAG}"
    fi
    cp "${TMP_DIR}/codebase-memory-mcp" "${CBM_BIN}.new"
    chmod +x "${CBM_BIN}.new"
    mv -f "${CBM_BIN}.new" "${CBM_BIN}"
    rm -rf "${TMP_DIR}"
    echo -e "✅ Installed codebase-memory-mcp ${LATEST_TAG} to ${CBM_BIN}"
elif [ -f "${CBM_BIN}" ]; then
    if [ -n "${LATEST_TAG}" ]; then
        echo -e "✅ codebase-memory-mcp ${INSTALLED_TAG} is already the latest release"
    else
        echo -e "${YELLOW}⚠️  Could not check for engine updates; keeping installed ${INSTALLED_TAG}${NC}"
    fi
else
    echo -e "${RED}❌ Could not resolve the latest codebase-memory-mcp release. Check your network and retry.${NC}"
    exit 1
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

# 3.1 Install templates
SHARE_DIR="${HOME}/.local/share/agent-harness/templates"
mkdir -p "${SHARE_DIR}"
if [ -d "${SCRIPT_DIR}/templates" ]; then
    cp -r "${SCRIPT_DIR}/templates/"* "${SHARE_DIR}/" 2>/dev/null || true
else
    curl -sL "https://raw.githubusercontent.com/ArCzyL/agent-harness/main/templates/karpathy_rules.md" -o "${SHARE_DIR}/karpathy_rules.md" 2>/dev/null || true
fi

# 4. Ensure ~/.local/bin in PATH
SHELL_RC=""
if [ -n "${ZSH_VERSION}" ] || [ -n "${ZSH_NAME}" ] || [ -f "${HOME}/.zshrc" ] || [ "$(basename "${SHELL:-}")" = "zsh" ]; then
    SHELL_RC="${HOME}/.zshrc"
elif [ -f "${HOME}/.bashrc" ]; then
    SHELL_RC="${HOME}/.bashrc"
fi

if [ -n "${SHELL_RC}" ]; then
    if ! grep -q "export PATH=\"${INSTALL_DIR}:\$PATH\"" "${SHELL_RC}" 2>/dev/null && ! echo "$PATH" | grep -q "${INSTALL_DIR}"; then
        echo -e "\n# agent-harness\nexport PATH=\"${INSTALL_DIR}:\$PATH\"" >> "${SHELL_RC}"
        echo -e "✅ Added ${INSTALL_DIR} to PATH in ${SHELL_RC}"
    fi
fi

# 5. Run auto-configuration across all supported IDEs
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
echo "  4. Before delivery: agent-harness check   (agent-harness sync if stack facts drifted)"
echo ""
echo "Or in AI chat, simply say: '为当前项目建图并初始化开发规范'"
echo ""
if [ -n "${CBM_UPGRADED}" ]; then
    echo -e "${YELLOW}⚠️  Engine upgraded (${CBM_UPGRADED}). Restart codebase-memory-mcp in each open AI tool"
    echo -e "   (Cursor: Settings → MCP → toggle it off/on; or restart the app) so the new engine takes over.${NC}"
    echo ""
fi
