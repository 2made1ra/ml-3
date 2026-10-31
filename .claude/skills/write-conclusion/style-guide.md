# Conclusion style guide

Describes the author's voice in lab conclusions, based on last semester's notebooks (repo `~/dev/maga/second/ml-2`): `LAB_I/notebooks/lab_1.ipynb`, `LAB_II/notebooks/lab_2.ipynb`, `LAB_III/solution/lab_3.ipynb`.

Goal: new conclusions read like the author's own text — technically meaningful, not over-polished, with personal judgments, careful assumptions and concrete results. Conclusions are written in Russian; all Russian examples below are reference text, reuse their tone, not their content.

## 0. Corpus

- `lab_1` — the densest and most interpretive. Long conclusions, explicit model comparisons, causal links, evaluative words: `критическое переобучение`, `более здоровая картина обучения`, `универсального лидера нет`. Analysis is built on contrast: Random Forest vs CatBoost, global vs local methods, precision vs recall.
- `lab_2` — drier, report-like. Short, states facts: configuration, metrics, confused classes. Almost no personal remarks. Use it as the model for short technical notes.
- `lab_3` — the most alive. Explains the course of work: what failed first, why `Unknown Genre` was dropped, why some decisions were compromises. Honest phrases like `до меня дошло`, `мне стало лень`, `результат меня удивил`. Transfer such remarks carefully so not every conclusion becomes chatty.

Target mix: analytical density and model comparison from `lab_1`, honesty and "how I got here" from `lab_3`, `lab_2` for short technical notes.

## 1. Overall

Between a course report and a personal experiment review. Not a dry automatic summary: the author explains why the result is what it is, where the model fails, what that says about the data, what to try next.

Main principle: a conclusion interprets the result; it does not retell the plot or table.

A good conclusion answers four questions:

- what exactly happened;
- why it could have happened;
- what limitation or problem remains;
- what can be done next.

## 2. Author's voice

Moderately personal, still report-like. First person fits choices, doubts, surprises and limitations of the experiment.

Typical phrases:

- `я отдаю свое предпочтение`
- `в моем случае`
- `я ожидал`
- `мне очевидно`
- `я посчитал`
- `до меня дошло`
- `можно было бы`
- `стоит попробовать`
- `вероятно`
- `в целом ожидаемо`
- `по сути`
- `если говорить по простому`

Do not put first person in every paragraph. It works best as a single human remark after a technical explanation.

Example structure:

```markdown
Модель показала ожидаемый рост качества по `macro F1`, однако полностью проблему дисбаланса это не решило. В целом результат выглядит логично: архитектура стала сильнее, но редкие классы все еще представлены слишком слабо.

Если говорить по простому - модель стала увереннее на типичных примерах, но на пограничных случаях ей все еще не хватает данных.
```

## 3. Formality

Technical, not bureaucratic. Mixing Russian explanations with English ML terms is normal: `baseline`, `feature engineering`, `transfer learning`, `backbone`, `fine-tuning`, `macro F1`, `accuracy`, `recall`, `precision`, `pipeline`.

Formality comes from facts, metrics and terms; liveliness from the author's judgment.

Good:

```markdown
CatBoost демонстрирует более здоровую картину обучения: модель не вызубрила тренировочную выборку и лучше пытается находить редкие классы. Однако эта попытка приводит к большему числу ложных срабатываний, поэтому precision на миноритарных оценках проседает.
```

Too dry:

```markdown
CatBoost имеет лучшие показатели recall, но худшие precision. Это обусловлено дисбалансом классов.
```

Too artificial:

```markdown
Можно с уверенностью заключить, что предложенный подход блестяще демонстрирует высокую эффективность и открывает широкие перспективы дальнейших исследований.
```

## 4. Paragraph logic

Use 1–3 connected paragraphs, not a list. A typical paragraph:

1. Main result.
2. Comparison or contrast.
3. Cause.
4. Human interpretation or limitation.

