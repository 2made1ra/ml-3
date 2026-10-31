---
name: lab-flow
description: Drive a whole lab end to end by calling the other skills in order — /new-lab, then for each stage of task/task.md its «Как» chain (/code-lab, /tune, /train, /log-iteration, /write-conclusion), closing the stage with [x] and /kva-sync, then /lab-review, /pack-submission, /prep-defense — asking the user to confirm before every step. Resumes from the lab's current state. Use when the user wants Claude to lead the lab («веди лабу», «делай всё сам», «автопилот») or invokes /lab-flow.
argument-hint: "<lab number> [assignment file]"
---

# /lab-flow

An orchestrator. It adds no new work: every step is another skill, invoked with the Skill tool and run exactly as its own `SKILL.md` says. Its job is to find where the lab stands, propose the next step, get the user's yes, run it, and repeat. The flow itself: "Workflow" in `CLAUDE.md` and `docs/workflow.md`.

## 1. Confirmation gate

Before every step, ask one AskUserQuestion. Text: progress (`Этап K/M`), the step (skill + target, e.g. `/code-lab stage 3`), what it produces, the expected time if known. Options:

- «Да» (recommended)
- «Пропустить» — mark the step skipped, propose the next one
- «Стоп» — end with a status line: where the lab stands and the next step; `/lab-flow N` resumes later

Any other answer is the user's instruction for this step.

- One confirmation = one step. Never run two steps under one yes.
- Questions inside a step stay as they are: the `/plan-lab` interview, the `/code-lab` forks, `/train` asking who starts the run. The gate does not replace them.
- A yes to a commit step is the user's request to commit (and push, if the step says so).

## 2. Find the state

- No `lab-N/task/task.md` → the first step is `/new-lab N <file>`. No assignment file → ask for it (`docs/workflow.md`, section 0).
- Otherwise read `task.md`. The current stage is the first `### [ ]`. Evidence for it: `runs/` and `reports/iterations/` listed in «Результаты», the stage's notebook sections (`TODO (этап K` still there or not), uncommitted changes (`git status`).
- From the evidence, propose the next step of the stage's «Как» chain. If the evidence is ambiguous, say what you see and ask where to start.

## 3. Steps

1. **Start:** `/new-lab N` — branch `lab-N`, transcript, interview, `task.md`, board, scaffold. Resuming: make sure the current branch is `lab-N`.
2. **Each stage, in `task.md` order:** its «Как» chain, step by step, e.g. `/code-lab stage K` → `/tune` → `/train` → `/log-iteration` → `/write-conclusion`.
   - Experiment stages loop: after `/log-iteration`, compare with «Готово, когда» (e.g. «≥ 3 гипотезы на модель»). Propose the next iteration: a new hypothesis → `/code-lab` if code changes → `/train` → `/log-iteration`. Or propose `/write-conclusion` once the criterion holds.
   - Before `/train`: the code must be committed (`/train`, section 1). If it is not, the commit is its own gated step.
3. **Close the stage:** check every item of «Готово, когда» with evidence (file, run, cell). All hold → gated step: tick `[x]`, fill «Результаты», `/kva-sync`. Then a gated commit step: «Коммит и push этапа K». Some item fails → say which and propose the step that fixes it.
4. **Finish:**
   - `/write-conclusion` for «Итоговые выводы».
   - `/lab-review`. It is better in a fresh session: offer «Стоп» so the user runs `/clear` and `/lab-flow N` again.
   - Fixes from the review via `/code-lab`, one finding per gated step.
   - Run all: the user runs it, or Claude runs `uv run jupyter nbconvert --to notebook --execute --inplace lab-N.ipynb` from `lab-N/`. Ask who.
   - `/pack-submission` + the size limit from «Оформление и сдача».
   - Commit and push the lab branch.
   - Merge into `main` ("Git" in `CLAUDE.md`): `git switch main && git pull && git merge --no-ff lab-N && git push`. The branch stays.
   - `/prep-defense`.

## 4. Rules

- Never shortcut a skill: its checks, smoke, sanity checks and questions all run.
- A step fails (error, failed check, a run worse than the input-independent baseline) → stop the chain, report the cause, propose a fix step (`/code-lab исправь: …`), gated like any other.
- A model, library or approach the user chose does not work → stop and decide with the user. Never switch to a fallback alone, even one named in `task.md`.
- Numbers only from `runs/`, notebook outputs or MLflow.
- Long sessions: when the context grows long, propose «Стоп» at the end of a stage so the user continues in a new session with `/lab-flow N`.
