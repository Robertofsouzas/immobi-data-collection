# 📊 Análise de Anúncios de Imóveis — Projeto Completo

## 📋 Sumário Executivo

Este projeto realiza a **coleta automatizada de dados imobiliários** do portal **Chaves na Mão** (foco em imóveis de alto padrão em Salvador e Lauro de Freitas - BA), armazena os dados em um **banco SQL Server**, e disponibiliza análises interativas através de um **relatório Power BI**.

**Fluxo Principal:**
```
Web Scraping (Python) → SQL Server → Power BI (Análise)
```

---

## 🏗️ Arquitetura do Projeto

```
Projeto_WebScraping/
├── Projeto_webscraping_imoveis/          # 🐍 Backend Python
│   ├── main.py                           # Orquestrador principal
│   ├── scraper.py                        # Lógica de coleta de dados
│   ├── database.py                       # Integração SQL Server
│   └── requirements.txt                  # Dependências Python
│
├── Projeto_AnaliseAnuncios.pbip/         # 📈 Projeto Power BI
│   ├── Projeto_AnaliseAnuncios.Report/   # Relatórios
│   │   └── definition/
│   │       ├── pages/                    # 5 páginas de análise
│   │       └── visuals/                  # Gráficos e tabelas
│   │
│   └── Projeto_AnaliseAnuncios.SemanticModel/  # Modelo Semântico
│       └── definition/
│           ├── tables/                   # Tabelas TMDL
│           ├── model.tmdl                # Definição do modelo
│           ├── relationships.tmdl        # Relacionamentos
│           └── cultures/                 # Idiomas (pt-BR)
│
└── README.md                             # Esta documentação
```

---

## 🐍 Componente Python: Web Scraping

### Visão Geral

O módulo Python automatiza a coleta de anúncios imobiliários com foco em propriedades de **alto padrão** em duas localidades principais (Salvador e Lauro de Freitas) e dois tipos de negócio (Venda e Aluguel).

### 📁 Arquivos Principais

#### **main.py** — Orquestrador Principal
- **Responsabilidade:** Gerenciar o fluxo geral de coleta de dados
- **Configurações:**
  - **VENDA:** 19 bairros de Salvador + 3 de Lauro de Freitas (preço: R$ 400k a R$ 20M)
  - **ALUGUEL:** 15 bairros de Salvador + 3 de Lauro de Freitas (preço: R$ 2k a R$ 35k)
  - **PAGINAS:** 4 páginas por bairro
- **Fluxo:**
  1. Itera sobre cidades e bairros configurados
  2. Para cada página, obtém a URL da lista de imóveis
  3. Extrai URLs individuais dos anúncios
  4. Coleta dados detalhados de cada imóvel
  5. Salva no banco de dados
  6. Exibe resumo final com estatísticas

**Exemplo de Saída:**
```
==================================================
VENDA | Cidade: BA-SALVADOR | Bairro: CORREDOR-DA-VITORIA
==================================================
  Página 1...
    ✓ 12345 | Corredor da Vitória | R$ 1500000
    ✓ 12346 | Corredor da Vitória | R$ 2000000
...
==================================================
RESUMO FINAL
  Venda   — Salvos: 75 | Erros: 3 | Pulados: 5
  Aluguel — Salvos: 120 | Erros: 2 | Pulados: 8
  Total   — Salvos: 195
==================================================
```

---

#### **scraper.py** — Engine de Coleta

**Funções Principais:**

| Função | Objetivo | Tecnologia |
|--------|----------|-----------|
| `fetch_html(url)` | Busca o HTML da página usando browser real | Playwright |
| `parse_listing(html)` | Extrai URLs de imóveis de uma página de listagem | BeautifulSoup4 |
| `parse_imovel(html, url)` | Extrai dados estruturados de um anúncio individual | JSON-LD + BeautifulSoup4 |

**Detalhes Técnicos:**

- **fetch_html():** 
  - Usa Playwright (browser headless) para garantir carregamento completo de JavaScript
  - User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
  - Locale: pt-BR
  - Viewport: 1280x800px

- **parse_listing():**
  - Extrai todos os links que contenham `/imovel/` na URL
  - Remove duplicatas usando set
  - Retorna lista de URLs completas

