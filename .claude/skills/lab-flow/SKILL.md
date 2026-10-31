---
name: lab-flow
description: Drive a whole lab end to end by calling the other skills in order — /new-lab, then for each stage of task/task.md its «Как» chain (/code-lab, /tune, /train, /log-iteration, /write-conclusion), closing the stage with [x], /kva-sync and a board report, then /lab-review, /pack-submission, /prep-defense — one stage per fresh session (resumed by /continue-lab), hypotheses chosen with the user, other questions only at critical points, a commit per experiment. Use when the user wants Claude to lead the lab («веди лабу», «делай всё сам», «автопилот») or invokes /lab-flow.
argument-hint: "<lab number> [assignment file]"
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/lab_state.sh *)
---

# /lab-flow

An orchestrator. It adds no new work: every step is another skill, invoked with the Skill tool and run exactly as its own `SKILL.md` says. Its job is to find where the lab stands, run the steps of the current stage, and hand over to a fresh session. The flow itself: "Workflow" in `CLAUDE.md` and `docs/workflow.md`.

Current state (the lab of the current branch `lab-N`):

!`bash ${CLAUDE_SKILL_DIR}/scripts/lab_state.sh ${CLAUDE_PROJECT_DIR}`

## 1. Sessions

Every model call rereads the whole conversation, so a stage must not carry the previous stage's code, diffs and logs. Everything the next session needs lives in files: `task.md` (stages, «Гипотезы», «Решения», «Неясности», «Результаты»), `reports/iterations/vN.md` («Что дальше»), `runs/`, the notebook. The state block above tells a fresh session where to resume.

- **One stage per session.** `/lab-flow N` starts a lab; `/continue-lab` resumes it in a fresh session. Either is the go for the current stage: no question at the start. After the stage is closed (section 3, step 3) say «Дальше: /clear (или новая сессия), затем `/continue-lab` — этап K+1 в свежем контексте» and stop, no question.
- **Experiment stages** (a loop of iterations): the session also ends after every 2 `/log-iteration`s with the same line. The hypothesis list in `task.md` and the last iteration's «Что дальше» are the handoff.
- **Before any stop, write the handoff:** the user's decisions of this session that no file holds go to `task.md` «Решения» with the date; open questions go to «Неясности». Never leave it for after the user returns: the prompt cache lives an hour, and a session continued after a longer pause rewrites its whole context. A user who comes back after a pause gets «/clear, затем `/continue-lab`» instead of continuing.
- **Read narrowly:** the state block replaces exploration. Read the current stage's sources (the `assignment.md` sections it cites, the files it touches), not the whole lab.

## 2. Questions

Ask one AskUserQuestion only to pick hypotheses (below) and at a critical point: real uncertainty or an ambiguity you cannot resolve yourself, i.e. a decision that needs the user. Examples: a fork with no clear winner, a failed step whose fix changes the plan, a model or library the user chose that does not work. Recommendation first; «Стоп» ends with a status line (where the lab stands, the next step).

Inside a step:

- Real forks stay as questions: the `/plan-lab` interview, `/code-lab` forks, the Optuna analysis (`/tune`, section 4).
- Routine confirmations of other skills are skipped: plan approvals (`/tune` round plan), offers to commit.
- `/train` and `/tune` on the Mac: Claude starts the run itself in the background when the estimate is ≤ 20 min. Longer runs, and any PC run, still ask who starts it.

Commits: Claude commits itself, so every full run trains on a clean tree (`git_dirty: false`) and git history is the experiment log. Types and checks: "Git" in `CLAUDE.md`.

- Before a full run (`/train`, `/tune`), if code changed: `feat(labN): H<n> — <изменение>` (or `bug(labN)` for a fix).
- After its `/log-iteration`: `run(labN): vN — H<n>, <модель>, val <метрика> <число> (Δ <±> к vM)` with `runs/vN/` (or `runs/tune/<study>.db`) and `reports/`. Body: the hypothesis, the changed parameters, train time, the verdict.
- Other work (notebook sections, conclusions, `task.md`): `docs(labN): …` when the stage closes.
- Push when the stage closes (board links need it). Merge into `main` only on the user's go.

