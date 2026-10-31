#!/usr/bin/env bash
# Where a lab stands, for /lab-flow: injected into the skill at load, so a fresh session
# needs no exploration calls. Usage: lab_state.sh <repo-dir> [<lab number>]
# Without a number the lab comes from the branch name lab-N.
set -u
repo="$1"
cd "$repo" || exit 0
branch=$(git branch --show-current)
echo "Branch: $branch"
if [ -z "${2:-}" ] && [[ "$branch" != lab-* ]]; then
  echo "Not on a lab-N branch: a new lab starts with /new-lab N; resuming → git switch lab-N"
  exit 0
fi
n="${2:-${branch#lab-}}"
lab="lab-$n"
if [ ! -f "$lab/task/task.md" ]; then
  echo "$lab/task/task.md: missing → start with /new-lab $n"
  exit 0
fi
echo
echo "## Stages ($lab/task/task.md)"
grep -E '^### \[[ x]\]' "$lab/task/task.md"
echo
echo "## Current stage (first [ ])"
awk '/^### \[ \]/{f=1} f&&/^### /&&!/^### \[ \]/{exit} f&&/^### \[ \]/&&n++{exit} f' "$lab/task/task.md"
echo
echo "## runs/"
ls "$lab/runs" 2>/dev/null | grep -v -- '-smoke$' | tr '\n' ' '
echo
echo "## reports/iterations/"
ls "$lab/reports/iterations" 2>/dev/null | tr '\n' ' '
echo
echo "## Notebook TODO markers by stage"
grep -o 'TODO (этап [0-9]*' "$lab/$lab.ipynb" 2>/dev/null | sort | uniq -c
echo
echo "## git status"
git status --short
