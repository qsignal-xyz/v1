const CHART_W = 1040;
const CHART_H = 430;
const PLOT = { x: 66, y: 44, w: 820, h: 296 };
let currentBacktest = null;
let modelLeverage = 1;
let logScale = true;
let chartFrame = 0;
function pct1(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${Number(value) >= 0 ? "+" : ""}${(Number(value) * 100).toFixed(1)}%`;
}
function num2(value) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "-";
}
function xRet(value) {
  return `${num2(value)}x`;
}
function usdShort(value) {
  const abs = Math.abs(Number(value || 0));
  if (abs >= 1_000_000_000) return `$${(abs / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(abs / 1_000).toFixed(2)}K`;
  return `$${abs.toFixed(0)}`;
}
function yieldMethodText(bt) {
  const opts = bt.yield_options || {};
  const best = opts.best;
  const bestText = best
    ? `Current best route: ${best.symbol} on ${best.project} at ${Number(best.apy).toFixed(2)}% APY (${usdShort(best.tvl_usd)} TVL).`
    : "Current best route: unavailable.";
  const basketText = opts.basket_apy !== undefined
    ? `Current basket: ${Number(opts.basket_apy).toFixed(2)}% APY across ${opts.pool_count || 0} pools / ${usdShort(opts.basket_tvl_usd)} TVL.`
    : "Current basket unavailable.";
  return `${bestText} ${basketText}`;
}
function posText(value) {
  if (value > 1) return `${value.toFixed(1)}x long`;
  if (value === 1) return "1x long";
  return "yield";
}
function scale(values, pad = 0.05, floor = 0) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return [Math.max(floor, min - span * pad), max + span * pad];
}
function sharpe(returns) {
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(returns.length - 1, 1);
  return variance ? (mean / Math.sqrt(variance)) * Math.sqrt(365) : 0;
}
function stats(label, returns, equity, cls, liquidation = null) {
  let peak = 1;
  let maxDd = 0;
  equity.forEach((value) => {
    peak = Math.max(peak, value);
    maxDd = Math.min(maxDd, value / peak - 1);
  });
  const x = equity.at(-1);
  return { label, cls, liquidation, sharpe: liquidation ? null : sharpe(returns), x, cagr: x > 0 ? x ** (365 / returns.length) - 1 : -1, maxDd };
}
function equityFromReturns(returns) {
  let value = 1;
  return returns.map((ret) => {
    value *= 1 + ret;
    return value;
  });
}
function modelReturns(points, leverage) {
  const fee = currentBacktest.assumptions.fee_rate;
  let prevPosition = 0;
  const returns = [];
  let liquidation = null;
  for (const p of points) {
    if (liquidation) {
      returns.push(0);
      continue;
    }
    const direction = Math.max(p.direction, 0);
    const position = direction * leverage;
    const turnover = Math.abs(position - prevPosition);
    prevPosition = position;
    const liqDown = direction > 0 && p.next_low > 0 && p.next_low / p.mnt_price - 1 <= -1 / leverage;
    if (leverage > 1 && liqDown) {
      liquidation = { date: p.date, side: "long" };
      returns.push(-1);
      continue;
    }
    returns.push(position * p.mnt_ret_1d - position * p.funding_daily + (position === 0 ? p.yield_daily : 0) - turnover * fee);
  }
  return { returns, liquidation };
}
function buildSeries(bt) {
  const points = bt.points;
  const mntReturns = points.map((p) => p.mnt_ret_1d);
  const btcReturns = points.map((p) => p.btc_ret_1d);
  const model = modelReturns(points, modelLeverage);
  const series = [
    { key: "mnt", label: "MNT", cls: "bt-mnt", returns: mntReturns, equity: equityFromReturns(mntReturns) },
    { key: "btc", label: "BTC", cls: "bt-btc", returns: btcReturns, equity: equityFromReturns(btcReturns) },
    { key: "model", label: "Model Long / Yield", cls: "bt-model", returns: model.returns, equity: equityFromReturns(model.returns), liquidation: model.liquidation },
  ];
  series.forEach((row) => Object.assign(row, stats(row.label, row.returns, row.equity, row.cls, row.liquidation)));
  return series;
}
function xAt(index, count) {
  return PLOT.x + (index / Math.max(count - 1, 1)) * PLOT.w;
}
function linePath(values, yFn) {
  return values.map((value, i) => `${i ? "L" : "M"}${xAt(i, values.length).toFixed(1)},${yFn(value).toFixed(1)}`).join(" ");
}
function tableRows(series) {
  return series.map((row) => `<tr class="${row.liquidation ? "liquidated" : ""}"><td><span class="bt-mode ${row.cls}"><i></i>${row.label}${row.liquidation ? `<b>${row.liquidation.side.toUpperCase()} LIQ ${row.liquidation.date}</b>` : ""}</span></td>
    <td>${row.liquidation ? "LIQ" : num2(row.sharpe)}</td><td class="${row.x >= 1 ? "positive" : "negative"}">${xRet(row.x)}</td>
    <td class="${row.cagr >= 0 ? "positive" : "negative"}">${pct1(row.cagr)}</td>
    <td class="negative">${pct1(row.maxDd)}</td></tr>`).join("");
}
function leverageControl() {
  return `<div class="bt-top"><div class="lev-row"><label>Lev <b>${modelLeverage.toFixed(1)}x</b></label><div class="lev-control">
    <input id="levSlider" type="range" min="1" max="10" step="0.1" value="${modelLeverage}">
    <div class="lev-scale"><span>1x</span><span>10x</span></div></div></div></div>`;
}
function tableShell() {
  return `<div class="bt-table"><table><thead><tr><th class="bt-tip" data-tip="Compared portfolio or benchmark line.">Mode</th><th class="bt-tip" data-tip="Annualized return divided by return volatility. Higher means smoother risk-adjusted performance.">Sharpe</th><th class="bt-tip" data-tip="Final equity multiple. 3.0x means capital tripled.">Return (x)</th><th class="bt-tip" data-tip="Annualized compounded growth rate over the replay window.">CAGR</th><th class="bt-tip" data-tip="Largest peak-to-trough equity loss during the replay.">Max DD</th></tr></thead><tbody id="btRows"></tbody></table></div>`;
}
function scheduleRender() { if (chartFrame) cancelAnimationFrame(chartFrame); chartFrame = requestAnimationFrame(() => { chartFrame = 0; renderBacktest(currentBacktest); }); }
function axisLabels(points, minY, maxY) {
  const equityTicks = [0, .25, .5, .75, 1].map((n) => {
    const value = logScale ? Math.exp(maxY - n * (maxY - minY)) : maxY - n * (maxY - minY);
    return `<text class="equity-axis" x="10" y="${(PLOT.y + n * PLOT.h).toFixed(1)}">${xRet(value)}</text>`;
  }).join("");
  const dateTicks = [0, .25, .5, .75, 1].map((n) => {
    const i = Math.min(points.length - 1, Math.round(n * (points.length - 1)));
    return `<text class="date-axis" x="${xAt(i, points.length).toFixed(1)}" y="372" text-anchor="middle">${points[i].date}</text>`;
  }).join("");
  const grid = [0, .25, .5, .75, 1].map((n) => {
    const y = PLOT.y + n * PLOT.h;
    return `<line class="grid" x1="${PLOT.x}" x2="${PLOT.x + PLOT.w}" y1="${y}" y2="${y}"/>`;
  }).join("");
  return { equityTicks: `<text class="equity-axis axis-label" x="10" y="16">equity</text>${equityTicks}`, dateTicks, grid };
}
function chartSvg(bt, series, yFn, minY, maxY) {
  const points = bt.points;
  const liq = series.find((row) => row.liquidation);
  const liqIndex = liq ? points.findIndex((p) => p.date === liq.liquidation.date) : -1;
  const liqMark = liqIndex >= 0 ? `<line class="liq-line" x1="${xAt(liqIndex, points.length)}" x2="${xAt(liqIndex, points.length)}" y1="${PLOT.y}" y2="${PLOT.y + PLOT.h}"/><text class="liq-text" x="${xAt(liqIndex, points.length) + 6}" y="${PLOT.y + 16}">${liq.liquidation.side.toUpperCase()} LIQ ${liq.liquidation.date}</text>` : "";
  const labels = series.map((row) => `<text class="right-label ${row.cls}" x="900" y="${yFn(row.equity.at(-1)).toFixed(1)}">${row.key === "model" ? "Model" : row.label} ${xRet(row.x)}</text>`).join("");
  const { equityTicks, dateTicks, grid } = axisLabels(points, minY, maxY);
  const lines = series.map((row) => `<path class="line ${row.key}" d="${linePath(row.equity, yFn)}"/>`).join("");
  const dots = series.map((row) => `<circle class="hover-dot ${row.key}" data-dot="${row.key}" r="4"/>`).join("");
  return `<div class="tv-chart" id="tvChart">
    <div class="chart-overlay"><label class="log-toggle"><input id="scaleToggle2" type="checkbox" ${logScale ? "checked" : ""}/> Log</label></div>
    <svg viewBox="0 0 ${CHART_W} ${CHART_H}" role="img">
    ${grid}${equityTicks}${dateTicks}${lines}${liqMark}${labels}
    <line class="hover-line" id="hoverLine" y1="${PLOT.y}" y2="${PLOT.y + PLOT.h}"/>${dots}
    <rect id="hoverPane" x="${PLOT.x}" y="${PLOT.y}" width="${PLOT.w}" height="${PLOT.h}" fill="transparent"/></svg>
    <div class="chart-tip" id="chartTip"></div></div>`;
}
function tooltipHtml(point, series, index) {
  const rows = [
    ["MNT", `$${point.mnt_price.toFixed(4)}`], ["BTC", `$${point.btc_price.toFixed(0)}`],
    ["action", point.direction > 0 ? "long" : "yield"], ["position", posText(Math.max(point.direction, 0) * modelLeverage)],
    ["yield APY", `${point.yield_apy.toFixed(2)}%`], ["funding/day", pct1(point.funding_daily)],
    ...series.map((row) => [row.key === "model" ? "Model" : row.label, xRet(row.equity[index])]),
  ];
  return `<div class="tip-date">${point.date}</div>${rows.map(([k, v]) => `<div class="tip-row"><span>${k}</span><b>${v}</b></div>`).join("")}`;
}
function bindHover(points, series, yFn) {
  const chart = $("tvChart");
  const pane = $("hoverPane");
  pane.addEventListener("mousemove", (event) => {
    const rect = chart.getBoundingClientRect();
    const svgX = ((event.clientX - rect.left) / rect.width) * CHART_W;
    const idx = Math.max(0, Math.min(points.length - 1, Math.round(((svgX - PLOT.x) / PLOT.w) * (points.length - 1))));
    const x = xAt(idx, points.length);
    chart.classList.add("on");
    $("hoverLine").setAttribute("x1", x);
    $("hoverLine").setAttribute("x2", x);
    document.querySelectorAll("[data-dot]").forEach((dot) => {
      const row = series.find((item) => item.key === dot.dataset.dot);
      dot.setAttribute("cx", x);
      dot.setAttribute("cy", yFn(row.equity[idx]).toFixed(1));
    });
    $("chartTip").innerHTML = tooltipHtml(points[idx], series, idx);
    $("chartTip").style.left = `${Math.min(rect.width - 244, Math.max(8, event.clientX - rect.left + 14))}px`;
    $("chartTip").style.top = `${Math.min(rect.height - 236, Math.max(8, event.clientY - rect.top + 10))}px`;
  });
  pane.addEventListener("mouseleave", () => chart.classList.remove("on"));
}
function renderBacktest(bt) {
  currentBacktest = bt;
  const series = buildSeries(bt);
  const values = series.flatMap((row) => row.equity).filter((value) => value > 0);
  const [minY, maxY] = logScale ? scale(values.map(Math.log), 0.05, -Infinity) : scale(series.flatMap((row) => row.equity));
  const yFn = (value) => {
    const scaled = logScale ? Math.log(Math.max(value, Math.exp(minY))) : value;
    return PLOT.y + (1 - (scaled - minY) / (maxY - minY || 1)) * PLOT.h;
  };
  if (!$("btRows")) {
    $("btCards").innerHTML = leverageControl() + tableShell();
    $("levSlider").addEventListener("input", (event) => {
      modelLeverage = Number(event.target.value);
      document.querySelector(".lev-row b").textContent = `${modelLeverage.toFixed(1)}x`;
      scheduleRender();
    });
    $("scaleToggle").addEventListener("change", (event) => { logScale = event.target.checked; renderBacktest(bt); });
  }
  $("btRows").innerHTML = tableRows(series);
  $("btChart").innerHTML = chartSvg(bt, series, yFn, minY, maxY);
  if ($("btRange")) $("btRange").textContent = `${bt.points[0].date} -> ${bt.points.at(-1).date}`;
  if ($("btRange2")) $("btRange2").textContent = `${bt.points[0].date} → ${bt.points.at(-1).date}`;
  if ($("scaleToggle2")) $("scaleToggle2").addEventListener("change", (event) => { logScale = event.target.checked; if ($("scaleToggle")) $("scaleToggle").checked = logScale; renderBacktest(bt); });
  $("btMethod").textContent = `Method: daily close-to-close replay from ${bt.assumptions.backtest_start}; prior data is warmup for walk-forward signal health. Model goes long on positive signals and allocates to stable yield on risk-off or neutral signals. Yield carry is included, but even a few percent APY adds only about 0.01%/day, so flat yield stretches look nearly horizontal at this chart scale. ${yieldMethodText(bt)} Capacity: suitable for modest strategy size; stable-yield capacity depends on Mantle pool TVL, while MNT exposure is constrained by exchange depth, slippage, funding, and borrow/margin availability. Leverage simulation: simplified notional scaling with fees/funding and next-day low liquidation check; it does not model maintenance margin tiers, partial liquidation, intraday order fills, slippage, ADL, or funding changes after entry. Fees: ${bt.assumptions.fee_source} Funding: ${bt.assumptions.funding} Yield: ${bt.assumptions.yield} ${bt.assumptions.leverage}`;
  bindHover(bt.points, series, yFn);
}