Template:

```markdown
[Модель/эксперимент/график] показал [главный результат]. Однако [ограничение или обратная сторона]. Это объясняется тем, что [причина, связанная с данными, архитектурой или метрикой]. В целом [авторская оценка результата].
```

Example:

```markdown
Оптимизация через Optuna подняла `F1 Macro`, но не решила кардинально проблему переобучения. Ограничение глубины деревьев дает свои плоды, однако разрыв между train и test все еще остается заметным. В целом это ожидаемо: при таком дисбалансе классов одного подбора гиперпараметров недостаточно.
```

## 5. Required content

### Concrete numbers

Tie conclusions to metrics, object counts, class or feature names. Never stay generic when numbers exist.

Bad:

```markdown
Улучшенная модель стала заметно лучше базовой.
```

Better:

```markdown
Переход от `baseline` с `test_acc=0.9077` к финальной модели с `test_acc=0.9436` показывает, что изменение архитектуры и режима обучения дало реальный прирост качества.
```

### Comparison

The author explains results through contrast:

- `Random Forest` vs `CatBoost`;
- `CNN` vs `ViT`;
- train vs test;
- accuracy vs macro F1;
- global vs local interpretation;
- frequent vs rare classes.

Connectors: `в отличие от`, `при этом`, `однако`, `зато`, `напротив`, `с другой стороны`, `тем не менее`, `в свою очередь`.

### Causal interpretation

After the metrics, explain why. Usual causes: class imbalance, few rare examples, overlapping features, subjective labels, overfitting, architecture capacity, pretrained backbone, feature engineering quality, the optimized metric.

Typical phrases:

- `Это объясняется тем, что...`
- `Основной причиной стал...`
- `Такой разрыв ожидаем...`
- `Практический вывод...`
- `Наличие такой доли ошибок говорит о...`
- `Это делает результаты более содержательными...`

## 6. Personal remarks

Honest remarks about the course of work make the text read like a real report by someone who experimented, failed and decided.

Topics: what failed first; why the setup changed; what result was surprising; where time ran out; what could have been done better; which option was a reasonable compromise.

Examples:

```markdown
Вообще, результат меня удивил: для такой небольшой сети я ожидал более скромного качества.
```

```markdown
Как вариант решения этой проблемы можно было бы отдельно разметить изображения технического класса, но я до этого дошел поздно, а обучение занимает слишком много времени.
```

```markdown
В будущем хочу попробовать погонять Optuna дольше, когда разберусь с более стабильным обучением на GPU.
```

Use 0–1 remark per conclusion, otherwise the text becomes too conversational. Only remarks about things that actually happened (see `reports/iterations/`).

## 7. Problems and errors

The author does not hide weaknesses. Errors are stated directly, with why they are natural: the model is not simply bad; the problem is often the data, the setup, imbalance or ambiguous labels; even wrong answers can be meaningfully explained.

Examples:

```markdown
Большинство промахов приходится на соседние классы, что ожидаемо из-за сильного пересечения их признакового пространства.
```

```markdown
Ошибки содержательно объяснимы: одна картина может иметь признаки нескольких жанров, а датасет задает только одну целевую метку.
```

```markdown
Редкие классы модель практически не распознает, потому что в тестовой выборке слишком мало примеров для устойчивой оценки.
```

## 8. Sentences

Medium length. Long connected sentences with `однако`, `при этом`, `поскольку`, `из-за чего` are fine, but follow a long analytical sentence with a short human one.

Characteristic constructions:

```markdown
В отличие от [модель A], [модель B] показала более [качество], поскольку [причина].
```

```markdown
Это не полностью решает проблему [X], но показывает, что [Y] действительно влияет на результат.
```

```markdown
Если говорить по простому - [простое объяснение технического результата].
```

```markdown
В целом результат выглядит ожидаемо: [причина].
```

