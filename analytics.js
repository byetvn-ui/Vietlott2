/* AI Prediction Lab: chỉ đọc JSON do GitHub Actions sinh, không tính toán nặng trên thiết bị. */
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));
  const gameNow = () => document.querySelector('#gp button[aria-pressed="true"]')?.dataset.g || "655";
  const fmtDraw = (s) => {
    if (!s) return "—";
    const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}))?$/);
    return m ? `${m[3]}/${m[2]}/${m[1]}${m[4] ? " · "+m[4]+"h" : ""}` : esc(s);
  };
  const pct = (x) => x == null ? "—" : (100*x).toFixed(1)+"%";
  const balls = (nums, bonus) => (nums || []).map(n => `<span class="ball sm">${esc(n)}</span>`).join(" ") +
    (bonus == null ? "" : ` <b>+</b> <span class="ball sm gold">${esc(bonus)}</span>`);
  async function get(path) {
    const r = await fetch(path + "?v=" + Date.now(), {cache:"no-store"});
    if (!r.ok) throw new Error(path + " chưa được tạo");
    return r.json();
  }
  async function getLog() {
    const r = await fetch("predictions_log.jsonl?v=" + Date.now(), {cache:"no-store"});
    if (!r.ok) return [];
    const t = await r.text();
    return t.split(/\r?\n/).filter(Boolean).map(line => { try { return JSON.parse(line); } catch (_) { return null; } }).filter(Boolean);
  }
  function renderPrediction(events, game) {
    const preds = events.filter(e => e.event_type === "prediction" && e.game === game);
    const latest = preds[preds.length-1];
    const evals = new Map(events.filter(e => e.event_type === "evaluation").map(e => [e.prediction_id,e]));
    if (!latest) return `<p class="hint">Chưa có bản dự đoán đã khóa cho game này. Bot sẽ tự khóa bộ số trước kỳ quay kế tiếp khi workflow chạy.</p>`;
    const result = evals.get(latest.prediction_id);
    const rows = (latest.tickets || []).map((t,i) => {
      const scored = result?.tickets?.find(x => x.strategy === t.strategy);
      return `<div class="ticket">
        <div class="tl"><b>Bộ ${i+1} · ${esc(t.label)}</b><span class="badge">${esc(t.strategy)}</span></div>
        <div class="balls">${balls(t.numbers,t.bonus)}</div>
        ${scored ? `<div class="hint">Kết quả đối chiếu: <b>${scored.main_hits}/${t.numbers.length}</b> số chính${scored.bonus_hit ? " · trúng số phụ/đặc biệt" : ""}</div>` : ""}
      </div>`;
    }).join("");
    const overlap = latest.diversity?.pairwise_overlap || [];
    const maxOverlap = Math.max(0,...overlap.flatMap((row,i)=>row.filter((_,j)=>i!==j)));
    return `<div class="res">
      <b>🔒 Dự đoán đã khóa · ${esc(game)}</b>
      <div class="hint">Kỳ mục tiêu: <b>${fmtDraw(latest.target_draw)}</b> · tạo lúc ${esc(latest.created_at || "—")}</div>
      <div class="hint">Nguồn dữ liệu đến kỳ: ${fmtDraw(latest.source_latest_draw)} · seed: <code>${esc(latest.seed)}</code></div>
      ${rows}
      <div class="hint">Độ phủ: ${esc(latest.diversity?.unique_main_numbers_covered ?? "—")} số khác nhau · giao lớn nhất giữa hai vé: ${maxOverlap} số.</div>
      ${result ? `<div class="badge new">Đã tự động đối chiếu kết quả</div>` : `<div class="badge wait">Đang chờ kết quả kỳ mục tiêu</div>`}
    </div>`;
  }
  function renderHistory(events, game) {
    const preds = events.filter(e => e.event_type === "prediction" && e.game === game).slice(-12).reverse();
    const evals = new Map(events.filter(e => e.event_type === "evaluation").map(e => [e.prediction_id,e]));
    if (!preds.length) return `<p class="hint">Chưa có dự đoán được khóa trong lịch sử.</p>`;
    return preds.map((p,i) => {
      const ev = evals.get(p.prediction_id);
      const ticketCount = (p.tickets || []).length;
      const hits = ev ? (ev.tickets || []).reduce((n,t)=>n+(t.main_hits||0),0) : null;
      return `<div class="nrow"><b>${fmtDraw(p.target_draw)}</b> · ${ticketCount} vé · <span class="badge ${ev ? "new" : "wait"}">${ev ? "Đã đối chiếu" : "Đang chờ"}</span>${ev ? `<div class="pc">Tổng số chính trùng trên danh mục: ${hits}</div>` : ""}<div class="pc">Tạo lúc ${esc(p.created_at || "—")} · phiên bản ${esc(p.algorithm_version || "—")}</div></div>`;
    }).join("");
  }
  function renderAnalytics(data, game) {
    const g = data?.games?.[game];
    if (!g) return `<p>Chưa có thống kê cho game ${esc(game)}.</p>`;
    const hot = g.windows?.["60"]?.frequency || [];
    const gap = g.gap || [];
    const pairs = g.pairs || [];
    const triples = g.triples || [];
    return `<div class="hint">Số kỳ dữ liệu: <b>${esc(g.draw_count)}</b> · mới nhất: <b>${fmtDraw(g.latest_draw)}</b></div>
      <div class="hl most"><b>🔥 Tần suất 60 kỳ gần nhất</b><div class="balls">${hot.slice(0,8).map(x=>`<span class="ball sm">${x.number}</span><small>${x.count}</small>`).join(" ")}</div></div>
      <div class="hl gap"><b>⏳ Vắng mặt lâu nhất</b><div class="balls">${gap.slice(0,8).map(x=>`<span class="ball sm plain">${x.number}</span><small>${x.draws_absent} kỳ</small>`).join(" ")}</div></div>
      <p class="hint">Chu kỳ xuất hiện mô tả: ${(g.cycles||[]).slice(0,6).map(x=>`<b>${x.number}</b> · TB ${x.mean_interval} kỳ · hiện vắng ${x.current_gap}`).join(" / ") || "—"}</p>
      <p class="hint">Cặp thường xuất hiện cùng nhau: ${pairs.slice(0,5).map(x=>`<b>${x.numbers.join("-")}</b> (${x.count})`).join(" · ") || "—"}</p>
      <p class="hint">Bộ ba nổi bật: ${triples.slice(0,4).map(x=>`<b>${x.numbers.join("-")}</b> (${x.count})`).join(" · ") || "—"}</p>
      <p class="hint">Phân phối tổng: ${esc(g.distribution?.sum?.min)}–${esc(g.distribution?.sum?.max)}, trung bình ${esc(g.distribution?.sum?.mean)}. Mức lệch tần suất 60 kỳ: <b>${esc(g.anomaly?.level || "—")}</b> (max |z|=${esc(g.anomaly?.max_abs_z ?? "—")}).</p>
      ${g.bonus ? `<p class="hint">Số phụ/đặc biệt: phạm vi ${g.bonus.range.join("–")}. ${game==="535" ? "Tách riêng dữ liệu kỳ 13h và 21h." : "Được thống kê riêng với số chính."}</p>` : ""}
      <p class="hint">Cập nhật: ${esc(data.generated_at || "—")}. ${esc(g.methodology || "")}</p>`;
  }
  function renderEvaluation(data, game) {
    const g = data?.games?.[game];
    if (!g) return `<p>Chưa có kết quả kiểm định cho game này.</p>`;
    const entries = Object.entries(g.methods || {}).sort((a,b)=>(b[1].ge2_rate||0)-(a[1].ge2_rate||0));
    const body = entries.map(([key,m]) => `<tr>
      <td><b>${esc(m.label)}</b></td><td>${pct(m.ge2_rate)}</td>
      <td>${m.ge2_ci95 ? pct(m.ge2_ci95[0])+"–"+pct(m.ge2_ci95[1]) : "—"}</td>
      <td>${pct(m.ge2_rate_diff_vs_random)} (${m.paired_diff_ci95 ? pct(m.paired_diff_ci95[0])+"–"+pct(m.paired_diff_ci95[1]) : "—"})</td>
      <td>${esc(m.bh_q_value)}</td><td>${m.significant_after_bh_0_05 ? "Có" : "Không"}</td>
    </tr>`).join("");
    const random = g.random_control || {};
    const segments = (g.segments || []).slice(0,5).map(s=>`#${s.target_offset[0]}–${s.target_offset[1]}: ${pct(s.rnd?.ge2_rate)}`).join(" · ");
    return `<div class="hint">Walk-forward: <b>${esc(g.draws_evaluated)}</b> kỳ · tối thiểu ${esc(g.minimum_training_draws)} kỳ huấn luyện · ${esc(g.random_simulations_per_target)} mô phỏng ngẫu nhiên/kỳ.</div>
      <div class="note">Đối chứng ngẫu nhiên: TB ${esc(random.mean_hits_per_ticket)} số chính/vé · tỷ lệ ≥2 số ${pct(random.ge2_rate)} · CI95 ${random.ge2_ci95 ? pct(random.ge2_ci95[0])+"–"+pct(random.ge2_ci95[1]) : "—"}.</div>
      <p class="table-scroll-hint">↔ Vuốt ngang để xem đầy đủ các cột</p><div class="table-scroll table-scroll--wide" role="region" aria-label="Bảng kiểm định các phương pháp" tabindex="0"><table><thead><tr><th>Phương pháp</th><th>≥2 số</th><th>CI95</th><th>Δ vs ngẫu nhiên</th><th>BH q</th><th>Ý nghĩa*</th></tr></thead><tbody>${body}</tbody></table></div>
      <p class="hint">Các đoạn 100 kỳ gần nhất (tính từ kỳ đích mới nhất): ${segments || "—"}</p>
      <p class="hint">* Ý nghĩa thống kê sau hiệu chỉnh Benjamini–Hochberg ở ngưỡng 0,05. q-value không chứng minh lợi thế dự báo.</p>
      <p class="hint">${esc(g.interpretation || "")}</p>`;
  }
  async function refresh() {
    const status=$("#labStatus"), pred=$("#labPrediction"), ana=$("#labAnalytics"), eva=$("#labEvaluation"), hist=$("#labHistory");
    if (!status || !pred || !ana || !eva) return;
    const game=gameNow();
    try {
      const [events, analytics, evaluation] = await Promise.all([getLog(),get("analytics.json"),get("evaluation.json")]);
      status.textContent = `Đã tải dữ liệu Lab · game ${game} · ${new Date().toLocaleString("vi-VN")}`;
      const predictionHtml = renderPrediction(events,game);
      pred.innerHTML=predictionHtml;
      const official = $("#predOfficial"); if (official) official.innerHTML = predictionHtml;
      ana.innerHTML=renderAnalytics(analytics,game);
      eva.innerHTML=renderEvaluation(evaluation,game);
      if (hist) hist.innerHTML=renderHistory(events,game);
    } catch (e) {
      status.textContent="Dữ liệu Lab đang chờ GitHub Actions chạy lần đầu hoặc chưa tạo đủ tệp.";
      if (!pred.innerHTML) pred.innerHTML=`<p class="hint">${esc(e.message)}</p>`;
    }
  }
  window.VietlottLab={refresh};
  document.addEventListener("click",e=>{
    if (e.target.closest("#gp button")) setTimeout(refresh,100);
    if (e.target.closest(".tab") || e.target.closest('[data-tab="pred"]')) setTimeout(refresh,150);
  });
  document.addEventListener("DOMContentLoaded",refresh);
  setTimeout(refresh,1200);
  setInterval(()=>{ if (!$("#t-lab")?.hidden || !$("#t-pred")?.hidden) refresh(); },60000);
})();