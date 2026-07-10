# 🏗️ Visão Geral da Solução — Workshop_DMF-DEV

> **Workspace**: Workshop_DMF-DEV  
> **ID**: `fde1670c-0b60-4fab-9a34-544986eb8788`  
> **Capacidade**: Brazil South (`266e82d0-e057-4607-b3e6-0fb37c579c85`)  
> **Descrição**: Workspace do Workshop CICD no Microsoft Fabric — ambiente de DEV  
> **Data do relatório**: 10/07/2026

---

## 📋 Sumário

1. [Propósito da Solução](#propósito-da-solução)
2. [Arquitetura](#arquitetura)
3. [Padrão Medallion](#padrão-medallion)
4. [Fluxo de Dados de Ponta a Ponta](#fluxo-de-dados-de-ponta-a-ponta)
5. [Tecnologias Utilizadas](#tecnologias-utilizadas)
6. [Estrutura de Pastas no Workspace](#estrutura-de-pastas-no-workspace)

---

## 🎯 Propósito da Solução

Esta solução implementa um **Data Lakehouse completo** no Microsoft Fabric, usando a base de dados **AdventureWorks** (esquema `SalesLT`) do Azure SQL Database como fonte de dados. O objetivo é criar uma pipeline de dados de ponta a ponta que processa dados de vendas e clientes para análise via Power BI.

A solução é utilizada como **workshop de CI/CD no Microsoft Fabric**, demonstrando boas práticas de engenharia de dados com:
- Arquitetura Medallion (Bronze → Silver → Gold)
- Historização de dados com SCD Tipo 2
- Star Schema para analytics
- Modelo semântico com DirectLake para relatórios em Power BI

---

## 🏛️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    Microsoft Fabric Workspace                    │
│                     Workshop_DMF-DEV                             │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │   🥉 BRONZE   │   │   🥈 SILVER   │   │      🥇 GOLD         │ │
│  │   Lakehouse   │   │   Lakehouse   │   │     Lakehouse        │ │
│  │               │   │               │   │                      │ │
│  │ 10 tabelas    │   │ ~20 tabelas   │   │ 4 dimensões          │ │
│  │ (raw delta)   │   │ (clean+hist)  │   │ + 1 fato             │ │
│  └──────┬────────┘   └──────┬────────┘   └──────────┬───────────┘ │
│         │                  │                        │             │
│         ▼                  ▼                        ▼             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Pipeline: AdventureWorks                       │  │
│  │  (orquestração completa do fluxo Bronze → Silver → Gold)   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │   Semantic Model: Sales (DirectLake)                      │    │
│  │   Report: Sales Report (Power BI)                        │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         ▲
         │
┌────────┴────────┐
│  Azure SQL DB    │
│  AdventureWorks  │
│  (schema SalesLT)│
└─────────────────┘
```

---

## 🥉🥈🥇 Padrão Medallion

### Bronze — Ingestão Bruta
- **Fonte**: Azure SQL Database (AdventureWorks, esquema `SalesLT`)
- **Formato**: Delta tables com coluna adicional `loading_date`
- **Esquema**: `adventureworks.*`
- **10 tabelas**: address, customer, customeraddress, product, productcategory, productdescription, productmodel, productmodelproductdescription, salesorderdetail, salesorderheader
- **Lógica**: Cópia direta via pipeline (Copy Activity → Parquet → Delta)

### Silver — Limpeza e Historização
- **Transformações**: Remoção de colunas técnicas, enriquecimento, normalização de dados
- **Padrão SCD Tipo 2**: Histórico completo com colunas `current`, `effectiveDate`, `endDate`
- **Tabelas `clean_*`**: Dados limpos sem historização
- **Tabelas `hist_*`**: Dados historizado com SCD2 (10 tabelas cada)
- **Enriquecimento notável**: Derivação de gênero a partir do título (`Mr.` → Male, `Ms.` → Female)

### Gold — Star Schema Analítico
- **Modelo dimensional**: 4 dimensões + 1 tabela de fatos
- **Dimensões com SCD2 no Gold**: `current_flag`, `current_date`, `end_date`
- **Hash surrogate keys**: SHA-256 gerado a partir das colunas de negócio
- **Upsert via Delta MERGE**: Atualização incremental com `whenMatchedUpdate`, `whenNotMatchedInsert`, `whenNotMatchedBySourceUpdate`

---

## 🔄 Fluxo de Dados de Ponta a Ponta

```
Azure SQL (SalesLT)
        │
        │ 1. LOOKUP: lista todas as tabelas
        │ 2. FOR EACH tabela:
        │    a. COPY → Parquet → bronze/Files/{schema}/{table}.parquet
        │    b. NOTEBOOK load_bronze → Delta table em bronze
        │    c. LOOKUP metadata → [dbo].[SchemaMetadata]
        │    d. IF metadata existir → NOTEBOOK TechnicalValidation
        │
        ▼
bronze.adventureworks.{tabela}  (10 tabelas raw)
        │
        │ 3. NOTEBOOK clean_data
        │    → limpa colunas técnicas, enriquece, normaliza
        │
        ▼
silver.adventureworks.clean_{tabela}  (10 tabelas limpas)
        │
        │ 4. NOTEBOOK historize_data_scd2
        │    → aplica SCD2 (full merge com ações: NOACTION/INSERT/UPDATE/DELETE)
        │
        ▼
silver.adventureworks.hist_{tabela}  (10 tabelas historizadas)
        │
        │ 5. NOTEBOOK create_gold_tables
        │    → cria tabelas gold com schema definido (se não existirem)
        │
        ▼
gold.adventureworks.dimension_* / fact_*  (criação de estrutura)
        │
        │ 6. NOTEBOOKS dimension_address, dimension_customer,
        │         dimension_date, dimension_product  (paralelo)
        │    → lê silver hist_*, filtra current=true, deduplicação,
        │       enriquece (joins), gera ID=SHA256, faz MERGE no gold
        │
        ▼
gold.adventureworks.dimension_{address|customer|date|product}
        │
        │ 7. NOTEBOOK fact_sales
        │    → joins orderdetail+orderheader, resolve surrogate keys
        │       via join com dimensões, MERGE em fact_sales
        │
        ▼
gold.adventureworks.fact_sales
        │
        │ 8. Semantic Model: Sales (DirectLake)
        │    → lê diretamente do gold lakehouse via OneLake
        │
        ▼
Report: Sales Report (Power BI)
```

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| **Microsoft Fabric Lakehouse** | Armazenamento em três camadas (Bronze, Silver, Gold) |
| **Apache Spark / PySpark** | Processamento de dados em todos os notebooks |
| **Delta Lake** | Formato de tabelas com suporte a MERGE, time travel |
| **Fabric Data Pipeline** | Orquestração completa do fluxo |
| **Azure SQL Database** | Fonte de dados (AdventureWorks SalesLT) |
| **Power BI DirectLake** | Acesso direto ao gold lakehouse no modelo semântico |
| **Variable Library** | Centralização de configurações (IDs, conexões) |
| **SHA-256 Hash Keys** | Surrogate keys baseadas em hash de negócio |

---

## 📁 Estrutura de Pastas no Workspace

| Pasta | Conteúdo |
|---|---|
| `Lakehouses` | bronze, silver, gold (3 lakehouses + 3 SQL Endpoints) |
| `Notebooks` | 9 notebooks de transformação + 1 de validação |
| `Pipelines` | Pipeline AdventureWorks (orquestração principal) |
| `Reports` | Sales Report |
| `Semantic Models` | Modelo Sales (DirectLake) |
| `Environments` | Ambiente NEE (configuração Spark) |
| `Variable Libraries` | EnvironmentVariables (configuração centralizada) |
| `CopyJobs` | CopyJob_1 |
