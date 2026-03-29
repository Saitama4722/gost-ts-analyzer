# GOST TS Analyzer

## 🚀 Overview

**GOST TS Analyzer** is a self-contained web service and UI for analyzing Russian technical specification documents (**DOCX** and **PDF**). It extracts and normalizes text, infers a lightweight section structure, runs **deterministic, rule-based checks** aligned with common expectations for GOST-style technical documentation, and returns structured findings with locations, severity, and recommendations. Results are browsable in the browser and exportable as **JSON**, **CSV**, or a minimal **DOCX** report.

---

## ✨ Key Features

- **DOCX / PDF ingestion** with MIME and extension validation; clear HTTP error responses for unsupported types and extraction failures  
- **Text extraction** via `python-docx` and `pypdf`, plus **normalization** and a **unified internal document model** (blocks and full text)  
- **Structure pipeline**: heading/section detection, internal tree, and enrichment used by all structure-aware checks  
- **Broad check coverage**: structure, required content signals, requirement wording quality, numeric signals and units, references, terminology, and duplicate formulations  
- **Unified issue model** aggregated from check outputs, plus a **summary report** object in the API response  
- **Web UI**: upload flow with progress, expandable issue cards, filtering by issue type, exports  
- **Windows launcher** (`start_app.bat`): resolves Python/venv, binds **127.0.0.1** on **8000**, else **8765**, else the first free port in **8001–8100**; waits for `/api/health`; opens the default browser (uses `curl` for the health probe)

---

## 🎯 Why this project matters

Technical specifications are long, dense, and easy to ship with inconsistent structure, weak requirements, broken cross-references, and terminology drift. Manual review does not scale and varies between reviewers. This tool automates **repeatable, transparent checks** so teams can surface likely gaps and quality risks **before** heavy review cycles. It targets **document quality and GOST-oriented conformance signals**; it does not replace expert judgment or certify compliance against a specific standard edition or legal regime.

---

## 🧠 How it works

1. **Upload** — The client sends a file to `POST /api/upload`; the server stores it under `uploads/` (ignored by Git) for processing.  
2. **Parse** — DOCX and PDF paths extract paragraph/page text into the unified representation.  
3. **Normalize** — Text is normalized for consistent matching across checks.  
4. **Structure** — Headings and sections are detected and assembled into an enriched structure graph.  
5. **Checks** — Modular validators read structure and full text (and blocks where needed); each produces structured results merged into one `checks` object.  
6. **Output** — Issues are serialized, a human-oriented `report` is built, and the full payload is returned as JSON for the UI and export actions. DOCX report export reposts that payload to `POST /api/export/report-docx`.

---

## 🏗 Tech stack

| Area | Technology |
|------|------------|
| **Backend** | Python 3.10+, **FastAPI**, Uvicorn |
| **Uploads** | `python-multipart` |
| **DOCX** | `python-docx` |
| **PDF** | `pypdf` |
| **Analysis** | Rule modules under `backend/app/rules/`, regex and string heuristics (no ML stack in runtime dependencies) |
| **Structure** | `structure_detector`, `structure_builder`, `structure_enricher` |
| **Frontend** | `templates/index.html`, `static/css`, `static/js` (vanilla JavaScript) |
| **Packaging** | `pyproject.toml`, `requirements.txt`; dev/test extras in `requirements-dev.txt` |

---

## ⚙️ Implemented functionality

Grounded on `docs/progress.md` and the current codebase:

- **Project foundation** — Repository layout, FastAPI app, pinned dependencies, local run path documented below  
- **UI** — Main page, responsive layout, upload block, states, polished styling, mobile-oriented refinements, readable results flow  
- **Upload API** — Backend `POST /api/upload`, frontend wiring, type validation, error handling  
- **Progress UX** — Progress bar, percentage, staged status text, stable stage transitions  
- **Extraction** — DOCX extraction, basic PDF text extraction, normalization, unified document format  
- **Structure** — Heading/section detection, internal structure representation, enrichment for downstream checks  
- **Rules data** — Templates for required sections, vague-wording and related dictionaries, glossary-oriented terminology data  
- **Checks** — Required sections, section order, structure completeness; purpose/goal; scope; functional requirements; non-functional requirement signals (headings and phrase lists); acceptance criteria; vague wording; unverifiable formulations; numerical characteristics; measurement units; figure/table/appendix references; terminology consistency; duplicate formulations  
- **Reporting** — Issue list serialization, final analysis report object, UI rendering with fragments and type differentiation, filtering  
- **Exports** — Client-side JSON and CSV from the last successful analysis; server-side minimal DOCX from posted analysis JSON  
- **Quality pass** — DOCX/PDF scenarios, check coverage smoke behavior, UI error paths, stabilization  
- **Windows** — One-click `start_app.bat` with health check and browser launch  

