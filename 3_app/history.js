let historyData = null;
let pastPage = 0;
const PAST_PAGE_SIZE = 30;
const routeByView = { live: "/live", signals: "/reports", backtest: "/backtest" };
const viewByRoute = { "/": "live", "/live": "live", "/live-signal": "live", "/live-signals": "live", "/signal": "signals", "/signals": "signals", "/reports": "signals", "/singal": "signals", "/past-signal": "signals", "/past-signals": "signals", "/backtest": "backtest" };

function fmtPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${Number(value) >= 0 ? "+" : ""}${(Number(value) * 100).toFixed(2)}%`;
}

function fmtPp(value) {
  return `${Number(value) >= 0 ? "+" : ""}${(Number(value) * 100).toFixed(2)}pp`;
}

function fmtScore(value) {
  return Number(value) === 0 ? "-" : Math.round(Math.abs(Number(value)) * 100);
}

function fmtX(value) {
  return `${Number(value).toFixed(2)}x`;
}

function fmtPct0(value) {
  return `${Number(value) >= 0 ? "+" : ""}${(Number(value) * 100).toFixed(0)}%`;
}

function fmtApy(value) {
  return `${Number(value || 0).toFixed(2)}%`;
}

function fmtUsd(value) {
  const abs = Math.abs(Number(value || 0));
  if (abs >= 1_000_000_000) return `$${(abs / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(abs / 1_000).toFixed(2)}K`;
  return `$${abs.toFixed(0)}`;
}

function titleCaseText(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function actionLabel(day) {
  if (Number(day.direction) > 0) return "long";
  return "yield";
}

function actionClass(day) {
  return `action action-${actionLabel(day)}`;
}

function signalLabel(day) {
  const factors = day.active_factors || [];
  if (!factors.length) return "No valid edge";
  const label = factors[0].name.replaceAll("_", " ");
  return factors.length > 1 ? `${label} +${factors.length - 1}` : label;
}

function viewFromPath() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  return viewByRoute[path] || "signals";
}

function showView(name, push = true) {
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  document.querySelectorAll(".nav3-center a").forEach((tab) => tab.classList.toggle("on", tab.dataset.view === name));
  $(`${name}View`).classList.add("active");
  if (push && window.location.pathname !== routeByView[name]) history.pushState({ view: name }, "", routeByView[name]);
}

function factorLine(factor) {
  return `${factor.name}:${factor.horizon} ${factor.side}, health ${factor.health}, hit ${factor.hit_rate}, median ${factor.median} - ${factor.reason}`;
}

function yieldOptions() {
  return historyData?.yield_options || historyData?.backtest?.yield_options || {};
}

function bestYield() {
  return yieldOptions().best || null;
}

function yieldShortText() {
  const best = bestYield();
  if (!best) return "Mantle stable yield";
  return `${best.symbol} on ${best.project} at ${fmtApy(best.apy)} APY`;
}

function yieldUrl() {
  const best = bestYield();
  if (!best) return "";
  return best.url || `https://defillama.com/yields/pool/${best.pool}`;
}

function yieldLinkHtml() {
  const text = yieldShortText();
  const url = yieldUrl();
  if (!url) return escapeHtml(text);
  return `<a class="yield-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(text)}</a>`;
}

function yieldLongText() {
  const best = bestYield();
  const opts = yieldOptions();
  if (!best) return "Mantle stable yield basket.";
  return `${best.symbol} on ${best.project}: ${fmtApy(best.apy)} APY, ${fmtUsd(best.tvl_usd)} TVL. Basket: ${fmtApy(opts.basket_apy)} APY across ${opts.pool_count || 0} pools / ${fmtUsd(opts.basket_tvl_usd)} TVL.`;
}

function yieldEvidence(day) {
  return `Yield replay APY for this day: ${fmtApy(day.yield_apy)} (${fmtPct(day.yield_ret_1d)} daily). Current best route: ${yieldLongText()}`;
}

function reportForDay(day) {
  const active = day.active_factors.map(factorLine);
  const rejected = day.rejected_factors.map(factorLine);
  const action = day.direction > 0 ? "MNT long exposure." : `Move idle capital to stable yield. Suggested route: ${yieldShortText()}.`;
  return [
    `${day.date} · ${actionLabel(day)}`,
    `Daily recommendation: ${actionLabel(day)}. Score ${fmtScore(day.net_score)} from ${day.active_signal_count} active model signal(s). ${day.direction > 0 ? "" : yieldEvidence(day)}`,
    action,
    `Active model signals:\n${active.join("\n") || "none passed health filters"}\n\nRejected model signals:\n${rejected.join("\n") || "none"}\n\nWatched but not fired:\n${day.not_fired.join(", ") || "none"}\n\nYield context:\n${yieldEvidence(day)}`,
  ];
}

