const $ = (id) => document.getElementById(id);

function toast(msg){
  const t = $("toast");
  t.textContent = msg;
  t.hidden = false;
  setTimeout(()=> t.hidden = true, 2200);
}

async function searchCompany(){
  const ticker = $("ticker").value.trim();
  const start = $("startDate").value;
  const end   = $("endDate").value;

  if(!ticker){ toast("Please enter a company ticker"); return; }

  const res = await fetch(`/api/company/${encodeURIComponent(ticker)}`);
  if(!res.ok){
    toast("Company not found");
    clearStats();
    Plotly.purge("chart");
    return;
  }
  const data = await res.json();

  // Optional date filter on client side
  let rec = data.records;
  if(start) rec = rec.filter(r => r.date >= start);
  if(end)   rec = rec.filter(r => r.date <= end);

  if(rec.length === 0){
    toast("No data in this date range");
    clearStats();
    Plotly.purge("chart");
    return;
  }

  // Update stats
  $("avgVol").textContent   = Number(data.analytics.avg_volume).toFixed(2);
  $("high").textContent     = data.analytics.summary.highest;
  $("low").textContent      = data.analytics.summary.lowest;
  $("firstOpen").textContent= data.analytics.summary.first_open;
  $("lastClose").textContent= data.analytics.summary.last_close;

  // Build candlestick
  const trace = {
    x: rec.map(r => r.date),
    open: rec.map(r => r.open),
    high: rec.map(r => r.high),
    low:  rec.map(r => r.low),
    close:rec.map(r => r.close),
    type: "candlestick",
    increasing: {line:{width:1.5}},
    decreasing: {line:{width:1.5}}
  };

  const layout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor:  "rgba(0,0,0,0)",
    margin: {l:40, r:20, t:20, b:40},
    xaxis: {
      rangeslider: {visible: true},  // ✅ range slider for mobile
      showgrid: false
    },
    yaxis: {gridcolor: "rgba(255,255,255,0.08)"},
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      "select2d","lasso2d","autoScale2d"
    ]
  };

  $("chartTitle").textContent = `${data.company} — Candlestick`;
  Plotly.newPlot("chart", [trace], layout, config);
  toast("Loaded!");
}

function clearStats(){
  ["avgVol","high","low","firstOpen","lastClose"].forEach(id => $(id).textContent = "—");
}

$("goBtn").addEventListener("click", searchCompany);
$("clearDates").addEventListener("click", ()=>{
  $("startDate").value = ""; $("endDate").value = "";
  toast("Cleared dates");
});
$("themeToggle").addEventListener("click", ()=>{
  document.body.classList.toggle("light");
  $("themeToggle").textContent =
    document.body.classList.contains("light") ? "☀️" : "🌙";
});
