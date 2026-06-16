const $ = (id) => document.getElementById(id);
const latestDaily = () => days[0];
let payload = null;
let livePayload = null;
let aiPayload = { reports: [] };
let selectedReport = latestDaily().report;
let selectedSeverities = new Set(["all"]);
let feedHovering = false;
let refreshingLiveData = false;
let aiWorking = false;
let aiStatusMessage = null;
const LIVE_DATA_POLL_MS = 15_000;
const TX_ACTIVITY_POLL_MS = 60_000;
const COOLDOWN_SECONDS = 60;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function dayLabel(date) {
  const parts = date.slice(0, 10).split("-");
  return new Date(`${parts[0]}-${parts[1]}-${parts[2]}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "long", day: "numeric", timeZone: "UTC",
  });
}

function signalTone(day) {
  if (day.action === "Positive") return "pos";
  if (day.action === "Neutral") return "neu";
  return "";
}

function titleHtml(signal, day) {
  const words = signal.split(" ");
  const last = words.pop() || signal;
  const head = words.join(" ");
  const tone = day?.action === "Positive" ? "pos" : day?.action === "Neutral" ? "neu" : "neg";
  const isNeutral = tone === "neu";
  const arrow = tone === "pos" ? "↑" : isNeutral ? "→" : "↓";
  const arrowColor = tone === "pos" ? "var(--pos)" : isNeutral ? "var(--text-dim)" : "var(--neg)";
  const lastColor = tone === "pos" ? "positive" : isNeutral ? "dim" : "negative";
  return `<span class="sig-arrow" style="color:${arrowColor}">${arrow}</span>${head ? escapeHtml(head) + " " : ""}<span class="${lastColor}">${escapeHtml(last)}</span>`;
}

function hoursAgo(ts) {
  const iso = ts.replace(/^(\d{4})-(\d{2})-(\d{2}):/, "$1-$2-$3T") + "Z";
  const reference = Date.now();
  const hours = Math.max(0, Math.round((reference - Date.parse(iso)) / 36e5));
  if (hours < 1) return "just now";
  if (hours === 1) return "1h ago";
  return `${hours}h ago`;
}

function alertTime(ts) {
  return Date.parse(ts.replace(/^(\d{4})-(\d{2})-(\d{2}):/, "$1-$2-$3T") + "Z");
}

function rollingWindow() {
  const end = Date.now();
  return { start: end - 24 * 36e5, end };
}

function feedWindow() {
  const { start: windowStart, end: nowMs } = rollingWindow();
  const now = new Date(nowMs);
  const windowEnd = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), now.getUTCHours() + 1);
  const windowSpan = windowEnd - windowStart;
  const nowPct = ((nowMs - windowStart) / windowSpan) * 100;
  const nowLabelPct = Math.min(98.5, Math.max(1.5, nowPct));
  const nowTime = String(now.getUTCHours()).padStart(2, "0") + ":" + String(now.getUTCMinutes()).padStart(2, "0");
  return { windowStart, windowEnd, windowSpan, nowMs, now, nowPct, nowLabelPct, nowTime };
}

function displayTimestamp(ts) {
  return ts.replace(/^(\d{4}-\d{2}-\d{2}):/, "$1 ");
}

function shortHash(hash) {
  if (!hash) return "-";
  return `${hash.slice(0, 10)}...${hash.slice(-6)}`;
}

function alertValue(alert) {
  if (alert && typeof alert === "object" && Number.isFinite(Number(alert.value_usd))) {
    const sign = ["stableBurn", "tokenBurn", "bridgeOut"].includes(alert.signal) ? -1 : 1;
    return sign * Number(alert.value_usd);
  }
  const raw = String(alert && typeof alert === "object" ? alert.value : alert).trim();
  const sign = raw.startsWith("-") ? -1 : 1;
  let number = raw.replace(/[$,+-]/g, "");
  let scale = 1;
  if (number.endsWith("M")) { scale = 1_000_000; number = number.slice(0, -1); }
  if (number.endsWith("K")) { scale = 1_000; number = number.slice(0, -1); }
  return sign * Number(number || 0) * scale;
}

function money(value) {
  const sign = value < 0 ? "-" : value > 0 ? "+" : "";
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(2)}K`;
  return `${sign}$${abs.toFixed(0)}`;
}

function moneyAbs(value) {
  return money(Math.abs(value)).replace("+", "");
}

function parseBlockNumber(value) {
  return Number(String(value || "").replace(/\D/g, "")) || 0;
}

function formatBlockNumber(value) {
  return `#${parseBlockNumber(value).toLocaleString("en-US")}`;
}

function setBlockNumber(value) {
  const next = parseBlockNumber(value);
  ["blockNumber"].forEach((id) => {
    const el = $(id);
    if (!el) return;
    const current = parseBlockNumber(el.textContent);
    if (next >= current) el.textContent = formatBlockNumber(next);
  });
}

function compactAlertDetail(alert) {
  const detail = alert.detail || "";
  return detail.replace(/\s*Tx\s+0x[a-fA-F0-9]+\.?/i, "").trim() || "-";
}

function eventBlock(detail) {
  return (detail || "").match(/\bblock\s+([0-9]+)/i)?.[1] || "";
}

function tipMetric(label, value, className = "") {
  return `<div class="tip-metric"><span>${escapeHtml(label)}</span><b class="${className}">${escapeHtml(value)}</b></div>`;
}

function tipEvent(event) {
  const value = alertValue(event);
  return `<div class="tip-event"><b class="${value >= 0 ? "positive" : "negative"}">${money(value)}</b><span>${escapeHtml(event.signal)}</span><em>${escapeHtml(sevLabel(event.severity))}</em></div>`;
}

function valueClass(value) {
  if (value.startsWith("-")) return "negative";
  if (value.startsWith("+")) return "positive";
  return "";
}

function hitRateClass(value) {
  const hitRate = Number(value);
  if (hitRate > 50) return "positive";
  if (hitRate < 50) return "negative";
  return "neutral";
}

function recentAlerts() {
  const alerts = payload?.alerts || latestDaily().alerts.map((a) => ({
    timestamp: a[0], severity: a[1], signal: a[2], proposed_action: a[3], value: a[4], detail: a[6], token: "",
  }));
  const { start, end } = rollingWindow();
  return alerts.filter((a) => {
    const timestamp = alertTime(a.timestamp);
    return timestamp >= start && timestamp <= end;
  }).sort((a, b) => b.timestamp.localeCompare(a.timestamp));
}

function visibleAlerts() {
  const alerts = recentAlerts();
  if (selectedSeverities.has("all")) return alerts;
  return alerts.filter((a) => selectedSeverities.has(a.severity));
}

function summarizeIntraday(alerts, day) {
  if (!alerts.length) {
    return {
      label: "No intraday on-chain alerts in the last 24h.",
      evidence: "No alert crossed the current Mantle stable/WMNT anomaly thresholds.",
      verdict: "neutral",
    };
  }
  const mints = alerts.filter((a) => a.signal === "stableMint");
  const burns = alerts.filter((a) => a.signal === "stableBurn");
  const transfers = alerts.filter((a) => a.signal === "stableTransfer");
  const bridgeIn = alerts.filter((a) => a.signal === "bridgeIn");
  const bridgeOut = alerts.filter((a) => a.signal === "bridgeOut");
  const yieldRisk = alerts.filter((a) => a.risk_scope === "yield_pool");
  const high = alerts.filter((a) => a.severity === "high").length;
  const mintUsd = mints.reduce((sum, a) => sum + Math.max(0, alertValue(a)), 0);
  const burnUsd = burns.reduce((sum, a) => sum + Math.min(0, alertValue(a)), 0);
  const transferUsd = transfers.reduce((sum, a) => sum + Math.abs(alertValue(a)), 0);
  const bridgeInUsd = bridgeIn.reduce((sum, a) => sum + Math.max(0, alertValue(a)), 0);
  const bridgeOutUsd = bridgeOut.reduce((sum, a) => sum + Math.min(0, alertValue(a)), 0);
  const netIssuance = mintUsd + burnUsd;
  const largest = alerts.reduce((best, a) => Math.abs(alertValue(a)) > Math.abs(alertValue(best)) ? a : best, alerts[0]);
  let verdict = "neutral";
  if (netIssuance > 500_000 && day.action === "Negative") verdict = "weakens";
  if (netIssuance < -500_000 && day.action !== "Positive") verdict = "confirms";
  if (netIssuance > 500_000 && day.action === "Positive") verdict = "confirms";
  if (netIssuance < -500_000 && day.action === "Positive") verdict = "weakens";
  if (yieldRisk.length) verdict = "exit_yield";
  const label =
    `${alerts.length} alerts: ${mints.length} mints, ${burns.length} burns, ${bridgeIn.length} bridge-ins, ${bridgeOut.length} bridge-outs. ` +
    `Net stable issuance ${money(netIssuance)}; net bridge flow ${money(bridgeInUsd + bridgeOutUsd)}; transfer volume ${moneyAbs(transferUsd)}. ` +
    (yieldRisk.length
      ? `Yield-pool risk alerts: ${yieldRisk.length}; exit or review affected pool before allocating.`
      : `Verdict: ${verdict} the daily signal.`);
  const evidence = [
    `24h alert count: ${alerts.length}`,
    `stable mints: ${money(mintUsd)} across ${mints.length}`,
    `stable burns: ${money(burnUsd)} across ${burns.length}`,
    `bridge inflows: ${money(bridgeInUsd)} across ${bridgeIn.length}`,
    `bridge outflows: ${money(bridgeOutUsd)} across ${bridgeOut.length}`,
    `large stable transfers: ${moneyAbs(transferUsd)} across ${transfers.length}`,
    `yield-pool risk alerts: ${yieldRisk.length}`,
    `high-severity alerts: ${high}`,
    `largest event: ${largest.token || "-"} ${largest.signal} ${largest.value} at ${largest.timestamp.slice(11, 16)}`,
  ].join("\n");
  return { label, evidence, verdict };
}

function dailyReport(day, intraday) {
  const action = intraday.verdict === "exit_yield"
    ? `${day.report[2]}\n\nYield-pool risk override: exit the affected pool or hold cash until token/protocol anomaly clears.`
    : day.report[2];
  return [
    day.report[0],
    `${day.report[1]}\n\nIntraday on-chain check: ${intraday.label}`,
    action,
    `${day.report[3]}\n\nIntraday on-chain events:\n${intraday.evidence}`,
  ];
}

function linkYieldText(text, day) {
  const route = day.yield_text || "";
  if (!day.yield_url || !route || !text.includes(route)) return escapeHtml(text);
  const index = text.indexOf(route);
  const before = text.slice(0, index);
  const after = text.slice(index + route.length);
  return `${escapeHtml(before)}<a class="yield-link" href="${escapeHtml(day.yield_url)}" target="_blank" rel="noreferrer">${escapeHtml(route)}</a>${escapeHtml(after)}`;
}

function renderSignal() {
  const day = latestDaily();
  const alerts = recentAlerts();
  const intraday = summarizeIntraday(alerts, day);
  selectedReport = dailyReport(day, intraday);
  const briefingDate = (historyData?.generated_at || "").slice(0, 10) || day.date.slice(0, 10);
  $("signalDate").textContent = `${briefingDate} · 09:00 UTC`;
  $("signalTitle").innerHTML = titleHtml(day.signal, day);
  $("signalText").innerHTML =
    `<p>${escapeHtml(day.report[1])}</p>` +
    `<div class="intraday-check"><span>Intraday on-chain check</span>${escapeHtml(intraday.label)}</div>`;
  const proposed = day.proposed.replace(/^Recommendation:\s*/i, "");
  const tone = day.action === "Positive" ? "pos" : day.action === "Neutral" ? "neu" : "neg";
  const dirLabel = tone === "pos" ? "Long" : tone === "neu" ? "Neutral" : "Risk-Off";
  const dirColor = tone === "pos" ? "var(--pos)" : tone === "neu" ? "var(--text-dim)" : "var(--neg)";
  $("signalPill").className = `brief-reco reco-${tone}`;
  $("signalPill").innerHTML = `<span class="reco-bar" style="background:${dirColor}"></span><span class="reco-dir" style="color:${dirColor}">${dirLabel}</span><span class="reco-action">${linkYieldText(proposed, day)}</span><a class="lnk" id="reportLink">full report</a>`;
  const metrics = [
    ["Strength", day.strength.replace("/100", ""), "/100", ""],
    ["Fired 120d", "9", "x", ""],
    ["Hit Rate", "55.6", "%", hitRateClass("55.6")],
    ["Median 1d", "+0.5", "%", valueClass("+0.5")],
    ["All Time", "+14.2", "%", valueClass("+14.2")],
  ];
  $("metrics").innerHTML = metrics.map(([k, v, s, c]) => `<div class="brief-cell"><div class="k">${k}</div><div class="v ${c}">${v}<small>${s}</small></div></div>`).join("");
  $("reportLink").addEventListener("click", (e) => { e.preventDefault(); openReport(selectedReport); });
}

function liveSignals() {
  return (livePayload?.signals || [])
    .slice()
    .sort((a, b) => String(b.timestamp || "").localeCompare(String(a.timestamp || "")));
}

function severityClass(severity) {
  if (severity === "high") return "high";
  if (severity === "medium") return "medium";
  return "low";
}

function renderLiveSignals() {
  const el = $("liveSignals");
  if (!el) return;
  const generatedAt = livePayload?.generated_at ? new Date(livePayload.generated_at).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, timeZone: "UTC" }) : "--";
  if ($("radarSub")) $("radarSub").textContent = `Live market/on-chain context · refreshed ${generatedAt} UTC`;
  const signals = liveSignals().slice(0, 5);
  if (!signals.length) {
    el.innerHTML = `<button class="live-signal empty" type="button" disabled><div class="ls-label">Live context loading</div><div class="ls-detail">Waiting for market, perp, and on-chain signal refresh.</div></button>`;
    return;
  }
  el.innerHTML = signals.map((signal, i) => {
    const severity = severityClass(signal.severity);
    const valueClassName = String(signal.value || "").startsWith("-") ? "negative" : String(signal.value || "").startsWith("+") ? "positive" : "";
    return `<button class="live-signal ${severity}" type="button" data-live-idx="${i}">` +
      `<div class="ls-top"><span class="ls-type">${escapeHtml(signal.type || "live")}</span><span class="ls-sev ${severity === "high" ? "negative" : severity === "medium" ? "neutral" : "dim"}">${escapeHtml(severity)}</span></div>` +
      `<div class="ls-label">${escapeHtml(signal.label || "Live signal")}</div>` +
      `<div class="ls-value ${valueClassName}">${escapeHtml(signal.value || "-")}</div>` +
      `<div class="ls-detail">${escapeHtml(signal.detail || "-")}</div>` +
      `</button>`;
  }).join("");
  el.querySelectorAll("[data-live-idx]").forEach((button) => {
    button.addEventListener("click", () => openLiveSignal(signals[Number(button.dataset.liveIdx)]));
  });
}