### Hypotheses

Claude proposes, the user picks. At the start of an experiment stage and after each tested batch:

1. Read the results: `reports/results.md`, the latest `vN.md` («Интерпретация», «Что дальше»), the stage's Optuna studies (`/tune`, section 4).
2. One AskUserQuestion, `multiSelect: true`, one question per category, 2–4 options each:
   - **данные**: EDA follow-up, transformations, features, class balancing, augmentation;
   - **гиперпараметры**: what to tune or fix next, from the Optuna analysis.

   Option label: the change. Description: expected effect on the main val metric, the number it rests on, cost in time. Recommended first. Model choice is not offered: models are fixed in «Решения»; a model that does not work is a critical point.
3. Write the ticked ones (and free-text answers) into the stage in `task.md`, bullet «Гипотезы»: `- [ ] H<n> (<категория>): <изменение> → <ожидаемый эффект>`. After its `/log-iteration`: `- [x] H<n> …: vN, val <метрика> <число>`.
4. Never start an iteration on a hypothesis that is not in the list.

## 3. Steps

1. **Start:** no `task.md` → `/new-lab N <file>` (no assignment file → ask for it, `docs/workflow.md`, section 0). Branch `lab-N`, transcript, interview, `task.md`, board, scaffold; then the «Дальше» line.
2. **The current stage** (the first `### [ ]`). First, if its board task is not `in_progress`: `update_task` to `in_progress` (`/kva-sync`, section 2). Then its «Как» chain, step by step, e.g. `/code-lab stage K` → `/tune` → `/train` → `/log-iteration` → `/write-conclusion`. Where to start inside it: the state block (runs and iteration files listed in «Результаты», open «Гипотезы», `TODO (этап K` left in the notebook, uncommitted files). Ambiguous → say what you see and ask.
   - Experiment stages loop in batches: pick hypotheses (section 2) → for each ticked one: `/code-lab` if code changes → `/tune` or `/train` → `/log-iteration` → tick it. After the batch, compare with «Готово, когда» (e.g. «≥ 3 гипотезы на модель»): the next batch, or `/write-conclusion` once the criterion holds.
3. **Close the stage:** check every item of «Готово, когда» with evidence (file, run, cell). All hold → tick `[x]`, fill «Результаты», `/kva-sync`, the stage report comment (`/kva-sync`, section 6), write the handoff, commit and push (section 2), then the «Дальше» line. Some item fails → say which and run the step that fixes it.
4. **Finish** (stage «Итоговые выводы и сдача»; `/lab-review` and what follows run in their own fresh session):
   - `/write-conclusion` for «Итоговые выводы».
   - `/lab-review`.
   - Fixes from the review via `/code-lab`, one finding at a time.
   - Run all: Claude runs `uv run jupyter nbconvert --to notebook --execute --inplace lab-N.ipynb` from `lab-N/`.
   - `/pack-submission` + the size limit from «Оформление и сдача».
   - Commit and push the lab branch (section 2).
   - Ask: merge into `main` ("Git" in `CLAUDE.md`): `git switch main && git pull && git merge --no-ff lab-N && git push`. The branch stays.
   - `/prep-defense`.

## 4. Rules

- Never shortcut a skill: its checks, smoke, sanity checks and questions all run.
- A step fails (error, failed check, a run worse than the input-independent baseline) → find the cause and fix it via `/code-lab исправь: …` without asking. Ask only if the fix changes the plan or you are unsure of the cause.
- A model, library or approach the user chose does not work → stop and decide with the user. Never switch to a fallback alone, even one named in `task.md`.
- Numbers only from `runs/`, notebook outputs or MLflow.
