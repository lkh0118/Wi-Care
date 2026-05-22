// 대시보드 데이터를 주기적으로 가져와 표, 장치 드롭다운, LED 상태를 갱신한다.
const LEVELS = ["normal", "caution", "warning", "danger"];
// Python API에서 내려주는 단계명을 화면 표시용 한글로 매핑한다.
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

// 마지막으로 선택한 장치를 브라우저에 저장해 새로고침 후에도 유지한다.
let selectedDeviceId = localStorage.getItem("wiCareSelectedDeviceId") || "home-001";
let knownDeviceIds = [];

async function refreshDashboard() {
  try {
    // 캐시된 JSON을 받지 않도록 현재 시각을 쿼리 파라미터에 붙인다.
    const params = new URLSearchParams({
      deviceId: selectedDeviceId,
      ts: Date.now().toString(),
    });
    const response = await fetch(`/api/dashboard?${params.toString()}`, { cache: "no-store" });
    const payload = await response.json();

    if (!response.ok || payload.status !== "ok") {
      throw new Error(payload.message || "대시보드 데이터를 불러오지 못했습니다.");
    }

    // 서버가 선택 가능한 장치 목록과 실제 선택된 장치를 다시 알려준다.
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
  // 장치 목록이 바뀌지 않았으면 select를 다시 그리지 않아 선택 깜빡임을 줄인다.
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
  // 상단 요약 문구에는 현재 장치, 분석 날짜, 파일 수정 시각을 표시한다.
  const updatedAt = formatDateTime(payload.updatedAt);
  summaryText.textContent = `${payload.deviceId} / 분석 기준일 ${payload.analysisDate} / 최신 수정 ${updatedAt}`;
}

function renderTable(rows) {
  // API의 rows 배열을 표의 tr 목록으로 변환한다.
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
  // 각 지표마다 정상/주의/경고/위험 LED 4개를 그리고 현재 단계만 강조한다.
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
  // API 호출 성공/실패에 따라 우측 상단 연결 상태를 갱신한다.
  serverDot.classList.toggle("connected", connected);
  serverDot.classList.toggle("error", !connected);
  serverStatus.textContent = text;
}

function formatDateTime(value) {
  // ISO 날짜 문자열을 한국어 로캘의 날짜/시간 형태로 표시한다.
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
  // 서버 데이터가 HTML로 해석되지 않도록 특수 문자를 이스케이프한다.
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

deviceSelect.addEventListener("change", () => {
  // 드롭다운을 바꾸면 즉시 해당 장치 데이터로 다시 조회한다.
  selectedDeviceId = deviceSelect.value;
  localStorage.setItem("wiCareSelectedDeviceId", selectedDeviceId);
  refreshDashboard();
});

refreshDashboard();
// 현재 프로토타입의 실시간성은 2초 폴링 방식이다.
setInterval(refreshDashboard, 2000);
