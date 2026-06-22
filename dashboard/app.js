/*
  Monitoring Rakyat dashboard bridge.

  Contract:
  - Dashboard reads only dashboard_summary.json for public-facing totals.
  - Fiscal ratio chart reads fiscal_ratio_annual.json, a lightweight yearly aggregate.
  - Raw CSV stays in gudang-db/ as the source of truth.
  - AI tools use gudang-db/_index/ai_index.json to find module/year files.
*/

const SUMMARY_PATH = "dashboard_summary.json";
const FISCAL_RATIO_PATH = "fiscal_ratio_annual.json";
const NEMESIS_STATUS_PATH = "nemesis_integration_status.json";
const READINESS_PATH = "pre_github_readiness.json";
const AI_TASKS_PATH = "ai_agent_tasks.json";
const SOURCE_PATROL_PATH = "ai_agent_source_patrol.json";
const AI_ORCHESTRATOR_PATH = "ai_orchestrator_status.json";
const AI_INDEX_PATH = "../gudang-db/_index/ai_index.json";
const GUDANG_DB_REPO_LINK = "../gudang-db/index.html";

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

function fmtIDR(value) {
  const n = Number(value || 0);
  if (n >= 1e12) return `Rp ${(n / 1e12).toFixed(2).replace(".00", "")} T`;
  if (n >= 1e9) return `Rp ${(n / 1e9).toFixed(2).replace(".00", "")} M`;
  if (n >= 1e6) return `Rp ${(n / 1e6).toFixed(2).replace(".00", "")} Jt`;
  return `Rp ${Math.round(n).toLocaleString("id-ID")}`;
}

function ensureGudangPanel() {
  let panel = document.getElementById("mr-gudang-db-panel");
  if (panel) return panel;

  const target =
    document.querySelector(".hero") ||
    document.querySelector(".page.active") ||
    document.body;

  panel = document.createElement("section");
  panel.id = "mr-gudang-db-panel";
  panel.style.cssText = [
    "background:#111827",
    "border-top:1px solid #2e3248",
    "border-bottom:1px solid #2e3248",
    "padding:16px 28px",
    "color:#f1f5f9",
    "font-family:Inter,Arial,sans-serif"
  ].join(";");

  if (target === document.body) {
    document.body.insertBefore(panel, document.body.firstChild);
  } else {
    target.insertAdjacentElement("afterend", panel);
  }

  return panel;
}

function renderMiniTrend(history) {
  if (!history || !Object.keys(history).length) return "";
  const years = Object.keys(history).sort();
  const max = Math.max(...years.map((year) => Number(history[year] || 0)), 1);
  const bars = years
    .map((year) => {
      const val = Number(history[year] || 0);
      const width = Math.max(4, Math.round((val / max) * 100));
      return `
        <div style="display:grid;grid-template-columns:52px 1fr 90px;gap:8px;align-items:center">
          <span style="color:#94a3b8;font-size:12px">${year}</span>
          <span style="height:8px;background:#1f2937;border-radius:999px;overflow:hidden">
            <span style="display:block;height:8px;width:${width}%;background:#f59e0b"></span>
          </span>
          <span style="color:#cbd5e1;font-size:12px;text-align:right">${fmtIDR(val)}</span>
        </div>`;
    })
    .join("");
  return `<div style="display:grid;gap:6px;margin-top:10px">${bars}</div>`;
}

function renderReadiness(readiness) {
  if (!readiness) return "";
  const ok = readiness.status && !String(readiness.status).includes("NEEDS_WORK");
  const color = ok ? "#22c55e" : "#f59e0b";
  const blockers = Array.isArray(readiness.blockers) && readiness.blockers.length
    ? readiness.blockers.slice(0, 2).map((item) => `<li>${item}</li>`).join("")
    : "<li>Gate periode berjalan tidak menemukan blocker.</li>";
  return `
    <div style="margin-top:12px;border:1px solid ${color};border-radius:8px;padding:10px;background:#0f1117">
      <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <b style="color:${color};font-size:12px">Pre-GitHub Readiness: ${readiness.status || "-"}</b>
        <span style="color:#cbd5e1;font-size:11px">Rill bulan berjalan: ${readiness.current_period_rill_rows ?? 0}</span>
      </div>
      <ul style="margin:8px 0 0 16px;color:#94a3b8;font-size:11px;line-height:1.5">${blockers}</ul>
    </div>`;
}

