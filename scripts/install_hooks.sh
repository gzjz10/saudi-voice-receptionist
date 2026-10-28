#!/usr/bin/env bash
# Install a git pre-commit hook that scans staged changes for secrets with gitleaks.
# Pinned version: 8.30.1 (install it yourself: macOS `brew install gitleaks`,
# Windows `winget install Gitleaks.Gitleaks`; then check `gitleaks version`).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WANT="8.30.1"
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "gitleaks is not installed; hook NOT installed. Install gitleaks $WANT and re-run." >&2
  exit 1
fi
HAVE="$(gitleaks version | tr -d 'v')"
[ "$HAVE" = "$WANT" ] || echo "warning: gitleaks $HAVE installed, $WANT pinned" >&2
cat > "$ROOT/.git/hooks/pre-commit" <<'HOOK'
#!/usr/bin/env bash
exec gitleaks git --pre-commit --staged --redact --config .gitleaks.toml
HOOK
chmod +x "$ROOT/.git/hooks/pre-commit"
echo "pre-commit hook installed (gitleaks $HAVE)"
