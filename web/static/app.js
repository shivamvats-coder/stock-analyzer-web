/* app.js — Compare, Upload, Export, improved UI */
const $ = id => document.getElementById(id);
const toast = (m) => { const t = $("toast"); t.textContent = m; t.hidden = false; setTimeout(()=> t.hidden=true, 2400); }

function setLoading(on){ document.body.classList.toggle("loading", !!on); }
function csvFromRecords(records){
  const header = ["date","open","high","low","close","volume"];
  const rows = records.map(r => header.map(h => r[h]));
  const csv = [header.join(",")].concat(rows.map(r => r.join(","))).join("\n");
  return csv;
}
function downloadText(filename, text, type="text/csv"){
  const blob = new Blob([text], {type});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
}

/* Populate company dropdowns from backend */
async function loadCompanies(){
  try{
    const res = await fetch("/api/companies");
    const j = await res.json();
    const sample = j.sample || [];
    const live = j.live || [];
    // build full options sets
    const source = $("source").value;
    const arr = source === "live" ? live : sample;
    fillTickers(arr);
  }catch(e){
    console.error(e); toast("Could not load companies");
  }
}
function fillTickers(list){
  const t1 = $("ticker1"), t2 = $("ticker2");
  t1.innerHTML = ""; t2.innerHTML = "";
  // Add a placeholder option
  const placeholder = document.createElement("option");
  placeholder.value = ""; placeholder.text = "-- select --";
  t1.appendChild(placeholder.cloneNode(true));
  t2.appendChild(placeholder.cloneNode(true));
  for(const v of list){
    const o1 = document.createElement("option"); o1.value=v; o1.text=v; t1.appendChild(o1);
    const o2 = document.createElement("option"); o2.value=v; o2.text=v; t2.appendChild(o2);
  }
}

/* Compare action */
async function compare(){
  const src = $("source").value, t1 = $("ticker1").value.trim(), t2 = $("ticker2").value.trim();
  const period = $("period").value, interval = $("interval").value;
  const mode = $("mode").value;
  if(!t1 || !t2){ toast("Select both tickers"); return; }
  setLoading(true);
  try{
    const url = `/api/compare?t1=${encodeURIComponent(t1)}&t2=${encodeURIComponent(t2)}&source=${encodeURIComponent(src)}&period=${encodeURIComponent(period)}&interval=${encodeURIComponent(interval)}&mode=${encodeURIComponent(mode)}`;
    const res = await fetch(url);
    setLoading(false);
    if(!res.ok){ toast("Compare failed"); return; }
    const j = await res.json();
    renderCompare(j);
  }catch(e){
    setLoading(false); toast("Error fetching compare");
    console.error(e);
  }
}

/* Render compare result (overlay or stacked) */
function renderCompare(data){
  const left = data.left, right = data.right;
  const lrec = left.records || [], rrec = right.records || [];
  // compute common date range if both exist
  const datesL = lrec.map(r=>r.date), datesR = rrec.map(r=>r.date);
  const common = datesL.filter(d => datesR.includes(d));
  $("tA").textContent = data.t1; $("tB").textContent = data.t2;
  // percent change over available window
  const pct = (arr) => arr.length>1 ? ((arr[arr.length-1].close - arr[0].open)/arr[0].open*100).toFixed(2) : "—";
  $("pA").textContent = lrec.length ? pct(lrec) + "%" : "—";
  $("pB").textContent = rrec.length ? pct(rrec) + "%" : "—";
  $("range").textContent = common.length ? `${common[0]} → ${common[common.length-1]}` : "—";

  const mode = data.mode || "overlay";
  const chartDiv = $("chart");
  Plotly.purge(chartDiv);

  if(mode === "overlay"){
    // overlay close-price lines with legends
    const traces = [];
    if(lrec.length){
      traces.push({x: lrec.map(r=>r.date), y: lrec.map(r=>r.close), mode:"lines", name:data.t1, line:{width:2}});
    }
    if(rrec.length){
      traces.push({x: rrec.map(r=>r.date), y: rrec.map(r=>r.close), mode:"lines", name:data.t2, line:{width:2}});
    }
    const layout = {margin:{l:40,r:10,t:30,b:40}, xaxis:{rangeslider:{visible:true}}, paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)"};
    Plotly.newPlot(chartDiv, traces, layout, {responsive:true,displaylogo:false});
  } else {
    // stacked candlesticks: two subplots
    const traces = [];
    if(lrec.length){
      traces.push(Object.assign({x: lrec.map(r=>r.date), open: lrec.map(r=>r.open), high: lrec.map(r=>r.high), low: lrec.map(r=>r.low), close: lrec.map(r=>r.close), type:"candlestick", name:data.t1}, {xaxis:"x", yaxis:"y"}));
    }
    if(rrec.length){
      traces.push(Object.assign({x: rrec.map(r=>r.date), open: rrec.map(r=>r.open), high: rrec.map(r=>r.high), low: rrec.map(r=>r.low), close: rrec.map(r=>r.close), type:"candlestick", name:data.t2}, {xaxis:"x2", yaxis:"y2"}));
    }
    const layout = {
      grid: {rows:2, columns:1, pattern:"independent", roworder:"top to bottom"},
      margin:{l:40, r:10, t:30, b:40},
      xaxis:{rangeslider:{visible:true}}, xaxis2:{rangeslider:{visible:false}},
      paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)"
    };
    Plotly.newPlot(chartDiv, traces, layout, {responsive:true,displaylogo:false});
  }
}