function renderAgentTasks(tasks) {
  if (!Array.isArray(tasks) || !tasks.length) return "";
  const top = tasks.slice(0, 5);
  return `
    <div style="margin-top:12px;border:1px solid #334155;border-radius:8px;padding:10px;background:#0f1117">
      <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <b style="color:#7dd3fc;font-size:12px">Tim AI Agent: Proactive DB Search Queue</b>
        <span style="color:#cbd5e1;font-size:11px">${tasks.length} tugas aktif</span>
      </div>
      <div style="display:grid;gap:6px;margin-top:8px">
        ${top.map((task) => `
          <div style="border-top:1px solid #1f2937;padding-top:6px;color:#94a3b8;font-size:11px;line-height:1.5">
            <b style="color:#f8fafc">${task.module}</b> ${task.month}/${task.year}
            <span style="color:${task.priority === "HIGH" ? "#f87171" : "#f59e0b"}"> ${task.priority}</span><br>
            ${task.fallback_note || "Belum ada fallback lokal."}<br>
            Sumber prioritas: ${(task.source_priorities || []).slice(0, 3).join(", ")}
          </div>`).join("")}
      </div>
    </div>`;
}

function renderSourcePatrol(patrolPayload) {
  const patrol = patrolPayload && Array.isArray(patrolPayload.patrol) ? patrolPayload.patrol : [];
  if (!patrol.length) return "";
  const totalPatrol = Number(patrolPayload.patrol_count || patrol.length);
  const sources = [...new Set(patrol.map((item) => item.source).filter(Boolean))].slice(0, 10);
  const countByCategory = patrol.reduce((acc, item) => {
    acc[item.category || "UNKNOWN"] = (acc[item.category || "UNKNOWN"] || 0) + 1;
    return acc;
  }, {});
  return `
    <div style="margin-top:12px;border:1px solid #334155;border-radius:8px;padding:10px;background:#0f1117">
      <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <b style="color:#a7f3d0;font-size:12px">Source Patrol 24/7</b>
        <span style="color:#cbd5e1;font-size:11px">${totalPatrol} query/source pending</span>
      </div>
      <p style="margin:8px 0 0;color:#94a3b8;font-size:11px;line-height:1.5">
        Sumber: ${sources.join(", ")}. Kategori: ${Object.entries(countByCategory).map(([k, v]) => `${k}:${v}`).join(", ")}.
      </p>
    </div>`;
}

function renderNemesisStatus(status) {
  if (!status) return "";
  const color = status.input_present ? "#22c55e" : "#f59e0b";
  const note = status.input_present
    ? `${status.candidates_written || 0} kandidat pengadaan masuk draft queue.`
    : "Belum ada dump lokal di intake, tetapi jalur import sudah siap.";
  return `
    <div style="margin-top:12px;border:1px solid ${color}66;border-radius:8px;padding:10px;background:#0f1117">
      <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <b style="color:${color};font-size:12px">Nemesis Procurement Signal</b>
        <span style="color:#cbd5e1;font-size:11px">${status.input_present ? "INTAKE_READY" : "WAITING_INTAKE"}</span>
      </div>
      <p style="margin:8px 0 0;color:#94a3b8;font-size:11px;line-height:1.5">
        ${note} Status default: ${status.default_status || "DRAFT_REVIEW"}.
        Guard: klasifikasi AI harus cross-check LKPP/SiRUP sebelum menjadi data final.
      </p>
    </div>`;
}

function renderOrchestratorStatus(status) {
  if (!status) return "";
  const top = Array.isArray(status.top_candidates) ? status.top_candidates.slice(0, 5) : [];
  const byStatus = status.by_status || {};
  const taskCounts = status.task_counts || {};
  const controller = status.daily_flow_controller || {};
  const statusText = Object.entries(byStatus).map(([key, value]) => `${key}:${value}`).join(", ") || "draft queue kosong";
  return `
    <div style="margin-top:12px;border:1px solid #f59e0b66;border-radius:8px;padding:10px;background:#1f1304">
      <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <b style="color:#fbbf24;font-size:12px">AI Pengawas Orchestrator 24/7</b>
        <span style="color:#fde68a;font-size:11px">${status.total_candidates || 0} kandidat DB</span>
      </div>
      <p style="margin:8px 0 0;color:#cbd5e1;font-size:11px;line-height:1.5">
        Scope: ${status.cashflow_scope || "ALL_APBN_APBD_RP1_TRACE"}.
        Kandidat baru run terakhir: ${status.new_candidates_this_run || 0}.
        Task historis wajib: ${taskCounts.historical_backfill || 0}.
        Status: ${statusText}.
      </p>
      ${controller.id ? `
        <p style="margin:8px 0 0;color:#fde68a;font-size:11px;line-height:1.5">
          Koordinator harian: <b>${controller.name || controller.id}</b>.
          Tugas permanen: ${(controller.daily_hardcoded_tasks || []).slice(0, 4).join(", ")}.
        </p>` : ""}
      ${top.length ? `
        <div style="display:grid;gap:6px;margin-top:8px">
          ${top.map((item) => `
            <div style="border-top:1px solid #3b2a0b;padding-top:6px;color:#cbd5e1;font-size:11px;line-height:1.45">
              <b style="color:#fff">${item.module || "-"}</b>
              <span style="color:#fbbf24">${item.confidence || 0}</span>
              <span style="color:#94a3b8">${item.status || "DRAFT_REVIEW"}</span><br>
              ${(item.title || "").slice(0, 130)}
            </div>`).join("")}
        </div>` : ""}
    </div>`;
}