function openLiveSignal(signal) {
  const evidence = Array.isArray(signal.evidence) ? signal.evidence : [];
  $("modalLabel").textContent = "Live Signal";
  $("detail").innerHTML =
    `<h2>${escapeHtml(signal.label || "Live signal")}</h2>` +
    `<div class="event-detail-grid">` +
    `<div class="event-k">Time</div><div>${escapeHtml(displayTimestamp(signal.timestamp || ""))}</div>` +
    `<div class="event-k">Type</div><div>${escapeHtml(signal.type || "-")}</div>` +
    `<div class="event-k">Severity</div><div>${escapeHtml(severityClass(signal.severity))}</div>` +
    `<div class="event-k">Value</div><div>${escapeHtml(signal.value || "-")}</div>` +
    `<div class="event-k">Source</div><div>${escapeHtml(signal.source || "-")}</div>` +
    `</div>` +
    `<div class="rc-section">Detail</div><p>${escapeHtml(signal.detail || "-")}</p>` +
    `<div class="rc-section">Proposed Action</div><p>${escapeHtml(signal.proposed_action || "Watch only")}</p>` +
    `<div class="rc-section">Evidence</div><div class="rc-evidence">${escapeHtml(evidence.length ? evidence.join("\n") : "-")}</div>`;
  $("modal").hidden = false;
}

