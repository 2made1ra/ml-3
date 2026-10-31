---
name: continue-lab
description: Resume the lab of the current branch lab-N in a fresh session (after /clear) — continue /lab-flow at the current stage of task/task.md, no arguments, no question at the start. Use when the user runs /continue-lab or says «продолжаем лабу», «дальше по лабе».
allowed-tools: Bash(git branch --show-current)
---

# /continue-lab

Current branch: !`git branch --show-current`

- `lab-N` → invoke the `lab-flow` skill with argument `N` and resume the current stage (its section 1: the call is the go).
- Any other branch → say «Не на ветке лабы: `git switch lab-N`, затем `/continue-lab`; новая лаба — `/lab-flow N`» and stop.