function formatTrillion(value) {
  const n = Number(value || 0);
  if (!n) return "Kosong";
  return n.toFixed(n >= 100 ? 0 : 1).replace(".0", "");
}

function renderFiscalRatioChart(payload) {
  const chart = document.getElementById("cmp-chart");
  if (!chart || !payload || !Array.isArray(payload.data)) return false;

  const minimumYears = Math.max(10, Number(payload.minimum_years || 10));
  const rows = payload.data
    .filter((row) => row && row.year)
    .sort((a, b) => Number(a.year) - Number(b.year))
    .slice(-Math.max(minimumYears, Number(payload.trend_years || minimumYears)));

  if (!rows.length) return false;

  const maxVal = Math.max(
    ...rows.map((row) => Math.max(
      Number(row.belanja_apbn_t || 0),
      Number(row.pendapatan_pajak_t || 0),
      Number(row.hasil_sda_t || 0)
    )),
    1
  );
  const barHeight = (value) => {
    const n = Number(value || 0);
    return n > 0 ? Math.max(4, Math.round((n / maxVal) * 200)) : 2;
  };

  chart.dataset.source = "fiscal_ratio_annual.json";
  chart.dataset.minimumYears = String(minimumYears);
  chart.innerHTML = rows.map((row) => {
    const year = row.year;
    const apbn = Number(row.belanja_apbn_t || 0);
    const pajak = Number(row.pendapatan_pajak_t || 0);
    const sda = Number(row.hasil_sda_t || 0);
    return `
      <div class="cmp-group" title="Sinkron Gudang DB ${year}: ${row.status || "UNKNOWN"}">
        <div class="cmp-bars">
          <div class="cmp-bar b-apbn" title="Belanja APBN ${year}: ${formatTrillion(apbn)} Rp T" style="height:${barHeight(apbn)}px;opacity:${apbn ? 1 : .28}"><span class="cmp-val">${formatTrillion(apbn)}</span></div>
          <div class="cmp-bar b-pajak" title="Pendapatan Pajak ${year}: ${formatTrillion(pajak)} Rp T" style="height:${barHeight(pajak)}px;opacity:${pajak ? 1 : .28}"><span class="cmp-val">${formatTrillion(pajak)}</span></div>
          <div class="cmp-bar b-sda" title="Hasil SDA ${year}: ${formatTrillion(sda)} Rp T" style="height:${barHeight(sda)}px;opacity:${sda ? 1 : .28}"><span class="cmp-val">${formatTrillion(sda)}</span></div>
        </div>
        <div class="cmp-year">${year}</div>
      </div>`;
  }).join("");

  const desc = chart.closest(".sec")?.querySelector(".sec-desc");
  if (desc && !desc.dataset.fiscalRatioSync) {
    desc.dataset.fiscalRatioSync = "1";
    desc.innerHTML += `<br><span style="color:#7dd3fc">Sinkron Gudang DB: ${payload.data.length} baris agregasi tahunan, minimum ${minimumYears} tahun. Tahun kosong bukan simulasi, melainkan menunggu CSV resmi.</span>`;
  }
  return true;
}

function installFiscalRatioRenderer(payload) {
  if (!payload) return;
  window.MR_FISCAL_RATIO_PAYLOAD = payload;
  const oldRenderer = window.renderCmpChart;
  window.renderCmpChart = function renderCmpChartFromGudangDb() {
    if (!renderFiscalRatioChart(window.MR_FISCAL_RATIO_PAYLOAD) && typeof oldRenderer === "function") {
      oldRenderer();
    }
  };
  window.renderCmpChart();
}

