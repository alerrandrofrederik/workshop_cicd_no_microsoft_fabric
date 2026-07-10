# 📦 Inventário Completo — Workshop_DMF-DEV

> **Workspace ID**: `fde1670c-0b60-4fab-9a34-544986eb8788`  
> **Total de itens**: 22

---

## 📋 Sumário

1. [Lakehouses](#lakehouses)
2. [SQL Endpoints](#sql-endpoints)
3. [Notebooks](#notebooks)
4. [Data Pipeline](#data-pipeline)
5. [Semantic Model](#semantic-model)
6. [Report](#report)
7. [Variable Library](#variable-library)
8. [Environment](#environment)
9. [CopyJob](#copyjob)

---

## 🏠 Lakehouses

| Nome | ID | Papel na Solução |
|---|---|---|
| **bronze** | `84d4c516-90ee-4963-a892-2f1da3090e13` | Camada de ingestão bruta — armazena dados copiados do Azure SQL sem transformação |
| **silver** | `6fa320a8-96a3-438b-aba6-98093b3669e9` | Camada de transformação — dados limpos (clean_*) e historização SCD2 (hist_*) |
| **gold** | `bdf8983d-cdb5-4ff1-ae1f-655460db8890` | Camada analítica — star schema com dimensões e fato para consumo pelo Power BI |

> ⚠️ **Nota**: Todos os lakehouses têm **schemas habilitados** (`enableSchemas: true`), utilizando o esquema `adventureworks` para organizar as tabelas.

---

## 🔌 SQL Endpoints (Análise SQL)

| Nome | ID | Lakehouse Associado |
|---|---|---|
| **bronze** (SQL Endpoint) | `5335a13e-2f48-4b16-a62c-87717d9e7f15` | Lakehouse bronze |
| **silver** (SQL Endpoint) | `ecc15741-acc7-4c3c-a3c5-411dfe285e54` | Lakehouse silver |
| **gold** (SQL Endpoint) | `1cf7dbc2-37ab-4896-8e77-936ac93cc091` | Lakehouse gold |

---

## 📓 Notebooks (10)

| Nome | ID | Lakehouse Padrão | Propósito |
|---|---|---|---|
| **load_bronze** | `cec4fab0-577a-4ebb-b5d9-7ba2ed959251` | bronze | Lê parquet, adiciona `loading_date`, salva como delta table no bronze |
| **TechnicalValidation** | `63062c26-7060-4173-94ff-09fdfafd084c` | bronze | Valida existência de colunas esperadas no bronze com base em metadados JSON |
| **clean_data** | `b8df2fa9-4923-4b27-a018-ef5db55611c1` | silver | Limpa 10 tabelas do bronze (remove colunas técnicas, normaliza, enriquece) |
| **historize_data_scd2** | `feb23a6e-674a-4fcc-a8cf-52cc8a2bfb74` | silver | Aplica SCD Tipo 2 em 10 tabelas → silver.hist_* |
| **create_gold_tables** | `515bf9b2-2c09-4919-a6e5-96ca448e8256` | gold | Cria estrutura vazia das tabelas gold com schemas definidos |
| **dimension_address** | `9d596ce6-f679-48fc-8800-b2725a231161` | gold | Constrói dimension_address com hash ID e SCD no gold |
| **dimension_customer** | `da7e240d-cf99-480b-91cd-8a7828041abe` | gold | Constrói dimension_customer com hash ID e SCD no gold |
| **dimension_date** | `bf5bb233-d2b5-4012-9df7-483b3ff70694` | gold | Constrói dimension_date a partir das datas de pedidos |
| **dimension_product** | `fd435ed3-26bc-4a68-a9b4-6ce7a889f18a` | gold | Constrói dimension_product com joins de categoria e modelo |
| **fact_sales** | `f6e97967-a7b5-497a-9cbf-717c5d4648d4` | gold | Constrói fact_sales com surrogate keys via join com dimensões |

---

## 🔗 Data Pipeline (1)

| Nome | ID | Propósito |
|---|---|---|
| **AdventureWorks** | `a274d88f-4be9-4dc0-83c8-a08d265d1235` | Orquestração completa: ingestão Bronze → transformação Silver → construção Gold |

---

## 📊 Semantic Model (1)

| Nome | ID | Modo | Fonte |
|---|---|---|---|
| **Sales** | `66830f47-dfad-480f-a054-34d0d9bfd761` | DirectLake | gold lakehouse (adventureworks schema) |

---

## 📈 Report (1)

| Nome | ID | Modelo Semântico |
|---|---|---|
| **Sales Report** | `b8abc982-c8b2-464e-a3d2-c234cbec3623` | Sales |

---

## ⚙️ Variable Library (1)

| Nome | ID | Propósito |
|---|---|---|
| **EnvironmentVariables** | `5ec3e173-765a-4981-bb11-3a01eb3d07c3` | Centraliza IDs dos lakehouses, notebooks e connection ID do Azure SQL |

**Variáveis definidas**:

| Variável | Tipo | Valor |
|---|---|---|
| `workspace_name` | String | `Workshop_DMF-DEV` |
| `workspace_id` | String | `fde1670c-0b60-4fab-9a34-544986eb8788` |
| `lakehouse_bronze` | ItemReference | ID: `84d4c516-90ee-4963-a892-2f1da3090e13` |
| `lakehouse_silver` | ItemReference | ID: `6fa320a8-96a3-438b-aba6-98093b3669e9` |
| `lakehouse_gold` | ItemReference | ID: `bdf8983d-cdb5-4ff1-ae1f-655460db8890` |
| `connection` / `connection_id` | String | `03112c5e-549e-4e0e-9e80-1443247bb8a2` |
| `nb_load_bronze` | ItemReference | Notebook load_bronze |
| `nb_techinical_validation` | ItemReference | Notebook TechnicalValidation |
| `nb_clean_data` | ItemReference | Notebook clean_data |
| `nb_historize_data_scd2` | ItemReference | Notebook historize_data_scd2 |
| `nb_create_gold_tables` | ItemReference | Notebook create_gold_tables |
| `nb_dimension_date` / `nb_dimension_date2` | ItemReference | Notebook dimension_date |
| `nb_dimension_product` | ItemReference | Notebook dimension_product |
| `nb_dimension_customer` | ItemReference | Notebook dimension_customer |
| `nb_dimension_address` | ItemReference | Notebook dimension_address |
| `nb_fact_sales` | ItemReference | Notebook fact_sales |
| `lakehouse_bronze_id` | String | `84d4c516-90ee-4963-a892-2f1da3090e13` |

---

## 🌍 Environment (1)

| Nome | ID | Propósito |
|---|---|---|
| **NEE** | `b02f60c3-3544-4479-aebb-ede205a92332` | Ambiente de execução Spark customizado para os notebooks |

---

## 📋 CopyJob (1)

| Nome | ID | Propósito |
|---|---|---|
| **CopyJob_1** | `b58d8bea-a32d-4616-a8b8-c9e9470437b5` | Job de cópia auxiliar (possivelmente testes ou cópia avulsa) |