**Not in scope today:** authentication, persistent user storage, layout-aware PDF parsing, optional items from the internal spec that are not wired in `main.py` (for example requirement–acceptance traceability is not implemented as a separate check).

---

## 🔍 Current checks / analysis

The same check set runs for **both DOCX and PDF** pipelines (`backend/app/main.py`).

| Theme | What it evaluates |
|-------|-------------------|
| **Structure** | Presence of required sections; expected section order; overall structure completeness (informed by presence results) |
| **Purpose & scope** | Signals for document purpose/goal and scope / application area |
| **Requirements** | Functional requirements; non-functional requirement signals (dedicated headings and body phrases—reliability, performance, security, usability, compatibility, and related attributes); acceptance criteria |
| **Requirement quality** | Vague or weak wording; formulations that are hard to verify objectively |
| **Numbers & units** | Presence of numerical characteristics; measurement-unit signals with an SI-oriented posture |
| **References** | References to figures, tables, and appendices |
| **Consistency** | Terminology vs canonical glossary-style terms; duplicate or near-duplicate formulations |

All checks are **heuristic and dictionary-driven**. They flag **likely** problems and gaps; they do not prove universal GOST compliance.

---

## 📂 Project structure

```text
gost-ts-analyzer/
├── backend/app/
│   ├── main.py              # FastAPI app, routes, orchestration
│   ├── docx_extraction.py   # DOCX text extraction
│   ├── pdf_extraction.py    # PDF text extraction
│   ├── text_normalizer.py   # Normalization
│   ├── document_unifier.py  # Unified blocks + full text
│   ├── structure_*.py       # Detection, tree, enrichment
│   ├── checks/              # One module per check family
│   ├── rules/               # Section templates, phrases, glossary data
│   └── reporting/           # Issues, report, DOCX export
├── static/                  # CSS, JavaScript
├── templates/               # index.html
├── tests/                   # pytest suite
├── docs/                    # progress notes, internal specification text
├── uploads/                 # temporary storage (gitignored)
├── start_app.bat            # Windows launcher
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

---

## ▶️ Getting started

### Prerequisites

- **Python 3.10+** and `pip`

### Install and run (any OS)

```bash
cd gost-ts-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/** in a browser.

### Windows quick start

From the project root, run **`start_app.bat`**. It tries **8000**, then **8765**, then **8001–8100** for the first bindable port, starts Uvicorn, polls **`GET /api/health`** via `curl`, then opens the app. Ensure dependencies are installed in `.venv` or `venv` if you use those.

### Example API usage

Health:

```bash
curl -s http://127.0.0.1:8000/api/health
```

Upload (multipart field name **`file`**):

```bash
curl -s -X POST http://127.0.0.1:8000/api/upload -F "file=@path/to/specification.docx"
```

DOCX report export accepts a JSON body matching the structured analysis payload returned by a successful upload (typically replayed from the client after analysis).

### Tests (optional)

```bash
pip install -r requirements-dev.txt pytest
pytest
```

---

## 🌐 Keywords / topics

**GOST**, **technical specification**, **technical assignment**, **document analysis**, **requirements validation**, **requirements quality**, **compliance checking**, **rule-based analysis**, **DOCX**, **PDF**, **text extraction**, **document structure**, **FastAPI**, **Python**, **Uvicorn**, **terminology consistency**, **reference validation**, **structured reporting**, **issue list**, **export JSON CSV DOCX**, **Russian technical documentation**.

---

## 📬 Contact

**Telegram:** [https://t.me/VadikQA](https://t.me/VadikQA)

---

## 📄 License

This project is released under the [MIT License](LICENSE).

---

# GOST TS Analyzer

## 🚀 Описание

**GOST TS Analyzer** — автономный веб-сервис с интерфейсом для анализа технических спецификаций на русском языке в форматах **DOCX** и **PDF**. Сервис извлекает и нормализует текст, восстанавливает упрощённую структуру разделов и выполняет **детерминированные проверки на основе правил**, ориентированные на типичные ожидания к оформлению и содержанию документов в духе ГОСТ. Результат — структурированные замечания с привязкой к фрагментам, уровнем серьёзности и рекомендациями; данные доступны в браузере и экспортируются в **JSON**, **CSV** или компактный отчёт **DOCX**.

---

## ✨ Ключевые возможности

- **Приём DOCX и PDF** с проверкой типа (расширение и MIME); понятные HTTP-ответы при неподдерживаемом формате и ошибках извлечения  
- **Извлечение текста** через `python-docx` и `pypdf`, **нормализация** и **единая внутренняя модель** документа  
- **Конвейер структуры**: заголовки и разделы, дерево, обогащение для всех зависимых проверок  
- **Широкий набор проверок**: структура, обязательные смысловые блоки, качество формулировок требований, числа и единицы, ссылки, терминология, дубликаты формулировок  
- **Единая модель замечаний** и **итоговый объект отчёта** в JSON-ответе API  
- **Веб-интерфейс**: загрузка с прогрессом, раскрывающиеся карточки замечаний, фильтрация по типу, экспорт  
- **Запуск в Windows** (`start_app.bat`): поиск Python/.venv/venv, привязка к **127.0.0.1** на **8000**, иначе **8765**, иначе первый свободный порт **8001–8100**; ожидание `/api/health`; открытие браузера (проверка готовности через `curl`)

---

## 🎯 Зачем это нужно

Технические задания и спецификации часто большие, с неоднородной структурой и формулировками, которые сложно проверить на полноту и однозначность. Ручная ревизия дорогая и субъективная. Инструмент выполняет **воспроизводимые, прозрачные проверки**, чтобы заранее выявлять вероятные пробелы и риски по качеству документа. Он даёт **сигналы соответствия ожиданиям ГОСТ-ориентированного ТЗ**, но **не заменяет** экспертизу и не является сертификацией по конкретной редакции нормативного документа.

---

## 🧠 Как это устроено

1. **Загрузка** — клиент отправляет файл на `POST /api/upload`; сервер временно сохраняет его в `uploads/` (каталог не коммитится).  
2. **Разбор** — для DOCX и PDF текст попадает в унифицированное представление.  
3. **Нормализация** — текст приводится к виду, удобному для сопоставления правилами.  
4. **Структура** — определяются заголовки и разделы, строится обогащённая структура.  
5. **Проверки** — модули читают структуру, полный текст и при необходимости блоки; результаты объединяются в объект `checks`.  
6. **Выдача** — строятся `issues` и `report`, ответ отдаётся JSON-ом для UI и экспорта; DOCX-отчёт собирается повторной отправкой этого JSON на `POST /api/export/report-docx`.

---

## 🏗 Технологический стек

| Область | Технологии |
|---------|------------|
| **Бэкенд** | Python 3.10+, **FastAPI**, Uvicorn |
| **Загрузки** | `python-multipart` |
| **DOCX** | `python-docx` |
| **PDF** | `pypdf` |
| **Анализ** | Модули правил в `backend/app/rules/`, регулярные выражения и эвристики (в зависимостях нет ML-стека) |
| **Структура** | `structure_detector`, `structure_builder`, `structure_enricher` |
| **Фронтенд** | `templates/index.html`, `static/css`, `static/js` (чистый JavaScript) |
| **Сборка** | `pyproject.toml`, `requirements.txt`; для разработки и тестов — `requirements-dev.txt` |

---

## ⚙️ Реализованная функциональность

Опираясь на `docs/progress.md` и текущий код:

- **База проекта** — структура репозитория, приложение FastAPI, зафиксированные зависимости, сценарий локального запуска  
- **Интерфейс** — главная страница, адаптивная вёрстка, блок загрузки, состояния интерфейса, выверенный стиль, доработки под мобильные ширины  
- **API загрузки** — `POST /api/upload` на бэкенде, связка с фронтендом, валидация типа, обработка ошибок  
- **Прогресс** — индикатор, процент, текстовые этапы, устойчивые переходы между этапами  
- **Извлечение** — DOCX, базовое извлечение текста из PDF, нормализация, унифицированный формат  
- **Структура** — распознавание заголовков и разделов, внутреннее представление, обогащение  
- **Данные правил** — шаблоны обязательных разделов, словари расплывчатых и родственных формулировок, глоссарий для терминологии  
- **Проверки** — обязательные разделы, порядок разделов, полнота структуры; назначение/цель; область применения; функциональные требования; сигналы нефункциональных требований (заголовки и фразы в тексте — надёжность, производительность, безопасность, удобство, совместимость и смежные аспекты); критерии приёмки; расплывчатые формулировки; труднопроверяемые утверждения; числовые характеристики; единицы измерения; ссылки на рисунки, таблицы и приложения; согласованность терминологии; дубликаты формулировок  
- **Отчётность** — сериализация списка замечаний, объект итогового отчёта, отображение в UI с фрагментами и различением типов, фильтрация  
- **Экспорт** — JSON и CSV на клиенте по последнему успешному анализу; сборка DOCX на сервере из переданного JSON  
- **Стабилизация** — прогоны DOCX/PDF, дымовые сценарии проверок, ошибки UI, финальная стабилизация  
- **Windows** — `start_app.bat` с проверкой здоровья и открытием браузера  

**Сейчас не реализовано:** аутентификация, постоянное хранилище пользовательских данных, «умное» извлечение из сложной вёрстки PDF, отдельная проверка трассируемости требований к критериям приёмки и другие пункты внутренней спецификации, если они не подключены в `main.py`.

---

## 🔍 Текущие проверки / анализ

Один и тот же набор выполняется для **DOCX и PDF** (`backend/app/main.py`).

| Тема | Содержание |
|------|------------|
| **Структура** | Наличие обязательных разделов; ожидаемый порядок; полнота структуры (с учётом результатов по наличию) |
| **Назначение и область** | Сигналы цели/назначения документа и области применения |
| **Требования** | Функциональные требования; нефункциональные (отдельные заголовки разделов и характерные фразы в тексте); критерии приёмки |
| **Качество требований** | Расплывчатые формулировки; формулировки, которые трудно проверить объективно |
| **Числа и единицы** | Наличие числовых характеристик; сигналы единиц измерения с ориентацией на СИ |
| **Ссылки** | Ссылки на рисунки, таблицы и приложения |
| **Согласованность** | Терминология относительно канонических терминов глоссария; дубликаты и близкие повторы формулировок |

Все проверки **эвристические** и опираются на словари и правила; они указывают на **вероятные** проблемы, а не доказывают полное соответствие ГОСТ во всех случаях.

---

## 📂 Структура проекта

```text
gost-ts-analyzer/
├── backend/app/
│   ├── main.py              # FastAPI, маршруты, оркестрация
│   ├── docx_extraction.py   # Извлечение из DOCX
│   ├── pdf_extraction.py    # Извлечение из PDF
│   ├── text_normalizer.py   # Нормализация
│   ├── document_unifier.py  # Блоки и полный текст
│   ├── structure_*.py       # Детектор, дерево, обогащение
│   ├── checks/              # Отдельные семейства проверок
│   ├── rules/               # Шаблоны разделов, фразы, глоссарий
│   └── reporting/           # Замечания, отчёт, экспорт DOCX
├── static/                  # CSS, JavaScript
├── templates/               # index.html
├── tests/                   # pytest
├── docs/                    # progress, внутренняя спецификация
├── uploads/                 # временные файлы (gitignore)
├── start_app.bat            # Запуск в Windows
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

---

## ▶️ Быстрый старт

### Требования

- **Python 3.10+** и `pip`

### Установка и запуск

```bash
cd gost-ts-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Откройте в браузере **http://127.0.0.1:8000/**.

### Windows

Из корня проекта запустите **`start_app.bat`**. Скрипт пробует **8000**, затем **8765**, затем порты **8001–8100**, поднимает Uvicorn, опрашивает **`GET /api/health`** через `curl` и открывает приложение. Зависимости должны быть установлены в `.venv` или `venv`, если вы их используете.

### Примеры запросов к API

Проверка готовности:

```bash
curl -s http://127.0.0.1:8000/api/health
```

Загрузка (поле multipart — **`file`**):

```bash
curl -s -X POST http://127.0.0.1:8000/api/upload -F "file=@path/to/specification.docx"
```

Экспорт DOCX принимает JSON с полным структурированным результатом анализа (как после успешной загрузки), обычно тот же объект, что держит клиент после анализа.

### Тесты (по желанию)

```bash
pip install -r requirements-dev.txt pytest
pytest
```

---

## 🌐 Ключевые слова / темы

**ГОСТ**, **техническое задание**, **техническая спецификация**, **анализ документов**, **проверка требований**, **качество требований**, **проверка соответствия**, **правила и эвристики**, **DOCX**, **PDF**, **извлечение текста**, **структура документа**, **FastAPI**, **Python**, **Uvicorn**, **согласованность терминологии**, **проверка ссылок**, **структурированный отчёт**, **список замечаний**, **экспорт JSON CSV DOCX**, **русскоязычная техническая документация**.

---

## 📬 Контакты

**Telegram:** [https://t.me/VadikQA](https://t.me/VadikQA)

---

## 📄 Лицензия

Проект распространяется на условиях [лицензии MIT](LICENSE).