function renderGudangPanel(summary, aiIndex, readiness, tasks, patrol, orchestrator, nemesisStatus) {
  const panel = ensureGudangPanel();
  const moduleCount = aiIndex && aiIndex.modules ? Object.keys(aiIndex.modules).length : 0;
  const masterCount = aiIndex && Array.isArray(aiIndex.master_files) ? aiIndex.master_files.length : 0;
  const note = summary && summary.catatan ? summary.catatan : "Update angka ini dari hasil agregasi Gudang DB.";

  panel.innerHTML = `
    <div style="max-width:1200px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr);gap:16px;align-items:start">
      <div>
        <div style="color:#f59e0b;font-size:12px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase">Gudang DB Nasional aktif</div>
        <h2 style="margin:4px 0 8px;font-size:20px;line-height:1.2;color:#fff">Dashboard ringan, data mentah tetap lengkap di Gudang DB</h2>
        <p style="margin:0;color:#94a3b8;font-size:13px;line-height:1.6">
          Data yang tampil di dashboard adalah ringkasan tahun berjalan. Untuk audit forensik mandiri,
          buka CSV asli per modul dan per tahun di repositori Gudang DB.
        </p>
        ${renderReadiness(readiness)}
        ${renderAgentTasks(tasks)}
        ${renderSourcePatrol(patrol)}
        ${renderNemesisStatus(nemesisStatus)}
        ${renderOrchestratorStatus(orchestrator)}
        ${renderMiniTrend(summary && summary.history_akumulasi)}
      </div>
      <div style="border:1px solid #2e3248;border-radius:8px;padding:12px;background:#0f1117">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div><div style="color:#94a3b8;font-size:11px">Tahun</div><b>${summary ? summary.tahun : "-"}</b></div>
          <div><div style="color:#94a3b8;font-size:11px">Kasus</div><b>${summary ? summary.jumlah_kasus : "-"}</b></div>
          <div><div style="color:#94a3b8;font-size:11px">Kerugian</div><b>${summary ? fmtIDR(summary.kerugian_total) : "-"}</b></div>
          <div><div style="color:#94a3b8;font-size:11px">Recovery</div><b>${summary ? fmtIDR(summary.recovery_total) : "-"}</b></div>
          <div><div style="color:#94a3b8;font-size:11px">Modul AI</div><b>${moduleCount || "-"}</b></div>
          <div><div style="color:#94a3b8;font-size:11px">Master</div><b>${masterCount || "-"}</b></div>
        </div>
        <p style="margin:10px 0;color:#64748b;font-size:11px;line-height:1.5">${note}</p>
        <a href="${GUDANG_DB_REPO_LINK}" target="_blank" rel="noopener"
           style="display:inline-flex;align-items:center;justify-content:center;border-radius:6px;background:#f59e0b;color:#111827;padding:8px 10px;text-decoration:none;font-size:12px;font-weight:800">
          Buka Gudang Data Rakyat
        </a>
      </div>
    </div>`;
}

document.addEventListener("DOMContentLoaded", async () => {
  const [summaryResult, fiscalRatioResult, nemesisResult, aiIndexResult, readinessResult, tasksResult, patrolResult, orchestratorResult] = await Promise.allSettled([
    fetchJson(SUMMARY_PATH),
    fetchJson(FISCAL_RATIO_PATH),
    fetchJson(NEMESIS_STATUS_PATH),
    fetchJson(AI_INDEX_PATH),
    fetchJson(READINESS_PATH),
    fetchJson(AI_TASKS_PATH),
    fetchJson(SOURCE_PATROL_PATH),
    fetchJson(AI_ORCHESTRATOR_PATH)
  ]);

  renderGudangPanel(
    summaryResult.status === "fulfilled" ? summaryResult.value : null,
    aiIndexResult.status === "fulfilled" ? aiIndexResult.value : null,
    readinessResult.status === "fulfilled" ? readinessResult.value : null,
    tasksResult.status === "fulfilled" ? tasksResult.value : null,
    patrolResult.status === "fulfilled" ? patrolResult.value : null,
    orchestratorResult.status === "fulfilled" ? orchestratorResult.value : null,
    nemesisResult.status === "fulfilled" ? nemesisResult.value : null
  );
  if (fiscalRatioResult.status === "fulfilled") {
    installFiscalRatioRenderer(fiscalRatioResult.value);
  }
});
