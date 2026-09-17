const API_URL = 'http://localhost:5000/model2';

// State
let requiredFeatures = [];
let allObservations = [];
let trendChartInstance = null;
let devChartInstance = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch(`${API_URL}/features`);
        const data = await res.json();
        requiredFeatures = data.features || [];
        
        await loadDatasetMetadata();
        await fetchModelInfo();
        
    } catch (e) {
        console.error("Could not load initial data. Is the backend running?", e);
        document.getElementById('data-status').innerHTML = '<h3 style="color:var(--danger)">Backend Offline</h3>';
    }
});

// UI Tabs
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabId).classList.add('active');
    document.querySelector(`[onclick="switchTab('${tabId}')"]`).classList.add('active');
    
    if(tabId !== 'scenarios') {
        document.getElementById('scenario-warning').style.display = 'none';
    }
}

// ----------------------------------------------------
// Dataset Loading & Metadata
// ----------------------------------------------------
async function loadDatasetMetadata() {
    try {
        const res = await fetch(`${API_URL}/dataset/info`);
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('data-status').innerHTML = `
                <h3 style="color:var(--success)">Historical CIP Dataset Loaded</h3>
                <p style="font-size: 0.9rem; margin-top: 0.5rem; color: var(--text-muted)">
                    Rows: ${data.total_rows} | 
                    Range: ${data.date_range[0]} to ${data.date_range[1]} | 
                    PHE Count: ${data.phe_list.length} | 
                    Steps: ${data.step_list.length}
                </p>
            `;
            
            // Populate quality panel
            document.getElementById('quality-list').innerHTML = `
                <li><span>Total Observations:</span> <span>${data.total_rows}</span></li>
                <li><span>Missing Values:</span> <span>${data.missing_values}</span></li>
                <li><span>Valid Observations:</span> <span>${data.valid_observations}</span></li>
                <li><span>PHE Coverage:</span> <span>${data.phe_list.join(', ')}</span></li>
                <li><span>Step Coverage:</span> <span>${data.step_list.join(', ')}</span></li>
            `;
            
            // Populate selectors
            const pheSel = document.getElementById('sel_phe');
            data.phe_list.forEach(phe => {
                pheSel.innerHTML += `<option value="${phe}">${phe}</option>`;
            });
            
            const stepSel = document.getElementById('sel_step');
            data.step_list.forEach(step => {
                stepSel.innerHTML += `<option value="${step}">${step}</option>`;
            });
            
            await fetchObservations();
            await renderTrendChart();
        } else {
            document.getElementById('data-status').innerHTML = `<h3 style="color:var(--danger)">Error: ${data.message}</h3>`;
        }
    } catch (e) {
        console.error(e);
    }
}

async function fetchModelInfo() {
    try {
        const res = await fetch(`${API_URL}/info`);
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('model-info-list').innerHTML = `
                <li><span>Method:</span> <span>${data.method}</span></li>
                <li><span>Baseline:</span> <span>${data.baseline}</span></li>
                <li><span>Technique:</span> <span>${data.technique}</span></li>
                <li><span>Output:</span> <span>${data.output}</span></li>
            `;
        }
    } catch (e) {
        console.error(e);
    }
}

// ----------------------------------------------------
// Observation Selector
// ----------------------------------------------------
async function fetchObservations() {
    const phe = document.getElementById('sel_phe').value;
    const step = document.getElementById('sel_step').value;
    
    let url = `${API_URL}/dataset/observations?limit=100`;
    if (phe) url += `&phe_id=${phe}`;
    if (step) url += `&process_step=${step}`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.status === 'success') {
            allObservations = data.observations;
            const obsSel = document.getElementById('sel_obs');
            obsSel.innerHTML = '';
            allObservations.forEach((obs, idx) => {
                obsSel.innerHTML += `<option value="${idx}">${obs.timestamp} | ${obs.phe_id} | ${obs.process_step}</option>`;
            });
            
            // Load the first one implicitly
            if(allObservations.length > 0) {
                // Not scoring immediately, just ready
            }
        }
    } catch (e) {
        console.error(e);
    }
}

async function submitObservation() {
    const idx = document.getElementById('sel_obs').value;
    if(idx !== "") {
        await scoreObservation(allObservations[idx]);
    }
}

// ----------------------------------------------------
// Synthetic Scenarios
// ----------------------------------------------------
async function runScenario(type) {
    document.getElementById('scenario-warning').style.display = 'block';
    
    let obs = {
        phe_id: 'PHE01',
        process_step: 'FINAL_FLUSH',
        flow_lph: 29886.7, // mean
        temp_in: 92.06,    // mean
        conductivity: 23.68, // mean
        steam_pressure: -2.33,
        sterilization_sp: 80.0
    };
    
    if (type === 'high_temp') {
        obs.temp_in += (1.00 * 4); // +4 std
    } else if (type === 'low_flow') {
        obs.flow_lph -= (723.3 * 3); // -3 std
    } else if (type === 'combined') {
        obs.temp_in += (1.00 * 3);
        obs.conductivity += (27.3 * 3);
        obs.steam_pressure -= (0.01 * 4);
    }
    
    await scoreObservation(obs);
}

