from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
import base64
import io
import os
import sys
import matplotlib.pyplot as plt

# ==========================================
# 1. Ajuste de Paths para importar a FNO Paramétrica
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
fno_core_path = os.path.join(current_dir, "model_core")
sys.path.append(fno_core_path)

try:
    from fno_parametric_architecture import ParametricFNO2d
except ImportError:
    print("Aviso: Não foi possível importar fno_parametric_architecture. Verifique se o caminho está correto.")

# ==========================================
# 2. Inicialização do Servidor e Modelo
# ==========================================
app = FastAPI(title="FNO Quantum Sandbox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Subindo servidor na placa: {device}")

# Parâmetros Universais
N = 100
L = 8.0
dx = L / (N - 1)
a = 1.0 # Raio da Esfera

# Grid Espacial
x = np.linspace(-L/2, L/2, N)
z = np.linspace(-L/2, L/2, N)
X, Z = np.meshgrid(x, z, indexing='ij')
R = np.sqrt(X**2 + Z**2)

# Carregando o Cérebro Neural Paramétrico
model = None
try:
    model = ParametricFNO2d(modes1=16, modes2=16, width=96).to(device)
    weights_path = os.path.join(current_dir, "model_core/fno_parametric_best_model_v2.pth")
    
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
        model.eval()
        print("Modelo FNO Paramétrico carregado e pronto para latência zero!")
    else:
        print("Aviso: Pesos do modelo paramétrico não encontrados.")
except Exception as e:
    print(f"Erro ao carregar os pesos da FNO: {e}")

# ==========================================
# 3. Modelos de Comunicação (Pydantic)
# ==========================================
class Charge(BaseModel):
    x: int
    z: int
    q: float
    r: float

class PredictionRequest(BaseModel):
    charges: list[Charge]
    b: float
    kappa: float
    u: float

class CompareRequest(BaseModel):
    stateA: PredictionRequest
    stateB: PredictionRequest

# ==========================================
# Funções Auxiliares
# ==========================================
def compute_density(charges, b_val, kappa_val, u_val):
    V = np.zeros((N, N))
    for c in charges:
        # Re-link the UI radius (c.r) to the physical charge smearing (epsilon)
        epsilon = 0.1 + (c.r - 1) * 0.05
        
        idx_x = np.clip(c.x, 0, N - 1)
        idx_z = np.clip(c.z, 0, N - 1)
        pos_x = x[idx_x]
        pos_z = z[idx_z]
        dist = np.sqrt((X - pos_x)**2 + (Z - pos_z)**2)
        V += c.q * np.exp(-kappa_val * dist) / (dist + epsilon)

    V_clean = np.copy(V)
    V_clean[R < a] = 1000.0
    
    v_tensor = torch.tensor(V_clean, dtype=torch.float32)
    x_tensor = torch.tensor(X, dtype=torch.float32)
    z_tensor = torch.tensor(Z, dtype=torch.float32)
    
    b_plane = torch.full((N, N), b_val, dtype=torch.float32)
    kappa_plane = torch.full((N, N), kappa_val, dtype=torch.float32)
    u_plane = torch.full((N, N), u_val, dtype=torch.float32)
    
    inputs = torch.zeros(1, N, N, 6, dtype=torch.float32, device=device)
    inputs[0, :, :, 0] = v_tensor
    inputs[0, :, :, 1] = x_tensor
    inputs[0, :, :, 2] = z_tensor
    inputs[0, :, :, 3] = b_plane
    inputs[0, :, :, 4] = kappa_plane
    inputs[0, :, :, 5] = u_plane
    
    if model is not None:
        if len(charges) == 0:
            # Bypass FNO for 0 charges to prevent ML hallucination artifacts
            density = np.zeros((N, N))
        else:
            with torch.no_grad():
                out = model(inputs)
                density = out[0, :, :, 0].cpu().numpy()
    else:
        density = np.zeros((N, N))
    
    # Impedir densidades negativas (artefato da camada linear da IA)
    density = np.clip(density, 0, None)
    density[R < a] = np.nan
    return density

