---
name: plan-lab
description: Analyze a lab assignment (screenshot, PDF or md) — transcribe it to task/assignment.md, interview the user on open choices, and write task/task.md, the stage plan that the agent, the other skills and the user work from. Use when an assignment arrives (called by /new-lab), when it changes or a new part is released, or when the user asks to re-plan a lab.
argument-hint: "<lab number> [assignment file or attached image]"
---

# /plan-lab

Output, both in Russian: `task/assignment.md` (the assignment as text) and `task/task.md` (the plan). `task.md` is the lab's single source of truth for what must be done; every other skill works from it.

## 1. Intake

- Sources: md/txt — read; PDF — Read with `pages`; image — Read it.
- Never guess unreadable text. A full-page screenshot is often downscaled in transfer (e.g. 197×2000 px: only headings readable). Then tell the user what is readable and ask for a PDF (browser: Print → Save as PDF), the copied text, or one screenshot per screen.
- Copy the originals into `lab-N/task/`. macOS blocks reading `~/Downloads`, `~/Desktop`, `~/Documents` (EPERM): ask the user to move the file into `lab-N/task/`; never work around the block.
- Transcribe the assignment into `task/assignment.md`: full text with the original numbering, headings, points, links and code snippets; no paraphrasing. Mark unreadable spots `[неразборчиво]`.
- Re-plan (`task.md` exists): keep checked stages, «Решения», «Результаты» and «Доска» links; report what changed in the assignment.

## 2. Analyze

From `assignment.md` extract:

- parts and points: per section and totals;
- per section: what must be done and what must appear in the notebook;
- the teacher's conventions: required flags or variables (e.g. `FAST_MODE`), notebook formatting, file naming, what to submit, deadlines;
- constraints: allowed and forbidden models, libraries, metrics, datasets;
- choices left to the student: dataset, architectures, optional parts.

Map each convention onto our flow and note conflicts. Example: a quick-run flag vs `SMOKE`; "training runs inside the notebook" vs the notebook reading `runs/`.

## 3. Interview

AskUserQuestion, at most 4 questions per call, recommendation first. Ask only what the assignment does not settle:

- choices left to the student, 2–3 options each with a recommendation (e.g. a dataset: size that fits the Mac/4090 budget, clean target, explicit license);
- the target: which parts and points to aim for;
- conflicts between the teacher's conventions and our flow, with a proposed mapping;
- ambiguities in the text.

Answers go to «Решения». Unresolved items stay in «Неясности».

## 4. Write task/task.md

```markdown
# Лабораторная N: <тема>

Условие: `task/assignment.md` (оригиналы: `task/<файлы>`) · Разобрано: YYYY-MM-DD · Дедлайн: <если есть> · Доска: <эпик, пишет /kva-sync>

## Цель
<1–3 предложения>

## Баллы
| Часть | Максимум | Делаем |
| --- | ---: | --- |
| I. <название> | <N> | да / нет |

## Решения
- <вопрос> → <решение> (пользователь / по условию)

## Оформление и сдача
- <требования преподавателя: оформление ноутбука, обязательные флаги, имя файла, что сдавать>
- В нашем флоу: <как выполняем каждое требование>

## Ограничения
- <что запрещено или обязательно>

## Этапы

### [ ] Этап 1. <название> — п. <номера условия>, <баллы>
- Требование: <кратко, близко к условию>
- В ноутбуке: <секция, таблицы, графики, выводы>
- Как: <скиллы: `/code-lab`, `/tune`, `/train`, `/write-conclusion`>
- Готово, когда: <проверяемый критерий>
- Результаты: <runs/vN, reports/iterations/vN.md — заполняется по ходу>
- Доска: <задача, пишет /kva-sync>

## Неясности
- <открытые вопросы>
```

- One stage = one coherent piece of work that ends in something checkable in the notebook: usually one assignment section, sometimes two small ones. Stages are listed in the order of work.
- «Как» names the skills: `/code-lab` for any code, `/tune` when hyperparameters are tuned or options compared, `/train` when the stage trains, `/write-conclusion` when the section asks for conclusions.
- «Готово, когда» is checkable: a notebook element, a number in `runs/`, a passed check. Not "сделано хорошо".
- Requirement text stays close to the assignment; long passages are referenced by section number in `assignment.md`, not copied.
- Requirements that repeat across parts (formatting, submission, mandatory checks) live once in «Оформление и сдача»; the last stage checks them.

## 5. Finish

Run `/kva-sync` (`.claude/skills/kva-sync/SKILL.md`): the epic and the stage tasks on the board. Then show the user: the stages (one line each, with points), the decisions and the open questions. Next: `/new-lab` continues with the scaffold; after a re-plan, `/code-lab` on the next unchecked stage.