// ----------------------------------------------------
// CSV Upload & Batch
// ----------------------------------------------------
async function uploadCsv() {
    const fileInput = document.getElementById('csv-file');
    if (!fileInput.files[0]) {
        alert("Please select a CSV file first.");
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        const res = await fetch(`${API_URL}/batch`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (data.status === 'success' && data.results.length > 0) {
            updateDashboard(data.results[0]);
            alert(`Batch processed ${data.results.length} rows successfully.`);
        } else {
            alert("Error processing CSV: " + data.message);
        }
    } catch (e) {
        console.error(e);
        alert("API request failed.");
    }
}

async function analyzeEntireDataset() {
    alert("Starting batch analysis on entire dataset. This will download a CSV when complete.");
    try {
        const res = await fetch(`${API_URL}/batch_dataset`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            downloadCSV(data.results, 'model2_results.csv');
        } else {
            alert("Error: " + data.message);
        }
    } catch(e) {
        console.error(e);
        alert("API request failed.");
    }
}

function downloadCSV(dataArray, filename) {
    if(!dataArray || dataArray.length === 0) return;
    
    const headers = Object.keys(dataArray[0]);
    const csvContent = [
        headers.join(','),
        ...dataArray.map(row => headers.map(h => row[h]).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ----------------------------------------------------
// Scoring & Dashboard
// ----------------------------------------------------
async function scoreObservation(obs) {
    try {
        const res = await fetch(`${API_URL}/score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(obs)
        });
        const data = await res.json();
        updateDashboard(data, obs);
    } catch (e) {
        console.error(e);
        alert("API request failed.");
    }
}

function updateDashboard(result, rawObs = {}) {
    if (result.status === 'error') {
        document.getElementById('interpretation-text').innerText = "Error: " + result.message;
        return;
    }
    
    // Update Score Circle
    const scoreText = document.getElementById('score-text');
    const circle = document.getElementById('health-circle');
    
    scoreText.textContent = result.health_score;
    circle.setAttribute('stroke-dasharray', `${result.health_score}, 100`);
    
    circle.className = `circle grade-${result.grade}`;
    document.getElementById('grade-text').textContent = `Grade: ${result.grade}`;
    document.getElementById('context-text').textContent = `PHE: ${result.context.equipment} | Step: ${result.context.step}`;
    document.getElementById('coverage-text').textContent = `Data Coverage: ${result.data_coverage}`;
    document.getElementById('interpretation-text').textContent = result.interpretation;
    
    renderBaselineTable(result, rawObs);
    renderDeviationChart(result);
}

function renderBaselineTable(result, rawObs) {
    const tbody = document.querySelector('#baseline-table tbody');
    tbody.innerHTML = '';
    
    const rawDevs = result.raw_deviations || {};
    const bStats = result.baseline_stats || {};
    
    if (Object.keys(rawDevs).length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No deviations</td></tr>';
        return;
    }
    
    for(const [feat, dev] of Object.entries(rawDevs)) {
        const current = rawObs[feat] !== undefined ? parseFloat(rawObs[feat]).toFixed(2) : '--';
        const baseMean = bStats[feat] ? parseFloat(bStats[feat].mean).toFixed(2) : '--';
        
        let colorClass = 'dev-positive';
        if (dev < 0) colorClass = 'dev-negative';
        if (Math.abs(dev) > 3) colorClass = 'dev-critical';
        
        tbody.innerHTML += `
            <tr>
                <td>${feat}</td>
                <td>${current}</td>
                <td>${baseMean}</td>
                <td class="${colorClass}">${dev > 0 ? '+' : ''}${dev.toFixed(2)}σ</td>
            </tr>
        `;
    }
}

// ----------------------------------------------------
// Charts
// ----------------------------------------------------
function renderDeviationChart(result) {
    const rawDevs = result.raw_deviations || {};
    
    // Sort by absolute magnitude
    const sortedDevs = Object.entries(rawDevs).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
    
    const labels = sortedDevs.map(d => d[0]);
    const data = sortedDevs.map(d => d[1]);
    const colors = data.map(d => {
        if(Math.abs(d) > 3) return 'rgba(239, 68, 68, 0.8)'; // critical
        if(d > 0) return 'rgba(245, 158, 11, 0.8)'; // pos warning
        return 'rgba(59, 130, 246, 0.8)'; // neg accent
    });

    const ctx = document.getElementById('deviationChart').getContext('2d');
    
    if (devChartInstance) {
        devChartInstance.destroy();
    }
    
    devChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Deviation (σ)',
                data: data,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#f8fafc' }
                }
            }
        }
    });
}

async function renderTrendChart() {
    try {
        const res = await fetch(`${API_URL}/dataset/trend`);
        const data = await res.json();
        if (data.status === 'success') {
            
            const labels = data.trend.map(d => new Date(d.timestamp * 86400000).toLocaleDateString()); // Assuming excel timestamp, rough approx for display
            const scores = data.trend.map(d => d.health_score);
            
            const ctx = document.getElementById('trendChart').getContext('2d');
            
            if (trendChartInstance) {
                trendChartInstance.destroy();
            }
            
            trendChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Health Score',
                        data: scores,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8', maxTicksLimit: 10 }
                        },
                        y: {
                            min: 0,
                            max: 100,
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#94a3b8' }
                        }
                    }
                }
            });
        }
    } catch(e) {
        console.error("Trend chart error", e);
    }
}