/* Upload CSV action */
async function uploadCsv(){
  const fileInput = $("uploadFile");
  if(!fileInput.files || !fileInput.files[0]){ toast("Select a CSV file"); return; }
  const f = fileInput.files[0];
  const fd = new FormData(); fd.append("file", f);
  setLoading(true);
  try{
    const res = await fetch("/api/upload", {method:"POST", body: fd});
    setLoading(false);
    if(!res.ok){ toast("Upload failed"); return; }
    const j = await res.json();
    // show preview
    $("uploadPreview").hidden = false;
    $("previewTable").innerHTML = `<pre style="max-height:200px;overflow:auto">${JSON.stringify(j.records.slice(0,10), null, 2)}</pre>`;
    toast("Uploaded and parsed");
    // optionally populate ticker1 with uploaded name
    // we do not persist upload server-side in this simple demo
  }catch(e){
    setLoading(false); toast("Upload error"); console.error(e);
  }
}

/* Download CSV of currently plotted data */
async function downloadCurrentCsv(){
  // we will fetch current traces from Plotly chart and try to construct CSV for first trace
  const gd = $("chart");
  const data = gd.data;
  if(!data || data.length===0){ toast("No chart data"); return; }
  // try to choose the first candlestick or line trace and build records
  const t = data[0];
  let records = [];
  if(t.type === "candlestick"){
    for(let i=0;i<t.x.length;i++){
      records.push({date:t.x[i], open:t.open[i], high:t.high[i], low:t.low[i], close:t.close[i], volume:""});
    }
  } else {
    // line chart (overlay) — only close prices
    for(let i=0;i<t.x.length;i++){
      records.push({date:t.x[i], open:"", high:"", low:"", close:t.y[i], volume:""});
    }
  }
  const csv = csvFromRecords(records);
  downloadText("chart_export.csv", csv);
}

/* Download PNG via Plotly */
async function downloadPng(){
  const gd = $("chart");
  if(!gd) return;
  // Plotly.toImage returns a data URL
  try{
    const dataUrl = await Plotly.toImage(gd, {format:"png", height:600, width:1000});
    const a = document.createElement("a"); a.href = dataUrl; a.download = "chart.png"; document.body.appendChild(a); a.click(); a.remove();
  }catch(e){
    toast("PNG export failed");
    console.error(e);
  }
}

/* UI bindings */
$("compareBtn").addEventListener("click", compare);
$("uploadBtn").addEventListener("click", uploadCsv);
$("downloadCsv").addEventListener("click", downloadCurrentCsv);
$("downloadPng").addEventListener("click", downloadPng);
$("source").addEventListener("change", loadCompanies);
$("themeToggle").addEventListener("click", ()=>{ document.body.classList.toggle("light"); $("themeToggle").textContent = document.body.classList.contains("light") ? "☀️" : "🌙";});
$("resetZoom").addEventListener("click", ()=>{ Plotly.relayout($("chart"), { "xaxis.autorange": true, "yaxis.autorange": true }); });

document.querySelectorAll(".quick").forEach(b => b.addEventListener("click", e => { $("period").value = e.target.dataset.p; toast("Period: "+e.target.dataset.p); }));

/* Initial load */
loadCompanies();
