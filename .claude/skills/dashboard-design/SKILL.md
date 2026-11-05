---
name: dashboard-design
description: Use antes de criar qualquer dashboard, painel de KPIs, gráfico ou visualização de dados (HTML, React, Plotly, Power BI, matplotlib). Define forma, hierarquia visual, tamanhos, cores validadas, UX de filtros/tooltips e acessibilidade.
---

# Dashboard Design

Um dashboard é **lido por pessoas e executado por você**. Este guia transforma "deixa bonito"
num procedimento com checagens. Ele consolida as skills oficiais da Anthropic `dataviz`
(método de visualização) e `frontend-design` (direção visual e tipografia), com regras de
layout e tamanho para painéis. Os detalhes completos estão em `references/`.

## Procedimento — nesta ordem (cor vem POR ÚLTIMO)

1. **Defina a pergunta do painel.** Quem lê, que decisão toma, com que frequência. Uma frase.
   Se não houver resposta, pergunte antes de desenhar.
2. **Escolha a forma de cada bloco** pela tarefa do dado (tabela abaixo). Às vezes a resposta
   não é gráfico: é um número.
3. **Monte o layout** (hierarquia de leitura, grid, tamanhos — seção "Visão e tamanho").
4. **Atribua cor pela função**: categórica (identidade), sequencial (magnitude), divergente
   (polaridade) ou status (estado). Ordem fixa de matizes, nunca ciclar.
5. **Valide a paleta rodando o script** — não "no olho":
   `node scripts/validate_palette.js "#hex,#hex,..." --mode light` (e de novo `--mode dark`
   com a superfície escura). Corrija todo FAIL. Versão Python: `scripts/validate_palette.py`.
6. **Aplique as specs de marca** (barras finas, linhas 2px, gaps de 2px).
7. **Camada de hover por padrão**: crosshair + tooltip em linha/área; tooltip por marca em
   barra/ponto/célula. Filtros numa linha acima de tudo.
8. **Passe de acessibilidade**: legenda para ≥2 séries, visão em tabela, dark mode
   selecionado (não invertido).
9. **Renderize e olhe** (screenshot). O validador checa cor, não colisão de rótulos nem overflow.
10. Confira contra `references/dataviz/anti-patterns.md`. Se bater com algum item, está errado.

## Escolha da forma

| O dado é… | Use | Não use |
|---|---|---|
| Um valor atual (+ tendência) | **Stat tile**: valor + delta + sparkline | Gráfico de uma barra |
| Poucos números de manchete | **Linha de KPIs** (3–5 tiles) | Barras agrupadas |
| O número que lidera o painel | **Hero figure** (≥48px, mesma sans) — só UM por tela | Fonte display/serifa |
| Razão contra um limite | **Meter** (trilho no mesmo tom) | Pizza de 2 fatias |
| Parte-todo, ≤6 partes, à primeira vista | **Barra segmentada alta** | Donut / pizza |
| Comparar partes entre si | **Barras horizontais ranqueadas**, uma cor | Donut |
| Comparar magnitude | Barra/coluna; **heatmap** em grade | Rampa de cor em categorias sem ordem |
| Tendência no tempo | Linha (área só p/ série única) | Barras para séries longas |
| Uma série é a história | **Ênfase**: 1 cor de destaque + resto cinza | 8 cores categóricas |
| Acima/abaixo de meta | Barra divergente ou linha vs. baseline | — |
| Likert / sentimento | Barra empilhada divergente centrada no neutro | — |
| Antes → depois por item | Dumbbell | — |
| >7 classes com significado | **Tabela** (ou tabela + gráfico) | Mais cores |

**Escada de séries:** 1–3 cor basta (rotule direto) · 4 rótulos diretos obrigatórios ·
5–6 limite suave, legenda ou small multiples · 7–8 teto; depois disso, agrupe em "Outros",
facete ou combine matiz × forma. Scatter/bolha/mapa: máximo 3 séries.

## Visão e tamanho (layout do painel)

**Hierarquia de leitura (padrão F / Z):** o olho começa no canto superior esquerdo.
- **Topo:** título + filtros (data primeiro) numa única linha alinhada à esquerda.
- **Faixa 1:** hero figure ou linha de KPIs — responde "está tudo bem?" em 5 segundos.
- **Faixa 2:** 1–2 gráficos principais (tendência, comparação) — o "por quê".
- **Faixa 3:** detalhamento (tabelas, quebras por dimensão) — o "onde".
- Do geral para o específico. Máximo ~5–9 blocos por tela; mais que isso vira outra aba/página.
- Uma tela = uma pergunta. Se um gráfico precisa de filtro próprio, é outro dashboard.

