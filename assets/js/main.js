(function () {
  "use strict";
  var D = window.SITE_DATA;
  if (!D) { console.error("site_data 未載入"); return; }

  var ACCENT = "#00a37a";
  var ACCENT_SOFT = "#7fd3bb";
  var ACCENT_DARK = "#00795a";
  var GRAY = "#b4b2a9";
  var INK = "#111110";

  function setLink(id, url) { var el = document.getElementById(id); if (el && url) el.href = url; }
  setLink("nav-newsletter", D.links.newsletter);
  setLink("hero-register", D.links.register);
  setLink("hero-newsletter", D.links.newsletter);
  setLink("footer-newsletter", D.links.newsletter);

  var s = D.summary;
  var stats = [
    [s.events, "場活動"],
    [s.total_responses, "份問卷回饋"],
    [s.overall_nps, "整體 NPS"],
    [s.first_time_pct + "%", "首次參加比例"],
  ];
  document.getElementById("about-stats").innerHTML = stats.map(function (x) {
    return '<div class="stat"><div class="stat__num">' + x[0] + '</div><div class="stat__label">' + x[1] + '</div></div>';
  }).join("");
  document.getElementById("nps-overall").textContent = s.overall_nps;

  Chart.defaults.font.family = "'JetBrains Mono', 'Noto Sans TC', system-ui, sans-serif";
  Chart.defaults.color = INK;
  Chart.defaults.plugins.legend.display = false;

  new Chart(document.getElementById("chart-nps"), {
    type: "line",
    data: {
      labels: D.nps_by_event.map(function (e) { return e.event; }),
      datasets: [{
        data: D.nps_by_event.map(function (e) { return e.nps; }),
        borderColor: ACCENT, backgroundColor: "rgba(0,163,122,0.12)",
        pointBackgroundColor: ACCENT, pointRadius: 4, tension: 0.25, fill: true, borderWidth: 2,
      }],
    },
    options: {
      maintainAspectRatio: false,
      scales: { y: { suggestedMin: 0, suggestedMax: 100, title: { display: true, text: "NPS" } } },
      plugins: { tooltip: { callbacks: {
        title: function (it) { var i = it[0].dataIndex; return D.nps_by_event[i].event + "　" + (D.nps_by_event[i].theme || ""); },
        label: function (it) { var i = it.dataIndex; return "NPS " + it.formattedValue + "（n=" + D.nps_by_event[i].n + "）"; },
      } } },
    },
  });

  new Chart(document.getElementById("chart-occupation"), {
    type: "bar",
    data: {
      labels: D.occupation.map(function (o) { return o.value; }),
      datasets: [{ data: D.occupation.map(function (o) { return o.count; }), backgroundColor: ACCENT }],
    },
    options: {
      indexAxis: "y", maintainAspectRatio: false,
      scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
      plugins: { tooltip: { callbacks: { label: function (it) {
        return it.formattedValue + " 人（" + D.occupation[it.dataIndex].pct + "%）";
      } } } },
    },
  });

  new Chart(document.getElementById("chart-channel"), {
    type: "doughnut",
    data: {
      labels: D.channel.map(function (c) { return c.value; }),
      datasets: [{ data: D.channel.map(function (c) { return c.count; }),
        backgroundColor: [ACCENT, ACCENT_SOFT, "#bfe7da", GRAY, "#d3d1c7"], borderWidth: 2, borderColor: "#fff" }],
    },
    options: {
      maintainAspectRatio: false, cutout: "56%",
      plugins: {
        legend: { display: true, position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: function (it) {
          return it.label + "：" + it.formattedValue + " 人（" + D.channel[it.dataIndex].pct + "%）";
        } } },
      },
    },
  });

  var ft = {}; D.first_time.forEach(function (x) { ft[x.value] = x; });
  var first = ft["首次參加"] || { count: 0, pct: 0 };
  var ret = ft["回流參加"] || { count: 0, pct: 0 };
  new Chart(document.getElementById("chart-firsttime"), {
    type: "bar",
    data: {
      labels: [""],
      datasets: [
        { label: "首次參加", data: [first.count], backgroundColor: ACCENT },
        { label: "回流參加", data: [ret.count], backgroundColor: ACCENT_SOFT },
      ],
    },
    options: {
      indexAxis: "y", maintainAspectRatio: false,
      scales: { x: { stacked: true, display: false }, y: { stacked: true, display: false } },
      plugins: {
        legend: { display: true, position: "bottom", labels: { boxWidth: 12, font: { size: 12 } } },
        tooltip: { callbacks: { label: function (it) {
          var p = it.datasetIndex === 0 ? first.pct : ret.pct;
          return it.dataset.label + "：" + it.formattedValue + " 人（" + p + "%）";
        } } },
      },
    },
  });

  // 「想聽什麼」改為互動投票，渲染移到 vote.js（讀同一份 SITE_DATA 當問卷參考）

  document.getElementById("events-list").innerHTML = D.events.slice().reverse().map(function (e) {
    var links = [];
    if (e.event_url) links.push('<a href="' + e.event_url + '" target="_blank" rel="noopener">活動頁 ↗</a>');
    if (e.hackmd) links.push('<a href="' + e.hackmd + '" target="_blank" rel="noopener">共筆 ↗</a>');
    else links.push('<span class="muted">共筆待補</span>');
    if (e.video) links.push('<a href="' + e.video + '" target="_blank" rel="noopener">回放 ↗</a>');
    var nps = e.nps !== "" ? '<div class="event__nps">NPS ' + e.nps + '</div>' : "";
    return '<div class="event">' +
      '<div class="event__date">' + e.date + '<span class="event__term">' + (e.term || "") + '</span></div>' +
      '<div class="event__theme">' + e.theme + '</div>' + nps +
      '<div class="event__links">' + links.join("") + '</div></div>';
  }).join("");
})();
