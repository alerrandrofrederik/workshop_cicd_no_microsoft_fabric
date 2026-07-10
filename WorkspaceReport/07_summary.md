# 📝 Resumo Executivo — Workshop_DMF-DEV

> Uma visão concisa e orientada ao negócio da solução de dados implementada neste workspace.

---

## 🎯 O que é esta solução?

O workspace **Workshop_DMF-DEV** implementa um **pipeline de dados de ponta a ponta no Microsoft Fabric** usando a base de dados AdventureWorks como fonte. A solução demonstra boas práticas de **engenharia de dados moderna** com arquitetura Medallion, historização de dados SCD Tipo 2, e entrega final em um modelo semântico Power BI via DirectLake.

Trata-se de um **ambiente de DEV** para workshop de CI/CD no Microsoft Fabric — uma solução de referência e aprendizado.

---

## 📦 O que a solução processa?

Dados de **vendas e cadastros** do banco AdventureWorks (Microsoft), incluindo:

| Domínio | Dados |
|---|---|
| **Clientes** | Cadastro completo com nome, email, telefone, empresa, endereço |
| **Endereços** | Cidade, estado, país |
| **Produtos** | Catálogo com categorias, modelos, especificações técnicas |
| **Pedidos** | Cabeçalho de pedido (data, cliente, endereço) + linhas (produto, qtd, preço) |

---

## 🧭 Como os dados fluem?

```
Azure SQL (AdventureWorks)
        ↓ cópia automática via pipeline
Bronze Lakehouse (dados raw + data de carga)
        ↓ limpeza e enriquecimento
Silver Lakehouse (dados limpos + histórico SCD2 completo)
        ↓ modelagem dimensional
Gold Lakehouse (star schema: 4 dimensões + 1 fato)
        ↓ DirectLake
Modelo Semântico Sales (Power BI)
        ↓
Sales Report (dashboard de vendas)
```

---

## 📊 O que é entregue para o negócio?

### Relatório: Sales Report
- Visualizações de vendas com filtros por cliente, produto, data, localização
- Dados **sempre atualizados** via DirectLake (sem importação)
- Histórico completo preservado via SCD2

### Métricas disponíveis no modelo
| Métrica | Descrição |
|---|---|
| **Revenue** | Receita total (OrderQty × UnitPrice) |
| **OrderQty** | Quantidade de itens vendidos |
| **UnitPrice** | Preço unitário |

### Dimensões de análise disponíveis
| Dimensão | Atributos para análise |
|---|---|
| **Tempo** | Data do pedido, Dia, Mês, Ano |
| **Cliente** | Nome, empresa, email, telefone, título |
| **Produto** | Código, categoria, modelo, cor, tamanho |
| **Localização** | Cidade, estado, país |

---

## 🏛️ Arquitetura em 30 segundos

| Camada | Função | Tecnologia |
|---|---|---|
| **Ingestão** | Copia 10 tabelas do Azure SQL | Data Pipeline (Copy Activity) |
| **Bronze** | Dados raw em Delta Lake | Fabric Lakehouse + PySpark |
| **Silver** | Dados limpos + SCD2 histórico | PySpark + Delta MERGE |
| **Gold** | Star schema analítico | PySpark + Delta MERGE |
| **Semântico** | Modelo Power BI | DirectLake (zero latência) |
| **Visual** | Dashboard | Power BI Report |

---

## ✨ Destaques Técnicos

1. **SCD Tipo 2 genérico**: Função `fn_SCD2()` que processa qualquer tabela, com suporte a INSERT, UPDATE, DELETE e NOACTION
2. **Surrogate keys por hash**: SHA-256 como ID nas dimensões — determínistico e portável
3. **Delta MERGE incremental**: Gold atualiza apenas o que mudou (não recalcula tudo)
4. **4 dimensões em paralelo**: `dimension_date`, `dimension_product`, `dimension_customer`, `dimension_address` são executadas em paralelo no pipeline
5. **Data quality gate**: `TechnicalValidation` valida o contrato de schema na ingestão
6. **Variable Library centralizada**: IDs e conexões desacoplados do código
7. **DirectLake**: modelo semântico sem importação de dados — acessa o gold lakehouse diretamente

---

## ⚠️ Pontos de Atenção

| Ponto | Detalhe |
|---|---|
| 🔒 **Dados sensíveis no bronze** | `PasswordHash` e `PasswordSalt` do cliente existem no bronze — controle de acesso é necessário |
| ⚠️ **Dedup incorreto em fact_sales** | `salesorderdetail` é deduplicado por `SalesOrderID` em vez de `SalesOrderDetailID`, podendo perder linhas de pedidos com múltiplos itens |
| 📅 **Dimensão de data incompleta** | `dimension_date` contém apenas datas com pedidos — sem dias vazios para análises de "dias sem vendas" |
| 🐍 **Import com bug em clean_data** | `from Pathlib import Path` (maiúscula) pode causar erro dependendo do ambiente Spark |
| 📌 **Sem medidas DAX customizadas** | O modelo semântico usa apenas agregações nativas — sem KPIs, ratios ou medidas de negócio derivadas |

---

## 📁 Arquivos desta Documentação

| Arquivo | Conteúdo |
|---|---|
| [00_overview.md](./00_overview.md) | Visão geral da solução, arquitetura e fluxo |
| [01_inventory.md](./01_inventory.md) | Inventário completo de todos os 22 itens |
| [02_data_lineage.md](./02_data_lineage.md) | Linhagem de dados com diagramas Mermaid |
| [03_notebooks.md](./03_notebooks.md) | Análise detalhada dos 10 notebooks |
| [04_pipelines.md](./04_pipelines.md) | Análise do pipeline AdventureWorks |
| [05_semantic_models.md](./05_semantic_models.md) | Modelo semântico Sales (DirectLake) |
| [06_data_items.md](./06_data_items.md) | Tabelas dos lakehouses Bronze, Silver e Gold |
| [07_summary.md](./07_summary.md) | Este arquivo — resumo executivo |
