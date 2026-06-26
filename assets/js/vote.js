// 「想聽什麼」互動投票：主題與活動形式都可投（可複選、可取消）。
// 先用問卷資料把清單畫出來（永遠有內容、附問卷人次參考），
// 再向 /api 疊上「即時票數」並開放點擊；連不到 API 就停在唯讀狀態。
(function () {
  "use strict";
  var D = window.SITE_DATA || {};
  var wish = D.wish || {};
  var topicsEl = document.getElementById("vote-topics");
  var formatsEl = document.getElementById("vote-formats");
  if (!topicsEl || !formatsEl) return;
  var statusEl = document.getElementById("vote-status");
  var form = document.getElementById("vote-form");
  var msgEl = document.getElementById("vote-msg");
  var newEl = document.getElementById("vote-new");
  var toolsEl = document.getElementById("vote-tools");

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function flash(t) { if (msgEl) msgEl.textContent = t; }

  function itemHtml(text, ref, live) {
    var cnt = live && live.votes != null ? live.votes : "";
    var voted = live && live.voted ? " is-voted" : "";
    var disabled = live ? "" : " is-disabled";
    var refTxt = ref != null ? "問卷 " + ref + " 提過" : "新許願";
    return '<li class="vote__item' + voted + disabled + '" data-text="' + esc(text) + '"' +
      (live ? ' data-id="' + live.id + '"' : "") + '>' +
      '<button type="button" class="vote__btn" tabindex="-1"><span class="vote__thumb">👍</span>' +
      '<span class="vote__count">' + cnt + '</span></button>' +
      '<span class="vote__text">' + esc(text) + '</span>' +
      '<span class="vote__ref">' + refTxt + '</span></li>';
  }

  // 1) 先用問卷資料畫出清單（唯讀）
  function base(arr) { return (arr || []).map(function (x) { return { text: x.category, ref: x.demand }; }); }
  function renderBase(el, items) {
    el.innerHTML = items.map(function (x) { return itemHtml(x.text, x.ref, null); }).join("") || '<li class="vote__ref">—</li>';
  }
  var topicBase = base(wish.topics);
  var formatBase = base(wish.formats);
  renderBase(topicsEl, topicBase);
  renderBase(formatsEl, formatBase);
  if (toolsEl) {
    var tools = (wish.tools || []).map(function (t) { return t.category + "（" + t.demand + "）"; });
    toolsEl.textContent = tools.length ? "另有工具/平台類建議：" + tools.join("、") : "";
  }

  // file:// 無 API
  if (location.protocol === "file:") {
    if (statusEl) statusEl.textContent = "投票將於網站上線後開放（目前先顯示問卷裡大家提過的）。";
    return;
  }
  var API = "/api";

  var voter = localStorage.getItem("congressthon_voter");
  if (!voter) {
    voter = "v_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem("congressthon_voter", voter);
  }

  var refMap = {}; // text -> 問卷人次
  topicBase.concat(formatBase).forEach(function (x) { refMap[x.text] = x.ref; });

  // 2) 疊上即時票數並開放點擊
  function applyLive(rows) {
    var groups = { topic: topicsEl, format: formatsEl };
    var seen = {};
    rows.forEach(function (r) {
      var el = groups[r.kind] || topicsEl;
      var li = el.querySelector('[data-text="' + cssEsc(r.text) + '"]');
      if (!li) {
        el.insertAdjacentHTML("beforeend", itemHtml(r.text, refMap[r.text] != null ? refMap[r.text] : null, r));
      } else {
        li.classList.remove("is-disabled");
        li.classList.toggle("is-voted", !!r.voted);
        li.setAttribute("data-id", r.id);
        li.querySelector(".vote__count").textContent = r.votes;
      }
      seen[r.kind + "|" + r.text] = true;
    });
    if (statusEl) statusEl.textContent = "";
  }
  function cssEsc(s) { return String(s).replace(/"/g, '\\"'); }

  function load() {
    fetch(API + "/topics?voter=" + encodeURIComponent(voter))
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.topics) applyLive(d.topics); else readonly(); })
      .catch(readonly);
  }
  function readonly() {
    if (statusEl) statusEl.textContent = "暫時連不到投票伺服器，先顯示問卷參考；稍後再試。";
  }

  function onVote(e) {
    var li = e.target.closest(".vote__item");
    if (!li || li.classList.contains("is-disabled")) return;
    var id = li.getAttribute("data-id");
    if (!id) return;
    fetch(API + "/vote", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ topic_id: id, voter: voter }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.ok) {
        li.classList.toggle("is-voted", d.voted);
        li.querySelector(".vote__count").textContent = d.votes;
      } else { flash((d && d.error) || "投票失敗"); }
    }).catch(function () { flash("連線失敗"); });
  }
  topicsEl.addEventListener("click", onVote);
  formatsEl.addEventListener("click", onVote);

  if (form) form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = (newEl.value || "").trim();
    if (text.length < 2) { flash("主題至少 2 個字"); return; }
    flash("驗證中…");
    function send(token) {
      fetch(API + "/topics", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: text, voter: voter, turnstileToken: token }),
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (d && d.ok) { flash(d.message || "已送出，待審核後會出現"); newEl.value = ""; if (window.turnstile) window.turnstile.reset("#vote-turnstile"); }
        else { flash((d && d.error) || "送出失敗"); if (window.turnstile) window.turnstile.reset("#vote-turnstile"); }
      }).catch(function () { flash("連線失敗"); });
    }
    if (window.turnstile) {
      window.turnstile.execute("#vote-turnstile", {
        callback: function (token) { send(token); },
        "error-callback": function () { flash("人機驗證失敗，請重試"); },
      });
    } else {
      send("");
    }
  });

  load();
})();
