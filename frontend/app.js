const canvas = document.getElementById('inputCanvas');
const ctx = canvas.getContext('2d');
const chargeSlider = document.getElementById('chargeSlider');
const chargeValueLabel = document.getElementById('chargeValue');
const radiusSlider = document.getElementById('radiusSlider');
const clearBtn = document.getElementById('clearBtn');
const outputImage = document.getElementById('outputImage');
const loading = document.getElementById('loading');
const latencyLabel = document.getElementById('latency');

const kuhnSlider = document.getElementById('kuhnSlider');
const kuhnValue = document.getElementById('kuhnValue');
const debyeSlider = document.getElementById('debyeSlider');
const debyeValue = document.getElementById('debyeValue');
const florySlider = document.getElementById('florySlider');
const floryValue = document.getElementById('floryValue');

const lossImage = document.getElementById('lossImage');
const lossLoading = document.getElementById('lossLoading');

// Novos Elementos UI
const massValue = document.getElementById('massValue');
const rgValue = document.getElementById('rgValue');
const comValue = document.getElementById('comValue');
const phaseThermometer = document.getElementById('phaseThermometer');
const phaseValue = document.getElementById('phaseValue');

const saveStateBtn = document.getElementById('saveStateBtn');
const compareBtn = document.getElementById('compareBtn');
const diffContainer = document.getElementById('diffContainer');
const diffImage = document.getElementById('diffImage');
const diffLoading = document.getElementById('diffLoading');

let charges = [];
const N = 100; // Resolução do modelo FNO

let savedStateA = null;
let currentPayload = null;

// Atualiza labels dos parâmetros físicos
kuhnSlider.addEventListener('input', (e) => { kuhnValue.textContent = e.target.value; requestPrediction(); });
debyeSlider.addEventListener('input', (e) => { debyeValue.textContent = e.target.value; requestPrediction(); });
florySlider.addEventListener('input', (e) => { floryValue.textContent = e.target.value; requestPrediction(); });

// Atualiza o label do slider de carga
chargeSlider.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    if(val > 0) {
        chargeValueLabel.textContent = `Repulsivo (+${val})`;
        chargeValueLabel.style.color = '#fca5a5';
    } else if (val < 0) {
        chargeValueLabel.textContent = `Atrativo (${val})`;
        chargeValueLabel.style.color = '#38bdf8';
    } else {
        chargeValueLabel.textContent = `Neutro (0)`;
        chargeValueLabel.style.color = '#cbd5e1';
    }
});

// Desenha a esfera, o grid e as partículas
function drawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Fundo
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Variáveis Físicas
    const L = 8.0;
    const a = 1.0;
    const pxPerUnit = canvas.width / L; // 400 / 8 = 50 pixels por unidade

    // Desenhar Grid Físico
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.font = '12px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    for(let i = -4; i <= 4; i++) {
        const px = (i + L/2) * pxPerUnit; // Normaliza de -4..4 para 0..8
        
        // Linhas de Grade
        ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, canvas.height); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(0, px); ctx.lineTo(canvas.width, px); ctx.stroke();
        
        // Textos dos eixos
        if(i !== 0) {
            ctx.fillText(i.toString(), px, canvas.height/2 + 10); // Eixo X
            ctx.fillText((-i).toString(), canvas.width/2 - 10, px); // Eixo Z (invertido visualmente para y)
        }
    }

    // Interior Sólido (Nanopartícula)
    ctx.beginPath();
    ctx.arc(canvas.width/2, canvas.height/2, a * pxPerUnit, 0, 2*Math.PI);
    ctx.fillStyle = 'rgba(30, 41, 59, 0.8)'; // Cor escura para o sólido
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Desenha as cargas
    charges.forEach(c => {
        const px = (c.x / N) * canvas.width;
        const py = (c.z / N) * canvas.height;
        
        ctx.beginPath();
        ctx.arc(px, py, c.r * 2, 0, 2*Math.PI);
        
        if(c.q > 0) {
            ctx.fillStyle = `rgba(239, 68, 68, ${Math.min(1.0, c.q/5)})`; // Vermelho (Repulsivo)
            ctx.shadowColor = '#ef4444';
        } else {
            ctx.fillStyle = `rgba(56, 189, 248, ${Math.min(1.0, Math.abs(c.q)/5)})`; // Azul (Atrativo)
            ctx.shadowColor = '#38bdf8';
        }
        ctx.shadowBlur = 15;
        ctx.fill();
        ctx.shadowBlur = 0; // reset
    });
}

// Limpa tudo
clearBtn.addEventListener('click', () => {
    charges = [];
    kuhnSlider.value = 1.0;
    kuhnValue.textContent = '1.0';
    debyeSlider.value = 1.0;
    debyeValue.textContent = '1.0';
    florySlider.value = 0.0;
    floryValue.textContent = '0.0';
    chargeSlider.value = 5;
    chargeValueLabel.textContent = `Repulsivo (+5)`;
    chargeValueLabel.style.color = '#fca5a5';
    radiusSlider.value = 5;
    
    savedStateA = null;
    compareBtn.disabled = true;
    diffContainer.style.display = 'none';

    drawCanvas();
    outputImage.style.display = 'none';
    requestPrediction();
});

