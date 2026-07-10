# 📓 Análise dos Notebooks — Workshop_DMF-DEV

> Análise detalhada de cada notebook: propósito, entradas, transformações e saídas.

---

## 📋 Sumário

1. [load_bronze](#1-load_bronze)
2. [TechnicalValidation](#2-technicalvalidation)
3. [clean_data](#3-clean_data)
4. [historize_data_scd2](#4-historize_data_scd2)
5. [create_gold_tables](#5-create_gold_tables)
6. [dimension_address](#6-dimension_address)
7. [dimension_customer](#7-dimension_customer)
8. [dimension_date](#8-dimension_date)
9. [dimension_product](#9-dimension_product)
10. [fact_sales](#10-fact_sales)

---

## 1. load_bronze

| Atributo | Detalhe |
|---|---|
| **ID** | `cec4fab0-577a-4ebb-b5d9-7ba2ed959251` |
| **Lakehouse padrão** | bronze |
| **Chamado por** | Pipeline AdventureWorks → ForEach → CreateBronzeTables |
| **Parâmetros** | `schemaName`, `tableName`, `filePath` (injetados pelo pipeline) |
| **Células** | 2 |

### Propósito
Lê um arquivo Parquet do bronze lakehouse e o persiste como tabela Delta com uma coluna de metadados (`loading_date`). É o notebook genérico de ingestão — chamado uma vez por tabela no ForEach do pipeline.

### Transformações
1. Cria o schema no lakehouse (`CREATE SCHEMA IF NOT EXISTS {schemaName}`)
2. Apaga a tabela existente (`DROP TABLE IF EXISTS {schemaName}.{tableName}`)
3. Lê o Parquet em `Files/{schemaName}/{filePath}/{tableName}.parquet`
4. Adiciona coluna `loading_date = current_date()` (tipo string)
5. Salva como tabela Delta com `mode("Overwrite")`

### Saída
`bronze.adventureworks.{tableName}` — tabela Delta com dados raw + `loading_date`

---

## 2. TechnicalValidation

| Atributo | Detalhe |
|---|---|
| **ID** | `63062c26-7060-4173-94ff-09fdfafd084c` |
| **Lakehouse padrão** | bronze |
| **Chamado por** | Pipeline → ForEach → IfCondition → TechnicalValidation |
| **Parâmetros** | `schemaName`, `tableName`, `metadata` (JSON string) |
| **Células** | 2 |

### Propósito
Valida se as colunas esperadas (definidas nos metadados do banco) existem na tabela bronze recém-carregada. Funciona como **data contract**: se alguma coluna estiver ausente, o notebook aborta a execução com uma mensagem de erro.

### Transformações
1. Faz parse do parâmetro `metadata` como JSON; se inválido, chama `mssparkutils.notebook.exit("Metadata is not a valid JSON object.")`
2. Lê a tabela `bronze.{schemaName}.{tableName}` 
3. Compara colunas do JSON de metadados com colunas do DataFrame
4. Se houver colunas faltando, chama `mssparkutils.notebook.exit(f"Technical validations have failed: {colunas_faltando}")`

### Lógica de Negócio Notável
> 🔍 Este notebook implementa um **data quality gate** na ingestão bronze. O metadado vem de `[dbo].[SchemaMetadata]` no Azure SQL DB — indicando um contrato centralizado de schema na fonte.

### Entrada/Saída
- **Entrada**: Tabela bronze + JSON de metadados com lista de `ColumnName` esperadas
- **Saída**: Sem escrita — apenas validação. Falha com saída controlada se colunas faltarem.

---

## 3. clean_data

| Atributo | Detalhe |
|---|---|
| **ID** | `b8df2fa9-4923-4b27-a018-ef5db55611c1` |
| **Lakehouse padrão** | silver |
| **Chamado por** | Pipeline → DataCleasing |
| **Parâmetros** | Nenhum (processa todas as tabelas) |
| **Células** | 10 (uma por tabela) |

### Propósito
Lê as 10 tabelas do bronze, remove colunas desnecessárias (principalmente técnicas como `rowguid`, `PasswordHash`, `PasswordSalt`, `ModifiedDate`), aplica transformações de negócio e salva as tabelas limpas no silver.

### Transformações por Tabela

| Tabela Bronze | Ação Principal | Saída Silver |
|---|---|---|
| `customer` | Remove `PasswordHash, PasswordSalt, rowguid, ModifiedDate`; deriva `Gender` a partir de `Title`; remove prefixo `adventure-works\` de `SalesPerson`; normaliza telefones | `adventureworks.clean_customer` |
| `address` | Remove `rowguid` | `adventureworks.clean_address` |
| `customeraddress` | Remove `rowguid` | `adventureworks.clean_customeraddress` |
| `product` | Remove `rowguid` | `adventureworks.clean_product` |
| `productcategory` | Remove `rowguid` | `adventureworks.clean_productcategory` |
| `productdescription` | Remove `rowguid` | `adventureworks.clean_productdescription` |
| `productmodel` | Remove `rowguid` | `adventureworks.clean_productmodel` |
| `productmodelproductdescription` | Remove `rowguid` | `adventureworks.clean_productmodelproductdescription` |
| `salesorderdetail` | Remove `rowguid` | `adventureworks.clean_salesorderdetail` |
| `salesorderheader` | Remove `rowguid` | `adventureworks.clean_salesorderheader` |

### Lógica de Negócio Notável
> 🔍 **Derivação de Gênero**: A coluna `Gender` é inferida a partir do campo `Title` do cliente:
> - `"Mr."` → `"Male"`
> - `"Ms."` → `"Female"`
> - Outros → `"Unknown"`

> 🔍 **Normalização de SalesPerson**: O prefixo `"adventure-works\"` é removido dos nomes dos vendedores.

> 🔍 **Normalização de Telefone**: O padrão `"1 (XX) "` é removido para padronizar formatos de telefone.

> ⚠️ **Bug potencial**: A importação usa `from Pathlib import Path` (letra maiúscula) — no Python padrão é `pathlib` (minúsculo). Pode causar erro se o módulo não existir com esse nome no ambiente.

---

## 4. historize_data_scd2

| Atributo | Detalhe |
|---|---|
| **ID** | `feb23a6e-674a-4fcc-a8cf-52cc8a2bfb74` |
| **Lakehouse padrão** | silver |
| **Chamado por** | Pipeline → DataHistorization |
| **Parâmetros** | Nenhum (processa todas as tabelas via chamada direta) |
| **Células** | 3 |

### Propósito
Implementa **SCD Tipo 2 (Slowly Changing Dimensions)** genérico para as 10 tabelas do silver. Mantém histórico completo das mudanças, com colunas `current` (boolean), `effectiveDate` e `endDate`.

### Função fn_SCD2(schemaName, tableName, primaryKey)

**Algoritmo**:
1. Lê `silver.{schemaName}.clean_{tableName}` (dados atuais)
2. Remove a coluna `loading_date`
3. Se `primaryKey` vazio → gera `hash = SHA-256(todas colunas concatenadas)` como chave
4. Tenta ler `silver.{schemaName}.hist_{tableName}`; se não existir → **first load** (insere tudo como `current=True, effectiveDate=hoje, endDate=9999-12-31`)
5. Realiza **FULL OUTER JOIN** entre dados novos e histórico
6. Classifica cada linha com uma ação:
   - `NOACTION`: sem mudança ou registro já inativo
   - `INSERT`: registro novo (não existe no histórico)
   - `UPDATE`: registro existente com dados diferentes → expira o atual, insere novo
   - `DELETE`: registro não mais presente na fonte → marca `current=False, endDate=hoje`
7. Gera DataFrame final via `UNION ALL` dos 5 subconjuntos
8. Salva como `overwrite` em `silver.{schemaName}.hist_{tableName}`

### Tabelas Processadas

```python
fn_SCD2("adventureworks", "address",                        "AddressID")
fn_SCD2("adventureworks", "customer",                       "CustomerID")
fn_SCD2("adventureworks", "customeraddress",                "")           # hash key
fn_SCD2("adventureworks", "product",                        "ProductID")
fn_SCD2("adventureworks", "productcategory",                "ProductCategoryID")
fn_SCD2("adventureworks", "productdescription",             "ProductDescriptionID")
fn_SCD2("adventureworks", "productmodel",                   "ProductModelID")
fn_SCD2("adventureworks", "productmodelproductdescription", "")           # hash key
fn_SCD2("adventureworks", "salesorderdetail",               "")           # hash key
fn_SCD2("adventureworks", "salesorderheader",               "SalesOrderID")
```

### Schema das Tabelas hist_*
Adiciona 3 colunas de controle temporal:

| Coluna | Tipo | Significado |
|---|---|---|
| `current` | Boolean | `True` = versão ativa |
| `effectiveDate` | Date | Data de início de validade |
| `endDate` | Date | Data de fim (`9999-12-31` = ativo) |

---

## 5. create_gold_tables

| Atributo | Detalhe |
|---|---|
| **ID** | `515bf9b2-2c09-4919-a6e5-96ca448e8256` |
| **Lakehouse padrão** | gold |
| **Chamado por** | Pipeline → CreateGoldTables |
| **Células** | 1 |

### Propósito
Cria as tabelas gold com schemas explicitamente definidos, usando DataFrames vazios. Garante idempotência: usa `mode("append")` para não sobrescrever dados existentes — apenas cria a estrutura se não existir.

### Tabelas Criadas

| Tabela | Colunas Chave |
|---|---|
| `adventureworks.dimension_address` | `ID` (hash), `AddressID`, `AddressLine1/2`, `City`, `StateProvince`, `CountryRegion`, `current_flag`, `current_date`, `end_date` |
| `adventureworks.dimension_customer` | `ID` (hash), `CustomerID`, `Title`, `FirstName`, `MiddleName`, `LastName`, `CompanyName`, `EmailAddress`, `Phone`, `current_flag`, `current_date`, `end_date` |
| `adventureworks.dimension_date` | `ID` (hash), `OrderDate`, `Day`, `Month`, `Year` |
| `adventureworks.dimension_product` | `ID` (hash), `ProductID`, `ProductNumber`, `Color`, `Size`, `Weight`, `CategoryName`, `ProductModelName`, `current_flag`, `current_date`, `end_date` |
| `adventureworks.fact_sales` | `SalesKey`, `AddressKey`, `CustomerKey`, `ProductKey`, `DateKey`, `Revenue`, `OrderQty`, `UnitPrice`, `current_flag`, `current_date`, `end_date` |

---

## 6. dimension_address

| Atributo | Detalhe |
|---|---|
| **ID** | `9d596ce6-f679-48fc-8800-b2725a231161` |
| **Lakehouse padrão** | gold |
| **Chamado por** | Pipeline → AddressDimension |
| **Células** | 3 |

### Propósito
Constrói a dimensão de endereços no gold com surrogate key SHA-256 e aplica MERGE incremental via Delta Lake.

### Transformações
1. Configura Spark para V-Order writing e otimização de escrita
2. Lê `silver.adventureworks.hist_address` filtrando `current=True`
3. Deduplicação por `AddressID`
4. Seleciona: `AddressID, AddressLine1, AddressLine2, City, StateProvince, CountryRegion`
5. Gera `ID = SHA-256(todas as colunas concatenadas com "||")`
6. Delta MERGE em `gold.adventureworks.dimension_address` por `gold.ID = updates.ID`:
   - **Match**: atualiza `current_flag=1, current_date=hoje, end_date=9999-12-31`
   - **Not Matched Insert**: insere novo registro com todos os campos
   - **Not Matched By Source**: marca `current_flag=0, end_date=hoje`

---

## 7. dimension_customer

| Atributo | Detalhe |
|---|---|
| **ID** | `da7e240d-cf99-480b-91cd-8a7828041abe` |
| **Lakehouse padrão** | gold |
| **Chamado por** | Pipeline → CustomerDimension |
| **Células** | 2 |

### Propósito
Constrói a dimensão de clientes no gold com surrogate key SHA-256 e MERGE incremental.

### Transformações
1. Lê `silver.adventureworks.hist_customer` filtrando `current=True`
2. Deduplicação por `CustomerID`
3. Seleciona: `CustomerID, Title, FirstName, MiddleName, LastName, CompanyName, EmailAddress, Phone`
4. Gera `ID = SHA-256(concatenação das colunas)`
5. Delta MERGE por `gold.ID = updates.ID` (mesma lógica da dimension_address)

---

## 8. dimension_date

| Atributo | Detalhe |
|---|---|
| **ID** | `bf5bb233-d2b5-4012-9df7-483b3ff70694` |
| **Lakehouse padrão** | gold |
| **Chamado por** | Pipeline → DateDimension |
| **Células** | 2 |

### Propósito
Constrói a dimensão de datas a partir das datas de pedido (não usa tabela calendário pré-existente).

### Transformações
1. Lê `silver.adventureworks.hist_salesorderheader` filtrando `current=True`
2. Deduplicação por `OrderDate`
3. Deriva colunas temporais: `Day = dayofmonth()`, `Month = month()`, `Year = year()`
4. Ordena por `OrderDate`
5. Gera `ID = SHA-256(OrderDate, Day, Month, Year)`
6. Delta MERGE por `gold.ID = updates.ID` (apenas `whenNotMatchedInsert` — sem updates)

### Lógica Notável
> 📅 A dimensão de datas é derivada das próprias datas de pedidos, não de um gerador de calendário. Isso significa que apenas datas que tiveram pedidos existem na tabela — não há cobertura de dias sem vendas.

---

## 9. dimension_product

| Atributo | Detalhe |
|---|---|
| **ID** | `fd435ed3-26bc-4a68-a9b4-6ce7a889f18a` |
| **Lakehouse padrão** | gold |
| **Chamado por** | Pipeline → ProductDimension |
| **Células** | 2 |

### Propósito
Constrói a dimensão de produtos com enriquecimento via joins com categorias e modelos.

### Transformações
1. Lê `silver.adventureworks.hist_product` (`current=True`), dedup por `ProductID`
2. Lê `silver.adventureworks.hist_productcategory` (`current=True`), dedup por `ProductCategoryID`, renomeia `Name` → `CategoryName`
3. Lê `silver.adventureworks.hist_productmodel` (`current=True`), dedup por `ProductModelID`, renomeia `Name` → `ProductModelName`
4. Join LEFT: `product + category` por `ProductCategoryID`
5. Join LEFT: `resultado + model` por `ProductModelID`
6. Seleciona: `ProductID, Name, ProductNumber, Color, Size, Weight, CategoryName, ProductModelName`
7. Gera `ID = SHA-256(colunas)`
8. Delta MERGE por `gold.ID = updates.ID` (mesmo padrão das outras dimensões)

---

## 10. fact_sales

| Atributo | Detalhe |
|---|---|
| **ID** | `f6e97967-a7b5-497a-9cbf-717c5d4648d4` |
| **Lakehouse padrão** | gold |
| **Chamado por** | Pipeline → SalesFact |
| **Células** | 3 |

### Propósito
Constrói a tabela fato de vendas, resolvendo surrogate keys via joins com as dimensões gold.

### Transformações
1. **Célula 1 — Prepara dados de vendas**:
   - Lê `silver.hist_salesorderdetail` (`current=True`), dedup por `SalesOrderID`
   - Seleciona `SalesOrderID, SalesOrderDetailID, ProductID, OrderQty, UnitPrice`
   - Calcula `Revenue = OrderQty * UnitPrice`
   - Lê `silver.hist_salesorderheader` (`current=True`), dedup por `SalesOrderID`
   - Join entre detail e header para trazer `CustomerID, BillToAddressID, OrderDate`
   - Cria `SalesKey = concat(SalesOrderID, SalesOrderDetailID)`

2. **Célula 2 — Resolve surrogate keys**:
   - Carrega todas as 4 dimensões do gold (`current_flag=True`)
   - Joins LEFT:
     - `sales.BillToAddressID = dimension_address.AddressID` → `AddressKey`
     - `sales.CustomerID = dimension_customer.CustomerID` → `CustomerKey`
     - `sales.ProductID = dimension_product.ProductID` → `ProductKey`
     - `sales.OrderDate = dimension_date.OrderDate` → `DateKey`
   - Seleciona apenas as foreign keys + métricas: `AddressKey, CustomerKey, ProductKey, DateKey, SalesKey, Revenue, OrderQty, UnitPrice`

3. **Célula 3 — MERGE no gold**:
   - Delta MERGE por `SalesKey + AddressKey + CustomerKey + ProductKey + DateKey` combinados
   - **Match**: atualiza `current_flag=1, current_date=hoje, end_date=9999-12-31`
   - **Not Matched Insert**: insere novo registro
   - **Not Matched By Source**: marca `current_flag=0, end_date=hoje`

### Lógica Notável
> ⚠️ A deduplicação de `salesorderdetail` por `SalesOrderID` pode perder linhas, pois um pedido pode ter múltiplos itens. O correto seria deduplicar por `SalesOrderDetailID` ou não deduplicar.
