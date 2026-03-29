# GOST TS Analyzer

**GOST TS Analyzer** is a self-contained web application that ingests Russian technical specification documents (DOCX or PDF), extracts and normalizes text, infers a lightweight section structure, and runs a battery of **rule-based compliance and quality checks** aligned with common expectations for GOST-oriented technical specifications. Results are shown in the browser as structured issues with fragments and recommendations, and can be exported as JSON, CSV, or a simple DOCX report.

---

## Key capabilities

- Upload **DOCX** and **PDF** files with type validation and clear error responses  
- **Text extraction** (python-docx / PyPDF) and **normalization** for consistent downstream analysis  
- **Structure detection**: headings, sections, and an enriched internal tree used by checks  
- **Many distinct checks** covering structure, required content signals, wording quality, numbers and units, references, terminology, and duplicate phrasing  
- **Unified issue model** with severity, locations, and recommendations  
- **Web UI**: progress feedback, expandable issue cards, filtering by issue type  
- **Exports**: full analysis JSON (download), issues CSV, DOCX report via server endpoint  
- **Windows one-click launcher** (`start_app.bat`): free port selection, health check, browser open  

---

## Why this project matters

Technical specifications are often long, inconsistent, and hard to review manually. This tool automates **repeatable, deterministic checks** so teams can catch missing sections, weak requirement wording, broken figure/table/appendix references, and terminology drift **before** formal review cycles. It is aimed at **document quality and GOST-related conformance signals**, not at replacing human judgment or legal certification.

---

## Technology stack

| Layer | Technology |
|--------|------------|
| Backend | Python 3.10+, **FastAPI**, Uvicorn |
| Documents | **python-docx**, **pypdf** |
| Analysis | Rule dictionaries, regex, heuristics (no heavy ML stack in dependencies) |
| Frontend | HTML, CSS, vanilla JavaScript |
| Packaging | `pyproject.toml` + `requirements.txt` |

---

## Architecture overview

```text
Browser (static JS + templates)
        │  HTTP
        ▼
FastAPI (`backend.app.main`)
        │  upload → extract → normalize → unify blocks
        ▼
Structure pipeline (`structure_detector`, `structure_builder`, `structure_enricher`)
        │
        ▼
Check modules (`backend.app.checks.*`) + rules data (`backend.app.rules.*`)
        │
        ▼
Reporting (`issues_builder`, `report_builder`, optional `docx_report_export`)
        │
        ▼
JSON response: extraction, structure, checks, issues, report
```

The primary analysis entry point is **`POST /api/upload`**, which returns a single structured payload consumed by the UI and export actions.

---

## Implemented functionality

- **HTTP API**: `GET /` (main page), `GET /api/health`, `POST /api/upload`, `POST /api/export/report-docx`  
- **DOCX/PDF ingestion** with unsupported-type handling and extraction error responses  
- **Section and heading logic** feeding all structure-dependent checks  
- **Issue aggregation** and a human-oriented **report** object in the API response  
- **Client-side** JSON and CSV generation from the last successful analysis; **server-side** minimal DOCX report build from posted JSON  

---

## Analysis checks currently available

The following checks are wired in `backend.app.main` for both DOCX and PDF pipelines (same set):

| Area | Check focus |
|------|-------------|
| Structure | Required sections presence, expected section order, structure completeness |
| Content signals | Purpose / goal, scope, functional requirements, non-functional requirements (headings and phrase signals for reliability, performance, security, usability, compatibility, etc.), acceptance criteria |
| Requirement quality | Vague wording, hard-to-verify formulations |
| Metrics | Numerical characteristics presence, measurement units (SI-oriented signals) |
| References | Figure, table, and appendix references |
| Consistency | Terminology vs glossary-style canonical terms, duplicate or near-duplicate formulations |

Checks are **heuristic and dictionary-driven**; they flag likely problems and gaps rather than proving full standard compliance in every jurisdiction or edition.

---

## Project structure

```text
gost-ts-analyzer/
├── backend/app/           # FastAPI app, extraction, normalization, structure, checks, rules, reporting
│   ├── checks/            # Individual check implementations
│   ├── rules/             # Section templates, phrases, glossary data
│   └── reporting/       # Issues, report, DOCX export
├── static/                # CSS and JavaScript
├── templates/             # index.html
├── tests/                 # Pytest suite
├── docs/                  # Internal progress notes and specification notes
├── start_app.bat          # Windows launcher
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Dev/test extras
├── pyproject.toml         # Project metadata and dependency list
└── README.md
```

---

## How to run locally

### Prerequisites

- **Python 3.10+**  
- `pip`  

### Install and start (any OS)

```bash
cd gost-ts-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in a browser.

### Windows quick start

Double-click or run **`start_app.bat`** from the project root. It picks a free port (8000–8100), starts Uvicorn, waits for **`/api/health`**, and opens the app. **curl** must be available (included on recent Windows 10/11).

### Run tests (optional)

```bash
pip install -r requirements-dev.txt
pytest
```

---

## API notes

- **`POST /api/upload`** — multipart file field `file`; response includes `extraction`, `structure`, `checks`, `issues`, and `report` on success.  
- **`GET /api/health`** — `{"status": "ok"}`.  
- **`POST /api/export/report-docx`** — JSON body shaped like the client-held analysis payload; returns a DOCX download.  

Uploaded files are stored under **`uploads/`** during processing; this directory is **gitignored** and should not be committed.

---

## Interface notes

- Upload with visual progress and stage text  
- Results as **cards** with expand/collapse for full messages and fragments  
- **Filtering** by issue category/type  
- **Export** buttons for JSON, CSV, and DOCX (DOCX uses the export API)  

---

## Possible future improvements

Grounded extensions only; none of these are required for the current codebase to run.

- Richer PDF layout-aware extraction where needed  
- Additional languages or document profiles beyond the current Russian TS focus  
- Persistent storage and user accounts (not present today)  
- Optional CI workflow if the maintainers want automated tests on every push  
- Optional hardening of deployment and configuration (reverse proxy, limits) for multi-user hosting  

---

## Keywords / topics

**GOST document analysis**, **technical specification analyzer**, **requirements analysis**, **compliance checking**, **document validation**, **DOCX and PDF analysis**, **FastAPI**, **Python**, **rule-based NLP**, **requirement quality**, **Russian technical documentation**, **structured reporting**, **issue tracking**, **terminology consistency**, **reference validation**.

Suggested **GitHub topics**: `gost`, `gost-analyzer`, `technical-specification`, `requirements-analysis`, `compliance-checking`, `document-analysis`, `fastapi`, `python`, `docx`, `pdf`, `validation`, `nlp`.

---

## Contact

- **Telegram**: [https://t.me/VadikQA](https://t.me/VadikQA)

---

## License

This project is released under the [MIT License](LICENSE).

---

---

# GOST TS Analyzer — русская версия

**GOST TS Analyzer** — это автономное веб-приложение для загрузки технических заданий и спецификаций в форматах **DOCX** и **PDF**, извлечения и нормализации текста, построения упрощённой структуры разделов и выполнения **набора детерминированных проверок** на соответствие распространённым ожиданиям к оформлению и содержанию документов в духе требований ГОСТ. Результаты отображаются в браузере в виде структурированных замечаний с фрагментами и рекомендациями; доступен экспорт в **JSON**, **CSV** и упрощённый **DOCX**.

---

## Ключевые возможности

- Загрузка **DOCX** и **PDF** с проверкой типа и понятными ответами об ошибках  
- **Извлечение текста** (python-docx / PyPDF) и **нормализация**  
- **Определение структуры**: заголовки, разделы, внутреннее дерево для проверок  
- **Множество отдельных проверок**: структура, обязательные смысловые блоки, качество формулировок, числа и единицы, ссылки, терминология, дубликаты формулировок  
- **Единая модель замечаний** с серьёзностью, привязкой к фрагментам и рекомендациями  
- **Веб-интерфейс**: прогресс, карточки замечаний с раскрытием, фильтрация  
- **Экспорт**: JSON и CSV на стороне клиента; DOCX через серверный endpoint  
- **Запуск одним кликом в Windows** (`start_app.bat`): свободный порт, health-check, открытие браузера  

---

## Зачем это нужно

Технические спецификации часто объёмны и неоднородны; ручная вычитка отнимает время и даёт расхождения между ревьюерами. Инструмент выполняет **повторяемые проверки**: пропущенные разделы, слабые формулировки требований, некорректные ссылки на рисунки, таблицы и приложения, расхождения терминологии. Он помогает **повысить качество документа** и выявить типичные несоответствия ожиданиям ГОСТ-ориентированного ТЗ, **не заменяя** экспертизу и официальное согласование.

---

## Технологический стек

| Уровень | Технологии |
|--------|------------|
| Бэкенд | Python 3.10+, **FastAPI**, Uvicorn |
| Документы | **python-docx**, **pypdf** |
| Анализ | Правила, словари, эвристики и регулярные выражения (без тяжёлых ML-библиотек в зависимостях) |
| Фронтенд | HTML, CSS, чистый JavaScript |
| Сборка | `pyproject.toml`, `requirements.txt` |

---

## Архитектура (кратко)

```text
Браузер (шаблоны + статический JS)
        │  HTTP
        ▼
