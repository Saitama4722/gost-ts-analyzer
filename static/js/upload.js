(function () {
  const fileInput = document.getElementById("ts-document-file");
  const submitBtn = document.getElementById("ts-upload-submit");
  const feedback = document.getElementById("upload-feedback");
  const selectedName = document.getElementById("upload-selected-name");
  const errorDetail = document.getElementById("interface-error-detail");

  const MSG_UNSUPPORTED_TYPE =
    "Формат файла не поддерживается. Загрузите документ в формате DOCX или PDF.";

  const MSG_NETWORK =
    "Не удалось завершить загрузку: сервер недоступен или соединение прервано. Проверьте сеть и повторите попытку.";

  const MSG_UNEXPECTED_RESPONSE =
    "Сервер вернул неожиданный ответ. Повторите попытку или обновите страницу.";

  if (!fileInput || !submitBtn) {
    return;
  }

  const stateEls = {
    idle: document.getElementById("interface-state-idle"),
    uploading: document.getElementById("interface-state-uploading"),
    analyzing: document.getElementById("interface-state-analyzing"),
    result: document.getElementById("interface-state-result"),
    error: document.getElementById("interface-state-error"),
  };

  const analysisSummaryEl = document.getElementById("analysis-result-summary");
  const analysisIssuesWrap = document.getElementById("analysis-issues-wrap");
  const analysisIssuesList = document.getElementById("analysis-issues-list");
  const analysisIssuesEmpty = document.getElementById("analysis-issues-empty");
  const filterTypeSelect = document.getElementById("analysis-filter-check-type");
  const filterSeveritySelect = document.getElementById("analysis-filter-severity");
  const filterResetBtn = document.getElementById("analysis-filter-reset");
  const filterEmptyMsg = document.getElementById("analysis-issues-filter-empty");
  const analysisExportWrap = document.getElementById("analysis-export-wrap");
  const analysisExportJsonBtn = document.getElementById("analysis-export-json");
  const analysisExportCsvBtn = document.getElementById("analysis-export-csv");
  const analysisExportDocxBtn = document.getElementById("analysis-export-docx");

  /** Полный структурированный ответ последнего успешного анализа (экспорт JSON, CSV, DOCX). */
  let lastStructuredAnalysisPayload = null;

  /** Внутренние значения для фильтрации при отсутствии поля в данных ответа. */
  const FILTER_CHECK_UNSET = "__filter_check_unset__";
  const FILTER_SEVERITY_UNSET = "__filter_severity_unset__";

  /** Подписи серьёзности для интерфейса (значения с сервера — латиница). */
  const SEVERITY_LABEL_RU = {
    critical: "Критично",
    warning: "Предупреждение",
    recommendation: "Рекомендация",
  };

  /** Короткие подписи типа проверки для интерфейса (ключи — как в API). */
  const CHECK_KEY_LABEL_RU = {
    vague_wording_check: "Неконкретные формулировки",
    unverifiable_requirements_check: "Проверяемость требований",
    figure_references_check: "Ссылки на рисунки",
    terminology_consistency_check: "Согласованность терминов",
    duplicate_formulations_check: "Повторы формулировок",
  };

  function clearAnalysisFilterControls() {
    if (filterEmptyMsg) {
      filterEmptyMsg.hidden = true;
    }
    if (filterTypeSelect) {
      filterTypeSelect.replaceChildren();
      const allTypes = document.createElement("option");
      allTypes.value = "";
      allTypes.textContent = "Все типы";
      filterTypeSelect.appendChild(allTypes);
    }
    if (filterSeveritySelect) {
      filterSeveritySelect.replaceChildren();
      const allSev = document.createElement("option");
      allSev.value = "";
      allSev.textContent = "Все уровни";
      filterSeveritySelect.appendChild(allSev);
    }
  }

  function clearStructuredAnalysisExportState() {
    lastStructuredAnalysisPayload = null;
    if (analysisExportWrap) {
      analysisExportWrap.hidden = true;
    }
    if (analysisExportJsonBtn) {
      analysisExportJsonBtn.disabled = false;
    }
    if (analysisExportCsvBtn) {
      analysisExportCsvBtn.disabled = false;
    }
    if (analysisExportDocxBtn) {
      analysisExportDocxBtn.disabled = false;
    }
  }

  function clearAnalysisResults() {
    clearStructuredAnalysisExportState();
    if (analysisSummaryEl) {
      analysisSummaryEl.textContent = "";
    }
    if (analysisIssuesList) {
      analysisIssuesList.replaceChildren();
      analysisIssuesList.hidden = false;
    }
    clearAnalysisFilterControls();
    if (analysisIssuesWrap) {
      analysisIssuesWrap.hidden = true;
    }
    if (analysisIssuesEmpty) {
      analysisIssuesEmpty.hidden = true;
    }
  }

  function cloneForJsonExport(value) {
    if (typeof structuredClone === "function") {
      try {
        return structuredClone(value);
      } catch {
        /* fall through */
      }
    }
    return JSON.parse(JSON.stringify(value));
  }

  /** Безопасное имя без расширения для экспорта (общая логика JSON / CSV / DOCX). */
  function safeExportFilenameStem(originalFilename) {
    const raw =
      typeof originalFilename === "string" && originalFilename.trim()
        ? originalFilename.trim()
        : "document";
    const base = raw.replace(/^[\\/]+/, "").split(/[/\\]/).pop() || "document";
    const dot = base.lastIndexOf(".");
    const stem = dot > 0 ? base.slice(0, dot) : base;
    const cleaned = stem
      .replace(/[\u0000-\u001f<>:"/\\|?*]+/g, "_")
      .replace(/^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)/i, "_$1")
      .trim();
    return cleaned.slice(0, 120) || "document";
  }

  function safeJsonReportFilename(originalFilename) {
    return safeExportFilenameStem(originalFilename) + "-report.json";
  }

  function safeIssuesCsvFilename(originalFilename) {
    return safeExportFilenameStem(originalFilename) + "-issues.csv";
  }

  function safeDocxReportFilename(originalFilename) {
    return safeExportFilenameStem(originalFilename) + "-report.docx";
  }

  function updateAnalysisExportAvailability() {
    const hasPayload =
      lastStructuredAnalysisPayload !== null &&
      typeof lastStructuredAnalysisPayload === "object";
    if (analysisExportWrap) {
      analysisExportWrap.hidden = !hasPayload;
    }
    if (analysisExportJsonBtn) {
      analysisExportJsonBtn.disabled = !hasPayload;
    }
    if (analysisExportCsvBtn) {
      analysisExportCsvBtn.disabled = !hasPayload;
    }
    if (analysisExportDocxBtn) {
      analysisExportDocxBtn.disabled = !hasPayload;
    }
  }

  function rememberStructuredAnalysisForExport(data) {
    if (!data || typeof data !== "object") {
      return;
    }
    try {
      lastStructuredAnalysisPayload = cloneForJsonExport(data);
    } catch {
      lastStructuredAnalysisPayload = null;
    }
    updateAnalysisExportAvailability();
  }

  function downloadAnalysisJson() {
    if (!lastStructuredAnalysisPayload) {
      return;
    }
    const nameHint =
      typeof lastStructuredAnalysisPayload.filename === "string"
        ? lastStructuredAnalysisPayload.filename
        : "";
    const filename = safeJsonReportFilename(nameHint);
    let jsonText;
    try {
      jsonText = JSON.stringify(lastStructuredAnalysisPayload, null, 2);
    } catch {
      return;
    }
    const blob = new Blob([jsonText], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 0);
  }

  async function downloadAnalysisDocx() {
    if (!lastStructuredAnalysisPayload || !analysisExportDocxBtn) {
      return;
    }
    const nameHint =
      typeof lastStructuredAnalysisPayload.filename === "string"
        ? lastStructuredAnalysisPayload.filename
        : "";
    const filename = safeDocxReportFilename(nameHint);
    analysisExportDocxBtn.disabled = true;
    let response;
    try {
      response = await fetch("/api/export/report-docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lastStructuredAnalysisPayload),
      });
    } catch {
      analysisExportDocxBtn.disabled = false;
      updateAnalysisExportAvailability();
      return;
    }
    if (!response.ok) {
      analysisExportDocxBtn.disabled = false;
      updateAnalysisExportAvailability();
      return;
    }
    let blob;
    try {
      blob = await response.blob();
    } catch {
      analysisExportDocxBtn.disabled = false;
      updateAnalysisExportAvailability();
      return;
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 0);
    analysisExportDocxBtn.disabled = false;
    updateAnalysisExportAvailability();
  }

  /** RFC 4180: экранирование поля CSV (запятые, кавычки, переводы строк). */
  function escapeCsvField(value) {
    if (value === null || value === undefined) {
      return "";
    }
    const s = String(value);
    if (/[",\r\n]/.test(s)) {
      return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  }

  function csvRowFromValues(values) {
    return values.map(escapeCsvField).join(",");
  }

  /**
   * Текст CSV по полному ответу анализа: все замечания из issues (без учёта фильтра UI).
   * Строка заголовка + по строке на замечание; UTF-8, BOM для совместимости с Excel.
   */
  function buildIssuesCsvTextFromPayload(payload) {
    const issues = issuesFromUploadResponse(payload);
    const header = [
      "index",
      "severity",
      "check_key",
      "issue_code",
      "message",
      "section_title",
      "fragment_text",
      "recommendation",
      "category",
    ];
    const lines = [csvRowFromValues(header)];
    issues.forEach(function (issue, i) {
      const meta = issue.metadata;
      const category =
        meta && typeof meta === "object"
          ? nonEmptyString(meta.category)
          : "";
      const severity =
        issue.severity !== null && issue.severity !== undefined
          ? String(issue.severity).trim()
          : "";
      lines.push(
        csvRowFromValues([
          String(i + 1),
          severity,
          nonEmptyString(issue.check_key),
          nonEmptyString(issue.issue_code),
          issue.message != null ? String(issue.message) : "",
          issue.section_title != null ? String(issue.section_title) : "",
          issueFragmentPlainText(issue),
          issue.recommendation != null ? String(issue.recommendation) : "",
          category,
        ])
      );
    });
    return lines.join("\r\n");
  }

  function downloadAnalysisCsv() {
    if (!lastStructuredAnalysisPayload) {
      return;
    }
    const nameHint =
      typeof lastStructuredAnalysisPayload.filename === "string"
        ? lastStructuredAnalysisPayload.filename
        : "";
    const filename = safeIssuesCsvFilename(nameHint);
    let csvText;
    try {
      csvText = buildIssuesCsvTextFromPayload(lastStructuredAnalysisPayload);
    } catch {
      return;
    }
    const blob = new Blob(["\uFEFF" + csvText], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 0);
  }

  function nonEmptyString(value) {
    if (value === null || value === undefined) {
      return "";
    }
    const s = String(value).trim();
    return s;
  }

  function issuesFromUploadResponse(data) {
    if (!data || typeof data !== "object") {
      return [];
    }
    if (Array.isArray(data.issues)) {
      return data.issues.filter(function (x) {
        return x && typeof x === "object";
      });
    }
    const fromReport = data.report && data.report.issues;
    if (Array.isArray(fromReport)) {
      return fromReport.filter(function (x) {
        return x && typeof x === "object";
      });
    }
    return [];
  }

  function summaryConclusionFromResponse(data) {
    if (!data || typeof data !== "object") {
      return "";
    }
    const s =
      data.report &&
      data.report.summary &&
      data.report.summary.conclusion;
    return nonEmptyString(s);
  }

  function severityChipClass(severity) {
    const s = nonEmptyString(severity);
    if (s === "critical" || s === "warning" || s === "recommendation") {
      return "analysis-issue__chip--" + s;
    }
    return "";
  }

  /** Допустимые значения серьёзности для атрибутов карточки (как в API). */
  function normalizedSeverityForCard(severity) {
    const s = nonEmptyString(severity);
    if (s === "critical" || s === "warning" || s === "recommendation") {
      return s;
    }
    return "";
  }

  /**
   * Атрибуты карточки для спокойной визуальной дифференциации.
   * Основная ось — тип проверки (check_key из белого списка подписей);
   * при неизвестном check_key — запасной вариант по severity.
   */
  function applyIssueCardVisualAttrs(li, issue) {
    if (!li || !issue || typeof issue !== "object") {
      return;
    }
    const ck = nonEmptyString(issue.check_key);
    const sev = normalizedSeverityForCard(issue.severity);

    if (ck && Object.prototype.hasOwnProperty.call(CHECK_KEY_LABEL_RU, ck)) {
      li.setAttribute("data-check-key", ck);
    } else if (sev) {
      li.setAttribute("data-severity", sev);
    }
  }

  function filterCheckValueForIssue(issue) {
    const ck = nonEmptyString(issue.check_key);
    return ck || FILTER_CHECK_UNSET;
  }

  function filterSeverityValueForIssue(issue) {
    const s = nonEmptyString(issue.severity);
    return s || FILTER_SEVERITY_UNSET;
  }

  /** Стабильные значения для фильтрации (не зависят от порядка узлов в DOM). */
  function setIssueRowFilterAttrs(li, issue) {
    if (!li || !issue || typeof issue !== "object") {
      return;
    }
    li.dataset.filterCheckKey = filterCheckValueForIssue(issue);
    li.dataset.filterSeverity = filterSeverityValueForIssue(issue);
  }

  function uniqueSortedStrings(values) {
    const seen = {};
    values.forEach(function (v) {
      seen[v] = true;
    });
    return Object.keys(seen).sort(function (a, b) {
      return a.localeCompare(b);
    });
  }

  function unmappedOrdinalMap(unmappedList) {
    const ord = {};
    unmappedList.forEach(function (v, i) {
      ord[v] = i + 1;
    });
    return ord;
  }

  function labelForFilterCheckKey(ck, ordinalByKey, severalUnmapped) {
    if (ck === FILTER_CHECK_UNSET) {
      return "Тип не указан";
    }
    if (Object.prototype.hasOwnProperty.call(CHECK_KEY_LABEL_RU, ck)) {
      return CHECK_KEY_LABEL_RU[ck];
    }
    const n = ordinalByKey[ck];
    if (severalUnmapped && n) {
      return "Иной тип проверки №" + n;
    }
    return "Иной тип проверки";
  }

  function labelForFilterSeverity(sv, ordinalByKey, severalUnmapped) {
    if (sv === FILTER_SEVERITY_UNSET) {
      return "Серьёзность не указана";
    }
    if (SEVERITY_LABEL_RU[sv]) {
      return SEVERITY_LABEL_RU[sv];
    }
    const n = ordinalByKey[sv];
    if (severalUnmapped && n) {
      return "Иная серьёзность №" + n;
    }
    return "Иная серьёзность";
  }

  function fillFilterSelect(selectEl, values, labelForValue, allOptionText) {
    if (!selectEl) {
      return;
    }
    selectEl.replaceChildren();
    const allOpt = document.createElement("option");
    allOpt.value = "";
    allOpt.textContent = allOptionText;
    selectEl.appendChild(allOpt);
    values.forEach(function (v) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = labelForValue(v);
      selectEl.appendChild(opt);
    });
    selectEl.value = "";
  }

  function rebuildIssueFilterOptions(issues) {
    if (!filterTypeSelect || !filterSeveritySelect) {
      return;
    }
    const checkVals = issues.map(filterCheckValueForIssue);
    const sevVals = issues.map(filterSeverityValueForIssue);
    const uniqueChecks = uniqueSortedStrings(checkVals);
    const uniqueSevs = uniqueSortedStrings(sevVals);

    const unmappedChecks = uniqueChecks.filter(function (v) {
      return (
        v !== FILTER_CHECK_UNSET &&
        !Object.prototype.hasOwnProperty.call(CHECK_KEY_LABEL_RU, v)
      );
    });
    const checkOrd = unmappedOrdinalMap(unmappedChecks);
    const severalUnmappedChecks = unmappedChecks.length > 1;

    const unmappedSevs = uniqueSevs.filter(function (v) {
      return (
        v !== FILTER_SEVERITY_UNSET &&
        !Object.prototype.hasOwnProperty.call(SEVERITY_LABEL_RU, v)
      );
    });
    const sevOrd = unmappedOrdinalMap(unmappedSevs);
    const severalUnmappedSevs = unmappedSevs.length > 1;

    fillFilterSelect(
      filterTypeSelect,
      uniqueChecks,
      function (v) {
        return labelForFilterCheckKey(v, checkOrd, severalUnmappedChecks);
      },
      "Все типы"
    );
    fillFilterSelect(
      filterSeveritySelect,
      uniqueSevs,
      function (v) {
        return labelForFilterSeverity(v, sevOrd, severalUnmappedSevs);
      },
      "Все уровни"
    );
  }

  function applyIssueListFilter() {
    if (!analysisIssuesList) {
      return;
    }
    const typeVal = filterTypeSelect ? filterTypeSelect.value : "";
    const sevVal = filterSeveritySelect ? filterSeveritySelect.value : "";
    const items = analysisIssuesList.querySelectorAll(".analysis-issue");
    let visible = 0;
    items.forEach(function (li) {
      const matchType =
        typeVal === "" || li.dataset.filterCheckKey === typeVal;
      const matchSev =
        sevVal === "" || li.dataset.filterSeverity === sevVal;
      const show = matchType && matchSev;
      li.hidden = !show;
      if (show) {
        visible += 1;
      }
    });
    const noMatches = items.length > 0 && visible === 0;
    if (filterEmptyMsg) {
      filterEmptyMsg.hidden = !noMatches;
    }
    if (analysisIssuesList) {
      analysisIssuesList.hidden = noMatches;
    }
  }

  function resetIssueFilters() {
    if (filterTypeSelect) {
      filterTypeSelect.value = "";
    }
    if (filterSeveritySelect) {
      filterSeveritySelect.value = "";
    }
    applyIssueListFilter();
  }

  function appendChipRow(row, text, extraClass) {
    const chip = document.createElement("span");
    chip.className = "analysis-issue__chip" + (extraClass ? " " + extraClass : "");
    chip.textContent = text;
    row.appendChild(chip);
  }

  function appendLabeledBlock(parent, labelText, bodyText, bodyClass) {
    const p = document.createElement("p");
    p.className = "analysis-issue__detail";
    const label = document.createElement("span");
    label.className = "analysis-issue__detail-label";
    label.textContent = labelText;
    p.appendChild(label);
    p.appendChild(document.createTextNode(" "));
    const body = document.createElement("span");
    body.className = bodyClass || "";
    body.textContent = bodyText;
    p.appendChild(body);
    parent.appendChild(p);
  }

  /** Текст фрагмента из полей ответа API (без HTML). */
  function issueFragmentPlainText(issue) {
    if (!issue || typeof issue !== "object") {
      return "";
    }
    let s = nonEmptyString(issue.fragment_text);
    if (s) {
      return s;
    }
    s = nonEmptyString(issue.excerpt);
    if (s) {
      return s;
    }
    const meta = issue.metadata;
    if (meta && typeof meta === "object") {
      const src = meta.source;
      if (src && typeof src === "object") {
        s = nonEmptyString(src.text_excerpt);
        if (s) {
          return s;
        }
      }
      s = nonEmptyString(meta.text_excerpt);
      if (s) {
        return s;
      }
    }
    return "";
  }

  function appendFragmentBlock(parent, fragmentText) {
    const wrap = document.createElement("div");
    wrap.className = "analysis-issue__fragment-wrap";
    const labelEl = document.createElement("div");
    labelEl.className = "analysis-issue__fragment-label";
    labelEl.textContent = "Фрагмент";
    const body = document.createElement("div");
    body.className = "analysis-issue__fragment";
    body.setAttribute("role", "note");
    body.textContent = fragmentText;
    wrap.appendChild(labelEl);
    wrap.appendChild(body);
    parent.appendChild(wrap);
  }

  function syncAnalysisIssueCardExpandedState(li, expanded) {
    const summaryBtn = li.querySelector(".analysis-issue__summary");
    const details = li.querySelector(".analysis-issue__details");
    const hint = summaryBtn && summaryBtn.querySelector(".analysis-issue__toggle-text");
    if (!summaryBtn || !details) {
      return;
    }
    details.hidden = !expanded;
    summaryBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
    if (hint) {
      hint.textContent = expanded ? "Свернуть" : "Показать полностью";
    }
    li.classList.toggle("analysis-issue--expanded", expanded);
  }

  function toggleAnalysisIssueCardFromSummary(summaryBtn) {
    const li = summaryBtn.closest(".analysis-issue");
    if (!li || !analysisIssuesList || !analysisIssuesList.contains(li)) {
      return;
    }
    const details = li.querySelector(".analysis-issue__details");
    if (!details) {
      return;
    }
    syncAnalysisIssueCardExpandedState(li, details.hidden);
  }

  function renderAnalysisResults(data) {
    clearAnalysisResults();
    const issues = issuesFromUploadResponse(data);
    const conclusion = summaryConclusionFromResponse(data);

    if (analysisSummaryEl) {
      analysisSummaryEl.textContent =
        conclusion ||
        (issues.length
          ? "Проверка завершена. Ниже перечислены выявленные замечания."
          : "Проверка завершена. Замечаний по поддерживаемым проверкам не обнаружено.");
    }

    if (issues.length === 0) {
      if (analysisIssuesEmpty) {
        analysisIssuesEmpty.hidden = Boolean(conclusion);
      }
      rememberStructuredAnalysisForExport(data);
      return;
    }

    if (analysisIssuesWrap) {
      analysisIssuesWrap.hidden = false;
    }

    if (!analysisIssuesList) {
      rememberStructuredAnalysisForExport(data);
      return;
    }

    issues.forEach(function (issue, idx) {
      const li = document.createElement("li");
      li.className = "analysis-issue";
      applyIssueCardVisualAttrs(li, issue);
      setIssueRowFilterAttrs(li, issue);

      const uid = "analysis-issue-" + idx;
      const summaryId = uid + "-summary";
      const detailsId = uid + "-details";

      const summaryBtn = document.createElement("button");
      summaryBtn.type = "button";
      summaryBtn.className = "analysis-issue__summary";
      summaryBtn.id = summaryId;
      summaryBtn.setAttribute("aria-expanded", "false");
      summaryBtn.setAttribute("aria-controls", detailsId);

      const summaryInner = document.createElement("span");
      summaryInner.className = "analysis-issue__summary-inner";

      const summaryMain = document.createElement("span");
      summaryMain.className = "analysis-issue__summary-main";

      const meta = document.createElement("div");
      meta.className = "analysis-issue__meta";

      const sev = nonEmptyString(issue.severity);
      if (sev && SEVERITY_LABEL_RU[sev]) {
        appendChipRow(meta, SEVERITY_LABEL_RU[sev], severityChipClass(sev));
      }

      const ck = nonEmptyString(issue.check_key);
      if (ck && Object.prototype.hasOwnProperty.call(CHECK_KEY_LABEL_RU, ck)) {
        appendChipRow(meta, CHECK_KEY_LABEL_RU[ck], "");
      }

      const metaObj = issue.metadata;
      const category =
        metaObj &&
        typeof metaObj === "object" &&
        nonEmptyString(metaObj.category);
      if (category) {
        appendChipRow(meta, category, "");
      }

      if (meta.childNodes.length) {
        summaryMain.appendChild(meta);
      }

      const msg = nonEmptyString(issue.message);
      const fullMessageText = msg || "Замечание без текста описания.";
      const previewEl = document.createElement("p");
      previewEl.className = "analysis-issue__preview";
      previewEl.textContent = fullMessageText;
      summaryMain.appendChild(previewEl);

      const summaryAside = document.createElement("span");
      summaryAside.className = "analysis-issue__summary-aside";
      const chevronEl = document.createElement("span");
      chevronEl.className = "analysis-issue__chevron";
      chevronEl.setAttribute("aria-hidden", "true");
      const toggleHint = document.createElement("span");
      toggleHint.className = "analysis-issue__toggle-text";
      toggleHint.textContent = "Показать полностью";
      summaryAside.appendChild(chevronEl);
      summaryAside.appendChild(toggleHint);

      summaryInner.appendChild(summaryMain);
      summaryInner.appendChild(summaryAside);
      summaryBtn.appendChild(summaryInner);

      const details = document.createElement("div");
      details.className = "analysis-issue__details";
      details.id = detailsId;
      details.setAttribute("role", "region");
      details.setAttribute("aria-labelledby", summaryId);
      details.hidden = true;

      const messageEl = document.createElement("p");
      messageEl.className = "analysis-issue__message";
      messageEl.textContent = fullMessageText;
      details.appendChild(messageEl);

      const issueCode = nonEmptyString(issue.issue_code);
      if (issueCode) {
        appendLabeledBlock(details, "Код:", issueCode, "");
      }

      const sectionTitle = nonEmptyString(issue.section_title);
      if (sectionTitle) {
        appendLabeledBlock(details, "Раздел:", sectionTitle, "");
      }

      const fragment = issueFragmentPlainText(issue);
      if (fragment) {
        appendFragmentBlock(details, fragment);
      }

      const rec = nonEmptyString(issue.recommendation);
      if (rec) {
        const recP = document.createElement("p");
        recP.className = "analysis-issue__recommendation";
        const recLabel = document.createElement("span");
        recLabel.className = "analysis-issue__detail-label";
        recLabel.textContent = "Рекомендация:";
        recP.appendChild(recLabel);
        recP.appendChild(document.createTextNode(" "));
        recP.appendChild(document.createTextNode(rec));
        details.appendChild(recP);
      }

      li.appendChild(summaryBtn);
      li.appendChild(details);
      analysisIssuesList.appendChild(li);
    });

    rebuildIssueFilterOptions(issues);
    applyIssueListFilter();
    rememberStructuredAnalysisForExport(data);
  }

  if (analysisExportJsonBtn) {
    analysisExportJsonBtn.addEventListener("click", function () {
      downloadAnalysisJson();
    });
  }
  if (analysisExportCsvBtn) {
    analysisExportCsvBtn.addEventListener("click", function () {
      downloadAnalysisCsv();
    });
  }
  if (analysisExportDocxBtn) {
    analysisExportDocxBtn.addEventListener("click", function () {
      downloadAnalysisDocx();
    });
  }

  if (filterTypeSelect) {
    filterTypeSelect.addEventListener("change", applyIssueListFilter);
  }
  if (filterSeveritySelect) {
    filterSeveritySelect.addEventListener("change", applyIssueListFilter);
  }
  if (filterResetBtn) {
    filterResetBtn.addEventListener("click", function () {
      resetIssueFilters();
    });
  }

  if (analysisIssuesList) {
    analysisIssuesList.addEventListener("click", function (ev) {
      const summaryBtn = ev.target.closest(".analysis-issue__summary");
      if (
        !summaryBtn ||
        !analysisIssuesList.contains(summaryBtn) ||
        summaryBtn.disabled
      ) {
        return;
      }
      toggleAnalysisIssueCardFromSummary(summaryBtn);
    });
  }

  /** Увеличивается при смене файла или сбросе выбора — ответы устаревших запросов не трогают интерфейс. */
  let uiEpoch = 0;

  const progressBar = document.getElementById("upload-progress-bar");
  const progressFill = document.getElementById("upload-progress-fill");
  const progressPercent = document.getElementById("upload-progress-percent");
  const processStatus = document.getElementById("upload-process-status");
  let progressIntervalId = null;

  function setProgressPercentDisplay(rounded) {
    if (progressPercent) {
      progressPercent.textContent = rounded + "%";
    }
  }

  /** Текстовый этап обработки по проценту (согласован с визуальным прогрессом, без реальных шагов на сервере). */
  function processStatusTextForPercent(rounded) {
    if (rounded <= 17) {
      return "Подготовка файла";
    }
    if (rounded <= 35) {
      return "Загрузка файла";
    }
    if (rounded <= 52) {
      return "Извлечение текста";
    }
    if (rounded <= 70) {
      return "Анализ структуры";
    }
    return "Формирование отчёта";
  }

  function setProcessStatusText(text) {
    if (processStatus) {
      processStatus.textContent = text;
    }
  }

  function syncProcessStatusWithPercent(rounded) {
    setProcessStatusText(processStatusTextForPercent(rounded));
  }

  function stopUploadProgressAnimation() {
    if (progressIntervalId !== null) {
      clearInterval(progressIntervalId);
      progressIntervalId = null;
    }
  }

  function resetUploadProgressVisual() {
    if (progressFill) {
      progressFill.style.width = "0%";
    }
    if (progressBar) {
      progressBar.setAttribute("aria-valuenow", "0");
    }
    setProgressPercentDisplay(0);
    setProcessStatusText("");
  }

  function resetUploadProgress() {
    stopUploadProgressAnimation();
    resetUploadProgressVisual();
  }

  function startUploadProgress() {
    resetUploadProgress();
    if (!progressFill || !progressBar) {
      return;
    }
    let value = 0;
    const cap = 88;
    let handedOffToAnalyzing = false;
    syncProcessStatusWithPercent(0);
    progressIntervalId = window.setInterval(() => {
      if (value >= cap) {
        if (!handedOffToAnalyzing) {
          handedOffToAnalyzing = true;
          stopUploadProgressAnimation();
          showState("analyzing");
        }
        return;
      }
      const delta = Math.max(0.4, (cap - value) * 0.07);
      value = Math.min(cap, value + delta);
      const rounded = Math.round(value);
      progressFill.style.width = value + "%";
      progressBar.setAttribute("aria-valuenow", String(rounded));
      setProgressPercentDisplay(rounded);
      syncProcessStatusWithPercent(rounded);
    }, 380);
  }

  function showState(name) {
    Object.entries(stateEls).forEach(([key, el]) => {
      if (el) {
        el.hidden = key !== name;
      }
    });
  }

  /** Прокрутка к области результатов после успешного анализа (без сдвига фокуса с поля ввода до завершения сценария). */
  function revealResultsRegion() {
    const root = document.getElementById("analysis-results-root");
    const panel = stateEls.result;
    const target = root || panel;
    if (!target) {
      return;
    }
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        target.scrollIntoView({ behavior: "smooth", block: "nearest" });
        if (typeof target.focus === "function") {
          try {
            target.focus({ preventScroll: true });
          } catch {
            target.focus();
          }
        }
      });
    });
  }

  function revealErrorRegion() {
    const panel = stateEls.error;
    if (!panel) {
      return;
    }
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
        if (typeof panel.focus === "function") {
          try {
            panel.focus({ preventScroll: true });
          } catch {
            panel.focus();
          }
        }
      });
    });
  }

  function setSubmitBusy(busy) {
    if (!submitBtn) {
      return;
    }
    submitBtn.setAttribute("aria-busy", busy ? "true" : "false");
  }

  function isStaleRequest(epochAtSubmit) {
    return epochAtSubmit !== uiEpoch;
  }

  /** Разрешённые типы: расширение имени файла без учёта регистра — .docx или .pdf */
  function isAllowedUploadFile(file) {
    const name = file.name || "";
    const dot = name.lastIndexOf(".");
    const ext = dot >= 0 ? name.slice(dot).toLowerCase() : "";
    return ext === ".docx" || ext === ".pdf";
  }

  function hasRetryableFile() {
    const f = fileInput.files && fileInput.files[0];
    return Boolean(f && isAllowedUploadFile(f));
  }

  function setFeedback(text, variant) {
    if (!feedback) {
      return;
    }
    feedback.classList.toggle("upload-panel__feedback--error", variant === "error");
    if (text) {
      feedback.textContent = text;
      feedback.hidden = false;
    } else {
      feedback.textContent = "";
      feedback.hidden = true;
    }
  }

  function messageForHttpStatus(status) {
    if (status === 415) {
      return "Поддерживаются только файлы форматов DOCX и PDF. Выберите другой файл.";
    }
    if (status === 400) {
      return "Не удалось обработать имя файла. Переименуйте файл и попробуйте снова.";
    }
    if (status === 422) {
      return "Не удалось обработать файл: документ повреждён или не соответствует формату. Выберите корректный файл DOCX или PDF.";
    }
    if (status === 413) {
      return "Файл не принят: превышен допустимый размер или ограничение на стороне сервера.";
    }
    if (status === 404 || status === 405) {
      return "Служба загрузки недоступна по адресу. Обновите страницу или обратитесь к администратору.";
    }
    if (status === 429) {
      return "Слишком много запросов. Подождите немного и повторите попытку.";
    }
    if (status >= 500) {
      return "Сервер временно недоступен. Проверьте подключение и повторите попытку.";
    }
    return "Не удалось загрузить файл. Повторите попытку.";
  }

  /** Ответ FastAPI при отсутствии поля формы `file` (и аналогичные случаи). */
  function messageFor422UploadBody(data) {
    if (!data || typeof data !== "object" || !Array.isArray(data.detail)) {
      return "";
    }
    const missingFile = data.detail.some(function (item) {
      return (
        item &&
        item.type === "missing" &&
        Array.isArray(item.loc) &&
        item.loc.indexOf("file") !== -1
      );
    });
    if (missingFile) {
      return "Файл не был передан. Выберите документ и повторите попытку.";
    }
    return "";
  }

  function showUploadError(message, epochAtSubmit) {
    if (epochAtSubmit !== undefined && isStaleRequest(epochAtSubmit)) {
      setSubmitBusy(false);
      return;
    }
    clearAnalysisResults();
    stopUploadProgressAnimation();
    showState("error");
    resetUploadProgressVisual();
    if (errorDetail) {
      errorDetail.textContent = message;
    }
    setFeedback(message, "error");
    submitBtn.disabled = !hasRetryableFile();
    setSubmitBusy(false);
    revealErrorRegion();
  }

  fileInput.addEventListener("change", () => {
    uiEpoch += 1;
    setSubmitBusy(false);
    setFeedback("");
    resetUploadProgress();
    clearAnalysisResults();
    showState("idle");

    const f = fileInput.files && fileInput.files[0];
    if (!f) {
      if (selectedName) {
        selectedName.hidden = true;
        selectedName.textContent = "";
      }
      submitBtn.disabled = true;
      return;
    }

    if (!isAllowedUploadFile(f)) {
      fileInput.value = "";
      if (selectedName) {
        selectedName.hidden = true;
        selectedName.textContent = "";
      }
      submitBtn.disabled = true;
      setFeedback(MSG_UNSUPPORTED_TYPE, "error");
      return;
    }

    if (selectedName) {
      selectedName.textContent = "Выбран файл: " + f.name;
      selectedName.hidden = false;
    }
    submitBtn.disabled = false;
  });

  submitBtn.addEventListener("click", async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) {
      return;
    }

    if (!isAllowedUploadFile(file)) {
      fileInput.value = "";
      if (selectedName) {
        selectedName.hidden = true;
        selectedName.textContent = "";
      }
      submitBtn.disabled = true;
      setFeedback(MSG_UNSUPPORTED_TYPE, "error");
      showState("idle");
      return;
    }

    const epochAtSubmit = uiEpoch;

    clearAnalysisResults();
    showState("uploading");
    startUploadProgress();
    setFeedback("");
    submitBtn.disabled = true;
    setSubmitBusy(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (isStaleRequest(epochAtSubmit)) {
        setSubmitBusy(false);
        return;
      }

      let data = null;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (isStaleRequest(epochAtSubmit)) {
        setSubmitBusy(false);
        return;
      }

      if (response.ok) {
        if (data && typeof data === "object" && data.status === "accepted") {
          if (isStaleRequest(epochAtSubmit)) {
            setSubmitBusy(false);
            return;
          }
          stopUploadProgressAnimation();
          resetUploadProgressVisual();
          if (progressFill && progressBar) {
            progressFill.style.width = "100%";
            progressBar.setAttribute("aria-valuenow", "100");
            setProgressPercentDisplay(100);
          }
          const displayName =
            typeof data.filename === "string" && data.filename
              ? data.filename
              : file.name;
          const hasAnalysisPayload =
            Object.prototype.hasOwnProperty.call(data, "issues") ||
            (data.report &&
              typeof data.report === "object" &&
              Object.prototype.hasOwnProperty.call(data.report, "issues"));
          if (hasAnalysisPayload) {
            renderAnalysisResults(data);
            showState("result");
            setFeedback("");
            setSubmitBusy(false);
            revealResultsRegion();
          } else {
            clearAnalysisResults();
            showState("idle");
            setFeedback(
              "Файл «" +
                displayName +
                "» успешно загружен на сервер."
            );
            setSubmitBusy(false);
          }
          fileInput.value = "";
          if (selectedName) {
            selectedName.hidden = true;
            selectedName.textContent = "";
          }
          submitBtn.disabled = true;
          return;
        }
        showUploadError(MSG_UNEXPECTED_RESPONSE, epochAtSubmit);
        return;
      }

      let errMsg = messageForHttpStatus(response.status);
      if (response.status === 422 && data && typeof data === "object") {
        const missingPart = messageFor422UploadBody(data);
        if (missingPart) {
          errMsg = missingPart;
        } else if (
          typeof data.message === "string" &&
          data.message.trim() &&
          /[\u0400-\u04FF]/.test(data.message)
        ) {
          errMsg = data.message.trim();
        }
      }
      showUploadError(errMsg, epochAtSubmit);
    } catch {
      showUploadError(MSG_NETWORK, epochAtSubmit);
    }
  });
})();
