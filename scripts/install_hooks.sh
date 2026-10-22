#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
git -C "$root" config core.hooksPath .githooks
echo "Configured .githooks as the repository hooks path."
