# 🗄️ Itens de Dados — Lakehouses e SQL Endpoints

> Análise das camadas de dados: Bronze, Silver e Gold, com esquemas, tabelas e padrões de armazenamento.

---

## 📋 Sumário

1. [Configuração Geral dos Lakehouses](#configuração-geral-dos-lakehouses)
2. [Bronze Lakehouse](#bronze-lakehouse)
3. [Silver Lakehouse](#silver-lakehouse)
4. [Gold Lakehouse](#gold-lakehouse)
5. [SQL Endpoints](#sql-endpoints)
6. [Padrões de Acesso a Dados](#padrões-de-acesso-a-dados)

---

## ⚙️ Configuração Geral dos Lakehouses

Todos os três lakehouses têm **schemas habilitados** (`enableSchemas: true`), o que significa:
- As tabelas são organizadas em um schema chamado `adventureworks`
- O path completo de acesso é `{lakehouse}.{schema}.{tabela}` (ex: `bronze.adventureworks.customer`)
- A API padrão de listagem de tabelas (`/lakehouses/{id}/tables`) **não é suportada** para lakehouses com schemas habilitados

---

## 🥉 Bronze Lakehouse

| Atributo | Valor |
|---|---|
| **Nome** | bronze |
| **ID** | `84d4c516-90ee-4963-a892-2f1da3090e13` |
| **SQL Endpoint ID** | `5335a13e-2f48-4b16-a62c-87717d9e7f15` |
| **Schema habilitado** | Sim |
| **Schema principal** | `adventureworks` |

### 📦 Tabelas (schema: adventureworks)

Todas as tabelas são ingestadas do Azure SQL Database (AdventureWorks, schema `SalesLT`) sem transformação de negócio. A única coluna adicionada é `loading_date`.

| Tabela | Chave Primária | Coluna Extra | Propósito |
|---|---|---|---|
| `adventureworks.address` | `AddressID` | `loading_date` | Endereços de clientes |
| `adventureworks.customer` | `CustomerID` | `loading_date` | Dados de clientes (com hash de senha raw) |
| `adventureworks.customeraddress` | composta | `loading_date` | Associação cliente-endereço |
| `adventureworks.product` | `ProductID` | `loading_date` | Catálogo de produtos |
| `adventureworks.productcategory` | `ProductCategoryID` | `loading_date` | Categorias de produtos |
| `adventureworks.productdescription` | `ProductDescriptionID` | `loading_date` | Descrições de produtos |
| `adventureworks.productmodel` | `ProductModelID` | `loading_date` | Modelos de produtos |
| `adventureworks.productmodelproductdescription` | composta | `loading_date` | Relação modelo-descrição |
| `adventureworks.salesorderdetail` | `SalesOrderDetailID` | `loading_date` | Linhas de pedidos de venda |
| `adventureworks.salesorderheader` | `SalesOrderID` | `loading_date` | Cabeçalhos de pedidos de venda |

### 📁 Estrutura de Files (OneLake)

O pipeline copia os dados do SQL para o bronze como arquivos Parquet antes de transformar em Delta:

```
bronze/
└── Files/
    └── saleslt/
        ├── {table_schema}/
        │   ├── address.parquet
        │   ├── customer.parquet
        │   ├── customeraddress.parquet
        │   ├── product.parquet
        │   ├── productcategory.parquet
        │   ├── productdescription.parquet
        │   ├── productmodel.parquet
        │   ├── productmodelproductdescription.parquet
        │   ├── salesorderdetail.parquet
        │   └── salesorderheader.parquet
└── Tables/
    └── adventureworks/
        ├── address/       (Delta)
        ├── customer/      (Delta)
        └── ... (10 tabelas Delta)
```

### ⚠️ Dados Sensíveis no Bronze
> 🔒 A tabela `customer` no bronze contém as colunas `PasswordHash` e `PasswordSalt` da fonte original. Essas colunas são **removidas no silver** pelo notebook `clean_data`, mas **existem no bronze** — atenção para controle de acesso ao bronze lakehouse.

---

## 🥈 Silver Lakehouse

| Atributo | Valor |
|---|---|
| **Nome** | silver |
| **ID** | `6fa320a8-96a3-438b-aba6-98093b3669e9` |
| **SQL Endpoint ID** | `ecc15741-acc7-4c3c-a3c5-411dfe285e54` |
| **Schema habilitado** | Sim |
| **Schema principal** | `adventureworks` |

### 📦 Tabelas clean_* (dados limpos)

Dados do bronze após limpeza, sem historização. Servem como base para o SCD2.

| Tabela | Principais Transformações |
|---|---|
| `adventureworks.clean_address` | Remove `rowguid` |
| `adventureworks.clean_customer` | Remove `PasswordHash, PasswordSalt, rowguid, ModifiedDate`; adiciona `Gender`; normaliza `SalesPerson` e `Phone` |
| `adventureworks.clean_customeraddress` | Remove `rowguid` |
| `adventureworks.clean_product` | Remove `rowguid` |
| `adventureworks.clean_productcategory` | Remove `rowguid` |
| `adventureworks.clean_productdescription` | Remove `rowguid` |
| `adventureworks.clean_productmodel` | Remove `rowguid` |
| `adventureworks.clean_productmodelproductdescription` | Remove `rowguid` |
| `adventureworks.clean_salesorderdetail` | Remove `rowguid` |
| `adventureworks.clean_salesorderheader` | Remove `rowguid` |

### 📦 Tabelas hist_* (SCD Tipo 2)

Dados historizado com controle de versão temporal. Cada versão de um registro é mantida com colunas de controle.

| Tabela | Chave de Negócio | Schema SCD2 |
|---|---|---|
| `adventureworks.hist_address` | `AddressID` | + `current, effectiveDate, endDate` |
| `adventureworks.hist_customer` | `CustomerID` | + `current, effectiveDate, endDate` |
| `adventureworks.hist_customeraddress` | hash SHA-256 | + `current, effectiveDate, endDate` |
| `adventureworks.hist_product` | `ProductID` | + `current, effectiveDate, endDate` |
| `adventureworks.hist_productcategory` | `ProductCategoryID` | + `current, effectiveDate, endDate` |
| `adventureworks.hist_productdescription` | `ProductDescriptionID` | + `current, effectiveDate, endDate` |
| `adventureworks.hist_productmodel` | `ProductModelID` | + `current, effectiveDate, endDate` |
| `adventureworks.hist_productmodelproductdescription` | hash SHA-256 | + `current, effectiveDate, endDate` |
| `adventureworks.hist_salesorderdetail` | hash SHA-256 | + `current, effectiveDate, endDate` |
| `adventureworks.hist_salesorderheader` | `SalesOrderID` | + `current, effectiveDate, endDate` |

### Schema SCD2 (colunas de controle)

| Coluna | Tipo | Valor Ativo | Valor Inativo |
|---|---|---|---|
| `current` | Boolean | `True` | `False` |
| `effectiveDate` | Date | Data de inserção | (inalterada) |
| `endDate` | Date | `9999-12-31` | Data de expiração |

---

## 🥇 Gold Lakehouse

| Atributo | Valor |
|---|---|
| **Nome** | gold |
| **ID** | `bdf8983d-cdb5-4ff1-ae1f-655460db8890` |
| **SQL Endpoint ID** | `1cf7dbc2-37ab-4896-8e77-936ac93cc091` |
| **Schema habilitado** | Sim |
| **Schema principal** | `adventureworks` |

### 📦 Tabelas (Star Schema)

#### `adventureworks.dimension_address`

| Coluna | Tipo | Notas |
|---|---|---|
| `ID` | string | Surrogate key SHA-256 |
| `AddressID` | int | Chave de negócio |
| `AddressLine1` | string | |
| `AddressLine2` | string | |
| `City` | string | |
| `StateProvince` | string | |
| `CountryRegion` | string | |
| `current_flag` | boolean | `1` = ativo |
| `current_date` | date | Data de início de validade |
| `end_date` | date | `9999-12-31` = ativo |

#### `adventureworks.dimension_customer`

| Coluna | Tipo | Notas |
|---|---|---|
| `ID` | string | Surrogate key SHA-256 |
| `CustomerID` | int | Chave de negócio |
| `Title` | string | Sr./Sra./Dr. etc. |
| `FirstName` | string | |
| `MiddleName` | string | |
| `LastName` | string | |
| `CompanyName` | string | |
| `EmailAddress` | string | |
| `Phone` | string | Normalizado (sem prefixo de país) |
| `current_flag` | boolean | |
| `current_date` | date | |
| `end_date` | date | |

#### `adventureworks.dimension_date`

| Coluna | Tipo | Notas |
|---|---|---|
| `ID` | string | Surrogate key SHA-256 |
| `OrderDate` | date | Data do pedido |
| `Day` | int | Dia do mês (1-31) |
| `Month` | int | Mês (1-12) |
| `Year` | int | Ano |

#### `adventureworks.dimension_product`

| Coluna | Tipo | Notas |
|---|---|---|
| `ID` | string | Surrogate key SHA-256 |
| `ProductID` | int | Chave de negócio |
| `ProductNumber` | string | Código do produto |
| `Color` | string | |
| `Size` | string | |
| `Weight` | string | |
| `CategoryName` | string | Desnormalizado de hist_productcategory |
| `ProductModelName` | string | Desnormalizado de hist_productmodel |
| `current_flag` | boolean | |
| `current_date` | date | |
| `end_date` | date | |

#### `adventureworks.fact_sales`

| Coluna | Tipo | Notas |
|---|---|---|
| `SalesKey` | string | Chave natural: SalesOrderID + SalesOrderDetailID |
| `AddressKey` | string | FK → dimension_address.ID |
| `CustomerKey` | string | FK → dimension_customer.ID |
| `ProductKey` | string | FK → dimension_product.ID |
| `DateKey` | string | FK → dimension_date.ID |
| `Revenue` | double | OrderQty × UnitPrice |
| `OrderQty` | int | Quantidade pedida |
| `UnitPrice` | double | Preço unitário |
| `current_flag` | boolean | |
| `current_date` | date | |
| `end_date` | date | |

---

## 🔌 SQL Endpoints

Cada lakehouse expõe um SQL Endpoint para consultas T-SQL diretas:

| Lakehouse | SQL Endpoint | Uso |
|---|---|---|
| bronze | `5335a13e-2f48-4b16-a62c-87717d9e7f15` | Consultas exploratórias nos dados raw |
| silver | `ecc15741-acc7-4c3c-a3c5-411dfe285e54` | Consultas nos dados limpos e históricos |
| gold | `1cf7dbc2-37ab-4896-8e77-936ac93cc091` | Consultas analíticas no star schema |

---

## 🔍 Padrões de Acesso a Dados

### Cross-Lakehouse (3-part name)

Os notebooks usam referências cross-lakehouse com 3 partes:

```python
# Lendo do bronze estando no silver
spark.read.table("bronze.adventureworks.customer")

# Lendo do silver estando no gold
spark.read.table("silver.adventureworks.hist_address")
```

### Delta MERGE (upsert incremental)

Todos os notebooks gold usam Delta MERGE:

```python
deltaTable.alias('gold').merge(
    updates.alias('updates'),
    'gold.ID = updates.ID'
).whenMatchedUpdate(set={...})
 .whenNotMatchedInsert(values={...})
 .whenNotMatchedBySourceUpdate(set={...})
 .execute()
```

### Partição de Escrita (V-Order)

Os notebooks de dimensão gold configuram Spark para escrita otimizada:
```python
"spark.sql.parquet.vorder.enabled", "true"
"spark.microsoft.delta.optimizeWrite.enabled", "true"
"spark.microsoft.delta.optimizeWrite.binSize", "1073741824"  # 1GB bins
```