- **parse_imovel():**
  - Extrai ID do imóvel do padrão `id-(\d+)` na URL
  - Busca dados em JSON estruturado (schema.org RealEstateListing)
  - Valida e converte tipos de dados:
    - **Preço:** Remove pontos e converte virgula em ponto
    - **Área:** Converte para inteiro
    - **Preço/m²:** Cálculo automático
  - Determina tipo de negócio pela URL (aluguel vs venda)
  - Mapeia tipos de imóvel (Apartment → Apartamento, etc.)
  - Extrai garagens, condomínio e IPTU
  - Captura foto de capa (JSON estruturado ou tag og:image)

**Dados Capturados:**
```python
{
    'id': '12345',
    'titulo': 'Apartamento Luxo Barra',
    'url': 'https://...',
    'url_foto': 'https://...',
    'tipo_negocio': 'Venda|Aluguel',
    'tipo_imovel': 'Apartamento|Casa|Comercial',
    'bairro': 'Barra',
    'cidade': 'Salvador|Lauro de Freitas',
    'estado': 'BA',
    'area_m2': 150,
    'quartos': 3,
    'banheiros': 2,
    'garagens': 2,
    'preco_original': 1500000,
    'preco_atual': 1500000,
    'preco_m2': 10000.0,
    'condominio': 1200.0,
    'iptu': 350.0,
    'data_coleta': '2026-06-16 14:30:00'
}
```

---

#### **database.py** — Integração SQL Server

**Responsabilidade:** Salvar e atualizar dados de imóveis no banco de dados

**Configuração:**
```python
CONN_STR = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-MGR8475\\SQLEXPRESS;DATABASE=imoveis;Trusted_Connection=yes;"
```

**Funções:**

**`salvar_imovel(imovel: dict)`** — Lógica Inteligente de Armazenamento:

1. **Verifica se o imóvel já existe** (`SELECT id FROM fato_imoveis WHERE id = ?`)

2. **Se JÁ EXISTE (UPDATE):**
   - Atualiza apenas campos que podem mudar diariamente
   - Campos atualizados: `preco_atual`, `preco_m2`, `area_m2`, `condominio`, `iptu`, `url_foto`, `data_ultima_coleta`
   - Preserva `data_primeira_coleta` e `preco_original`

3. **Se NÃO EXISTE (INSERT):**
   - Cria novo registro com histórico completo
   - Define `data_primeira_coleta` e `data_ultima_coleta` iguais
   - Preserva preço original para rastreamento de flutuações

**Tratamento de Erros:**
- Usa transações (commit/rollback) para garantir integridade
- Em caso de erro, desfaz operação e relança exceção
- Fecha conexão sempre para não sobrecarregar SQL Server

---

#### **requirements.txt** — Dependências

```
playwright          # Browser automation (headless)
beautifulsoup4      # Web scraping e parsing HTML
pyodbc              # Conexão SQL Server
```

**Instalação:**
```bash
pip install -r requirements.txt
playwright install  # Baixa drivers do navegador
```

---

### 🚀 Como Executar

```bash
# 1. Navegar ao diretório do projeto
cd Projeto_webscraping_imoveis

# 2. Ativar ambiente Python (opcional)
python -m venv venv
.\venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt
playwright install

# 4. Executar coleta
python main.py
```

---

## 📈 Componente Power BI: Análise e Relatórios

### Arquitetura

```
Semantic Model (Tabelas TMDL)
│
├── Tabelas Fato
│   └── fato_anuncios (Dados de imóveis)
│
├── Tabelas Dimensão
│   ├── dim_localidade (Bairros e Cidades)
│   ├── dim_tipoNegocio (Venda/Aluguel)
│   ├── dim_tipoImovel (Apt/Casa/Comercial)
│   └── dim_calendario (Datas)
│
├── Tabelas Medidas (Cálculos DAX)
│   ├── medidas (KPIs principais)
│   └── medidas_kpi's (KPIs secundários)
│
└── Relatórios (5 Páginas)
    ├── Página 1: Visão Geral
    ├── Página 2: Análise de Preços
    ├── Página 3: Análise Geográfica
    ├── Página 4: Comparativo Venda x Aluguel
    └── Página 5: Detalhes e Filtros
```

---

### 🗂️ Modelo Semântico (TMDL)

**Localização:** `Projeto_AnaliseAnuncios.SemanticModel/definition/`

#### Tabelas Principais

| Tabela | Tipo | Colunas | Origem |
|--------|------|---------|--------|
| `fato_anuncios` | Fato | 20 colunas | SQL Server (banco: imoveis, tabela: fato_imoveis) |
| `dim_localidade` | Dimensão | Bairro, Cidade, Estado | Dimensão de locais |
| `dim_tipoNegocio` | Dimensão | Tipo (Venda/Aluguel) | Dimensão de tipos |
| `dim_tipoImovel` | Dimensão | Tipo (Apto/Casa/etc) | Dimensão de tipos |
| `dim_calendario` | Dimensão | Data, Mês, Trimestre, Ano | Tabela de data |
| `medidas` | Cálculo | Medidas DAX | Tabela de cálculos |
| `medidas_kpi's` | Cálculo | KPIs | Tabela de cálculos |

