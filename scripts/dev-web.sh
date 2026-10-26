#!/usr/bin/env bash
# Run just the new React UI. Existing Streamlit processes are untouched.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root/web"
exec npm run dev