function historyDayToSignal(day) {
  const isLong = Number(day.direction) > 0;
  const isNegative = !isLong && Number(day.net_score) < 0;
  const report = reportForDay(day);
  return {
    date: `${day.date}:00:00:00`,
    action: isLong ? "Positive" : isNegative ? "Negative" : "Neutral",
    proposed: isLong ? "Recommendation: Long MNT" : `Recommendation: Move to Stable Yield - ${yieldShortText()}`,
    yield_text: yieldShortText(),
    yield_url: yieldUrl(),
    strength: `${fmtScore(day.net_score) === "-" ? 0 : fmtScore(day.net_score)}/100`,
    signal: titleCaseText(signalLabel(day)),
    report,
    alerts: [],
  };
}

function syncLatestDaily() {
  if (!historyData?.past_signals?.length) return;
  days = historyData.past_signals.slice(0, 3).map(historyDayToSignal);
  renderSignal();
}

const DONUT_COLORS = ["#5b8cff", "#ff8a65", "#FFB302", "#ef5350", "#2DCCFF", "#9c6ade", "#66bb6a", "#42a5f5", "#ab47bc", "#78909c"];

function renderPast() {
  const rows = historyData.past_signals;
  const pages = Math.max(1, Math.ceil(rows.length / PAST_PAGE_SIZE));
  pastPage = Math.min(pastPage, pages - 1);
  const start = pastPage * PAST_PAGE_SIZE;
  const shown = rows.slice(start, start + PAST_PAGE_SIZE);
  $("pastRows").innerHTML = shown.map((day, i) => `<tr class="past-parent" data-i="${start + i}">
    <td>${day.date}</td>
    <td class="signal-cell">${escapeHtml(signalLabel(day))}</td>
    <td class="${actionClass(day)}">${escapeHtml(actionLabel(day))}</td>
    <td>${fmtScore(day.net_score)}</td>
    <td class="r ${valueClass(fmtPct(day.dir_ret_1d))}">${fmtPct(day.dir_ret_1d)}</td>
    <td><button class="report-btn" data-report="${start + i}">report</button></td>
  </tr>`).join("");
  document.querySelectorAll(".report-btn").forEach((button) => button.addEventListener("click", (event) => {
    event.stopPropagation();
    openReport(reportForDay(rows[Number(button.dataset.report)]), "Daily Signal Report");
  }));
  $("pastPager").innerHTML =
    `<button id="firstPast" ${pastPage === 0 ? "disabled" : ""}>First</button>` +
    `<button id="prevPast" ${pastPage === 0 ? "disabled" : ""}>Prev</button>` +
    `<span>${pastPage + 1} / ${pages}</span>` +
    `<button id="nextPast" ${pastPage >= pages - 1 ? "disabled" : ""}>Next</button>` +
    `<button id="lastPast" ${pastPage >= pages - 1 ? "disabled" : ""}>Last</button>`;
  $("firstPast").addEventListener("click", () => { pastPage = 0; renderPast(); });
  $("prevPast").addEventListener("click", () => { pastPage -= 1; renderPast(); });
  $("nextPast").addEventListener("click", () => { pastPage += 1; renderPast(); });
  $("lastPast").addEventListener("click", () => { pastPage = pages - 1; renderPast(); });
}

function renderProof(backtest) {
  const summary = Object.fromEntries(backtest.summary.map((row) => [row.label, row]));
  const model = summary["Model Long / Yield"];
  const signalName = escapeHtml(latestDaily().signal);
  const allTimeRet = fmtPct0(model.return);
  const dayCount = model.days;
  const cagr = fmtPct0(model.cagr);
  $("btTeaser").innerHTML =
    `<strong>Methodology:</strong> Walk-forward AI model evaluates 12 on-chain + cross-market signals daily. The combined signal set generated <span class="positive">${allTimeRet}</span> over ${dayCount} days (<span class="positive">${cagr}</span>/year), going long on positive signals and moving to stable yield on neutral/risk-off. <a class="lnk" id="btLink">See backtest results &rarr;</a>`;
}

async function loadHistory() {
  const response = await fetch(`./history_backtest.json?v=${Date.now()}`);
  historyData = await response.json();
  syncLatestDaily();
  renderPast();
  renderProof(historyData.backtest);
  renderBacktest(historyData.backtest);
  renderFeed(true);
  document.body.classList.add("is-ready");
}

function latestCompleteUtcDay() {
  return new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function refreshHistoryIfStale() {
  const latest = historyData?.past_signals?.[0]?.date || "";
  if (latest && latest < latestCompleteUtcDay()) {
    loadHistory().catch((error) => console.error("history_backtest.json refresh failed", error));
  }
}

document.querySelectorAll(".nav3-center a").forEach((tab) => tab.addEventListener("click", (event) => {
  event.preventDefault();
  showView(tab.dataset.view);
}));
window.addEventListener("popstate", () => showView(viewFromPath(), false));
$("btTeaser").addEventListener("click", (event) => {
  if (event.target.id === "btLink" || event.target.closest("#btLink")) {
    event.preventDefault();
    showView("backtest");
  }
});
showView(viewFromPath(), false);
loadHistory().catch((error) => {
  console.error("history_backtest.json unavailable", error);
  renderSignal();
  renderFeed(true);
  document.body.classList.add("is-ready");
});
setInterval(refreshHistoryIfStale, 10 * 60 * 1000);
