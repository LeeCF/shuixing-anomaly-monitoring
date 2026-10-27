const $ = (id) => document.getElementById(id);

function scoreClass(s){ return s >= 80 ? "high" : s >= 60 ? "mid" : "low"; }

function renderList(items){
  const rows = $("alert-rows");
  rows.innerHTML = "";
  items.forEach((a) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${a.alert_no}</td>
      <td><span class="score ${scoreClass(a.risk_score)}">${a.risk_score}</span></td>
      <td><span class="level-badge level-${a.level}">${a.level}</span></td>
      <td>${a.scenario}</td>
      <td>${a.parties.submitter} → ${a.parties.approver}</td>
      <td>${a.created_at}</td>`;
    tr.addEventListener("click", () => showDetail(a.id));
    rows.appendChild(tr);
  });
}

async function loadList(){
  const r = await fetch("/api/alerts");
  renderList(await r.json());
}

function showView(name){
  $("view-list").classList.toggle("hidden", name !== "list");
  $("view-detail").classList.toggle("hidden", name !== "detail");
}

function layerTile(label, text){
  return `<div class="layer-tile"><div class="lt">${label}</div><div class="lb">${text}</div></div>`;
}

function renderCard(a){
  const d = a.anomaly_description, t = a.trigger_reasons;
  const cases = a.similar_cases.map(c =>
    `<div class="case"><span class="when">${c.date} · ${c.dept}</span>${c.summary}</div>`).join("");
  const actions = a.recommended_actions.map(x =>
    `<div class="action"><span class="urg urg-${x.urgency}">${x.urgency}</span><span>${x.action}</span></div>`).join("");
  $("card").innerHTML = `
    <div class="card">
      <div class="card-head">
        <span class="big-score score ${scoreClass(a.risk_score)}">${a.risk_score}</span>
        <span class="meta">
          <span class="alert-no">${a.alert_no} · 级别 ${a.level}</span>
          <span class="scenario">${a.scenario}</span>
        </span>
      </div>
      <div class="card-sec">
        <h3>① 异常描述</h3>
        <div class="desc-line"><span class="k">涉及人</span>${d.who}</div>
        <div class="desc-line"><span class="k">时间</span>${d.when}</div>
        <div class="desc-line"><span class="k">事件</span>${d.what}</div>
        <div class="desc-line"><span class="k">背景</span>${d.context}</div>
      </div>
      <div class="card-sec">
        <h3>② 触发原因（三层联动）</h3>
        <div class="layers">
          ${layerTile("规则层", t.rule_layer)}
          ${layerTile("统计层", t.stat_layer)}
          ${layerTile("画像层", t.profile_layer)}
        </div>
      </div>
      <div class="card-sec">
        <h3>③ 相似历史案例（Top ${a.similar_cases.length}）</h3>${cases}
      </div>
      <div class="card-sec">
        <h3>④ 建议动作</h3>${actions}
      </div>
      <div class="card-sec parties">
        <h3>⑤ 涉及方</h3>
        <span>提交人：${a.parties.submitter}</span>
        <span>审批人：${a.parties.approver}</span>
        <span>供应商：${a.parties.vendor}</span>
      </div>
      <div class="card-sec">
        <h3>⑥ 数据溯源</h3><div class="lineage">${a.data_lineage}</div>
      </div>
    </div>`;
}

async function showDetail(id){
  const r = await fetch(`/api/alerts/${id}`);
  renderCard(await r.json());
  showView("detail");
  window.scrollTo(0, 0);
}

function sleep(ms){ return new Promise(r => setTimeout(r, ms)); }

async function runDetection(){
  const box = $("detect-status");
  const btn = $("btn-detect");
  btn.disabled = true;
  $("alert-rows").innerHTML = "";
  box.classList.remove("hidden");
  const steps = [
    "连接鼎捷 ERP / 电商结算数据源…",
    "规则层扫描：重复付款 / 拆单 / 账户变更…",
    "统计层计算：Z-Score / 滑动窗口聚集…",
    "画像层比对：人员 / 供应商行为偏差…",
    "AI 生成告警卡（原因 + 历史案例 + 建议动作）…",
  ];
  for (const s of steps){
    box.innerHTML = `<span class="spinner"></span>${s}`;
    await sleep(650);
  }
  const r = await fetch("/api/detect/run", {method: "POST"});
  const body = await r.json();
  box.innerHTML = `✓ 检测完成：扫描全量交易，发现 <b>${body.detected}</b> 条高风险异常`;
  renderList(body.alerts);
  btn.disabled = false;
}

$("btn-detect").addEventListener("click", runDetection);
$("btn-back").addEventListener("click", () => showView("list"));

loadList();