**Grid e espaçamento:**
- Grid de **12 colunas**; KPIs em 3 ou 4 colunas cada (4 ou 3 por linha); gráfico principal
  8–12 colunas; secundário 4–6.
- Escala de espaçamento em múltiplos de **4/8px**: 4 · 8 · 12 · 16 · 24 · 32 · 48.
- Padding interno do card **16–24px**; gap entre cards **16–24px**; margem de página
  **24–32px** no desktop, **16px** no mobile.
- Alinhe tudo a uma borda esquerda comum; números alinhados à direita em tabelas.
- Altura do container do gráfico **inclui a faixa do eixo X** (senão gera scroll interno).
- Alturas típicas: stat tile ~96–140px; gráfico principal 280–400px; secundário 200–280px;
  sparkline 24–40px.

**Breakpoints:** ≥1280 desktop (4 KPIs por linha) · 768–1279 tablet (2) · <768 mobile
(1 coluna, KPIs empilhados, sem scroll horizontal, gutter 16px). Teste em largura de celular.

**Tipografia (uma família sans de UI para tudo, inclusive números):**
- Escala sugerida: 12 (eixos/legenda) · 14 (corpo, labels de tile) · 16 · 20 (título de card)
  · 24–32 (valor do tile) · 48+ (hero).
- Labels em sentence case, sem dois-pontos no fim, sem CAPS LOCK.
- `font-variant-numeric: tabular-nums` **só** em colunas alinhadas (tabelas, ticks);
  números grandes isolados usam algarismos proporcionais.
- Formato compacto: 1.284 / 12,9 mil / R$ 4,2 mi (respeite pt-BR: vírgula decimal).

## Specs de marca (fixas)

| Elemento | Spec |
|---|---|
| Barra / coluna | **≤24px de espessura**, ponta de dados arredondada 4px, base reta |
| Linha | **2px**, junção/ponta arredondada |
| Marcador | **≥8px** (r ≥ 4), anel de 2px na cor da superfície |
| Área | cor da série a **~10% de opacidade** |
| Grid / eixos | hairline **1px sólida** (nunca tracejada), um tom acima da superfície |
| Separação | **gap de 2px** na cor da superfície entre barras/segmentos — nunca borda |

**Rótulos:** seletivos (fim da linha, extremo, a série da história) — nunca número em todo
ponto. Texto usa tokens de texto (primário/secundário/muted), **nunca a cor da série**.
Rótulo que não cabe na barra vai para fora ou para o tooltip; nunca `overflow: hidden`.

**Stat tile:** `label` · `valor` (sans semibold) · `delta` opcional (com sinal, vs. período
nomeado; cor = direção × se subir é bom) · `sparkline` opcional (12 pontos, cinza, período
atual em destaque).

## Cor

- **Sequencial** = um matiz, claro → escuro. **Divergente** = dois matizes opostos
  (quente/frio) + cinza neutro no meio. **Nunca arco-íris.**
- **Cor segue a entidade, não o ranking**: filtrar não pode repintar as séries restantes.
- **Status reservado** (bom / atenção / sério / crítico) — nunca usado como "série 4", e
  sempre com ícone + rótulo.
- **Ênfase** é a forma mais subutilizada: destaque uma série, o resto em cinza.
- Paleta de referência validada (claro / escuro), ordem fixa:
  1 azul `#2a78d6`/`#3987e5` · 2 laranja `#eb6834`/`#d95926` · 3 aqua `#1baf7a`/`#199e70`
  · 4 amarelo `#eda100`/`#c98500` · 5 magenta `#e87ba4`/`#d55181` · 6 verde `#008300`
  · 7 violeta `#6250d6`/`#9085e9` · 8 vermelho `#e34948`/`#e66767`.
  Superfícies: `#fcfcfb` (claro) / `#1a1a19` (escuro). Detalhes, rampas e status em
  `references/dataviz/palette.md`.
- **Para usar a cor da marca da empresa:** substitua os valores em `palette.md`, teste
  ordens candidatas com o validador e fique só com as que passam. Alvo CVD ΔE ≥ 8;
  visão normal ΔE ≥ 15 é piso duro.