#### Colunas da Tabela Fato (fato_anuncios)

```tmdl
table fato_anuncios

column id              → string   | ID único do anúncio
column titulo          → string   | Título do anúncio
column url             → string   | URL do anúncio
column tipo_negocio    → string   | "Venda" ou "Aluguel"
column tipo_imovel     → string   | "Apartamento", "Casa", "Comercial"
column bairro          → string   | Bairro do imóvel
column cidade          → string   | "Salvador" ou "Lauro de Freitas"
column estado          → string   | "BA"
column area_m2         → int64    | Área em metros quadrados
column quartos         → int64    | Número de quartos
column banheiros       → int64    | Número de banheiros
column garagens        → double   | Número de garagens
column preco_atual     → float    | Preço atual do anúncio
column preco_original  → float    | Preço quando foi coletado
column preco_m2        → float    | Preço por metro quadrado
column condominio      → float    | Taxa de condomínio mensal
column iptu            → float    | Imposto predial mensal
column url_foto        → string   | URL da foto de capa
column data_coleta     → datetime | Data/hora da coleta
column data_ultima_atualizacao → datetime | Última atualização
```

---

#### Relacionamentos

```
fato_anuncios
├─ relacionamento: tipo_negocio → dim_tipoNegocio (1:N)
├─ relacionamento: tipo_imovel → dim_tipoImovel (1:N)
├─ relacionamento: bairro → dim_localidade (1:N)
└─ relacionamento: data_coleta → dim_calendario (1:N)
```

---

### 📊 Páginas do Relatório

**Localização:** `Projeto_AnaliseAnuncios.Report/definition/pages/`

O relatório contém **5 páginas** com múltiplos visuais (14+ gráficos e tabelas):

#### **Página 1: Dashboard Executivo** (1df01ffabc6d2076db98/)
- Visão geral de anúncios
- KPIs principais (total anúncios, preço médio, etc.)
- Distribuição por tipo de negócio
- Tendências

#### **Página 2: Análise de Preços** (40609e987a24a27e2583/)
- Distribuição de preços
- Preço médio por bairro
- Preço por m²
- Análise de flutuação de preços

#### **Página 3: Análise Geográfica** (61d9d48628757eccb754/)
- Mapa de calor por bairro
- Distribuição geográfica
- Localidades com maior atividade

#### **Página 4: Comparativo Venda vs Aluguel** (ba4fc90faa0eb63c6ab0/)
- Comparação de preços
- Rendimento esperado
- Análise de rentabilidade

#### **Página 5: Detalhes e Filtros** (d7d2f865ba88ab5d8432/)
- Tabela detalhada com todos os dados
- Filtros interativos
- Busca e navegação

---

#### Visuais Principais (14+ componentes)

Cada página contém múltiplos visuais como:
- **Gráficos de Barras:** Distribuição por bairro, tipo
- **Gráficos de Linha:** Tendências de preço ao longo do tempo
- **Tabelas:** Dados detalhados
- **Cartões:** KPIs em destaque
- **Mapas:** Distribuição geográfica
- **Imagens:** Fotos dos imóveís
- **Slicers:** Filtros para interatividade

---

### 🔗 Fluxo de Dados (Power BI)

```
SQL Server (imoveis.dbo.fato_imoveis)
            ↓
      [Importar dados]
            ↓
Semantic Model (TMDL)
    ├─ Transformações
    ├─ Relacionamentos
    └─ Medidas DAX
            ↓
      [Publicar]
            ↓
Relatórios Power BI
    ├─ Página 1: Dashboard
    ├─ Página 2: Preços
    ├─ Página 3: Geográfica
    ├─ Página 4: Comparativo
    └─ Página 5: Detalhes
```

---

## 🔄 Fluxo Completo de Dados