function aiReports() {
  return (aiPayload?.reports || [])
    .slice()
    .sort((a, b) => String(b.generated_at || "").localeCompare(String(a.generated_at || "")));
}

function aiReportsInWindow() {
  const { start, end } = rollingWindow();
  return aiReports().filter((report) => {
    const time = Date.parse(report.generated_at || report.timestamp || "");
    return Number.isFinite(time) && time >= start && time <= end;
  });
}

function latestAiReport() {
  return aiReports()[0] || null;
}

function aiReportSummary(report) {
  const body = report?.report || {};
  return body.summary || body.title || "AI analyst report ready.";
}

function setAiStatusMessage(message, className = "ready", ttlMs = 8000) {
  aiStatusMessage = { message, className, expires: ttlMs ? Date.now() + ttlMs : 0 };
  renderAiStatus();
}

function cooldownText(ms) {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function renderAiStatus() {
  const el = $("aiStatus");
  const button = $("aiAnalyzeBtn");
  if (!el || !button) return;
  if (aiWorking) {
    button.disabled = true;
    el.innerHTML = `<span class="aip-inline-loading" aria-label="AI report loading"></span>`;
    return;
  }
  if (aiStatusMessage && (!aiStatusMessage.expires || aiStatusMessage.expires > Date.now())) {
    el.innerHTML = `<span class="${escapeHtml(aiStatusMessage.className)}">${escapeHtml(aiStatusMessage.message)}</span>`;
  } else {
    aiStatusMessage = null;
    const latest = latestAiReport();
    const cooldownUntil = latest?.cooldown_until ? Date.parse(latest.cooldown_until) : 0;
    if (cooldownUntil > Date.now()) {
      button.disabled = true;
      const remaining = cooldownUntil - Date.now();
      const pct = Math.max(0, Math.min(100, (1 - remaining / (COOLDOWN_SECONDS * 1000)) * 100));
      el.innerHTML = `<div class="aip-cooldown"><div class="aip-cooldown-bar"><div style="width:${pct.toFixed(1)}%"></div></div><span>next in ${cooldownText(remaining)}</span></div>`;
      return;
    }
    el.innerHTML = latest
      ? `<span class="ready">ready</span> · ${escapeHtml(aiReportSummary(latest))}`
      : `<span class="ready">ready</span>`;
  }
  button.disabled = false;
}

function renderAiLoadingPanel() {
  const el = $("aiChartPanel");
  if (!el) return;
  el.innerHTML =
    `<div class="aip-row"><button class="ai-panel-btn" type="button" disabled><img src="./_0_assets/qsignal-ai.svg" alt="" /><span>Ask AI</span></button></div>` +
    `<div class="aip-loading" aria-label="AI report loading">` +
    `<div class="aip-loading-spinner"></div>` +
    `</div>`;
  requestAnimationFrame(syncAiPanelHeight);
}

function renderAiChartPanel() {
  const el = $("aiChartPanel");
  if (!el) return;
  if (aiWorking) {
    renderAiLoadingPanel();
    return;
  }
  const report = latestAiReport();
  const top =
    `<div class="aip-row"><button class="ai-panel-btn" type="button" id="aiAnalyzeBtn"><img src="./_0_assets/qsignal-ai.svg" alt="" /><span>Ask AI</span></button></div>` +
    `<div class="ai-status ai-status-panel" id="aiStatus"></div>`;
  if (!report) {
    el.innerHTML = top + `<div class="aip-empty">Summarize daily signal, live context, and 24h on-chain flow.</div>`;
    $("aiAnalyzeBtn")?.addEventListener("click", runAiAnalyze);
    renderAiStatus();
    requestAnimationFrame(syncAiPanelHeight);
    return;
  }
  const body = report.report || {};
  const why = Array.isArray(body.why) ? body.why.slice(0, 3) : [];
  const action = Array.isArray(body.action) ? body.action.slice(0, 3) : [];
  const confidence = Number(body.confidence ?? 0);
  const tone = body.stance === "long" ? "positive" : body.stance === "exit_yield" ? "negative" : body.stance === "yield" ? "neutral" : "dim";
  const confBar = Math.min(100, Math.max(0, confidence));
  el.innerHTML = top +
    `<div class="aip-result">` +
    `<div class="aip-meta"><span class="aip-stance ${tone}">${escapeHtml(body.stance || "watch")}</span><span class="aip-conf-val">${confidence.toFixed(0)}/100</span></div>` +
    `<div class="aip-title">${escapeHtml(body.title || "-")}</div>` +
    `<p class="aip-summary">${escapeHtml(body.summary || "-")}</p>` +
    (why.length || action.length ? `<div class="aip-bullets">` +
      why.map((item) => `<div class="aip-item">${escapeHtml(item)}</div>`).join("") +
      action.map((item) => `<div class="aip-action">${escapeHtml(item)}</div>`).join("") +
    `</div>` : "") +
    `<div class="aip-footer"><button class="ai-panel-link" type="button" id="aiPanelReport">full report</button></div>` +
    `</div>`;
  $("aiPanelReport")?.addEventListener("click", () => openAiReport(report));
  $("aiAnalyzeBtn")?.addEventListener("click", runAiAnalyze);
  renderAiStatus();
  requestAnimationFrame(syncAiPanelHeight);
}

function syncAiPanelHeight() {
  const panel = $("aiChartPanel");
  const chartWrap = document.querySelector(".intra-chart-wrap");
  if (!panel || !chartWrap) return;
  if (window.matchMedia("(max-width: 860px)").matches) {
    panel.style.height = "";
    panel.style.maxHeight = "";
    return;
  }
  const height = Math.round(chartWrap.getBoundingClientRect().height);
  if (height > 0) {
    panel.style.height = `${height}px`;
    panel.style.maxHeight = `${height}px`;
  }
}

function reportList(items) {
  if (Array.isArray(items)) return items.map((item) => `- ${item}`).join("\n");
  return items || "-";
}

function openAiReport(report) {
  const body = report?.report || {};
  $("modalLabel").textContent = "AI Analyst Report";
  $("detail").innerHTML =
    `<h2>${escapeHtml(body.title || "QSignal AI Analyst")}</h2>` +
    `<div class="event-detail-grid">` +
    `<div class="event-k">Generated</div><div>${escapeHtml(displayTimestamp(report.timestamp || ""))}</div>` +
    `<div class="event-k">Stance</div><div>${escapeHtml(body.stance || "-")}</div>` +
    `<div class="event-k">Confidence</div><div>${escapeHtml(String(body.confidence ?? "-"))}/100</div>` +
    `<div class="event-k">Sources</div><div>${escapeHtml(`${report.source_counts?.live_signals || 0} live, ${report.source_counts?.intraday_alerts || 0} intraday, ${report.source_counts?.daily_days || 0} daily`)}</div>` +
    `</div>` +
    `<div class="rc-section">Summary</div><p>${escapeHtml(body.summary || "-")}</p>` +
    `<div class="rc-section">Why</div><div class="rc-evidence">${escapeHtml(reportList(body.why))}</div>` +
    `<div class="rc-section">Action</div><div class="rc-evidence">${escapeHtml(reportList(body.action))}</div>` +
    `<div class="rc-section">Risks</div><div class="rc-evidence">${escapeHtml(reportList(body.risks))}</div>` +
    `<div class="rc-section">Evidence</div><div class="rc-evidence">${escapeHtml(reportList(body.evidence))}</div>`;
  $("modal").hidden = false;
}

async function runAiAnalyze() {
  if (aiWorking) return;
  aiWorking = true;
  renderAiLoadingPanel();
  try {
    const response = await fetch("/api/ai/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    let data;
    const text = await response.text();
    try { data = JSON.parse(text); } catch { throw new Error("Server returned invalid response"); }
    if (!response.ok || data.status === "error") {
      throw new Error(data.error || data.stderr || `HTTP ${response.status}`);
    }
    await loadAiReports();
    aiWorking = false;
    renderFeed(true);
    renderAiChartPanel();
    if (typeof renderAiReportHistory === "function") renderAiReportHistory();
    if (data.report) openAiReport(data.report);
    if (data.status === "cooldown") setAiStatusMessage("Cooldown active; showing latest.", "ready", 6000);
  } catch (error) {
    aiWorking = false;
    renderAiChartPanel();
    setAiStatusMessage(error.message, "err", 0);
  } finally {
    aiWorking = false;
  }
}

function sevDotColor(sev) {
  if (sev === "high") return "var(--neg)";
  if (sev === "medium") return "var(--warn)";
  return "var(--text-dim)";
}
function sevLabel(sev) {
  if (sev === "high") return "high";
  if (sev === "medium") return "medium";
  return "low";
}

function updateFeedClock() {
  const chart = $("intraChart");
  if (!chart) return;
  const windowStart = Number(chart.dataset.windowStart);
  const windowEnd = Number(chart.dataset.windowEnd);
  if (!Number.isFinite(windowStart) || !Number.isFinite(windowEnd) || windowEnd <= windowStart) return;
  const now = new Date();
  const nowMs = now.getTime();
  const nowPct = Math.min(100, Math.max(0, ((nowMs - windowStart) / (windowEnd - windowStart)) * 100));
  const nowLabelPct = Math.min(98.5, Math.max(1.5, nowPct));
  const nowTime = String(now.getUTCHours()).padStart(2, "0") + ":" + String(now.getUTCMinutes()).padStart(2, "0");
  chart.querySelectorAll(".intra-now-line,.intra-now-dot").forEach((el) => { el.style.left = `${nowPct}%`; });
  chart.querySelectorAll(".intra-now-tip").forEach((el) => {
    el.style.left = `${nowLabelPct}%`;
    el.textContent = nowTime;
  });
  const xNow = $("intraXAxis")?.querySelector(".intra-now-x");
  if (xNow) {
    xNow.style.left = `${nowLabelPct}%`;
    xNow.textContent = nowTime;
  }
}

function renderFeed(force = false) {
  if (feedHovering && !force) {
    updateFeedClock();
    return;
  }
  const alerts = visibleAlerts();
  let mints = 0, burns = 0, inflows = 0, outflows = 0;
  alerts.forEach((a) => {
    const v = alertValue(a);
    const sig = a.signal.toLowerCase();
    if (sig.includes("mint")) mints += Math.abs(v);
    else if (sig.includes("burn")) burns += Math.abs(v);
    else if (v > 0) inflows += v;
    else if (v < 0) outflows += Math.abs(v);
  });
  const net = mints + inflows - burns - outflows;
  const totalIn = mints + inflows;
  const totalOut = burns + outflows;
  const { windowStart, windowEnd, windowSpan, nowPct, nowLabelPct, nowTime } = feedWindow();
  const firstHour = new Date(windowStart);
  const firstHourStart = Date.UTC(firstHour.getUTCFullYear(), firstHour.getUTCMonth(), firstHour.getUTCDate(), firstHour.getUTCHours());
  const buckets = [];
  for (let start = firstHourStart; start < windowEnd; start += 36e5) {
    buckets.push({ start, end: start + 36e5, inflow: 0, outflow: 0, events: [] });
  }
  alerts.forEach((alert) => {
    const timestamp = alertTime(alert.timestamp);
    const index = Math.floor((timestamp - firstHourStart) / 36e5);
    if (index < 0 || index >= buckets.length) return;
    const value = alertValue(alert);
    if (value >= 0) buckets[index].inflow += value;
    else buckets[index].outflow += Math.abs(value);
    buckets[index].events.push(alert);
  });
  buckets.forEach((bucket) => bucket.events.sort((a, b) => alertTime(a.timestamp) - alertTime(b.timestamp)));
  const maxGross = Math.max(1, ...buckets.map((bucket) => Math.max(bucket.inflow, bucket.outflow)));
  const yHeight = (value) => value > 0 ? Math.min(47, (Math.log1p(value) / Math.log1p(maxGross)) * 47) : 0;
  const yPos = (value) => value >= 0 ? 50 - yHeight(value) : 50 + yHeight(Math.abs(value));
  const eventY = (value) => yPos(value);
  const hourLabel = (ms) => String(new Date(ms).getUTCHours()).padStart(2, "0");
  const chartX = (ms) => ((ms - windowStart) / windowSpan) * 100;
  const hourRange = (bucket) => {
    const date = new Date(bucket.start).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
    return `${date}, ${hourLabel(bucket.start)}-${hourLabel(bucket.end)} UTC`;
  };
  const hourGridLines = buckets
    .filter((bucket) => bucket.start > windowStart && bucket.start < windowEnd)
    .map((bucket) => `<div class="intra-hour-line" style="left:${chartX(bucket.start).toFixed(3)}%"></div>`)
    .join("");
  const midnightLines = buckets
    .filter((bucket) => new Date(bucket.start).getUTCHours() === 0 && bucket.start > windowStart && bucket.start < windowEnd)
    .map((bucket) => {
      const date = new Date(bucket.start).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
      return `<div class="intra-midnight-line" style="left:${chartX(bucket.start).toFixed(3)}%"><span>${date} 00:00</span></div>`;
    }).join("");

  let evDots = "";
  let aiDots = "";
  const empty = !alerts.length ? `<div class="intra-empty">No events for selected filters.</div>` : "";
  alerts.forEach((event, i) => {
    const x = Math.min(100, Math.max(0, chartX(alertTime(event.timestamp))));
    const rawValue = alertValue(event);
    evDots += `<div class="intra-ev-dot" data-event-idx="${i}" style="left:${x.toFixed(3)}%;top:${eventY(rawValue).toFixed(2)}%;background:${sevDotColor(event.severity)}"><div class="ev-tip"><div class="tip-title">${escapeHtml(displayTimestamp(event.timestamp))}</div>${tipEvent(event)}${tipMetric("token", event.token || "-", "")}</div></div>`;
  });
  const aiWindow = aiReportsInWindow();
  aiWindow.forEach((report, i) => {
    const time = Date.parse(report.generated_at || "");
    const x = Math.min(100, Math.max(0, chartX(time)));
    const body = report.report || {};
    const fresh = Date.now() - time < 120_000 ? " fresh" : "";
    aiDots += `<div class="intra-ai-dot${fresh}" data-ai-idx="${i}" style="left:${x.toFixed(3)}%;top:9%"><div class="ai-tip"><b>${escapeHtml(body.title || "AI Analyst")}</b><span>${escapeHtml(body.stance || "watch")} · ${escapeHtml(String(body.confidence ?? "-"))}/100</span><br/>${escapeHtml(body.summary || "-")}</div></div>`;
  });

  $("intraChart").innerHTML =
    `<div class="intra-grid"></div>` +
    hourGridLines +
    midnightLines +
    `<div class="intra-midline"></div>` +
    `<div class="intra-now-line" style="left:${nowPct}%"></div>` +
    `<div class="intra-now-dot" style="left:${nowPct}%"></div>` +
    `<div class="intra-now-tip" style="left:${nowLabelPct}%">${nowTime}</div>` +
    empty +
    evDots +
    aiDots +
    buckets.map((bucket) => {
      const left = Math.max(0, chartX(Math.max(bucket.start, windowStart)));
      const right = Math.min(100, chartX(Math.min(bucket.end, windowEnd)));
      const width = Math.max(0.25, right - left);
      const netFlow = bucket.inflow - bucket.outflow;
      const bodyClass = netFlow > 0 ? "positive" : netFlow < 0 ? "negative" : "neutral";
      const wickTop = yPos(bucket.inflow);
      const wickBottom = yPos(-bucket.outflow);
      const bodyTop = Math.min(yPos(0), yPos(netFlow));
      const bodyBottom = Math.max(yPos(0), yPos(netFlow));
      const wickHeight = Math.max(2, wickBottom - wickTop);
      const bodyHeight = Math.max(bucket.events.length ? 2 : 0, bodyBottom - bodyTop);
      const candle = mntCandles?.candles?.find((c) => c.t >= bucket.start && c.t < bucket.end);
      let tip = `<div class="col-tip"><div class="tip-title">${hourRange(bucket)}</div>`;
      if (candle) {
        const chg = ((candle.c - candle.o) / candle.o) * 100;
        const cls = candle.c >= candle.o ? "positive" : "negative";
        tip += `<div class="tip-price"><b class="${cls}">$${candle.c.toFixed(4)}</b><small class="${cls}">${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%</small><span class="tip-ohlc">O ${candle.o.toFixed(4)} H ${candle.h.toFixed(4)} L ${candle.l.toFixed(4)}</span></div>`;
      }
      tip += tipMetric("inflow", money(bucket.inflow), "positive");
      tip += tipMetric("outflow", money(-bucket.outflow), "negative");
      tip += tipMetric("net", money(netFlow), netFlow > 0 ? "positive" : netFlow < 0 ? "negative" : "neutral");
      if (bucket.events.length) {
        tip += `<div class="tip-count">${bucket.events.length} event${bucket.events.length > 1 ? "s" : ""}</div>` +
          bucket.events.map((e) => tipEvent(e)).join("");
      } else {
        tip += `<div class="tip-count">No events</div>`;
      }
      tip += "</div>";
      const body = netFlow === 0
        ? `<div class="flow-zero"></div>`
        : `<div class="flow-body ${bodyClass}" style="top:${bodyTop.toFixed(2)}%;height:${bodyHeight.toFixed(2)}%;"></div>`;
      return `<div class="intra-col" style="left:${left.toFixed(3)}%;width:${width.toFixed(3)}%;"><div class="flow-wick ${bodyClass}" style="top:${wickTop.toFixed(2)}%;height:${wickHeight.toFixed(2)}%;"></div>${body}${tip}</div>`;
    }).join("");
  $("intraChart").dataset.windowStart = String(windowStart);
  $("intraChart").dataset.windowEnd = String(windowEnd);

  $("intraFlowScale").innerHTML = [maxGross, maxGross * 0.1, 0, -maxGross * 0.1, -maxGross].map((value) => {
    return `<span class="${value >= 0 ? "pos" : "neg"}">${money(value)}</span>`;
  }).join("");

  $("intraXAxis").innerHTML =
    buckets
      .filter((bucket) => new Date(bucket.start).getUTCHours() % 3 === 0 && bucket.start > windowStart && bucket.start < windowEnd)
      .map((bucket) => `<div class="intra-x-cell" style="left:${chartX(bucket.start).toFixed(3)}%">${hourLabel(bucket.start)}</div>`)
      .join("") +
    `<span class="intra-now-x" style="left:${nowLabelPct}%">${nowTime}</span>`;

  $("intraLegend").innerHTML =
    `<span class="lg"><span class="bar-sw" style="background:var(--accent)"></span>MNT price</span>` +
    `<span class="lg"><span class="candle-sw positive" style="opacity:.25"></span>Inflow</span>` +
    `<span class="lg"><span class="candle-sw negative" style="opacity:.25"></span>Outflow</span>` +
    `<span class="lg"><span class="bar-sw" style="background:rgba(41,98,255,.4)"></span>Network txs</span>` +
    `<span class="lg"><span class="ai-sw"></span>AI analyst</span>`;
  renderActivity(buckets, windowStart, windowEnd, chartX);
  renderCandles(windowStart, windowEnd, chartX);

  const eventRows = alerts.length ? alerts.map((a, i) => {
      const v = alertValue(a);
      const tx = a.tx_hash ? `<a href="https://mantlescan.xyz/tx/${escapeHtml(a.tx_hash)}" target="_blank">tx</a>` : "-";
      const detail = compactAlertDetail(a);
      return `<tr data-event-idx="${i}"><td>${escapeHtml(displayTimestamp(a.timestamp))}</td><td class="age">${hoursAgo(a.timestamp)}</td><td>${tx}</td><td><span class="sev-dot" style="background:${sevDotColor(a.severity)}"></span>${sevLabel(a.severity)}</td><td>${escapeHtml(a.signal)}</td><td class="desc-col"><button class="event-detail-btn" type="button" data-event-idx="${i}" title="${escapeHtml(detail)}">details</button></td><td class="r ${v >= 0 ? "positive" : "negative"}">${money(v)}</td></tr>`;
    }).join("") : `<tr><td class="no-events" colspan="7">No events for selected filters.</td></tr>`;
  $("intraEvents").innerHTML = `<table><colgroup><col class="i-time"><col class="i-age"><col class="i-tx"><col class="i-sev"><col class="i-signal"><col class="i-detail"><col class="i-value"></colgroup><thead><tr><th>Time</th><th>Age</th><th>Tx</th><th>Severity</th><th>Signal</th><th>Detail</th><th class="r">Value</th></tr></thead><tbody>${eventRows}</tbody></table>`;
  $("intraEvents").querySelectorAll(".event-detail-btn").forEach((button) => {
    button.addEventListener("click", () => openEventDetail(alerts[Number(button.dataset.eventIdx)]));
  });
  $("intraEvents").querySelectorAll("tr[data-event-idx]").forEach((row) => {
    row.addEventListener("mouseenter", () => setEventDotActive(row.dataset.eventIdx, true));
    row.addEventListener("mouseleave", () => setEventDotActive(row.dataset.eventIdx, false));
  });
  $("intraChart").querySelectorAll(".intra-ai-dot").forEach((dot) => {
    dot.addEventListener("click", () => openAiReport(aiWindow[Number(dot.dataset.aiIdx)]));
  });
  requestAnimationFrame(syncAiPanelHeight);
}

function setEventDotActive(index, active) {
  const dot = document.querySelector(`.intra-ev-dot[data-event-idx="${index}"]`);
  if (dot) dot.classList.toggle("row-active", active);
}

function openReport(report, label = "Daily AI Report") {
  selectedReport = report;
  $("modalLabel").textContent = label;
  $("detail").innerHTML = `<h2>${escapeHtml(report[0])}</h2><p>${escapeHtml(report[1])}</p><div class="rc-section">Recommended Action</div><p>${escapeHtml(report[2])}</p><div class="rc-section">Evidence</div><div class="rc-evidence">${escapeHtml(report[3])}</div>`;
  $("modal").hidden = false;
}

function openEventDetail(alert) {
  const block = eventBlock(alert.detail);
  const txUrl = alert.tx_hash ? `https://mantlescan.xyz/tx/${alert.tx_hash}` : "";
  const rows = [
    ["Time", displayTimestamp(alert.timestamp)],
    ["Age", hoursAgo(alert.timestamp)],
    ["Signal", alert.signal],
    ["Severity", sevLabel(alert.severity)],
    ["Token", alert.token || "-"],
    ["Value", money(alertValue(alert))],
    ["Action", alert.proposed_action || "-"],
    ["Bridge", alert.bridge_protocol || "-"],
    ["Block", block || "-"],
  ];
  $("modalLabel").textContent = "Intraday On-Chain Event";
  $("detail").innerHTML =
    `<h2>${escapeHtml(alert.signal)}${alert.token ? ` · ${escapeHtml(alert.token)}` : ""}</h2>` +
    `<div class="event-detail-grid">${rows.map(([k, v]) => `<div class="event-k">${escapeHtml(k)}</div><div>${escapeHtml(v)}</div>`).join("")}</div>` +
    `<div class="rc-section">Detail</div><p>${escapeHtml(compactAlertDetail(alert))}</p>` +
    (txUrl ? `<div class="rc-section">Transaction</div><p><a class="tx-link" href="${escapeHtml(txUrl)}" target="_blank" title="${escapeHtml(alert.tx_hash)}">${escapeHtml(shortHash(alert.tx_hash))}</a></p>` : "");
  $("modal").hidden = false;
}

function tickClock() {
  const now = new Date();
  const day = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][now.getUTCDay()];
  const d = now.getUTCDate();
  const h = String(now.getUTCHours()).padStart(2, "0");
  const m = String(now.getUTCMinutes()).padStart(2, "0");
  const s = String(now.getUTCSeconds()).padStart(2, "0");
  $("clock").innerHTML = `<span class="clock-date">${day} ${d}</span> · ${h}:${m}:${s}`;
}

function tickBlock() {
  const current = parseBlockNumber($("blockNumber")?.textContent);
  setBlockNumber(current + 1);
  ["blockDot"].forEach((id) => {
    const dot = $(id);
    if (!dot) return;
    dot.classList.remove("pulse");
    void dot.offsetWidth;
    dot.classList.add("pulse");
  });
}

async function loadData() {
  try {
    const response = await fetch(`./intraday_events.json?v=${Date.now()}`);
    if (!response.ok) return false;
    const nextPayload = await response.json();
    const oldKey = payloadKey(payload);
    const newKey = payloadKey(nextPayload);
    payload = nextPayload;
    if (nextPayload.latest_block) setBlockNumber(nextPayload.latest_block);
    return oldKey !== newKey;
  } catch (error) {
    console.warn("intraday_events.json unavailable; using bundled mock feed", error);
    return false;
  }
}

let txActivity = null;
async function loadTxActivity() {
  try {
    const r = await fetch(`./tx_activity.json?v=${Date.now()}`);
    if (r.ok) txActivity = await r.json();
  } catch (e) { console.warn("tx_activity.json unavailable", e); }
}

let mntCandles = null;
async function loadMntCandles() {
  try {
    const r = await fetch(`./_3_live/mnt_candles.json?v=${Date.now()}`);
    if (r.ok) mntCandles = await r.json();
  } catch (e) { console.warn("mnt_candles.json unavailable", e); }
}

let mntLivePrice = null;
async function loadMntPrice() {
  try {
    const r = await fetch("https://api.bybit.com/v5/market/tickers?category=spot&symbol=MNTUSDT");
    if (!r.ok) return;
    const d = await r.json();
    const tick = d?.result?.list?.[0];
    if (tick) mntLivePrice = { price: parseFloat(tick.lastPrice), ts: Date.now(), pct24h: parseFloat(tick.price24hPcnt || 0) * 100 };
  } catch (e) { console.warn("bybit ticker unavailable", e); }
}

function livePayloadKey(data) {
  const signals = data?.signals || [];
  if (!signals.length) return `${data?.generated_at || ""}:0`;
  const first = signals[0];
  return `${data.generated_at || ""}:${signals.length}:${first.id || ""}:${first.value || ""}`;
}

async function loadLiveSignals() {
  try {
    const response = await fetch(`./live_signals.json?v=${Date.now()}`);
    if (!response.ok) return false;
    const nextPayload = await response.json();
    const oldKey = livePayloadKey(livePayload);
    const newKey = livePayloadKey(nextPayload);
    livePayload = nextPayload;
    return oldKey !== newKey;
  } catch (error) {
    console.warn("live_signals.json unavailable", error);
    return false;
  }
}

function aiPayloadKey(data) {
  const reports = data?.reports || [];
  if (!reports.length) return `${data?.generated_at || ""}:0`;
  return `${data.generated_at || ""}:${reports.length}:${reports[0].id || reports[0].generated_at || ""}`;
}

async function loadAiReports() {
  try {
    const response = await fetch(`./ai_reports.json?v=${Date.now()}`);
    if (!response.ok) return false;
    const nextPayload = await response.json();
    const oldKey = aiPayloadKey(aiPayload);
    const newKey = aiPayloadKey(nextPayload);
    aiPayload = nextPayload;
    return oldKey !== newKey;
  } catch (error) {
    console.warn("ai_reports.json unavailable", error);
    return false;
  }
}

function renderCandles(windowStart, windowEnd, chartX) {
  const chart = $("intraChart");
  if (!chart || !mntCandles?.candles?.length) return;
  const candles = mntCandles.candles.filter((c) => c.t + 36e5 > windowStart && c.t < windowEnd);
  if (!candles.length) return;
  const lp = mntLivePrice?.price;
  const allLows = candles.map((c) => c.l);
  const allHighs = candles.map((c) => c.h);
  if (lp) { allLows.push(lp); allHighs.push(lp); }
  const pMin = Math.min(...allLows);
  const pMax = Math.max(...allHighs);
  const pad = (pMax - pMin) * 0.08 || 0.001;
  const lo = pMin - pad, hi = pMax + pad;
  const pY = (p) => ((hi - p) / (hi - lo)) * 100;
  const pts = candles.map((c) => {
    const x = chartX(c.t + 18e5);
    return `${x.toFixed(3)},${pY(c.c).toFixed(2)}`;
  });
  if (lp) {
    const nowX = Math.min(100, Math.max(0, chartX(Date.now())));
    pts.push(`${nowX.toFixed(3)},${pY(lp).toFixed(2)}`);
  }
  const first = pts[0].split(",")[0];
  const last = pts[pts.length - 1].split(",")[0];
  const areaPoints = pts.join(" ") + ` ${last},100 ${first},100`;
  let liveLine = "";
  if (lp) {
    const y = pY(lp);
    liveLine = `<line class="price-now-line" x1="0" y1="${y.toFixed(2)}" x2="100" y2="${y.toFixed(2)}" />`;
  }
  const html =
    `<svg class="price-line-svg" viewBox="0 0 100 100" preserveAspectRatio="none">` +
    `<defs><linearGradient id="pFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(41,98,255,.18)"/><stop offset="100%" stop-color="rgba(41,98,255,0)"/></linearGradient></defs>` +
    `<polygon class="price-area" points="${areaPoints}" />` +
    `<polyline class="price-close" points="${pts.join(" ")}" />` +
    liveLine +
    candles.map((c) => {
      const x = chartX(c.t + 18e5);
      const y = pY(c.c);
      return `<circle class="price-dot" cx="${x.toFixed(3)}" cy="${y.toFixed(2)}" r="0.6" />`;
    }).join("") +
    `</svg>`;
  let liveTag = "";
  if (lp) {
    const y = pY(lp);
    const cls24 = (mntLivePrice.pct24h || 0) >= 0 ? "positive" : "negative";
    liveTag = `<div class="price-now-tag" style="top:${y.toFixed(2)}%"><b>$${lp.toFixed(4)}</b></div>`;
  }
  const existing = chart.querySelector(".price-layer");
  if (existing) existing.remove();
  chart.insertAdjacentHTML("afterbegin", `<div class="price-layer">${html}${liveTag}</div>`);
  const scale = $("intraScale");
  if (scale) {
    const ticks = [hi, lo + (hi - lo) * 0.75, lo + (hi - lo) * 0.5, lo + (hi - lo) * 0.25, lo];
    scale.innerHTML = ticks.map((v) => `<span>$${v.toFixed(4)}</span>`).join("");
  }
}

function renderActivity(buckets, windowStart, windowEnd, chartX) {
  const el = $("intraActivity");
  if (!el) return;
  if (!txActivity?.hours || !buckets?.length) {
    el.innerHTML = "";
    return;
  }
  const countsByHour = new Map(txActivity.hours.map((h) => [Number(h.hour), Number(h.tx_count_estimated || 0)]));
  const visible = buckets
    .filter((bucket) => bucket.end > windowStart && bucket.start < windowEnd)
    .map((bucket) => {
      const hour = new Date(bucket.start).getUTCHours();
      const count = countsByHour.get(hour) || 0;
      return { bucket, hour, count };
    });
  const max = Math.max(1, ...visible.map((item) => item.count));
  el.innerHTML = visible.map(({ bucket, hour, count }) => {
    const left = Math.max(0, chartX(Math.max(bucket.start, windowStart)));
    const right = Math.min(100, chartX(Math.min(bucket.end, windowEnd)));
    const width = Math.max(0.25, right - left);
    const pct = count > 0 ? Math.max(8, Math.min(100, (count / max) * 100)) : 0;
    return `<div class="act-col" style="left:${left.toFixed(3)}%;width:${width.toFixed(3)}%"><div class="act-bar" style="height:${pct.toFixed(1)}%"></div><div class="act-tip">${String(hour).padStart(2, "0")}:00 · ~${count} txs/hr</div></div>`;
  }).join("");
}

function payloadKey(data) {
  if (!data?.alerts?.length) return `${data?.latest_block || 0}:0`;
  const last = data.alerts[data.alerts.length - 1];
  return `${data.latest_block || 0}:${data.alerts.length}:${last.timestamp}:${last.tx_hash || ""}`;
}

function initFilter() {
  const severities = ["high", "medium", "low"];
  $("intraFilter").querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const value = button.dataset.severity;
      if (value === "all") {
        selectedSeverities = new Set(["all"]);
      } else {
        if (selectedSeverities.has("all")) selectedSeverities = new Set();
        if (selectedSeverities.has(value)) selectedSeverities.delete(value);
        else selectedSeverities.add(value);
        const active = severities.filter((item) => selectedSeverities.has(item));
        selectedSeverities = active.length === 0 || active.length === severities.length ? new Set(["all"]) : new Set(active);
      }
      syncFilterButtons();
      renderFeed(true);
    });
  });
  syncFilterButtons();
}

