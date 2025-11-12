const $ = (id) => document.getElementById(id);

function toast(msg){
  const t = $("toast");
  t.textContent = msg;
  t.hidden = false;
  setTimeout(()=> t.hidden = true, 2200);
}

function setLoading(on){
  document.body.classList.toggle("loading", !!on);
}

function clearStats(){
  ["avgVol","high","low","firstOpen","lastClose"].forEach(id => $(id).textContent = "—");
}

async function searchCompany(){
  const ticker = $("ticker").value.trim();
  const start  = $("startDate").value;
  const end    = $("endDate").value;
  const source = $("source").value;
  const period = $("period").value;
  const interval = $("interval").value;

  if(!ticker){ toast("Please enter a company ticker"); return; }

  setLoading(true);
  let url = source === "live"
    ? `/api/live/${encodeURIComponent(ticker)}?period=${encodeURIComponent(period)}&interval=${encodeURIComponent(interval)}`
    : `/api/company/${encodeURIComponent(ticker)}`;

  const res = await fetch(url);
  setLoading(false);

  if(!res.ok){
    toast("Data not found");
    clearStats();
    Plotly.purge("chart");
    return;
  }

  const data = await res.json();

  // Optional client-side date filter
  let rec = data.records;
  if(start) rec = rec.filter(r => r.date >= start);
  if(end)   rec = rec.filter(r => r.date <= end);

  if(rec.length === 0){
    toast("No data in this date range");
    clearStats(); Plotly.purge("chart"); return;
  }

  // Stats
  $("avgVol").textContent    = Number(data.analytics.avg_volume).toFixed(2);
  $("high").textContent      = data.analytics.summary.highest;
  $("low").textContent       = data.analytics.summary.lowest;
  $("firstOpen").textContent = data.analytics.summary.first_open;
  $("lastClose").textContent = data.analytics.summary.last_close;

  // Candlestick
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

  // MA/EMA overlays (if available from backend)
  const overlays = [];
  if(data.analytics && data.analytics.ma){
    const ma = data.analytics.ma, ema = data.analytics.ema || {};
    const x = rec.map(r => r.date);
    const align = (arr) => arr.slice(-(x.length));
    [5,10,20].forEach(w=>{
      if(ma[w])  overlays.push({x, y: align(ma[w]),  type:"scatter", mode:"lines", name:`MA ${w}`});
      if(ema[w]) overlays.push({x, y: align(ema[w]), type:"scatter", mode:"lines", name:`EMA ${w}`, line:{dash:"dot"}});
    });
  }

  const layout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor:  "rgba(0,0,0,0)",
    margin: {l:40, r:20, t:24, b:40},
    xaxis: { rangeslider: {visible: true}, showgrid:false },
    yaxis: { gridcolor: "rgba(255,255,255,0.08)" },
  };
  const config = { responsive:true, displaylogo:false };

  $("chartTitle").textContent = `${data.company} — ${source === "live" ? period+"/"+interval : "Sample"}`;
  Plotly.newPlot("chart", [trace, ...overlays], layout, config);
  toast("Loaded!");
}

// UI bindings
$("goBtn").addEventListener("click", searchCompany);
$("clearDates").addEventListener("click", ()=>{ $("startDate").value = ""; $("endDate").value = ""; toast("Cleared dates"); });
$("themeToggle").addEventListener("click", ()=>{
  document.body.classList.toggle("light");
  $("themeToggle").textContent = document.body.classList.contains("light") ? "☀️" : "🌙";
});
document.querySelectorAll(".quick").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    $("period").value = btn.dataset.p;
    toast(`Period: ${btn.dataset.p}`);
  });
});