```
┌─────────────────────────────────────────────────────────┐
│  1. COLETA (Python - Web Scraping)                      │
│  ─────────────────────────────────────────────────────  │
│  • Portal: https://www.chavesnamao.com.br               │
│  • Técnica: Playwright (browser headless) + BeautifulSoup│
│  • Frequência: Sob demanda (executar main.py)           │
│  • Escopo: Salvador + Lauro de Freitas (Alto Padrão)    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  2. ARMAZENAMENTO (SQL Server)                          │
│  ─────────────────────────────────────────────────────  │
│  • Banco: imoveis                                       │
│  • Tabela: fato_imoveis                                 │
│  • Lógica: INSERT (novo) ou UPDATE (existente)          │
│  • Servidor: DESKTOP-MGR8475\SQLEXPRESS                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  3. PROCESSAMENTO (Power BI - Modelo Semântico)         │
│  ─────────────────────────────────────────────────────  │
│  • Formato: TMDL (Tabular Model Definition Language)    │
│  • Relacionamentos: Dimensões + Fatos                   │
│  • Medidas: DAX (cálculos analíticos)                   │
│  • Culturas: pt-BR                                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  4. VISUALIZAÇÃO (Power BI - Relatórios)               │
│  ─────────────────────────────────────────────────────  │
│  • 5 páginas de análise                                 │
│  • 14+ visuais (gráficos, tabelas, cartões)            │
│  • Filtros interativos                                  │
│  • Tema: CY26SU05                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Exemplo de Uso Prático

### Cenário: Análise de Mercado Imobiliário

**Pergunta:** "Qual é o preço médio de apartamentos para venda na Barra?"

**Processo:**

1. **Coleta (Python):**
   ```
   Acessa: https://www.chavesnamao.com.br/imoveis-a-venda/ba-salvador/barra/
   Coleta: ~12-15 anúncios por página, 4 páginas = ~48-60 anúncios
   Armazena: ID, preço, área, tipo, etc.
   ```

2. **Armazenamento (SQL):**
   ```sql
   INSERT INTO fato_imoveis 
   WHERE tipo_negocio = 'Venda' 
   AND tipo_imovel = 'Apartamento'
   AND bairro = 'Barra'
   ```

3. **Análise (Power BI):**
   ```dax
   Preco_Medio_Apartamentos_Barra = 
       AVERAGEX(
           FILTER(fato_anuncios, 
               fato_anuncios[tipo_imovel] = "Apartamento" &&
               fato_anuncios[bairro] = "Barra" &&
               fato_anuncios[tipo_negocio] = "Venda"
           ),
           fato_anuncios[preco_atual]
       )
   ```

4. **Resultado (Dashboard):**
   - Cartão mostrando: **R$ 1.250.000** (preço médio)
   - Gráficos de distribuição, tendências
   - Comparativos com outros bairros

---

## 🛠️ Stack Tecnológico

| Camada | Tecnologia | Versão | Propósito |
|--------|-----------|--------|----------|
| **Web Scraping** | Python | 3.8+ | Coleta de dados |
| **Browser Automation** | Playwright | Latest | Simula navegador real |
| **Web Parsing** | BeautifulSoup4 | 4.x | Extração de HTML |
| **Banco de Dados** | SQL Server | 2019+ | Armazenamento persistente |
| **Driver SQL** | ODBC 17 | 17.x | Conexão Python ↔ SQL |
| **BI / Analytics** | Power BI | Desktop + Fabric | Análise e relatórios |
| **Modelo Semântico** | TMDL | v2 | Definição de dimensões/fatos |
| **Idioma Principal** | pt-BR | — | Português (Brasil) |

---

## 📋 Configurações Importantes

### Locais de Coleta

#### **Venda (Alto Padrão)**
- **Salvador:** Corredor da Vitória, Jaguaribe, Pátamares, Graça, Imbuí, Alphaville I/II, Cidade Jardim, Jardim Apipema, Ondina, Pituba, Barra, Itaigara, Horto Florestal
- **Lauro de Freitas:** Vilas do Atlântico, Buraquinho, Ipitanga
- **Faixa de Preço:** R$ 400.000 a R$ 20.000.000

#### **Aluguel (Alto Padrão)**
- **Salvador:** Pátamares, Jaguaribe, Pituba, Barra, Itaigara, Horto Florestal, Graça, Corredor da Vitória, Campo Grande, Vila Laura, Ondina, Rio Vermelho, Alphaville I/II
- **Lauro de Freitas:** Vilas do Atlântico, Buraquinho, Ipitanga
- **Faixa de Preço:** R$ 2.000 a R$ 35.000/mês

### Parâmetros de Coleta

| Parâmetro | Valor | Descrição |
|-----------|-------|----------|
| `PAGINAS` | 4 | Número de páginas coletadas por bairro |
| `WAIT_UNTIL` | domcontentloaded | Espera carregamento mínimo de JS |
| `TIMEOUT` | 60000ms | Timeout de página |
| `USER_AGENT` | Mozilla 5.0 | User-Agent para requisições |
| `VIEWPORT` | 1280x800 | Tamanho do navegador virtual |

---

## ⚠️ Tratamento de Erros e Validações

### Validações na Coleta

1. **ID do Imóvel:** Extrato do padrão `id-(\d+)` na URL
   - Se não encontrado → anúncio pulado

2. **Área (m²):** Converte e valida valor
   - Se < 5m² → ignorado (provável erro de extração)

3. **Preço:** Remove formatação e valida
   - Se nulo → anúncio pulado

4. **Preço/m²:** Calculado automaticamente
   - Se área = 0 → nulo

### Tratamento de Erros no Banco

```python
try:
    cursor.execute(...)
    conn.commit()