function syncFilterButtons() {
  $("intraFilter").querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", selectedSeverities.has(button.dataset.severity));
  });
}

async function refreshLiveData(force = false) {
  if (refreshingLiveData) return;
  refreshingLiveData = true;
  try {
    const [dataChanged, liveChanged, aiChanged] = await Promise.all([loadData(), loadLiveSignals(), loadAiReports()]);
    const changed = dataChanged || liveChanged || aiChanged;
    if (dataChanged || force) renderSignal();
    if (liveChanged || force) renderLiveSignals();
    renderAiStatus();
    renderAiChartPanel();
    if (aiChanged && typeof renderAiReportHistory === "function") renderAiReportHistory();
    renderFeed(changed || force);
  } finally {
    refreshingLiveData = false;
  }
}

async function refreshTxActivity() {
  await Promise.all([loadTxActivity(), loadMntCandles()]);
  renderFeed();
}

function initFeedHover() {
  const wrap = document.querySelector(".intra-chart-wrap");
  if (!wrap) return;
  wrap.addEventListener("mouseenter", () => { feedHovering = true; });
  wrap.addEventListener("mouseleave", () => {
    feedHovering = false;
    renderFeed(true);
  });
}

$("closeModal").addEventListener("click", () => ($("modal").hidden = true));
$("modal").addEventListener("click", (e) => { if (e.target === $("modal")) $("modal").hidden = true; });
if ($("burger")) $("burger").addEventListener("click", () => document.querySelector(".nav3-center").classList.toggle("open"));
if ($("aiAnalyzeBtn")) $("aiAnalyzeBtn").addEventListener("click", runAiAnalyze);
tickClock();
setInterval(tickClock, 1000);
setInterval(tickBlock, 2000);
setInterval(updateFeedClock, 1000);
setInterval(renderAiStatus, 1000);
setInterval(renderFeed, 30_000);
setInterval(refreshLiveData, LIVE_DATA_POLL_MS);
setInterval(refreshTxActivity, TX_ACTIVITY_POLL_MS);
setInterval(async () => { await loadMntPrice(); renderFeed(); }, 15_000);
window.addEventListener("focus", () => refreshLiveData(true));
window.addEventListener("resize", syncAiPanelHeight);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) refreshLiveData(true);
});
initFilter();
initFeedHover();
Promise.all([loadData(), loadTxActivity(), loadMntCandles(), loadMntPrice(), loadLiveSignals(), loadAiReports()]).finally(() => {
  tickClock();
  renderLiveSignals();
  renderAiStatus();
  renderAiChartPanel();
  renderFeed(true);
  if (document.body.classList.contains("is-ready")) renderSignal();
});
