# FNO Polymer Sandbox ⚛️ (v0.5)

Um laboratório computacional e interativo via web criado para simular, estudar e investigar o comportamento termodinâmico de nuvens poliméricas sob influência de campos de carga interativos em tempo real.

Este projeto tem o duplo propósito de:
1. **Física de Polímeros:** Fornecer uma ferramenta visual e intuitiva para o estudo da resposta estrutural de polímeros sob variação de parâmetros fundamentais (Rigidez da cadeia, Qualidade do solvente e Blindagem iônica).
2. **Scientific Machine Learning (SciML):** Demonstrar o poder formidável de **Fourier Neural Operators (FNOs)** na resolução de PDEs (Equações Diferenciais Parciais) e campos físicos complexos. A inferência da densidade polimérica é feita quase instantaneamente por uma IA, substituindo integrais de trajetória (Self-Consistent Field Theory - SCFT) que normalmente levariam horas para convergir.

## 🌟 Funcionalidades Atuais

* **Inferência em Tempo Real:** Clique na tela para posicionar cargas locais (atrativas ou repulsivas) e observe a rede neural prever o rearranjo da nuvem polimérica em milissegundos.
* **Ajuste Paramétrico (Física Dinâmica):**
  * **Comprimento de Kuhn ($b$):** Controle a rigidez da cadeia polimérica.
  * **Comprimento de Debye ($\kappa$):** Altere a blindagem iônica e o raio de interação eletrostática do meio.
  * **Parâmetro de Flory-Huggins ($u$):** Controle a qualidade do solvente (bom solvente vs. mau solvente) forçando o inchaço ou o colapso da nuvem.
* **Histórico de Treinamento:** Acompanhe a convergência do modelo paramétrico da FNO na aba dedicada, visualizando a *Loss* em escala logarítmica.

## 🏗️ Arquitetura do Sistema

O projeto é dividido de forma enxuta:
* **Frontend:** Interface moderna construída puramente em HTML5, CSS3 (com Glassmorphism) e Vanilla JavaScript. Utiliza a API do Canvas para capturar a topologia interativa do usuário.
* **Backend:** API leve e ultra-rápida construída em **FastAPI** (Python). Recebe a topologia do Canvas, acopla os parâmetros físicos (Kuhn, Debye, Flory) num tensor 6D, roda a inferência via `PyTorch` (FNO Paramétrica) e devolve a densidade topológica serializada via Base64.
* **Motor Matemático:** As predições de densidade são convertidas visualmente em *Heatmaps* por meio da biblioteca `Matplotlib` no backend antes de chegarem ao usuário final.

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.10+
- PyTorch (compatível com seu sistema operacional/GPU)
- FastAPI e Uvicorn
- Matplotlib e NumPy

**Aviso Importante:** Esta WebApp exige os pesos treinados (`fno_parametric_best_model.pth`) e a arquitetura (`fno_parametric_architecture.py`) que foram originalmente gerados no repositório de treinamento (Scientific Machine Learning). Certifique-se de que o backend aponte para esses recursos no diretório correto.

### Subindo o Servidor
1. Navegue até a pasta do backend:
```bash
cd backend
```
2. Inicie a API com Uvicorn:
```bash
uvicorn main:app --reload
```
3. Abra o arquivo `frontend/index.html` em qualquer navegador moderno. (Ou utilize extensões como o Live Server do VS Code).

## 🔮 Próximos Passos (Roadmap v1.0)
- Melhorias gerais na UX/UI e responsividade.
- Inclusão de novas restrições topológicas.
- Extrapolação investigativa profunda: empurrar a inteligência artificial aos limites fora de seu espectro de treinamento para mapear alucinações matemáticas da FNO.

---
*Este projeto é uma ponte entre a Termodinâmica Estatística e o estado da arte do Deep Learning na Física.*