def create_plot_base64(X_grid, Z_grid, matrix, cmap, label, vmin=None, vmax=None):
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    
    cax = ax.contourf(X_grid, Z_grid, matrix, levels=50, cmap=cmap, vmin=vmin, vmax=vmax, extend='both')
    cbar = fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors='white')
    cbar.outline.set_edgecolor('white')
    cbar.set_label(label, color='white', labelpad=10)
    
    circle = plt.Circle((0, 0), a, color='#1e293b', zorder=10)
    ax.add_artist(circle)
    
    ax.set_aspect('equal')
    ax.set_xlim(-L/2, L/2)
    ax.set_ylim(-L/2, L/2)
    
    ax.grid(color='white', alpha=0.3, linestyle='--')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_alpha(0.5)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='black', bbox_inches='tight', dpi=100)
    plt.close(fig)
    
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# ==========================================
# 4. Rota de Inferência
# ==========================================
@app.post("/predict")
async def predict_density(request: PredictionRequest):
    density = compute_density(request.charges, request.b, request.kappa, request.u)
    
    # 1. Preparar densidade limpa para os cálculos numéricos e visuais
    valid_mask = ~np.isnan(density)
    valid_density = density[valid_mask]
    valid_density = np.clip(valid_density, 0, None)
    
    # 2. Gerar Imagem com limite visual para não "esconder" a nuvem (satura o brilho nos picos)
    vmax_visual = np.percentile(valid_density, 98) if len(valid_density) > 0 else None
    if vmax_visual is not None and vmax_visual < 0.1:
        vmax_visual = 0.5 # mínimo de escala para nuvens muito fracas
        
    img_b64 = create_plot_base64(X, Z, density, 'inferno', 'Densidade Polimérica', vmax=vmax_visual)
    
    # 3. Cálculos Quantitativos (Massa, Centro de Massa, Raio de Giração)
    mass = float(np.sum(valid_density) * dx * dx)
    
    if mass > 1e-6:
        com_x = float(np.sum(X[valid_mask] * valid_density) * dx * dx / mass)
        com_z = float(np.sum(Z[valid_mask] * valid_density) * dx * dx / mass)
        rg_sq = np.sum(((X[valid_mask] - com_x)**2 + (Z[valid_mask] - com_z)**2) * valid_density) * dx * dx / mass
        rg = float(np.sqrt(rg_sq))
    else:
        com_x, com_z, rg = 0.0, 0.0, 0.0
        
    # 3. Heurística Termodinâmica de Fase (Termômetro)
    phase = "Estável (Intermediário)"
    if request.u > 0.2 and rg < 2.0:
        phase = "Colapsado (Globule)"
    elif request.u < -0.2:
        phase = "Inchado (Coil)"
        
    return {
        "image": img_b64,
        "metrics": {
            "mass": mass,
            "com_x": com_x,
            "com_z": com_z,
            "rg": rg,
            "phase": phase
        }
    }

# ==========================================
# 5. Rota de Comparação
# ==========================================
@app.post("/compare")
async def compare_states(request: CompareRequest):
    densityA = compute_density(request.stateA.charges, request.stateA.b, request.stateA.kappa, request.stateA.u)
    densityB = compute_density(request.stateB.charges, request.stateB.b, request.stateB.kappa, request.stateB.u)
    
    diff = densityB - densityA
    max_val = np.nanmax(np.abs(diff))
    if np.isnan(max_val) or max_val == 0:
        max_val = 1.0 # fallback
        
    img_b64 = create_plot_base64(X, Z, diff, 'RdBu_r', 'Diferença de Densidade (B - A)', vmin=-max_val, vmax=max_val)
    return {"image": img_b64}

# ==========================================
# 6. Rota do Histórico de Loss
# ==========================================
@app.get("/loss")
async def get_loss_history():
    loss_path = os.path.join(current_dir, "model_core/parametric_loss_history.pt")
    if not os.path.exists(loss_path):
        raise HTTPException(status_code=404, detail="Loss history not found yet")
        
    try:
        history = torch.load(loss_path)
        train_loss = history['train']
        test_loss = history['test']
        
        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        fig.patch.set_facecolor('#1e1030')
        ax.set_facecolor('#1e1030')
        
        ax.plot(train_loss, label='Train Loss', color='#818cf8', linewidth=2)
        ax.plot(test_loss, label='Test Loss', color='#fca5a5', linewidth=2)
        ax.set_yscale('log')
        ax.set_xlabel('Epochs', color='white')
        ax.set_ylabel('Loss (MSE)', color='white')
        
        ax.legend(facecolor='black', edgecolor='white', labelcolor='white')
        ax.grid(color='white', alpha=0.1, linestyle='--')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
            spine.set_alpha(0.3)
            
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#1e1030', bbox_inches='tight', dpi=100)
        plt.close(fig)
        
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode('utf-8')
        return {"image": img_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
