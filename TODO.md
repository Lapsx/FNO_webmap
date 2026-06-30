# 🚀 Plano de Ação - v1.0 (FNO Polymer Sandbox)

*Arquivo criado para não perdermos o contexto do nosso progresso e dos próximos experimentos teóricos.*

## Onde Paramos (v0.5 - 30/06/2026)
- **Estrutura**: O repositório foi limpo e dividido. O `FNO_WebApp` agora é 100% autossuficiente (standalone), carregando seu próprio modelo PyTorch e histórico de pesos localmente na pasta `backend/model_core`.
- **Frontend**: Sandbox funcionando em tempo real com sliders paramétricos ajustados ($b \in [0.5, 2.0]$). Corrigimos o CSS (`object-fit: contain`) para mostrar perfeitamente a Colorbar (Densidade Polimérica). Botão de "Limpar Tudo" funcional.
- **Backend**: FastAPI rodando redondo, imagens geradas pelo `matplotlib` dimensionadas corretamente `(5,4)`.

## Próximos Passos & Melhorias de Infraestrutura
1. **Refinamento do Treino**: 
   - Aumentar o tamanho do *dataset* (atualmente em 1500 amostras).
   - Treinar a FNO para reduzir ainda mais a *Loss* de teste (atualmente em ~0.09) visando maior precisão física e melhor generalização geométrica.
   - Expandir a variedade topológica das cargas no gerador de amostras SCFT (adicionar padrões mais complexos).
2. **Novas Funcionalidades (WebApp)**:
   - Adicionar métricas quantitativas em tempo real na tela (ex: calcular automaticamente o **Raio de Giração** $R_g$ da nuvem com base na matriz `density` e exibi-lo ao lado).

## 🔬 Laboratório Virtual: Experimentos para Investigação (Roadmap)
Aqui estão as análises de Física de Polímeros que testaremos na interface com a nova FNO v1.0:

1. **Transição Coil-Globule (Novelo-Glóbulo)**
   - Varrer o slider de Flory-Huggins ($u$) de ponta a ponta e plotar a derivada do Raio de Giração para achar o colapso e a Temperatura Theta crítica matemática do modelo.
2. **Transição Crítica de Adsorção**
   - Desenhar paredes planas de cargas atrativas, brincar com a blindagem iônica ($\kappa$) e descobrir em qual valor exato o polímero transita do estado livre ("free") para o grudado ("pinned").
3. **Confinamento Nano-Estérico**
   - Desenhar canais estreitos, forçar um Comprimento de Kuhn ($b$) extremo e observar o polímero perdendo entropia de conformação num canal 1D.
4. **Resiliência da FNO (O.O.D)**
   - Forçar propositalmente alucinações (artefatos) colocando sliders em valores absurdos (ex: $b=0.1$) para entender quão rígidas são as leis físicas apreendidas pelas Equações Integrais versus o viés estatístico dos dados.
