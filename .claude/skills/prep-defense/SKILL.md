---
name: prep-defense
description: Prepare the user to defend a lab (защита лабы) — likely teacher questions with short answers grounded in the lab's code, runs and theory, written to reports/defense.md; `quiz` mode asks the questions one by one and checks the user's answers. Use when the user prepares to defend or present a lab, or asks to explain the lab's code and decisions.
argument-hint: "[lab-N] [quiz]"
---

# /prep-defense

The code was written by an agent; the user defends it. Goal: the user can explain every decision, number and important line.

## 1. Collect

- `task/task.md`, `lab-N.ipynb` with outputs, `src/*.py`, `reports/iterations/*.md`, `reports/results.md`, `runs/*/summary.json`.
- Complications: `grep -n "# усложнение:" src/`.

## 2. Write reports/defense.md (Russian)

```markdown
# Защита лабораторной N

## Работа за минуту
<5–7 строк: задача, данные (источник, размер, сплит), модель, обучение, лучший результат с числами, главный вывод>

## Вопросы и ответы

### Данные и предобработка
**<вопрос>**
<ответ в 2–4 предложения> — `src/data.py:make_loaders`

### Модель
### Обучение
### Метрики и результаты
### Усложнения
### Эксперименты
### Теория

## Каверзные вопросы
<что будет, если убрать X / поднять lr в 10 раз / не нормализовать данные / делать early stopping по test>

## Слабые места
<ограничения работы, к которым может придраться преподаватель, и как на это ответить>
```

- Sections:
  - **Модель**: what each block does and why these sizes.
  - **Обучение**: loss, optimizer, lr and scheduler, early stopping, regularization.
  - **Метрики и результаты**: why this metric, how to read the curves and the confusion matrix, comparison with the baseline.
  - **Усложнения**: one question per `# усложнение:`.
  - **Эксперименты**: what was tried and rejected, from `reports/iterations/`.
  - **Теория**: concepts the code actually uses, with typical exam questions on them.
- 25–40 questions in total, the ones the teacher is most likely to ask about this lab first.
- Numbers come only from `runs/` and notebook outputs; code references as `file:function`.
- Theory must be correct. If unsure about a fact, mark it «проверить» instead of guessing.

## 3. Mode: quiz

- Use `reports/defense.md` (write it first if missing). Ask one question at a time, harder ones later.
- Wait for the user's answer. Reply: «верно / частично / неверно», what is missing in 1–3 sentences, and the reference.
- Every 5 questions: score and the weakest topic, then ask whether to continue.
- Append poorly answered questions to `reports/defense.md` under «Повторить».
