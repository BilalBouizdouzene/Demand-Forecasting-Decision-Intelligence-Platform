const state = {
  health: null,
  overview: null,
  catalog: { stores: [], series: [] },
  decisions: [],
  anomalies: [],
  metrics: [],
  monitoring: { summary: {}, drift: [], performance: [] },
  forecast: null,
};

const numberFormat = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
const decimalFormat = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 });

function $(selector) {
  return document.querySelector(selector);
}

function formatNumber(value) {
  return Number.isFinite(Number(value)) ? numberFormat.format(Number(value)) : "—";
}

function formatDecimal(value) {
  return Number.isFinite(Number(value)) ? decimalFormat.format(Number(value)) : "—";
}

function formatPercent(value, digits = 1) {
  return Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(digits).replace(".", ",")} %` : "—";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${detail || response.statusText}`);
  }
  return response.json();
}

function showNotice(message, isError = false) {
  const notice = $("#app-notice");
  if (!message) {
    notice.classList.add("is-hidden");
    notice.textContent = "";
    return;
  }
  notice.classList.toggle("is-error", isError);
  notice.classList.remove("is-hidden");
  notice.textContent = message;
}

function riskClass(value) {
  return String(value || "unknown").toLowerCase().replaceAll(" ", "-");
}

function riskPill(value) {
  const label = value || "Unknown";
  return `<span class="risk-pill ${riskClass(label)}">${escapeHtml(label)}</span>`;
}

function metricCard(label, value, meta, accent, metaClass = "") {
  return `<article class="metric-card"><span class="metric-label">${escapeHtml(label)}</span><span class="metric-value">${value}</span><span class="metric-meta ${metaClass}">${meta}</span><span class="metric-accent">${accent}</span></article>`;
}

function setApiStatus(healthy, label) {
  const status = $("#api-status");
  status.classList.toggle("is-error", !healthy);
  status.innerHTML = `<span class="status-dot"></span><span>${escapeHtml(label)}</span>`;
}

function showView(view) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => panel.classList.toggle("is-visible", panel.dataset.viewPanel === view));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
  const active = document.querySelector(`.nav-item[data-view="${view}"]`);
  const title = active?.dataset.title || "Overview";
  $("#breadcrumb-title").textContent = title;
  if (view === "models") renderModels();
  if (view === "monitoring") renderMonitoring();
  if (view === "decisions") renderDecisions();
  requestAnimationFrame(drawVisibleCharts);
}

function bindNavigation() {
  document.querySelectorAll("[data-view]").forEach((element) => element.addEventListener("click", () => showView(element.dataset.view)));
  document.querySelectorAll("[data-view-target]").forEach((element) => element.addEventListener("click", () => showView(element.dataset.viewTarget)));
  $("#refresh-button").addEventListener("click", () => loadWorkspace(true));
  $("#risk-filter").addEventListener("change", renderDecisions);
  $("#load-forecast").addEventListener("click", loadSelectedForecast);
  $("#forecast-store").addEventListener("change", updateItemOptions);
  $("#forecast-horizon").addEventListener("change", loadSelectedForecast);
  window.addEventListener("resize", () => requestAnimationFrame(drawVisibleCharts));
}

function renderOverview() {
  const overview = state.overview || {};
  const decisions = state.decisions || [];
  const metrics = state.metrics || [];
  const anomalyCount = Number(overview.anomaly_flags || 0);
  const avgWape = overview.avg_wape;
  $("#overview-metrics").innerHTML = [
    metricCard("Forecast units · next 7 days", formatNumber(overview.forecast_units_next_7d), `<span class="positive">${formatNumber(overview.forecast_series)} series</span> in scope`, "↗"),
    metricCard("High / critical stockouts", formatNumber(overview.high_risk_series), `<span class="attention">Planner review</span> recommended`, "!", "attention"),
    metricCard("Operational WAPE", avgWape ? formatPercent(avgWape) : "—", `<span class="positive">Ridge</span> average across horizons`, "◎"),
    metricCard("Anomaly flags", formatNumber(anomalyCount), `<span>Residual deviations in validation</span>`, "⌁"),
  ].join("");
  $("#forecast-date-label").textContent = `Forecast as of ${overview.forecast_date || "—"}`;
  $("#model-badge-text").textContent = `${state.modelInfo?.model_name || "Ridge"} · active`;
  $("#nav-risk-count").textContent = formatNumber(overview.high_risk_series);

  const highRisk = decisions.filter((row) => ["HIGH", "CRITICAL"].includes(String(row.stockout_risk))).length;
  $("#insight-title").textContent = highRisk ? `${formatNumber(highRisk)} series need review` : "No urgent stockout signal";
  $("#insight-copy").textContent = highRisk ? "The current stock estimate shows several series that need a planner review." : "Current risk signals remain within the configured service-level guardrails.";
  const top = [...decisions].sort((a, b) => Number(b.priority_score || 0) - Number(a.priority_score || 0))[0];
  $("#insight-list").innerHTML = top ? `<div class="insight-row"><span>Top priority</span><strong>${escapeHtml(top.store_id)} · ${escapeHtml(top.item_id)}</strong></div><div class="insight-row"><span>Recommended order</span><strong>${formatNumber(top.recommended_order_qty)} units</strong></div><div class="insight-row"><span>Model horizon</span><strong>28 days</strong></div>` : `<div class="insight-row"><span>Decision artifact</span><strong>Not available</strong></div>`;

  $("#overview-decisions").innerHTML = topDecisions(5);
  renderRiskBars();
}

