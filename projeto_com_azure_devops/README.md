# Versão legada — Azure DevOps (referência)

Esta pasta contém a versão **antiga** do CI/CD do workshop, que rodava em
**Azure DevOps Pipelines**. Ela é mantida apenas como **material de referência
didática** e **não é executada** — o projeto ativo migrou para **GitHub Actions**
(veja `.github/workflows/` na raiz do repositório).

## Conteúdo

- `azure_pipelines/deploy.yml` — pipeline de deploy para o Microsoft Fabric
  (trigger em push para `main`/`develop`, variable group `spn_credentials`,
  pool `windows-latest`, roda `scripts/deploy.py`).
- `azure_pipelines/test-pbip.yml` — validação de PR para `main` (pytest via `uv`).
- `scripts/deploy.py` e `scripts/utils.py` — cópia dos scripts **originais**, que
  dependiam de variáveis específicas do Azure DevOps:
  - `BUILD_SOURCEBRANCHNAME` (branch atual)
  - `SYSTEM_PULLREQUEST_TARGETBRANCH` (branch alvo do PR)
  - `$(Build.SourcesDirectory)` (diretório de trabalho)

> Os scripts **ativos** ficam em `Workshop_DMF/scripts/` e usam as variáveis
> nativas do GitHub (`GITHUB_REF_NAME`, `GITHUB_BASE_REF`).

## Equivalências Azure DevOps → GitHub Actions

| Azure DevOps | GitHub Actions |
|---|---|
| `trigger` / `pr` | `on.push` / `on.pull_request` |
| `parameters` | `on.workflow_dispatch.inputs` |
| `variables: - group: spn_credentials` | `secrets.*` (Environment/repo) |
| `pool.vmImage` | `runs-on` |
| `UsePythonVersion@0` | `actions/setup-python@v5` |
| `$(Build.SourcesDirectory)` | `working-directory` / `$GITHUB_WORKSPACE` |
| `BUILD_SOURCEBRANCHNAME` | `GITHUB_REF_NAME` |
| `SYSTEM_PULLREQUEST_TARGETBRANCH` | `GITHUB_BASE_REF` |
