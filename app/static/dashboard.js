const STORAGE_KEY = "credential-studio-jobs-v1";
const jobsList = document.querySelector("#runs-list");
const emptyState = document.querySelector("#empty-state");
const form = document.querySelector("#batch-form");
const recipientInput = document.querySelector("#recipients");
const formMessage = document.querySelector("#form-message");
const submitButton = document.querySelector("#submit-button");
const detailPanel = document.querySelector("#run-detail");
let jobs = loadJobs();

function loadJobs() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function saveJobs() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function formatDate(value) {
  if (!value) return "Just now";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function statusClass(status) {
  return `status-${String(status || "pending").toLowerCase()}`;
}

function render() {
  jobsList.innerHTML = jobs.map((job, index) => `
    <article class="run-row" data-job-id="${escapeHtml(job.id)}" style="animation-delay:${Math.min(index * 45, 180)}ms">
      <div><div class="run-name">${escapeHtml(job.course)}</div><div class="run-meta">${escapeHtml(formatDate(job.createdAt))} · ${escapeHtml(job.id.slice(0, 8))}</div></div>
      <div class="run-right"><span class="run-count">${job.successful || 0}/${job.total || 0}</span><span class="status-pill ${statusClass(job.status)}">${escapeHtml((job.status || "PENDING").replaceAll("_", " "))}</span></div>
    </article>`).join("");
  emptyState.hidden = jobs.length > 0;
  document.querySelector("#metric-batches").textContent = jobs.length;
  document.querySelector("#metric-total").textContent = jobs.reduce((sum, job) => sum + (Number(job.total) || 0), 0);
  document.querySelector("#metric-success").textContent = jobs.reduce((sum, job) => sum + (Number(job.successful) || 0), 0);
  document.querySelector("#metric-failed").textContent = jobs.reduce((sum, job) => sum + (Number(job.failed) || 0), 0);
}

function parseRecipients(text) {
  return text.split(/\r?\n/).map((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) return null;
    const separator = trimmed.indexOf(",");
    if (separator < 1 || separator === trimmed.length - 1) {
      throw new Error(`Line ${index + 1}: use name, email format.`);
    }
    return { name: trimmed.slice(0, separator).trim(), email: trimmed.slice(separator + 1).trim() };
  }).filter(Boolean);
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.error?.message || body?.detail || "Request failed. Check the API and try again.";
    throw new Error(typeof detail === "string" ? detail : "Please check the submitted fields.");
  }
  return body;
}

async function refreshJobs() {
  try {
    const history = await requestJson("/api/v1/jobs");
    const locallySaved = new Map(jobs.map((job) => [job.id, job]));
    const historyIds = new Set(history.map((job) => job.job_id));
    jobs = history.map((job) => ({
      id: job.job_id,
      course: job.course_name,
      status: job.status,
      total: job.total_certificates,
      successful: job.successful_certificates,
      failed: job.failed_certificates,
      pending: job.pending_certificates,
      progress: job.progress_percentage,
      createdAt: job.created_at
    }));
    jobs.push(...[...locallySaved.values()].filter((job) => !historyIds.has(job.id)));
  } catch {
    // Keep browser-saved history visible if the API cannot be reached.
  }

  await Promise.all(jobs.map(async (job) => {
    try {
      const status = await requestJson(`/api/v1/jobs/${encodeURIComponent(job.id)}`);
      Object.assign(job, {
        status: status.status,
        total: status.total_certificates,
        successful: status.successful_certificates,
        failed: status.failed_certificates,
        pending: status.pending_certificates,
        progress: status.progress_percentage,
        createdAt: status.created_at || job.createdAt
      });
    } catch (error) {
      if (error.message.includes("404")) job.unavailable = true;
    }
  }));
  saveJobs();
  render();
}

async function showRecipients(job) {
  detailPanel.hidden = false;
  document.querySelector("#detail-title").textContent = job.course;
  const results = document.querySelector("#recipient-results");
  results.innerHTML = '<div class="run-meta">Loading recipient results...</div>';
  try {
    const data = await requestJson(`/api/v1/jobs/${encodeURIComponent(job.id)}/certificates`);
    results.innerHTML = data.certificates.map((certificate) => `
      <div class="recipient-row">
        <div class="recipient-info"><strong>${escapeHtml(certificate.recipient_name)}</strong><span>${escapeHtml(certificate.recipient_email)}</span></div>
        <span class="status-pill ${statusClass(certificate.status)}">${escapeHtml(certificate.status)}</span>
        ${certificate.status === "SUCCESS" ? `<a class="download-link" href="/api/v1/certificates/${encodeURIComponent(certificate.id)}" target="_blank" rel="noreferrer">PDF ↗</a>` : "<span></span>"}
      </div>`).join("") || '<div class="run-meta">No recipient records were returned.</div>';
  } catch (error) {
    results.innerHTML = `<div class="form-message">${escapeHtml(error.message)}</div>`;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formMessage.textContent = "";
  formMessage.classList.remove("success");
  let recipients;
  try {
    recipients = parseRecipients(recipientInput.value);
    if (!recipients.length) throw new Error("Add at least one recipient.");
    if (recipients.some((recipient) => !recipient.name || !recipient.email)) throw new Error("Each row needs a name and email.");
  } catch (error) {
    formMessage.textContent = error.message;
    return;
  }

  submitButton.disabled = true;
  submitButton.querySelector("span:first-child").textContent = "Starting batch...";
  try {
    const created = await requestJson("/api/v1/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course_name: document.querySelector("#course-name").value.trim(),
        completion_date: document.querySelector("#completion-date").value,
        recipients
      })
    });
    jobs.unshift({ id: created.job_id, course: document.querySelector("#course-name").value.trim(), total: created.total_certificates, successful: 0, failed: 0, status: created.status, createdAt: new Date().toISOString() });
    jobs = jobs.slice(0, 40);
    saveJobs();
    render();
    form.reset();
    document.querySelector("#completion-date").value = new Date().toISOString().slice(0, 10);
    formMessage.textContent = "Batch started. Progress will update automatically.";
    formMessage.classList.add("success");
    void refreshJobs();
  } catch (error) {
    formMessage.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span:first-child").textContent = "Generate certificates";
  }
});

recipientInput.addEventListener("input", () => {
  const count = recipientInput.value.split(/\r?\n/).filter((line) => line.trim()).length;
  document.querySelector("#recipient-count").textContent = `${count} recipient${count === 1 ? "" : "s"}`;
});

jobsList.addEventListener("click", (event) => {
  const row = event.target.closest("[data-job-id]");
  if (row) {
    const job = jobs.find((item) => item.id === row.dataset.jobId);
    if (job) void showRecipients(job);
  }
});

document.querySelector("#refresh-button").addEventListener("click", () => void refreshJobs());
document.querySelector("#close-detail").addEventListener("click", () => { detailPanel.hidden = true; });
document.querySelector("#today-label").textContent = new Intl.DateTimeFormat(undefined, { dateStyle: "full" }).format(new Date());
document.querySelector("#completion-date").value = new Date().toISOString().slice(0, 10);

fetch("/health").then((response) => {
  if (!response.ok) throw new Error("offline");
  document.querySelector("#api-pulse").classList.add("online");
  document.querySelector("#api-label").textContent = "API operational";
}).catch(() => {
  document.querySelector("#api-pulse").classList.add("offline");
  document.querySelector("#api-label").textContent = "API unavailable";
});

render();
void refreshJobs();
window.setInterval(() => void refreshJobs(), 5000);