except pyodbc.Error as e:
    conn.rollback()  # Desfaz em caso de erro
    raise e  # Repassa para main.py
finally:
    conn.close()  # Sempre fecha conexão
```

### Estatísticas de Coleta

Cada execução retorna:
- **Salvos:** Registros inseridos/atualizados com sucesso
- **Erros:** Problemas durante coleta (timeout, parsing, BD)
- **Pulados:** Anúncios válidos mas com dados insuficientes

---

## 🔍 Monitoramento e Manutenção

### Checklist de Manutenção

- [ ] **Semanal:** Executar coleta para manter dados atualizados
- [ ] **Mensal:** Verificar integridade do banco de dados
- [ ] **Trimestral:** Revisar tendências de preço e localizar outliers
- [ ] **Anual:** Atualizar lista de bairros conforme necessidade

### Troubleshooting Comum

| Problema | Causa Provável | Solução |
|----------|----------------|--------|
| "Timeout de página" | Conexão lenta ou portal sobrecarregado | Aumentar timeout ou tentar novamente |
| "Conexão SQL Server negada" | Servidor inativo ou credenciais erradas | Verificar servidor e permissões |
| "Nenhum imóvel encontrado" | Bairro/cidade não existe | Validar nomes conforme portal |
| "Erro ODBC 17" | Driver não instalado | Instalar ODBC Driver 17 for SQL Server |

---

## 📚 Referências e Recursos

### Documentação
- [Playwright Documentation](https://playwright.dev/python/)
- [BeautifulSoup4 Guide](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Microsoft ODBC Documentation](https://docs.microsoft.com/en-us/sql/odbc/)
- [Power BI DAX Reference](https://dax.guide/)

### APIs / Portais
- [Chaves na Mão](https://www.chavesnamao.com.br/)
- [Schema.org RealEstateListing](https://schema.org/RealEstateListing)

---

## 📝 Notas Adicionais

### Por que Playwright e não Requests?

O portal Chaves na Mão carrega muitos dados com JavaScript. **Requests + BeautifulSoup** não conseguiriam capturar isso. **Playwright** executa um navegador real que interpreta JavaScript, garantindo captura completa.

### Por que TMDL e não PBIX?

**TMDL** (Tabular Model Definition Language):
- Formato texto (versionável em Git)
- Facilita controle de versão
- Permite diffs claros
- Melhor para CI/CD

**PBIX:**
- Formato binário (difícil versionamento)
- Não recomendado para source control

### Privacidade e Ética

- Este projeto scrapa apenas dados públicos do portal
- Respeita robots.txt e Terms of Service
- Não armazena dados de usuários finais
- Uso exclusivamente para análise de mercado

---

## 👤 Autor e Licença

**Projeto:** Análise de Anúncios de Imóveis - Alto Padrão BA  
**Versão:** 1.0.0  
**Data:** Junho 2026  
**Status:** ✅ Em Produção

---

## 📞 Suporte

Para dúvidas, bugs ou melhorias, consulte:
1. Esta documentação (README.md)
2. Comentários no código
3. Logs de execução do main.py

---

**Última Atualização:** 16 de Junho de 2026

<!-- rfstechs-cta -->
<br>

---

<div align="center">

### Quer algo assim na sua empresa?

Transformo planilhas e processos manuais em **dashboards, automações e agentes de IA** para pequenas e médias empresas.

<a href="https://rfstech.vercel.app/gh/immobi-data-collection">
  <img src="https://img.shields.io/badge/Fale%20comigo-RFStechs-4F46E5?style=for-the-badge" alt="Fale comigo — RFStechs" />
</a>

<sub>Roberto Souza · RFStechs · BI, dados e agentes de IA para PMEs</sub>

</div>