// Clique no Canvas
canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;

    const grid_x = Math.floor((px / canvas.width) * N);
    const grid_z = Math.floor((py / canvas.height) * N);
    const q = parseFloat(chargeSlider.value);
    const r = parseFloat(radiusSlider.value);

    charges.push({x: grid_x, z: grid_z, q: q, r: r});
    drawCanvas();
    requestPrediction();
});

// Botão direito para remover carga
canvas.addEventListener('contextmenu', (e) => {
    e.preventDefault(); // Impede o menu do navegador
    if (charges.length === 0) return;

    const rect = canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;

    const grid_x = Math.floor((px / canvas.width) * N);
    const grid_z = Math.floor((py / canvas.height) * N);

    let closestIdx = -1;
    let minDist = Infinity;

    for (let i = 0; i < charges.length; i++) {
        const c = charges[i];
        const dist = Math.sqrt(Math.pow(c.x - grid_x, 2) + Math.pow(c.z - grid_z, 2));
        if (dist < minDist) {
            minDist = dist;
            closestIdx = i;
        }
    }

    // Tolerância de ~10 pixels/grid para o clique
    if (closestIdx !== -1 && minDist < 10) {
        charges.splice(closestIdx, 1);
        drawCanvas();
        requestPrediction();
    }
});

// Salvar Estado e Comparar
saveStateBtn.addEventListener('click', () => {
    if (currentPayload) {
        savedStateA = JSON.parse(JSON.stringify(currentPayload));
        compareBtn.disabled = false;
        saveStateBtn.textContent = "Estado A Salvo! ✓";
        setTimeout(() => saveStateBtn.textContent = "Salvar Estado Atual (A)", 2000);
    }
});

compareBtn.addEventListener('click', async () => {
    if (!savedStateA || !currentPayload) return;
    
    diffContainer.style.display = 'flex';
    diffImage.style.display = 'none';
    diffLoading.style.display = 'block';
    
    try {
        const payload = {
            stateA: savedStateA,
            stateB: currentPayload
        };
        const response = await fetch('http://localhost:8000/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if(response.ok) {
            const data = await response.json();
            diffImage.src = "data:image/png;base64," + data.image;
            diffImage.style.display = 'block';
            diffLoading.style.display = 'none';
        }
    } catch (err) {
        console.error("Erro na Comparação:", err);
        diffLoading.style.display = 'none';
    }
});

// Comunicação com o Servidor Python (FastAPI)
async function requestPrediction() {
    const startTime = performance.now();
    
    if(charges.length > 0) {
        outputImage.style.display = 'none';
        loading.style.display = 'block';
    }

    currentPayload = {
        charges: charges,
        b: parseFloat(kuhnSlider.value),
        kappa: parseFloat(debyeSlider.value),
        u: parseFloat(florySlider.value)
    };

    try {
        const response = await fetch('http://localhost:8000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentPayload)
        });

        if(response.ok) {
            const data = await response.json();
            outputImage.src = "data:image/png;base64," + data.image;
            outputImage.style.display = 'block';
            loading.style.display = 'none';
            
            // Atualizar Métricas
            if (data.metrics) {
                massValue.textContent = data.metrics.mass.toFixed(2);
                rgValue.textContent = data.metrics.rg.toFixed(3);
                comValue.textContent = `(${data.metrics.com_x.toFixed(2)}, ${data.metrics.com_z.toFixed(2)})`;
                
                phaseValue.textContent = data.metrics.phase;
                
                // Atualizar Cor do Termômetro
                phaseThermometer.className = "alert-box"; // reset
                if (data.metrics.phase.includes('Colapsado')) {
                    phaseThermometer.classList.add('alert-globule');
                } else if (data.metrics.phase.includes('Inchado')) {
                    phaseThermometer.classList.add('alert-coil');
                }
            }
            
            const endTime = performance.now();
            latencyLabel.textContent = `Latência FNO: ${Math.round(endTime - startTime)} ms`;
        }
    } catch (err) {
        console.error("Erro ao chamar a FNO:", err);
        latencyLabel.textContent = "Servidor Offline";
        loading.style.display = 'none';
    }
}

async function fetchLoss() {
    try {
        const response = await fetch('http://localhost:8000/loss');
        if(response.ok) {
            const data = await response.json();
            if(data.image) {
                lossImage.src = "data:image/png;base64," + data.image;
                lossImage.style.display = 'block';
                lossLoading.style.display = 'none';
            } else {
                lossLoading.style.display = 'none';
                lossImage.alt = "Histórico não disponível ainda";
            }
        }
    } catch (err) {
        console.log("Loss endpoint not available yet");
    }
}

// Init
drawCanvas();
requestPrediction();
fetchLoss();
setInterval(fetchLoss, 10000); // Atualiza o gráfico de loss a cada 10 segundos

// Lógica de Troca de Abas
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-tab');
        document.getElementById(targetId).classList.add('active');
    });
});
