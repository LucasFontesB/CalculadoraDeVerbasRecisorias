import pandas as pd
from datetime import date
from functools import lru_cache

MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
TAXA_RENDIMENTO_FIXA = 0.0025  # 0,25% ao mês (remuneração base do FGTS)
URL_TABELA_TR = "https://brasilindicadores.com.br/tr"


@lru_cache(maxsize=1)
def _carregar_tabelas_tr() -> list:
    """Carrega as tabelas de TR do site. Cache para não repetir requisição."""
    return pd.read_html(URL_TABELA_TR)


def obter_taxa_tr(data: date) -> float:
    """
    Retorna a taxa TR (como decimal) para o mês/ano informado.
    Tenta as tabelas disponíveis no site em ordem.
    """
    mes_str = MESES_PT[data.month - 1]
    ano_str = str(data.year)

    tabelas = _carregar_tabelas_tr()

    for tabela in tabelas:
        if "Ano" not in tabela.columns:
            continue

        tabela = tabela.set_index("Ano").copy()
        tabela.index = tabela.index.astype(str)

        # Remove coluna de totais/médias se existir
        tabela = tabela.iloc[:, :-1]

        if ano_str not in tabela.index:
            continue
        if mes_str not in tabela.columns:
            continue

        valor = tabela.loc[ano_str, mes_str]
        if pd.isna(valor) or valor == "-":
            return 0.0

        return float(str(valor).replace("%", "").replace(",", ".")) / 100

    # Se não encontrou na tabela, assume TR zero (ocorre em períodos de TR zerada)
    return 0.0


def calcular_rendimento_mensal(fgts_acumulado: float, data: date) -> float:
    """
    Calcula o rendimento mensal do FGTS:
    - Taxa TR do mês
    - + 0,25% de remuneração fixa
    """
    taxa_tr = obter_taxa_tr(data)
    rendimento_tr = fgts_acumulado * taxa_tr
    rendimento_fixo = fgts_acumulado * TAXA_RENDIMENTO_FIXA
    return rendimento_tr + rendimento_fixo