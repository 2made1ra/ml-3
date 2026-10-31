---
name: kva-sync
description: Mirror a lab's stage plan (task/task.md) onto the kvatask board — one epic per lab, one task per stage linked to the epic, statuses from the stage checkboxes; list board tasks the plan lacks. Use after /plan-lab writes or updates task.md (it calls this), when a stage starts or is ticked (/code-lab calls this), or when the user asks to sync or check the board.
argument-hint: "[lab-N]"
---

# /kva-sync

`task/task.md` is the source of truth. The board mirrors it so the user sees the lab's work there. Board text is a deliverable: Russian.

## 1. Preconditions

- kvatask tools come from the MCP server `kvatask` in `.mcp.json`. If they are missing or return 401/403: tell the user in one line (no `secrets.yaml` on this machine or a revoked key, see `README.md`) and stop. The board never blocks lab work.
- Never read or print `secrets.yaml`.

## 2. Board API

Tools are deferred: load them with ToolSearch `select:mcp__kvatask__<name>,...`. The key is bound to project `DL` (ml-3): pass `project_prefix: "DL"`. IDs are `DL-<n>`. Descriptions are Markdown.

| Action | Tool and fields |
| --- | --- |
| Create the epic | `create_task`: `project_prefix`, `title`, `type: "epic"`, `status: "todo"`, `due_date: "YYYY-MM-DD"`, `description` |
| Create stage tasks | `bulk_create_tasks`: `project_prefix`, `tasks: [{title, type: "task", status: "todo", description}]`; returns `display_id` per item, in order |
| Link a task to the epic | `create_task_link`: `task_id: <epic>`, `linked_task_id: <task>`, `link_type: "subtask"` (one call per task; `create_task` has no parent field) |
| Update title, description, status, due date | `update_task`: `task_id` + changed fields only (`due_date: "null"` clears); many at once: `bulk_update_tasks` |
| List the epic's tasks | `list_task_links`: `task_id: <epic>` → `subtask → DL-n: <title>` lines; details: `bulk_get_tasks` |

Type codes: `epic`, `task`. A wrong code returns `ERR_INVALID_*` with `valid_codes`.

| `task.md` | Board status |
| --- | --- |
| new stage | `todo` |
| work on the stage started (`/code-lab`) | `in_progress` |
| `### [x]` | `done` |

## 3. Links in task.md

- Epic: `· Доска: <epic id>` at the end of the header line.
- Stage: last bullet `- Доска: <task id>`.
- A link means "update"; no link means "create, then write the link". This keeps reruns free of duplicates.

## 4. Sync

Every description ends with a «Подробно» block of clickable links to the lab's md files, where the work is described in full. Link base: `git remote get-url origin` without `.git` + `/blob/main/`, e.g. `https://github.com/<owner>/<repo>/blob/main/lab-N/task/task.md`. The links open what is pushed to `main`: if `git status` or `git log origin/main..` shows the linked files unpushed, warn the user that the board shows the old version until a push.

1. Epic: title = the `task.md` title (`Лабораторная N: <тема>`); description = «Цель» and the «Баллы» table; due date = «Дедлайн». «Подробно»:
   - План этапов: `lab-N/task/task.md`
   - Условие: `lab-N/task/assignment.md` and the originals in `task/`
   - Ноутбук: `lab-N/lab-N.ipynb`
2. Each stage, in order: title = the heading without the checkbox (`Этап K. <название> — п. …, <баллы>`); description = its bullets «Требование», «В ноутбуке», «Как», «Готово, когда». «Подробно»:
   - План этапа: `lab-N/task/task.md`, раздел «Этап K»
   - Условие: `lab-N/task/assignment.md`, пункты <номера из заголовка этапа>
   - Результаты: every `reports/iterations/vN.md` listed in the stage's «Результаты» (added as they appear)

   Create missing tasks; update only fields that differ.
3. Status:
   - `[x]` → done.
   - `[ ]` → keep the board status, since «в работе» is set by `/code-lab`. A new task → to do.
   - Done on the board but `[ ]` in `task.md`: report it; change neither.
4. A board task whose stage is gone from `task.md`: report it. Never delete board tasks without the user's consent.
5. Tasks in the epic without a link in `task.md` (added by the user): list them and propose for each: a new stage via `/plan-lab`, or a one-off `/code-lab <задача>`.

## 5. Report (Russian)

One line per created or updated task (`Этап K — создана / обновлено: <поля> / статус → <статус>`), then the lists from steps 3–5 of "Sync".
