"use strict";
const $ = id => document.getElementById(id);
const state = {courses: [], current: null, selected: new Set(), job: null, editKey: null};
const labels = {complete: "已有字幕", empty: "接口暂无字幕", pending: "待抓取"};
const jobLabels = {running:"正在运行",cancelling:"正在终止",cancelled:"已终止",success:"已完成",failed:"执行失败"};
const activeJob = () => ["running", "cancelling"].includes(state.job?.state);
const preferences = JSON.parse(localStorage.getItem("course-layout") || "{}");
let draggedCourse = null;
function savePreferences() { localStorage.setItem("course-layout", JSON.stringify(preferences)); }
function setSidebarHidden(hidden) {
  preferences.hidden = hidden;
  document.body.classList.toggle("sidebar-hidden", hidden);
  $("sidebar").inert = hidden;
  $("toggle-sidebar").textContent = hidden ? "显示课程" : "隐藏课程";
  $("toggle-sidebar").setAttribute("aria-expanded", String(!hidden));
  savePreferences();
}
function setSidebarWidth(width) {
  preferences.width = Math.max(240, Math.min(480, width));
  document.documentElement.style.setProperty("--sidebar-width", preferences.width + "px");
  $("sidebar-resizer").setAttribute("aria-valuenow", String(preferences.width));
  savePreferences();
}
const escapeHTML = text => String(text ?? "").replace(/[&<>"']/g, value => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[value]));

async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type":"application/json","X-Local-Token":document.querySelector('meta[name="local-token"]').content},
    body: JSON.stringify(body)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "请求失败：" + response.status);
  return result;
}
function message(error) {
  $("message").hidden = !error;
  $("message").textContent = error ? String(error.message || error) : "";
}
function currentCourse() { return state.courses.find(course => course.key === state.current); }
function visibleLessons() {
  const course = currentCourse();
  return course ? course.lessons.filter(row => $("filter").value === "all" || row.state === $("filter").value) : [];
}
function renderNavigation() {
  if (draggedCourse) return;
  const query = $("search").value.trim().toLowerCase();
  const order = preferences.order || [];
  const courses = [...state.courses].sort((a, b) => {
    const rank = key => order.includes(key) ? order.indexOf(key) : order.length;
    return rank(a.key) - rank(b.key);
  });
  $("courses").innerHTML = courses.filter(course => course.name.toLowerCase().includes(query)).map(course =>
    '<button draggable="true" class="course-item ' + (course.key === state.current ? "active" : "") + '" data-course="' + escapeHTML(course.key) + '" title="拖动调整顺序；Alt + 方向键也可调整"><strong><span class="drag-grip" aria-hidden="true">⠿</span>' +
    escapeHTML(course.name) + '</strong><small>' + course.counts.total + ' 节课程 · ' + course.counts.complete + ' 节已有字幕</small></button>'
  ).join("");
}
function render() {
  renderNavigation();
  const course = currentCourse();
  $("empty").hidden = Boolean(course);
  $("workspace").hidden = !course;
  if (!course) return;
  $("course-name").textContent = course.name;
  $("course-meta").textContent = (course.teachers.join("、") || "教师信息待读取") + "  ·  课程编号 " + (course.teclId || "待读取");
  $("output-path").textContent = "保存位置：" + course.output_dir;
  const cards = [["total","课程总数"],["complete","已有字幕"],["empty","接口暂无字幕"],["pending","待抓取"]];
  $("stats").innerHTML = cards.map(([key,label]) => '<div class="stat ' + key + '"><small>' + label + '</small><strong>' + course.counts[key] + '</strong></div>').join("");
  const rows = visibleLessons();
  $("lessons").innerHTML = rows.map(row => '<tr class="' + (state.selected.has(row.id) ? "selected" : "") + '"><td><input type="checkbox" data-lesson="' +
    escapeHTML(row.id) + '" aria-label="选择课次 ' + escapeHTML(row.id) + '"' + (state.selected.has(row.id) ? " checked" : "") + '></td><td>' +
    escapeHTML(row.date) + '</td><td>第 ' + escapeHTML(row.number) + ' 节</td><td><span class="badge ' + row.state + '">' + labels[row.state] +
    '</span></td><td>' + row.subtitle_count + '</td><td>' + (row.complete ? '<button class="text-button preview" data-preview="' + escapeHTML(row.id) +
    '">查看字幕 ↗</button>' : '<span class="muted">—</span>') + '</td></tr>').join("");
  $("no-lessons").hidden = rows.length > 0;
  $("no-lessons").textContent = course.lessons.length ? "当前筛选条件下没有课次。" : "还没有课次清单，点击“更新课次清单”读取。";
  $("selected-count").textContent = "已选 " + state.selected.size + " 节";
  $("toggle-all").checked = rows.length > 0 && rows.every(row => state.selected.has(row.id));
  $("toggle-all").indeterminate = rows.some(row => state.selected.has(row.id)) && !$("toggle-all").checked;
  const busy = activeJob();
  $("extract").disabled = busy || state.selected.size === 0;
  $("sync").disabled = busy;
  $("edit-course").disabled = busy;
  $("add-course").disabled = busy;
}
async function refresh() {
  state.courses = await api("/api/courses");
  if (!state.courses.some(course => course.key === state.current)) {
    state.current = state.courses[0]?.key || null;
    state.selected.clear();
  }
  const valid = new Set(currentCourse()?.lessons.map(row => row.id) || []);
  state.selected = new Set([...state.selected].filter(id => valid.has(id)));
  render();
}
function renderJob() {
  const job = state.job;
  if (!job) return;
  $("job-state").className = "badge " + job.state;
  $("job-state").textContent = jobLabels[job.state];
  $("cancel-job").hidden = !activeJob();
  $("cancel-job").disabled = job.state === "cancelling";
  $("cancel-job").textContent = job.state === "cancelling" ? "正在终止…" : "终止操作";
  $("job-time").textContent = job.started_at.replace("T", " ");
  $("job-caption").textContent = job.course_name + " · " + (job.mode === "inventory" ? "更新课次清单" : "抓取 " + job.selected.length + " 节课程") +
    (job.state === "running" ? " · 请留意 Edge 登录窗口" : "");
  const box = $("logs");
  const nearBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 30;
  const logText = job.logs.join("\n") || "正在启动浏览器，请稍候…";
  if (box.value !== logText && document.activeElement !== box) {
    box.value = logText;
    if (nearBottom) box.scrollTop = box.scrollHeight;
  }
  render();
}
function executionRecord() {
  const job = state.job;
  if (!job) return "暂无执行记录";
  return [
    "NUAA 课程字幕执行记录",
    "课程：" + job.course_name,
    "任务编号：" + job.id,
    "操作：" + (job.mode === "inventory" ? "更新课次清单" : "抓取字幕"),
    "所选课次编号：" + (job.selected.join(", ") || "未选择课次"),
    "开始时间：" + job.started_at,
    "结束时间：" + (job.ended_at || "尚未结束"),
    "状态：" + jobLabels[job.state],
    "退出码：" + (job.exit_code ?? "尚未结束"),
    "", "执行日志：", ...job.logs
  ].join("\n");
}
async function copyExecutionRecord() {
  try {
    await navigator.clipboard.writeText(executionRecord());
    $("copy-status").textContent = "已复制，可以直接粘贴发送";
  } catch (error) {
    $("logs").focus();
    $("logs").select();
    $("copy-status").textContent = "浏览器未允许复制，已选中日志，请按 Ctrl+C";
  }
}
function downloadExecutionRecord() {
  const blob = new Blob(["\uFEFF", executionRecord()], {type:"text/plain;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const name = (state.job?.course_name || "课程").replace(/[\\/:*?"<>|]/g, "_");
  link.href = url;
  link.download = name + "_执行记录.txt";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function poll() {
  try {
    const previous = state.job;
    state.job = await api("/api/job");
    renderJob();
    if (["running", "cancelling"].includes(previous?.state) && !activeJob()) await refresh();
  } catch (error) { message(error); }
  finally { setTimeout(poll, 1500); }
}
async function start(inventoryOnly) {
  message(null);
  try {
    state.job = await api("/api/job", {course:state.current,lesson_ids:[...state.selected],inventory_only:inventoryOnly,
      skip_existing:$("skip-existing").checked,wait:Number($("wait").value)});
    renderJob();
  } catch(error) { message(error); }
}
function openCourseDialog(edit) {
  const course = edit ? currentCourse() : null;
  state.editKey = course?.key || null;
  $("dialog-title").textContent = edit ? "更新课程网址" : "添加课程";
  $("input-name").value = course?.name || "";
  $("input-name").readOnly = Boolean(edit);
  $("input-url").value = course?.url || "";
  $("form-error").textContent = "";
  $("course-dialog").showModal();
}
$("course-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const result = await api("/api/course", {key:state.editKey,name:$("input-name").value,url:$("input-url").value});
    state.current = result.key;
    state.selected.clear();
    await refresh();
    $("course-dialog").close();
  } catch(error) { $("form-error").textContent = error.message; }
  finally { button.disabled = false; }
});
$("courses").addEventListener("click", event => {
  const target = event.target.closest("[data-course]");
  if (!target) return;
  state.current = target.dataset.course;
  state.selected.clear();
  $("filter").value = "all";
  render();
});
$("lessons").addEventListener("change", event => {
  const id = event.target.dataset.lesson;
  if (!id) return;
  if (event.target.checked) state.selected.add(id); else state.selected.delete(id);
  render();
});
$("lessons").addEventListener("click", async event => {
  const target = event.target.closest("[data-preview]");
  if (!target) return;
  try {
    const response = await fetch("/api/transcript?course=" + encodeURIComponent(state.current) + "&lesson=" + encodeURIComponent(target.dataset.preview));
    if (!response.ok) throw new Error("读取字幕失败");
    $("transcript").textContent = await response.text();
    $("transcript-dialog").showModal();
  } catch(error) { message(error); }
});
$("toggle-all").addEventListener("change", event => {
  visibleLessons().forEach(row => event.target.checked ? state.selected.add(row.id) : state.selected.delete(row.id));
  render();
});
$("select-all").onclick = () => { visibleLessons().forEach(row => state.selected.add(row.id)); render(); };
$("select-pending").onclick = () => { state.selected = new Set(currentCourse().lessons.filter(row => !row.complete).map(row => row.id)); render(); };
$("clear-selection").onclick = () => { state.selected.clear(); render(); };
$("filter").onchange = render;
$("search").oninput = renderNavigation;
$("add-course").onclick = () => openCourseDialog(false);
$("empty-add").onclick = () => openCourseDialog(false);
$("edit-course").onclick = () => openCourseDialog(true);
$("close-dialog").onclick = () => $("course-dialog").close();
$("close-transcript").onclick = () => $("transcript-dialog").close();
$("extract").onclick = () => start(false);
$("sync").onclick = () => start(true);
$("reload").onclick = () => refresh().then(() => message(null)).catch(message);
$("copy-logs").onclick = copyExecutionRecord;
$("download-logs").onclick = downloadExecutionRecord;
$("cancel-job").onclick = async () => {
  $("cancel-job").disabled = true;
  $("cancel-job").textContent = "正在终止…";
  try {
    state.job = await api("/api/job/cancel", {id: state.job.id});
    renderJob();
    await refresh();
  } catch (error) { message(error); renderJob(); }
};
$("toggle-sidebar").onclick = () => setSidebarHidden(!preferences.hidden);
$("hide-sidebar").onclick = () => { setSidebarHidden(true); $("toggle-sidebar").focus(); };
const resizer = $("sidebar-resizer");
resizer.addEventListener("pointerdown", event => {
  if (event.button !== 0) return;
  resizer.setPointerCapture(event.pointerId);
  document.body.classList.add("resizing");
});
resizer.addEventListener("pointermove", event => {
  if (resizer.hasPointerCapture(event.pointerId)) setSidebarWidth(event.clientX);
});
resizer.addEventListener("lostpointercapture", () => document.body.classList.remove("resizing"));
resizer.addEventListener("keydown", event => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  setSidebarWidth(event.key === "Home" ? 240 : event.key === "End" ? 480 : preferences.width + (event.key === "ArrowLeft" ? -20 : 20));
});
function reorderCourse(source, target, after) {
  const order = [...$("courses").querySelectorAll("[data-course]")].map(item => item.dataset.course);
  const fullOrder = [...new Set([...(preferences.order || []), ...state.courses.map(course => course.key)])].filter(key => key !== source);
  const index = fullOrder.indexOf(target);
  if (!order.includes(source) || index < 0) return;
  fullOrder.splice(index + Number(after), 0, source);
  preferences.order = fullOrder;
  savePreferences();
  renderNavigation();
}
$("courses").addEventListener("dragstart", event => {
  const item = event.target.closest("[data-course]");
  if (!item) return;
  draggedCourse = item.dataset.course;
  event.dataTransfer.setData("text/plain", draggedCourse);
  event.dataTransfer.effectAllowed = "move";
  item.classList.add("dragging");
});
$("courses").addEventListener("dragover", event => {
  const item = event.target.closest("[data-course]");
  if (!item || !draggedCourse) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  $("courses").querySelectorAll(".drop-target").forEach(row => row.classList.remove("drop-target"));
  item.classList.add("drop-target");
});
$("courses").addEventListener("drop", event => {
  event.preventDefault();
  const item = event.target.closest("[data-course]");
  if (item && draggedCourse && item.dataset.course !== draggedCourse) {
    const rect = item.getBoundingClientRect();
    reorderCourse(draggedCourse, item.dataset.course, event.clientY > rect.top + rect.height / 2);
  }
  draggedCourse = null;
  renderNavigation();
});
$("courses").addEventListener("dragend", () => { draggedCourse = null; renderNavigation(); });
$("courses").addEventListener("keydown", event => {
  if (!event.altKey || !["ArrowUp", "ArrowDown"].includes(event.key)) return;
  const item = event.target.closest("[data-course]");
  if (!item) return;
  const target = event.key === "ArrowUp" ? item.previousElementSibling : item.nextElementSibling;
  if (!target) return;
  event.preventDefault();
  const key = item.dataset.course;
  reorderCourse(key, target.dataset.course, event.key === "ArrowDown");
  [...$("courses").children].find(row => row.dataset.course === key).focus();
});
setSidebarWidth(Number(preferences.width) || 300);
setSidebarHidden(Boolean(preferences.hidden));
refresh().catch(message);
poll();
const pageId = crypto.randomUUID();
function pagePresence(closed = false) {
  const body = JSON.stringify({
    page_id: pageId, closed,
    token: document.querySelector('meta[name="local-token"]').content
  });
  if (closed) {
    navigator.sendBeacon("/api/page", new Blob([body], {type:"application/json"}));
  } else {
    fetch("/api/page", {method:"POST",headers:{"Content-Type":"application/json"},body,keepalive:true}).catch(() => {});
  }
}
pagePresence();
setInterval(() => pagePresence(), 5000);
window.addEventListener("pagehide", () => pagePresence(true));
window.addEventListener("pageshow", () => pagePresence());
