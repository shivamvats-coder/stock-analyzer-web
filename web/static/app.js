async function searchCompany() {
    const ticker = document.getElementById("ticker").value.trim();

    if (!ticker) {
        alert("Enter company name!");
        return;
    }

    const res = await fetch(`/api/company/${ticker}`);
    const data = await res.json();

    if (data.error) {
        alert("Company not found");
        return;
    }

    // Show analytics
    document.getElementById("analytics").innerHTML = `
        <h3>${data.company}</h3>
        <p>Average Volume: ${data.analytics.avg_volume.toFixed(2)}</p>
        <p>Highest Price: ${data.analytics.summary.highest}</p>
        <p>Lowest Price: ${data.analytics.summary.lowest}</p>
        <p>First Open: ${data.analytics.summary.first_open}</p>
        <p>Last Close: ${data.analytics.summary.last_close}</p>
    `;

    // Prepare candlestick data
    const dates = data.records.map(r => r.date);
    const opens = data.records.map(r => r.open);
    const highs = data.records.map(r => r.high);
    const lows = data.records.map(r => r.low);
    const closes = data.records.map(r => r.close);

    const trace = {
        x: dates,
        open: opens,
        high: highs,
        low: lows,
        close: closes,
        type: "candlestick"
    };

    Plotly.newPlot("chart", [trace]);
}