FastAPI (`backend.app.main`)
        │  загрузка → извлечение → нормализация → единые блоки
        ▼
Конвейер структуры (detector → builder → enricher)
        ▼
Модули проверок (`backend.app.checks.*`) + данные правил (`backend.app.rules.*`)
        ▼
Отчётность (issues, report, экспорт DOCX)
        ▼
JSON: extraction, structure, checks, issues, report
```

Основная точка анализа — **`POST /api/upload`**; ответ целиком используется UI и экспортом.

---

## Что уже реализовано

- **API**: главная страница, health, загрузка файла, экспорт отчёта DOCX  
- Приём **DOCX/PDF**, обработка ошибок типа и извлечения  
- Логика **разделов и заголовков** для всех зависимых проверок  
- **Сборка замечаний** и **итогового отчёта** в теле ответа  
- **Клиентский** экспорт JSON/CSV; **серверная** сборка минимального DOCX из JSON  

---

## Доступные проверки

Один и тот же набор подключается в `main.py` для DOCX и PDF:

| Область | Содержание проверки |
|--------|---------------------|
| Структура | Наличие обязательных разделов, порядок разделов, полнота структуры |
| Содержание | Назначение/цель, область применения, функциональные требования, нефункциональные требования (заголовки и текстовые сигналы: надёжность, производительность, безопасность, удобство, совместимость и т.д.), критерии приёмки |
| Качество требований | Расплывчатые формулировки, труднопроверяемые утверждения |
| Метрики | Наличие числовых характеристик, единицы измерения (ориентация на СИ) |
| Ссылки | Ссылки на рисунки, таблицы, приложения |
| Согласованность | Терминология относительно канонического глоссария, дубликаты формулировок |

Проверки **эвристические**; они указывают на вероятные пробелы и риски, а не сертифицируют документ по конкретной редакции стандарта.

---

## Структура проекта

См. англоязычный раздел [Project structure](#project-structure) — дерево каталогов идентично.

---

## Локальный запуск

### Требования

- **Python 3.10+**  
- `pip`  

### Установка и старт

```bash
cd gost-ts-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Откройте **http://127.0.0.1:8000**.

### Windows: `start_app.bat`

Запуск из корня проекта: выбор свободного порта, старт Uvicorn, ожидание **`/api/health`**, открытие браузера. Нужен **curl** (в современных Windows обычно уже есть).

### Тесты

```bash
pip install -r requirements-dev.txt
pytest
```

---

## API (кратко)

- **`POST /api/upload`** — поле `file` (multipart); при успехе: `extraction`, `structure`, `checks`, `issues`, `report`.  
- **`GET /api/health`** — проверка готовности сервиса.  
- **`POST /api/export/report-docx`** — JSON с полным результатом анализа; ответ — файл DOCX.  

Файлы сохраняются в **`uploads/`** на время обработки; каталог **не коммитится** (см. `.gitignore`).

---

## Интерфейс

- Загрузка с индикацией прогресса  
- Карточки замечаний с раскрытием полного текста  
- Фильтрация по типу замечания  
- Кнопки экспорта JSON, CSV, DOCX  

---

## Возможное развитие

Только реалистичные направления; в коде этого нет и не требуется для работы.

- Более точное извлечение из сложных PDF  
- Другие типы документов или языки  
- Учётные записи и хранилище (сейчас отсутствуют)  
- CI по желанию мейнтейнеров  
- Усиление конфигурации для публичного хостинга (лимиты, reverse proxy) при необходимости  

---

## Ключевые слова / темы

**Анализ документов ГОСТ**, **анализатор технического задания**, **анализ требований**, **проверка соответствия**, **валидация документов**, **DOCX и PDF**, **FastAPI**, **Python**, **правила и эвристики**, **качество требований**, **техническая документация на русском**, **структурированный отчёт**, **терминология**, **проверка ссылок**.

Рекомендуемые **топики GitHub**: `gost`, `gost-analyzer`, `technical-specification`, `requirements-analysis`, `compliance-checking`, `document-analysis`, `fastapi`, `python`, `docx`, `pdf`, `validation`, `nlp`.

---

## Контакты

- **Telegram**: [https://t.me/VadikQA](https://t.me/VadikQA)

---

## Лицензия

Проект распространяется на условиях [лицензии MIT](LICENSE).
