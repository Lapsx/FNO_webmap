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
    model = ParametricFNO2d(modes1=16, modes2=16, width=64).to(device)
    weights_path = os.path.join(current_dir, "model_core/fno_parametric_best_model.pth")
    
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
        model.eval()
        print("Modelo FNO Paramétrico carregado e pronto para latência zero!")
    else:
        print("Aviso: Pesos do modelo paramétrico não encontrados. Usando inicialização aleatória até que o treinamento termine.")
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

# ==========================================
# 4. Rota de Inferência Instantânea Paramétrica
# ==========================================
@app.post("/predict")
async def predict_density(request: PredictionRequest):
    # Base vazia de potencial
    V = np.zeros((N, N))
    
    # Injetando Cargas Locais
    for c in request.charges:
        pos_x = x[c.x]
        pos_z = z[c.z]
        sigma = c.r * dx * 1.5 
        V += c.q * np.exp(-((X - pos_x)**2 + (Z - pos_z)**2) / (2 * sigma**2))

    # A Física da Partícula Sólida
    V_clean = np.copy(V)
    V_clean[R < a] = 10.0
    
    # Preparando Tensor PyTorch [1, N, N, 6]
    v_tensor = torch.tensor(V_clean, dtype=torch.float32)
    x_tensor = torch.tensor(X, dtype=torch.float32)
    z_tensor = torch.tensor(Z, dtype=torch.float32)
    
    # Parâmetros Expandidos
    b_plane = torch.full((N, N), request.b, dtype=torch.float32)
    kappa_plane = torch.full((N, N), request.kappa, dtype=torch.float32)
    u_plane = torch.full((N, N), request.u, dtype=torch.float32)
    
    inputs = torch.zeros(1, N, N, 6, dtype=torch.float32, device=device)
    inputs[0, :, :, 0] = v_tensor
    inputs[0, :, :, 1] = x_tensor
    inputs[0, :, :, 2] = z_tensor
    inputs[0, :, :, 3] = b_plane
    inputs[0, :, :, 4] = kappa_plane
    inputs[0, :, :, 5] = u_plane
    
    if model is not None:
        with torch.no_grad():
            out = model(inputs)
            density = out[0, :, :, 0].cpu().numpy()
    else:
        density = np.zeros((N, N))
    
    density[R < a] = np.nan
    
    # Convertendo para Base64
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    
    cax = ax.contourf(X, Z, density, levels=50, cmap='inferno')
    
    # Adicionando a legenda (colorbar)
    cbar = fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors='white')
    cbar.outline.set_edgecolor('white')
    cbar.set_label('Densidade Polimérica', color='white', labelpad=10)
    
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
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    return {"image": img_b64}

# ==========================================
# 5. Rota do Histórico de Loss
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
        fig.patch.set_facecolor('#1e1030') # Roxo opaco solicitado
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