function topDecisions(limit = 5) {
  return [...state.decisions]
    .sort((a, b) => Number(b.priority_score || 0) - Number(a.priority_score || 0))
    .slice(0, limit)
    .map((row) => `<tr><td><div class="series-cell"><span class="series-avatar">${escapeHtml(String(row.store_id || "").slice(0, 2))}</span><span><strong>${escapeHtml(row.store_id)}</strong><br /><small>${escapeHtml(row.item_id)}</small></span></div></td><td>${riskPill(row.stockout_risk)}</td><td><strong>${formatNumber(row.recommended_order_qty)}</strong></td><td><span class="score">${formatDecimal(row.priority_score)}</span></td></tr>`)
    .join("") || `<tr><td colspan="4">No decision artifact available.</td></tr>`;
}

function renderRiskBars() {
  const counts = ["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((risk) => ({ risk, count: state.decisions.filter((row) => String(row.stockout_risk).toUpperCase() === risk).length }));
  const total = Math.max(state.decisions.length, 1);
  $("#risk-bars").innerHTML = counts.map(({ risk, count }) => `<div class="risk-bar-row"><div class="risk-bar-heading"><span>${risk[0] + risk.slice(1).toLowerCase()}</span><strong>${formatNumber(count)}</strong></div><div class="risk-bar-track"><div class="risk-bar-fill ${riskClass(risk)}" style="width:${Math.max(2, (count / total) * 100)}%"></div></div></div>`).join("");
}

function populateCatalog() {
  const storeSelect = $("#forecast-store");
  storeSelect.innerHTML = state.catalog.stores.map((store) => `<option value="${escapeHtml(store)}">${escapeHtml(store)}</option>`).join("");
  updateItemOptions();
}

function updateItemOptions() {
  const store = $("#forecast-store").value;
  const itemSelect = $("#forecast-item");
  const items = state.catalog.series.filter((entry) => entry.store_id === store).map((entry) => entry.item_id);
  itemSelect.innerHTML = items.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");
  if (items.length) loadSelectedForecast();
}

async function loadSelectedForecast() {
  const store = $("#forecast-store").value;
  const item = $("#forecast-item").value;
  const horizon = $("#forecast-horizon").value;
  if (!store || !item) return;
  const button = $("#load-forecast");
  button.disabled = true;
  button.innerHTML = "Loading…";
  try {
    state.forecast = await api(`/forecast/${encodeURIComponent(store)}/${encodeURIComponent(item)}?horizon=${horizon}`);
    renderForecastExplorer();
    requestAnimationFrame(drawVisibleCharts);
  } catch (error) {
    showNotice(`Unable to load this series: ${error.message}`, true);
  } finally {
    button.disabled = false;
    button.innerHTML = "Load series <span>→</span>";
  }
}

function renderForecastExplorer() {
  const forecast = state.forecast;
  if (!forecast) return;
  const store = escapeHtml(forecast.store_id);
  const item = escapeHtml(forecast.item_id);
  const total = forecast.forecast.reduce((sum, value) => sum + Number(value || 0), 0);
  const upper = forecast.upper_bound.reduce((sum, value) => sum + Number(value || 0), 0);
  $("#selected-series-title").textContent = `${store} · ${item}`;
  $("#forecast-model-badge").textContent = forecast.model_version || "Ridge";
  $("#series-risk-label").innerHTML = riskPill(forecast.stockout_risk);
  $("#forecast-metrics").innerHTML = [
    metricCard("Forecast demand", `${formatNumber(total)} <small>units</small>`, `Next ${forecast.horizon} days`, "↗"),
    metricCard("Upper uncertainty", `${formatNumber(upper)} <small>units</small>`, "90% calibrated range", "⌁"),
    metricCard("Recommended order", `${formatNumber(forecast.recommended_order_qty)} <small>units</small>`, `${escapeHtml(forecast.stockout_risk)} stockout risk`, "!", "attention"),
  ].join("");
  $("#series-decision-hero").innerHTML = `<span class="risk-pill ${riskClass(forecast.stockout_risk)}">${escapeHtml(forecast.stockout_risk)}</span><strong>${formatNumber(forecast.recommended_order_qty)} units to consider</strong><p>Recommended quantity from the inventory decision layer for this series.</p>`;
  $("#series-detail-stats").innerHTML = `<div class="detail-stat"><span>Model version</span><strong>${escapeHtml(forecast.model_version)}</strong></div><div class="detail-stat"><span>Forecast horizon</span><strong>${formatNumber(forecast.horizon)} days</strong></div>`;
  const start = state.overview?.forecast_date ? new Date(`${state.overview.forecast_date}T00:00:00`) : new Date();
  $("#series-table").innerHTML = forecast.forecast.map((value, index) => {
    const date = new Date(start);
    date.setDate(date.getDate() + index + 1);
    return `<tr><td><strong>${date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" })}</strong></td><td>J+${index + 1}</td><td><strong>${formatDecimal(value)}</strong></td><td>${formatDecimal(forecast.lower_bound[index])}</td><td>${formatDecimal(forecast.upper_bound[index])}</td></tr>`;
  }).join("");
}

function renderDecisions() {
  const rows = [...state.decisions].sort((a, b) => Number(b.priority_score || 0) - Number(a.priority_score || 0));
  const filter = $("#risk-filter")?.value || "ALL";
  const filtered = filter === "ALL" ? rows : rows.filter((row) => String(row.stockout_risk).toUpperCase() === filter);
  const critical = rows.filter((row) => String(row.stockout_risk).toUpperCase() === "CRITICAL").length;
  const high = rows.filter((row) => String(row.stockout_risk).toUpperCase() === "HIGH").length;
  const totalOrder = rows.reduce((sum, row) => sum + Number(row.recommended_order_qty || 0), 0);
  $("#decision-metrics").innerHTML = [
    metricCard("Series in queue", formatNumber(rows.length), `<span>${formatNumber(critical + high)} high / critical</span>`, "#"),
    metricCard("Units to consider", formatNumber(totalOrder), "Across all priority recommendations", "↗"),
    metricCard("Service level", "95 %", "Configured decision target", "✓"),
  ].join("");
  $("#decisions-table").innerHTML = filtered.map((row) => `<tr><td><strong>${escapeHtml(row.store_id)}</strong></td><td>${escapeHtml(row.item_id)}</td><td><strong>${formatDecimal(row.forecast_7d)}</strong></td><td>${formatDecimal(row.simulated_stock)}</td><td>${riskPill(row.stockout_risk)}</td><td><strong>${formatNumber(row.recommended_order_qty)} units</strong></td><td><span class="score">${formatDecimal(row.priority_score)}</span></td></tr>`).join("") || `<tr><td colspan="7">No rows match this filter.</td></tr>`;
  $("#decision-row-count").textContent = `${formatNumber(filtered.length)} rows shown`;
}

function aggregateMetrics() {
  const grouped = new Map();
  state.metrics.forEach((row) => {
    const model = String(row.model || "Unknown");
    if (!grouped.has(model)) grouped.set(model, []);
    grouped.get(model).push(Number(row.wape));
  });
  return [...grouped.entries()].map(([model, values]) => ({ model, value: values.reduce((a, b) => a + b, 0) / values.length })).sort((a, b) => a.value - b.value);
}

function renderModels() {
  const info = state.health || {};
  const rows = [...state.metrics].sort((a, b) => Number(a.horizon) - Number(b.horizon) || Number(a.wape) - Number(b.wape));
  $("#metrics-table").innerHTML = rows.map((row) => `<tr><td><strong>${escapeHtml(row.model)}</strong></td><td>H+${escapeHtml(row.horizon)}</td><td><strong>${formatPercent(row.wape)}</strong></td><td>${formatDecimal(row.mae)}</td><td>${formatDecimal(row.rmse)}</td><td>${escapeHtml(row.benchmark_type || "—")}</td></tr>`).join("") || `<tr><td colspan="6">Benchmark artifact not available.</td></tr>`;
  $("#operational-version").textContent = info.model_version || state.overview?.model_version || "—";
  $("#feature-count").textContent = state.modelInfo?.feature_count ? formatNumber(state.modelInfo.feature_count) : "53";
}

function renderMonitoring() {
  const summary = state.monitoring.summary || {};
  const action = String(summary.action || "No report");
  const recommended = Boolean(summary.retraining_recommended);
  $("#monitoring-action-badge").innerHTML = `<span class="badge-dot"></span>${escapeHtml(action)}`;
  $("#monitoring-metrics").innerHTML = [
    metricCard("Drift signals", formatNumber(summary.data_drift_rows), "Feature-level report rows", "⌁"),
    metricCard("Performance periods", formatNumber(summary.performance_periods), "Chronological windows", "◷"),
    metricCard("Degradation ratio", formatPercent(summary.degradation_ratio), `<span class="${recommended ? "attention" : "positive"}">${recommended ? "Retraining advised" : "Below threshold"}</span>`, recommended ? "!" : "✓"),
  ].join("");
  $("#monitoring-decision-title").textContent = recommended ? "Review retraining" : "Continue monitoring";
  const status = $("#monitoring-status");
  status.classList.toggle("warning", recommended);
  status.innerHTML = `<span class="status-icon">${recommended ? "!" : "✓"}</span><span>${escapeHtml(action)}</span>`;
  const driftRows = state.monitoring.drift || [];
  $("#drift-table").innerHTML = driftRows.map((row) => `<tr><td><strong>${escapeHtml(row.feature || row.column || "Feature")}</strong></td><td>PSI</td><td>Reference</td><td>${formatDecimal(row.psi)}</td><td><span class="status-cell ${row.drift_flag ? "warning" : ""}">${row.drift_flag ? "Review" : "Stable"}</span></td></tr>`).join("") || `<tr><td colspan="5">Drift report not available.</td></tr>`;
}

function drawVisibleCharts() {
  if ($("#view-overview").classList.contains("is-visible")) drawOverviewChart();
  if ($("#view-forecasts").classList.contains("is-visible")) drawSeriesChart();
  if ($("#view-models").classList.contains("is-visible")) drawModelChart();
  if ($("#view-monitoring").classList.contains("is-visible")) drawMonitoringChart();
}

function prepareCanvas(canvas) {
  if (!canvas) return null;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  return { ctx, width: rect.width, height: rect.height };
}

function chartFrame(canvas, labelCount = 5) {
  const prepared = prepareCanvas(canvas);
  if (!prepared) return null;
  const { ctx, width, height } = prepared;
  const pad = { top: 15, right: 12, bottom: 28, left: 42 };
  ctx.clearRect(0, 0, width, height);
  ctx.font = "10px Inter, system-ui, sans-serif";
  ctx.fillStyle = "#9aa6b6";
  ctx.strokeStyle = "#edf1f5";
  ctx.lineWidth = 1;
  for (let index = 0; index < 4; index += 1) {
    const y = pad.top + ((height - pad.top - pad.bottom) * index) / 3;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
  }
  return { ctx, width, height, pad, innerWidth: width - pad.left - pad.right, innerHeight: height - pad.top - pad.bottom, labelCount };
}

function drawLineChart(canvas, values, options = {}) {
  const frame = chartFrame(canvas, options.labels?.length || 5);
  if (!frame || !values?.length) return;
  const { ctx, width, height, pad, innerWidth, innerHeight } = frame;
  const low = Math.min(...values, ...(options.lower || values));
  const high = Math.max(...values, ...(options.upper || values), low + 1);
  const x = (index) => pad.left + (innerWidth * index) / Math.max(values.length - 1, 1);
  const y = (value) => pad.top + innerHeight - ((value - low) / (high - low)) * innerHeight;

  if (options.lower && options.upper) {
    ctx.beginPath();
    options.upper.forEach((value, index) => { const pointX = x(index); const pointY = y(value); if (index === 0) ctx.moveTo(pointX, pointY); else ctx.lineTo(pointX, pointY); });
    [...options.lower].reverse().forEach((value, reverseIndex) => ctx.lineTo(x(options.lower.length - 1 - reverseIndex), y(value)));
    ctx.closePath(); ctx.fillStyle = "rgba(21, 184, 166, 0.12)"; ctx.fill();
  }
  ctx.beginPath();
  values.forEach((value, index) => { const pointX = x(index); const pointY = y(value); if (index === 0) ctx.moveTo(pointX, pointY); else ctx.lineTo(pointX, pointY); });
  ctx.strokeStyle = options.color || "#15b8a6"; ctx.lineWidth = 2.3; ctx.lineJoin = "round"; ctx.lineCap = "round"; ctx.stroke();
  values.forEach((value, index) => { if (values.length > 14 && index % 4 !== 0 && index !== values.length - 1) return; ctx.beginPath(); ctx.arc(x(index), y(value), 2.8, 0, Math.PI * 2); ctx.fillStyle = options.color || "#15b8a6"; ctx.fill(); });
  const labels = options.labels || [];
  labels.forEach((label, index) => { if (labels.length > 8 && index % Math.ceil(labels.length / 6) !== 0 && index !== labels.length - 1) return; ctx.fillStyle = "#9aa6b6"; ctx.textAlign = index === 0 ? "left" : index === labels.length - 1 ? "right" : "center"; ctx.fillText(label, x(index), height - 8); });
  ctx.textAlign = "right";
  [high, low + (high - low) / 2, low].forEach((value, index) => { ctx.fillStyle = "#a1adbc"; ctx.fillText(formatNumber(value), pad.left - 8, pad.top + (innerHeight * index) / 2 + 3); });
}

function drawOverviewChart() {
  const curve = state.overview?.forecast_curve || [];
  drawLineChart($("#overview-chart"), curve.map((row) => Number(row.forecast)), { labels: curve.map((row) => `J+${row.horizon}`), color: "#15b8a6" });
}

function drawSeriesChart() {
  if (!state.forecast) return;
  drawLineChart($("#series-chart"), state.forecast.forecast, { lower: state.forecast.lower_bound, upper: state.forecast.upper_bound, labels: state.forecast.forecast.map((_, index) => `J+${index + 1}`), color: "#5576dd" });
}

function drawBarChart(canvas, values, labels) {
  const frame = chartFrame(canvas, labels.length);
  if (!frame || !values.length) return;
  const { ctx, width, height, pad, innerWidth, innerHeight } = frame;
  const max = Math.max(...values, 0.1);
  const slot = innerWidth / values.length;
  values.forEach((value, index) => {
    const barWidth = Math.min(58, slot * 0.52);
    const barHeight = (value / max) * innerHeight;
    const barX = pad.left + slot * index + (slot - barWidth) / 2;
    const barY = pad.top + innerHeight - barHeight;
    ctx.fillStyle = index === 0 ? "#15b8a6" : "#bac6f0";
    ctx.beginPath(); ctx.roundRect(barX, barY, barWidth, barHeight, 5); ctx.fill();
    ctx.fillStyle = "#68778d"; ctx.textAlign = "center"; ctx.font = "10px Inter, system-ui, sans-serif"; ctx.fillText(formatPercent(value), barX + barWidth / 2, barY - 8);
    ctx.fillStyle = "#9aa6b6"; ctx.fillText(labels[index].length > 13 ? `${labels[index].slice(0, 11)}…` : labels[index], barX + barWidth / 2, height - 8);
  });
}

function drawModelChart() {
  const aggregated = aggregateMetrics();
  drawBarChart($("#model-chart"), aggregated.map((entry) => entry.value), aggregated.map((entry) => entry.model));
}

function drawMonitoringChart() {
  const rows = state.monitoring.performance || [];
  drawLineChart($("#monitoring-chart"), rows.map((row) => Number(row.mae)), { labels: rows.map((row) => String(row.period || "").slice(5, 10)), color: "#8c71d3" });
}

async function loadWorkspace(showRefreshMessage = false) {
  if (showRefreshMessage) showNotice("Refreshing the workspace…");
  try {
    const [health, overview, catalog, decisions, anomalies, metrics, monitoring, modelInfo] = await Promise.all([
      api("/health"), api("/overview"), api("/catalog"), api("/decisions"), api("/anomalies"), api("/metrics"), api("/monitoring"), api("/model/info"),
    ]);
    state.health = health; state.overview = overview; state.catalog = catalog; state.decisions = decisions; state.anomalies = anomalies; state.metrics = metrics; state.monitoring = monitoring; state.modelInfo = modelInfo;
    setApiStatus(true, "API connected");
    renderOverview(); populateCatalog(); renderDecisions(); renderModels(); renderMonitoring();
    if (showRefreshMessage) showNotice("Workspace refreshed successfully.");
    setTimeout(() => showNotice(""), 2600);
    requestAnimationFrame(drawVisibleCharts);
  } catch (error) {
    setApiStatus(false, "API unavailable");
    showNotice(`The workspace could not load its data. Start the API and refresh. (${error.message})`, true);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  bindNavigation();
  loadWorkspace();
});
