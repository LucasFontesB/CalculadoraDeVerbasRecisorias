from datetime import date
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass, field

from core.models import Funcionario
from core.tr import calcular_rendimento_mensal

ALIQUOTA_FGTS = 0.08           # 8% do salário por mês
ALIQUOTA_FGTS_13 = 0.08 / 2   # 4% adicional em nov/dez referente ao 13º
TAXA_DESCONTO_MENSAL = 0.50    # Desconto fixo de R$0,50 por mês (taxa administrativa)


@dataclass
class DetalhesMes:
    """Representa o extrato de um mês de FGTS."""
    data: date
    salario: float
    deposito: float
    rendimento: float
    saldo_final: float
    observacao: str = ""


@dataclass
class ResultadoFGTS:
    saldo_total: float
    detalhes_por_mes: list[DetalhesMes] = field(default_factory=list)


def _dias_no_mes(data: date) -> int:
    """Retorna quantos dias tem o mês da data informada."""
    proximo_mes = data.replace(day=1) + relativedelta(months=1)
    return (proximo_mes - data.replace(day=1)).days


def _deposito_proporcional(salario: float, dia_inicio: int, dias_no_mes: int) -> float:
    """Calcula o depósito de FGTS proporcional aos dias trabalhados no mês."""
    dias_trabalhados = dias_no_mes - dia_inicio + 1
    deposito_diario = (salario * ALIQUOTA_FGTS) / dias_no_mes
    return deposito_diario * dias_trabalhados


def calcular_fgts(funcionario: Funcionario) -> ResultadoFGTS:
    """
    Calcula o FGTS acumulado de um funcionário no período de admissão até demissão.

    Regras aplicadas:
    - 8% do salário vigente em cada mês
    - Meses parciais (admissão/demissão no meio do mês) são calculados proporcionalmente
    - Rendimento mensal: TR + 0,25% aplicado sobre o saldo acumulado
    - Meses de novembro e dezembro: adicional de 4% referente ao 13º salário
    - Desconto de R$0,50 por mês (taxa administrativa da Caixa)
    """
    admissao = funcionario.data_admissao
    demissao = funcionario.data_demissao
    detalhes: list[DetalhesMes] = []

    saldo = 0.0
    cursor = admissao.replace(day=1)  # Itera mês a mês pelo primeiro dia
    fim = demissao.replace(day=1)

    while cursor <= fim:
        salario = funcionario.salario_em(cursor)
        dias_mes = _dias_no_mes(cursor)
        obs_parts = []

        # --- Depósito do mês ---
        eh_primeiro_mes = cursor == admissao.replace(day=1)
        eh_ultimo_mes = cursor == demissao.replace(day=1)

        if eh_primeiro_mes and admissao.day > 1:
            deposito = _deposito_proporcional(salario, admissao.day, dias_mes)
            dias_trab = dias_mes - admissao.day + 1
            obs_parts.append(f"Admissão dia {admissao.day} ({dias_trab} dias)")
        elif eh_ultimo_mes and demissao.day < dias_mes:
            deposito = _deposito_proporcional(salario, 1, dias_mes) * (demissao.day / dias_mes)
            obs_parts.append(f"Demissão dia {demissao.day} ({demissao.day} dias)")
        else:
            deposito = salario * ALIQUOTA_FGTS

        saldo += deposito

        # --- Adicional do 13º (nov e dez) ---
        adicional_13 = 0.0
        if cursor.month in (11, 12) and not eh_primeiro_mes:
            adicional_13 = salario * ALIQUOTA_FGTS_13
            saldo += adicional_13
            obs_parts.append(f"13º: +R${adicional_13:.2f}")

        # --- Rendimento TR + 0,25% (a partir do segundo mês) ---
        rendimento = 0.0
        if not eh_primeiro_mes:
            rendimento = calcular_rendimento_mensal(saldo - deposito - adicional_13, cursor)
            saldo += rendimento
            saldo -= TAXA_DESCONTO_MENSAL

        detalhes.append(DetalhesMes(
            data=cursor,
            salario=salario,
            deposito=round(deposito + adicional_13, 2),
            rendimento=round(rendimento, 2),
            saldo_final=round(saldo, 2),
            observacao=", ".join(obs_parts),
        ))

        cursor += relativedelta(months=1)

    return ResultadoFGTS(
        saldo_total=round(saldo, 2),
        detalhes_por_mes=detalhes,
    )