/* app.js: Home + Sidebar + Compare + Upload + Export */
const $ = id => document.getElementById(id);
const toast = (m) => { const t = $("toast"); t.textContent = m; t.hidden = false; setTimeout(()=> t.hidden=true, 2200); }

function navTo(tab){
  document.querySelectorAll(".tab").forEach(el=>el.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(b=>b.classList.remove("active"));
  document.querySelector(`[data-tab="${tab}"]`)?.classList.add("active");
  document.getElementById(tab).classList.add("active");
}

/* Sidebar nav binding */
document.querySelectorAll(".nav-item").forEach(b=>{
  b.addEventListener("click", ()=>{
    const t = b.getAttribute("data-tab");
    navTo(t);
    b.classList.add("active");
    if(t === "home") loadFeatured();
    if(t === "compare") loadCompaniesForCompare();
  });
});

/* Theme toggle */
$("themeToggle").addEventListener("click", ()=>{
  document.body.classList.toggle("light");
  $("themeToggle").textContent = document.body.classList.contains("light") ? "☀️" : "🌙";
});

/* Open compare from home */
$("openCompare").addEventListener("click", ()=>{ navTo("compare"); loadCompaniesForCompare(); });

/* Featured */
async function loadFeatured(){
  try{
    const res = await fetch("/api/featured");
    const j = await res.json();
    const area = $("featured");
    area.innerHTML = "";
    j.featured.forEach(item=>{
      const div = document.createElement("div"); div.className = "card feature";
      const up = (item.pct !== null && item.pct >= 0);
      div.innerHTML = `<div class="ticker">${item.ticker}</div>
        <div class="price">${item.last !== null ? item.last : "N/A"}</div>
        <div class="change ${up ? "up" : "down"}">${item.pct !== null ? (item.pct+"%") : ""}</div>`;
      area.appendChild(div);
    });
    // small market snapshot placeholder: show a simple line (we can reuse plotly)
    const marketTrace = { x: j.featured.map(f=>f.ticker), y: j.featured.map(f=>f.last || 0), type:"bar"};
    Plotly.newPlot("marketChart", [marketTrace], {margin:{t:10,b:30}}, {responsive:true,displaylogo:false});
  }catch(e){
    console.error(e); toast("Could not load featured");
  }
}
$("reloadFeatured").addEventListener("click", loadFeatured);

/* Compare: populate dropdowns */
async function loadCompaniesForCompare(){
  try{
    const res = await fetch("/api/companies");
    const j = await res.json();
    const live = j.live || [], sample = j.sample || [];
    const source = $("sourceC").value;
    const list = source === "live" ? live : sample;
    const t1 = $("t1"), t2 = $("t2");
    t1.innerHTML = "<option value=''>-- select --</option>";
    t2.innerHTML = "<option value=''>-- select --</option>";
    list.forEach(v=>{
      const o1 = document.createElement("option"); o1.value=v; o1.text=v; t1.appendChild(o1);
      const o2 = document.createElement("option"); o2.value=v; o2.text=v; t2.appendChild(o2);
    });
  }catch(e){
    console.error(e); toast("Company list load failed");
  }
}
$("sourceC").addEventListener("change", loadCompaniesForCompare);

/* Compare action */
$("doCompare").addEventListener("click", async ()=>{
  const s = $("sourceC").value, a = $("t1").value, b = $("t2").value, mode = $("modeC").value;
  const period = $("periodC").value, interval = $("intervalC").value;
  if(!a || !b){ toast("Select two companies"); return; }
  navTo("compare");
  setLoading(true);
  try{
    const url = `/api/compare?t1=${encodeURIComponent(a)}&t2=${encodeURIComponent(b)}&source=${encodeURIComponent(s)}&period=${encodeURIComponent(period)}&interval=${encodeURIComponent(interval)}&mode=${encodeURIComponent(mode)}`;
    const res = await fetch(url);
    setLoading(false);
    if(!res.ok){ toast("Compare failed"); return; }
    const j = await res.json();
    renderCompare(j);
  }catch(e){
    setLoading(false); toast("Compare error"); console.error(e);
  }
});

/* loading helper */
function setLoading(on){ document.body.classList.toggle("loading", !!on); }

/* Render compare results */
function renderCompare(data){
  const left = data.left, right = data.right;
  const lrec = left.records || [], rrec = right.records || [];
  $("cA").textContent = data.t1; $("cB").textContent = data.t2;
  const pct = (arr) => arr.length>1 ? ((arr[arr.length-1].close - arr[0].open)/arr[0].open*100).toFixed(2) : "—";
  $("cPA").textContent = lrec.length ? pct(lrec)+"%" : "—";
  $("cPB").textContent = rrec.length ? pct(rrec)+"%" : "—";
  const common = lrec.map(r=>r.date).filter(d=>rrec.map(rr=>rr.date).includes(d));
  $("cRange").textContent = common.length ? `${common[0]} → ${common[common.length-1]}` : "—";

  const mode = data.mode || "overlay";
  const chart = $("chartCompare");
  Plotly.purge(chart);

  if(mode === "overlay"){
    const traces = [];
    if(lrec.length) traces.push({x: lrec.map(r=>r.date), y: lrec.map(r=>r.close), mode:"lines", name:data.t1, line:{width:2}});
    if(rrec.length) traces.push({x: rrec.map(r=>r.date), y: rrec.map(r=>r.close), mode:"lines", name:data.t2, line:{width:2}});
    Plotly.newPlot(chart, traces, {margin:{t:20,b:40}, xaxis:{rangeslider:{visible:true}}}, {responsive:true,displaylogo:false});
  } else {
    const traces = [];
    if(lrec.length) traces.push(Object.assign({x: lrec.map(r=>r.date), open: lrec.map(r=>r.open), high: lrec.map(r=>r.high), low: lrec.map(r=>r.low), close: lrec.map(r=>r.close), type:"candlestick", name:data.t1}, {xaxis:"x", yaxis:"y"}));
    if(rrec.length) traces.push(Object.assign({x: rrec.map(r=>r.date), open: rrec.map(r=>r.open), high: rrec.map(r=>r.high), low: rrec.map(r=>r.low), close: rrec.map(r=>r.close), type:"candlestick", name:data.t2}, {xaxis:"x2", yaxis:"y2"}));
    const layout = {grid:{rows:2, columns:1, pattern:"independent", roworder:"top to bottom"}, margin:{t:20,b:40}, xaxis:{rangeslider:{visible:true}}};
    Plotly.newPlot(chart, traces, layout, {responsive:true,displaylogo:false});
  }
}

/* Upload CSV */
$("uploadNow").addEventListener("click", async ()=>{
  const fi = $("fileInput");
  if(!fi.files || !fi.files[0]){ toast("Select CSV"); return; }
  const fd = new FormData(); fd.append("file", fi.files[0]);
  setLoading(true);
  try{
    const res = await fetch("/api/upload", {method:"POST", body:fd});
    setLoading(false);
    if(!res.ok){ toast("Upload failed"); return; }
    const j = await res.json();
    $("uploadPreview").innerHTML = `<pre style="max-height:240px; overflow:auto">${JSON.stringify(j.records.slice(0,10), null, 2)}</pre>`;
    $("uploadPreview").hidden = false;
    toast("Uploaded");
  }catch(e){
    setLoading(false); toast("Upload error"); console.error(e);
  }
});

/* Export buttons (use Plotly toImage and client-side CSV) */
$("downloadCsvMain").addEventListener("click", ()=>{
  const chart = $("chartCompare");
  if(!chart || !chart.data || chart.data.length===0){ toast("No data to export"); return; }
  // use first trace to build CSV
  const t = chart.data[0];
  let recs = [];
  if(t.type === "candlestick"){
    for(let i=0;i<t.x.length;i++) recs.push({date:t.x[i], open:t.open[i], high:t.high[i], low:t.low[i], close:t.close[i], volume:""});
  } else {
    for(let i=0;i<t.x.length;i++) recs.push({date:t.x[i], open:"", high:"", low:"", close:t.y[i], volume:""});
  }
  const csv = ["date,open,high,low,close,volume"].concat(recs.map(r=>`${r.date},${r.open},${r.high},${r.low},${r.close},${r.volume}`)).join("\n");
  const blob = new Blob([csv], {type:"text/csv"}); const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download="export.csv"; a.click();
});

/* PNG download */
$("downloadPngMain").addEventListener("click", async ()=>{
  const chart = $("chartCompare");
  try{
    const d = await Plotly.toImage(chart, {format:"png", width:1200, height:700});
    const a = document.createElement("a"); a.href = d; a.download = "chart.png"; a.click();
  }catch(e){ toast("PNG export failed"); console.error(e); }
});

/* initial load */
loadFeatured();