- Defina cores como tokens CSS em `:root` e redefina para dark mode; o fundo do `body`
  é explícito.

## UX: interação e filtros

- **Tooltips complementam, nunca escondem**: todo valor também acessível por rótulo ou tabela.
  Mesmo conteúdo no foco do teclado.
- Linha/área: crosshair vertical que encaixa no ponto mais próximo; um tooltip lista todas
  as séries naquele X. Barras/células: a própria marca é o alvo e "acende" no hover.
- No tooltip, **o valor é o destaque** e o nome da série é secundário.
- **Alvo de clique maior que a marca**: mínimo ~24px; scatter denso usa nearest-point/Voronoi.
- **Filtros: uma linha, acima dos gráficos**, nunca dentro do card. **Data primeiro**, com
  presets (hoje, 7/30/90 dias, mês atual) antes do intervalo customizado.
- Filtros afetam tudo abaixo — os números sempre batem entre si.
- Ao recarregar, mantenha o render anterior com opacidade reduzida — sem skeleton, sem pulo.
- Estados vazios e erros dizem o que aconteceu e o que fazer, em linguagem do usuário.
- Nomes de série vindos de dados entram no DOM via `textContent`, nunca `innerHTML`.

## Acessibilidade (piso de qualidade)

- Legenda sempre para ≥2 séries (≤4 também com rótulo direto); série única não tem legenda.
- Todo gráfico tem **visão em tabela** equivalente.
- Contraste de texto WCAG AA (4,5:1 corpo, 3:1 marcas gráficas); aviso de contraste do
  validador obriga rótulos visíveis ou tabela.
- Foco de teclado visível; `prefers-reduced-motion` respeitado; textura (45°/135°) só como
  opção de acessibilidade/impressão, nunca decoração.

## Direção visual (de `frontend-design`)

- Ancore o visual no assunto e no público (painel para diretoria ≠ painel operacional).
- Gaste a ousadia em **um** lugar; o resto quieto e disciplinado. Os dados são os únicos
  autorizados a "gritar".
- Evite os vícios de UI genérica: todos os cards idênticos com a mesma sombra e raio,
  gradientes decorativos, eyebrow em CAPS acima de todo título, `→` em todo botão,
  monoespaçada em rótulos pequenos, numeração 01/02/03 sem sequência real.
- Copy: nomeie as coisas pelo que o usuário entende ("Vendas por região", não
  "fact_sales_agg"); botões dizem exatamente o que fazem.
- Texto completo: `references/frontend-design.md`.

## Antipadrões mais comuns (checklist rápido)

- [ ] Gráfico com **dois eixos Y** → dois gráficos, small multiples ou índice base 100.
- [ ] Pizza/donut para comparar valores próximos → barras ranqueadas.
- [ ] 8 cores quando a história é um número → ênfase ou stat tile.
- [ ] Barras grossas saturadas, grid pesado, sem respiro.
- [ ] Grid tracejado.
- [ ] Número em todo ponto.
- [ ] Borda em volta das marcas em vez de gap.
- [ ] Rótulo cortado dentro da barra.
- [ ] Container com altura fixa que corta o eixo X.
- [ ] Filtro por gráfico ou dentro do card.
- [ ] Tooltip como única forma de ler um valor.
- [ ] Recolorir séries ao filtrar.
Lista completa e explicada: `references/dataviz/anti-patterns.md`.

## Arquivos de referência

| Arquivo | Responde |
|---|---|
| `references/dataviz/choosing-a-form.md` | Que tipo de gráfico? É mesmo um gráfico? |
| `references/dataviz/color-formula.md` | As 4 funções de cor e as 6 checagens |
| `references/dataviz/marks-and-anatomy.md` | Specs de marca, rótulos, figuras, hero |
| `references/dataviz/interaction.md` | Tooltips, hover, filtros, períodos |
| `references/dataviz/components.md` | As peças de um gráfico |
| `references/dataviz/anti-patterns.md` | O que dá errado — conferir sempre |
| `references/dataviz/palette.md` | Paleta de referência completa (troque pela da marca) |
| `references/frontend-design.md` | Direção estética, tipografia, copy |
| `scripts/validate_palette.js` / `.py` | Validador de paleta — rode, não estime |
