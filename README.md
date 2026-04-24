# 🛒 Kazkubo — Plataforma de Inteligência de Vendas

Plataforma acadêmica de análise de dados e Machine Learning desenvolvida para auxiliar pequenos comércios na tomada de decisões estratégicas. O sistema foi aplicado em um mercadinho de bairro parceiro do projeto, utilizando dados reais de vendas para gerar análises, previsões e alertas automáticos.

---

## 📌 Sobre o projeto

O Kazkubo nasceu da necessidade de oferecer aos pequenos comerciantes uma ferramenta acessível de inteligência de vendas — algo que grandes redes já possuem, mas que raramente chega ao mercadinho da esquina.

A partir de um histórico real de vendas em formato CSV, o sistema:
- Armazena e organiza os dados em um banco MySQL
- Aplica Machine Learning para prever a demanda futura de cada produto
- Detecta automaticamente anomalias, quedas de vendas e produtos parados
- Apresenta tudo em um dashboard interativo e intuitivo

---

## 📊 Funcionalidades

### 🏠 Dashboard inicial
Visão consolidada do negócio com faturamento total, total de vendas, ticket médio e quantidade de produtos monitorados.

### 📈 Visão Geral
- Faturamento total, total de vendas e ticket médio com filtro por mês
- Gráfico de evolução do faturamento diário
- Faturamento por categoria de produto

### 🛍️ Análise de Produtos
- Top 10 produtos mais vendidos por quantidade
- Top 10 produtos com menor rotatividade
- Ranking completo de produtos com faturamento

### 🔮 Previsão de Demanda
- Previsão das próximas 8 semanas por produto
- Gráfico com histórico real + linha de previsão + intervalo de confiança de 95%
- Tabela detalhada com quantidade prevista, mínimo e máximo por semana

### 🚨 Alertas e Insights
- Produtos sem venda nos últimos 30 dias
- Produtos com queda de vendas superior a 50% (últimos 30 dias vs. 30 dias anteriores)
- Produtos com maior demanda prevista nas próximas 8 semanas

---

## 🤖 Como funciona o modelo de Machine Learning

O sistema utiliza o **Prophet**, modelo de previsão de séries temporais desenvolvido pelo Meta (Facebook), especialmente eficaz para dados com sazonalidade e tendências.

### Por que Prophet?
- Lida bem com séries temporais irregulares (dias sem vendas, feriados, picos)
- Detecta automaticamente sazonalidade semanal e anual
- Gera intervalos de confiança que indicam o grau de certeza da previsão
- Funciona bem mesmo com volumes moderados de dados históricos

### Pipeline de treinamento
1. Os dados da `tb_vendas` são agregados por SKU e por semana
2. Para cada SKU, uma série temporal é montada no formato `ds` (data) e `y` (quantidade vendida)
3. Um modelo Prophet é treinado individualmente para cada SKU com sazonalidade semanal e anual ativadas
4. O modelo gera previsões para as próximas 8 semanas a partir da última data de venda registrada
5. Os resultados (quantidade prevista, intervalo inferior e superior, confiança de 95%) são salvos na tabela `previsao_demanda`

### Lógica de alinhamento de datas
Para SKUs com última venda defasada em relação à data mais recente do sistema, o pipeline calcula automaticamente a diferença em semanas e estende o horizonte de previsão para garantir que as 8 semanas futuras sejam sempre a partir da data global mais recente.

---

## 🗄️ Banco de dados

O banco MySQL é composto por 5 tabelas:

| Tabela | Descrição |
|---|---|
| `tb_vendas` | Dados brutos de vendas importados do CSV |
| `produto` | Catálogo de produtos com SKU, nome, categoria e preço atual |
| `indicador_diario` | Faturamento, quantidade de vendas e ticket médio agregados por dia |
| `previsao_demanda` | Previsões geradas pelo modelo Prophet por SKU e semana |
| `alerta` | Registro de anomalias e insights detectados automaticamente |

### Regras de negócio implementadas
- **Produtos parados**: SKUs sem registro de venda nos últimos 30 dias são sinalizados como inativos
- **Queda de vendas**: produtos com volume de vendas nos últimos 30 dias menor que 50% do período anterior (30-60 dias atrás) geram alerta de queda
- **Alta demanda**: os 10 produtos com maior volume previsto nas próximas 8 semanas são destacados para apoiar o planejamento de estoque
- **Indicador diário**: populado via `INSERT INTO ... SELECT` a partir da `tb_vendas`, agrupando faturamento e quantidade por dia com conversão de data de `VARCHAR` para `DATE` via `STR_TO_DATE`

---

## 🛠️ Stack

| Tecnologia | Uso |
|---|---|
| Python 3.12 | Linguagem principal |
| Prophet (Meta) | Modelo de previsão de séries temporais |
| MySQL 8.0 | Banco de dados relacional |
| Streamlit | Dashboard interativo |
| Pandas | Manipulação e análise de dados |
| SQLAlchemy + PyMySQL | Conexão e queries ao banco |
| Plotly | Visualizações interativas |
| python-dotenv | Gerenciamento de variáveis de ambiente |

---

## ⚙️ Como rodar localmente

### Pré-requisitos
- Python 3.12+
- MySQL 8.0+
- Banco MySQL acessível remotamente

### Instalação

```bash
git clone https://github.com/juanplima/sistema_de_previsao_de_vendas_mercadoo.git
cd sistema_de_previsao_de_vendas_mercadoo
pip install -r requirements.txt
```
DB_USER=seu_usuario
DB_PASS=sua_senha
DB_HOST=seu_host
DB_NAME=seu_banco

### Execução

```bash
# 1. Roda o pipeline de ML (treina os modelos e salva previsões)
python ml_previsao.py

# 2. Inicia o dashboard
streamlit run app.py
```

---

## 📁 Estrutura do projeto

sistema_de_previsao_de_vendas_mercadoo/
├── app.py                  # Página inicial do dashboard
├── ml_previsao.py          # Pipeline de ML com Prophet
├── .env.example            # Exemplo de variáveis de ambiente
├── .gitignore
├── README.md
└── pages/
├── 1_visao_geral.py    # Visão geral e faturamento
├── 2_produtos.py       # Análise de produtos
├── 3_previsao.py       # Previsão de demanda
└── 4_alertas.py        # Alertas e insights

---

## 👥 Projeto acadêmico

Desenvolvido como projeto integrador — aplicação prática de banco de dados, análise de dados e Machine Learning em um contexto real de pequeno comércio.

**Stack:** Python · Prophet · MySQL · Streamlit


### Configuração

Cria um arquivo `.env` na raiz do projeto:
