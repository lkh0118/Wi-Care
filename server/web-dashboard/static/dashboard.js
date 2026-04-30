const LEVELS = ["normal", "caution", "warning", "danger"];
const LEVEL_LABELS = {
  normal: "정상",
  caution: "주의",
  warning: "경고",
  danger: "위험",
};

const metricRows = document.querySelector("#metricRows");
const ledGrid = document.querySelector("#ledGrid");
const summaryText = document.querySelector("#summaryText");
const serverDot = document.querySelector("#serverDot");
const serverStatus = document.querySelector("#serverStatus");
const deviceSelect = document.querySelector("#deviceSelect");

let selectedDeviceId = localStorage.getItem("wiCareSelectedDeviceId") || "home-001";
let knownDeviceIds = [];

async function refreshDashboard() {
  try {
    const params = new URLSearchParams({
      deviceId: selectedDeviceId,
      ts: Date.now().toString(),
    });
    const response = await fetch(`/api/dashboard?${params.toString()}`, { cache: "no-store" });
    const payload = await response.json();

    if (!response.ok || payload.status !== "ok") {
      throw new Error(payload.message || "대시보드 데이터를 불러오지 못했습니다.");
    }

    selectedDeviceId = payload.selectedDeviceId || payload.deviceId || selectedDeviceId;
    localStorage.setItem("wiCareSelectedDeviceId", selectedDeviceId);
    renderDeviceOptions(payload.devices || [], selectedDeviceId);
    renderSummary(payload);
    renderTable(payload.rows);
    renderLeds(payload.leds);
    setServerState(true, "실시간 갱신 중");
  } catch (error) {
    setServerState(false, error.message);
  }
}

function renderDeviceOptions(devices, activeDeviceId) {
  const nextDeviceIds = devices.join("|");
  if (nextDeviceIds === knownDeviceIds.join("|") && deviceSelect.value === activeDeviceId) {
    return;
  }

  knownDeviceIds = devices;
  deviceSelect.innerHTML = devices
    .map((deviceId) => {
      const selected = deviceId === activeDeviceId ? "selected" : "";
      return `<option value="${escapeHtml(deviceId)}" ${selected}>${escapeHtml(deviceId)}</option>`;
    })
    .join("");
  deviceSelect.value = activeDeviceId;
}

function renderSummary(payload) {
  const updatedAt = formatDateTime(payload.updatedAt);
  summaryText.textContent = `${payload.deviceId} / 분석 기준일 ${payload.analysisDate} / 최신 수정 ${updatedAt}`;
}

function renderTable(rows) {
  metricRows.innerHTML = rows
    .map((row) => {
      return `
        <tr>
          <td class="metricName">${escapeHtml(row.name)}</td>
          <td>${formatDateTime(row.updatedAt)}</td>
          <td class="metricValue">${escapeHtml(row.displayValue)}</td>
          <td><span class="badge level-${row.level}">${escapeHtml(row.levelLabel)}</span></td>
          <td class="criteria">${escapeHtml(row.criteria.normal)}</td>
          <td class="criteria">${escapeHtml(row.criteria.caution)}</td>
          <td class="criteria">${escapeHtml(row.criteria.warning)}</td>
          <td class="criteria">${escapeHtml(row.criteria.danger)}</td>
        </tr>
      `;
    })
    .join("");
}

function renderLeds(rows) {
  ledGrid.innerHTML = rows
    .map((row) => {
      const lights = LEVELS
        .map((level) => {
          const active = row.level === level ? "active" : "";
          return `<span class="led ${level} ${active}" aria-label="${LEVEL_LABELS[level]}"></span>`;
        })
        .join("");

      const labels = LEVELS.map((level) => `<span>${LEVEL_LABELS[level]}</span>`).join("");

      return `
        <article class="ledItem">
          <div class="ledName">${escapeHtml(row.name)}</div>
          <div class="ledLights">${lights}</div>
          <div class="ledLabels">${labels}</div>
          <div class="ledValue">${escapeHtml(row.displayValue)} / ${escapeHtml(row.levelLabel)}</div>
        </article>
      `;
    })
    .join("");
}

function setServerState(connected, text) {
  serverDot.classList.toggle("connected", connected);
  serverDot.classList.toggle("error", !connected);
  serverStatus.textContent = text;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

deviceSelect.addEventListener("change", () => {
  selectedDeviceId = deviceSelect.value;
  localStorage.setItem("wiCareSelectedDeviceId", selectedDeviceId);
  refreshDashboard();
});

refreshDashboard();
setInterval(refreshDashboard, 2000);