```markdown
Можно предположить, что [признак/фактор] будет сильно влиять на [результат].
```

## 9. Notebook formatting

Local conclusion after a plot or table:

```markdown
> **Вывод:**

Текст вывода в 1-3 абзаца.
```

Short conclusion on one line:

```markdown
> **Вывод:** сравнивая две базовые модели, я отдаю свое предпочтение CatBoost по одной простой причине - переобучение у RF слишком велико.
```

Final section with headings:

```markdown
## 1. Обзор результатов

## 2. Анализ ошибок

## 3. Возможные направления улучшения
```

In the text:

- models, variables, metrics and classes in backticks: `CatBoost`, `macro F1`, `Unknown Genre`;
- numbers inline: `test accuracy 0.7743`, `99 из 320 наблюдений`;
- class pairs with an arrow or slash: `Shirt -> T-shirt/top`, `landscape / cityscape`;
- lists only in final recommendations or summaries; analysis in paragraphs.

## 10. Natural imperfection

The source text has some unevenness: repetitions, colloquial inserts, not fully academic turns. Keep: slightly uneven but clear speech, personal judgments, colloquial connectors (`в целом`, `по сути`, `на самом деле`, `довольно`, `просто`). Do not keep: typos, wrong cases, accidental word repeats, run-on sentences without a period.

Rule: the text is a carefully proofread version of the author, not a deliberately damaged one.

## 11. Avoid

Too neutral:

```markdown
Были получены следующие результаты. Модель A имеет такие-то метрики. Модель B имеет такие-то метрики.
```

Advertising tone:

```markdown
Модель продемонстрировала выдающуюся эффективность и полностью подтвердила правильность выбранного подхода.
```

Generic words without facts:

```markdown
Результаты хорошие, но есть куда расти.
```

Definitions instead of interpretation (definitions belong to method sections):

```markdown
Accuracy - это метрика, которая показывает долю правильных ответов. Precision - это...
```

## 12. Templates

### After training a model

```markdown
> **Вывод:**

[Модель] показала [метрика/результат], что [краткая оценка результата]. При этом [ограничение: переобучение, дисбаланс, слабый recall, просадка precision]. Основная причина, вероятно, связана с [свойство данных или архитектуры].

В целом результат выглядит [ожидаемо/неожиданно/логично]: [человеческое объяснение]. Для дальнейшего улучшения стоит попробовать [следующий шаг].
```

### After comparing models

```markdown
> **Вывод:**

Сравнение показывает, что универсального лидера нет. [Модель A] лучше справляется с [метрика/тип примеров], но [слабость]. [Модель B], напротив, [сильная сторона], хотя [ограничение].

Мое предпочтение остается за [модель], потому что [простая причина, связанная с задачей]. В данной постановке важнее [критерий], чем [вторичный критерий].
```

### After error analysis

```markdown
> **Вывод:**

Большинство ошибок сосредоточено в [классы/пары/область], что ожидаемо из-за [причина]. Эти объекты выглядят как пограничные случаи: [короткое объяснение, почему модель путается].

Если говорить по простому - модель не столько ломается на случайных примерах, сколько упирается в неоднозначность самих данных. Поэтому дальнейшее улучшение стоит искать через [данные/аугментацию/балансировку/другую постановку].
```

### After feature/model interpretation

```markdown
> **Вывод:**

Наибольший вклад в предсказание вносят [признаки]. Это частично совпадает с [другой метод/предыдущий результат], однако есть важное отличие: [различие].

Такое расхождение естественно, потому что [метод A] оценивает [что именно], а [метод B] показывает [что именно]. По сути, модели находят разные пути в признаковом пространстве, но ключевая логика остается связанной с [главные факторы].
```

## 13. Checklist per conclusion

- 2–4 concrete facts from the result;
- one main contrast or problem;
- its cause;
- at most one personal remark, if it fits;
- end with the practical meaning or a next step.
