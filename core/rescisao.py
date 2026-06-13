"""
Cálculo completo das verbas rescisórias trabalhistas (CLT).
Lógica baseada no modelo da contabilidade do cliente (hotel).

Verbas calculadas:
  - Saldo de salário (dias trabalhados no mês da demissão)
  - Aviso prévio indenizado (Lei 12.506/2011: 30 + 3 dias/ano, máx 90)
  - Férias proporcionais (meses informados pelo usuário)
  - Férias do aviso prévio (1 mês extra separado)
  - 1/3 constitucional sobre férias proporcionais + férias do aviso
  - 13º proporcional (meses trabalhados no ANO CORRENTE, sem contar aviso)
  - 13º do aviso prévio (separado: 1 mês extra)
  - Férias vencidas + 1/3 (se houver períodos não tirados)
  - INSS: base 1 (saldo + aviso) e base 2 (13º), calculados separadamente
  - Multa FGTS (40% sem justa causa, 20% acordo mútuo)
"""

from dataclasses import dataclass, field
from datetime import date
import math
from dateutil.relativedelta import relativedelta

from core.models import Funcionario, TipoDemissao
from core.fgts import calcular_fgts, ResultadoFGTS

# ── Tabela INSS 2024/2025 — faixas progressivas ──────────────────────────────
_FAIXAS_INSS = [
    (1_518.00,  0.075),
    (2_793.88,  0.09),
    (4_190.83,  0.12),
    (8_157.41,  0.14),
]

# ── Tabela IRRF 2024/2025 ─────────────────────────────────────────────────────
_FAIXAS_IRRF = [
    (2_259.20,  0.000,   0.00),
    (2_826.65,  0.075, 169.44),
    (3_751.05,  0.150, 381.44),
    (4_664.68,  0.225, 662.77),
    (float("inf"), 0.275, 896.00),
]


def _calcular_inss(base: float) -> float:
    """INSS progressivo por faixa."""
    if base <= 0:
        return 0.0
    desconto = 0.0
    faixa_ant = 0.0
    for teto, aliq in _FAIXAS_INSS:
        if base <= teto:
            desconto += (base - faixa_ant) * aliq
            break
        desconto += (teto - faixa_ant) * aliq
        faixa_ant = teto
    else:
        desconto += (base - faixa_ant) * _FAIXAS_INSS[-1][1]
    return round(desconto, 2)


def _calcular_irrf(base_liquida: float) -> float:
    """IRRF sobre base líquida (após INSS)."""
    if base_liquida <= 0:
        return 0.0
    for teto, aliq, ded in _FAIXAS_IRRF:
        if base_liquida <= teto:
            return round(max(base_liquida * aliq - ded, 0), 2)
    return 0.0


def _dias_aviso(anos: int) -> int:
    """Lei 12.506/2011: 30 + 3 por ano completo, máx 90."""
    return min(30 + anos * 3, 90)


@dataclass
class LinhaVerba:
    descricao: str
    valor: float
    observacao: str = ""
    eh_deducao: bool = False


@dataclass
class ResultadoRescisao:
    funcionario: Funcionario
    verbas: list[LinhaVerba] = field(default_factory=list)
    deducoes: list[LinhaVerba] = field(default_factory=list)
    resultado_fgts: ResultadoFGTS | None = None

    total_bruto: float = 0.0
    total_deducoes: float = 0.0
    total_liquido: float = 0.0
    fgts_saldo: float = 0.0
    fgts_multa: float = 0.0
    fgts_multa_gov: float = 0.0
    dias_aviso_previo: int = 0



def calcular_ferias_automatico(admissao: date, demissao: date) -> tuple[int, int]:
    """
    Calcula automaticamente períodos de férias vencidos e meses do período em curso.

    Regra CLT:
    - A cada 12 meses completos de contrato, o funcionário adquire 1 período de férias.
    - O período em curso são os meses passados desde o último aniversário do contrato.
    - Meses parciais: conta se trabalhou >= 15 dias naquele mês.

    Retorna: (periodos_vencidos, meses_periodo_em_curso)
    """
    diff = relativedelta(demissao, admissao)
    periodos_vencidos = diff.years

    # Meses desde o último aniversário do contrato
    meses_em_curso = diff.months

    # Conta o mês da demissão se trabalhou >= 15 dias nele
    # (o dia de admissão já está embutido no relativedelta)
    if demissao.day >= 15:
        meses_em_curso += 1

    meses_em_curso = min(meses_em_curso, 11)  # máx 11, pois 12 vira novo período

    return periodos_vencidos, meses_em_curso


def calcular_rescisao(funcionario: Funcionario) -> ResultadoRescisao:
    f = funcionario
    salario = f.salario_atual
    admissao = f.data_admissao
    demissao = f.data_demissao
    tipo = f.tipo_demissao

    diff = relativedelta(demissao, admissao)
    anos_trabalhados = diff.years

    # Usa valores do usuário (pré-preenchidos automaticamente, ajustáveis)
    periodos_vencidos = f.ferias_vencidas_periodos
    meses_em_curso    = f.ferias_proporcionais_meses

    resultado = ResultadoRescisao(funcionario=f)
    verbas: list[LinhaVerba] = []

    # ── 1. Saldo de salário ──────────────────────────────────────────────────
    dias_trabalhados = demissao.day
    if tipo == TipoDemissao.AVULSO:
        # Rescisão avulsa: divisor fixo de 30 (padrão da contabilidade)
        divisor = 30
    else:
        divisor = (demissao.replace(day=1) + relativedelta(months=1) - demissao.replace(day=1)).days
    saldo_salario = round(salario / divisor * dias_trabalhados, 2)
    verbas.append(LinhaVerba(
        "Saldo de salário",
        saldo_salario,
        f"{dias_trabalhados} dias de {divisor}",
    ))

    # ── 2. Aviso prévio ──────────────────────────────────────────────────────
    dias_aviso = _dias_aviso(anos_trabalhados)
    resultado.dias_aviso_previo = dias_aviso
    valor_aviso = 0.0

    if tipo == TipoDemissao.SEM_JUSTA_CAUSA:
        valor_aviso = round(salario / 30 * dias_aviso, 2)
        verbas.append(LinhaVerba(
            "Aviso prévio indenizado",
            valor_aviso,
            f"{dias_aviso} dias (Lei 12.506/2011)",
        ))
    elif tipo == TipoDemissao.PEDIDO_DEMISSAO:
        verbas.append(LinhaVerba(
            "Aviso prévio (devido pelo empregado)",
            0.0,
            f"Funcionário deve {dias_aviso} dias ou desconto equivalente",
        ))
    elif tipo == TipoDemissao.ACORDO_MUTUO:
        valor_aviso = round((salario / 30 * dias_aviso) / 2, 2)
        verbas.append(LinhaVerba(
            "Aviso prévio indenizado (50% — acordo mútuo)",
            valor_aviso,
            f"{dias_aviso} dias × 50% (§484-A)",
        ))

    # ── 3. Férias vencidas + 1/3 ─────────────────────────────────────────────
    if periodos_vencidos > 0:
        ferias_venc = round(salario * periodos_vencidos, 2)
        terco_venc  = round(ferias_venc / 3, 2)
        verbas.append(LinhaVerba(
            "Férias vencidas",
            ferias_venc,
            f"{periodos_vencidos} período(s) não usufruído(s)",
        ))
        verbas.append(LinhaVerba(
            "1/3 constitucional sobre férias vencidas",
            terco_venc,
        ))

    # ── 4. Férias proporcionais ───────────────────────────────────────────────
    meses_ferias = meses_em_curso
    ferias_prop = 0.0
    ferias_aviso = 0.0

    if tipo not in (TipoDemissao.COM_JUSTA_CAUSA,) and meses_ferias > 0:
        ferias_prop = round(salario / 12 * meses_ferias, 2)
        verbas.append(LinhaVerba(
            "Férias proporcionais",
            ferias_prop,
            f"{meses_ferias}/12 avos",
        ))

    # Férias do aviso prévio — usa floor(dias/30), 1 mês
    meses_aviso_ferias = dias_aviso // 30  # floor: 33 dias = 1 mês
    if tipo in (TipoDemissao.SEM_JUSTA_CAUSA, TipoDemissao.ACORDO_MUTUO):
        ferias_aviso = round(salario / 12 * meses_aviso_ferias, 2)
        verbas.append(LinhaVerba(
            "Férias (aviso prévio indenizado)",
            ferias_aviso,
            f"{meses_aviso_ferias} mês do aviso",
        ))

    # 1/3 constitucional sobre férias proporcionais + férias do aviso
    base_terco = ferias_prop + ferias_aviso
    if base_terco > 0 and tipo != TipoDemissao.COM_JUSTA_CAUSA:
        terco = round(base_terco / 3, 2)
        verbas.append(LinhaVerba(
            "1/3 constitucional de férias",
            terco,
            f"Sobre R$ {base_terco:.2f}".replace(".", ","),
        ))

    # ── 5. 13º proporcional ───────────────────────────────────────────────────
    # Conta apenas os meses trabalhados no ANO CORRENTE (sem aviso)
    # Mês de admissão ou demissão conta se >= 15 dias trabalhados
    decimo_terceiro = 0.0
    decimo_terceiro_aviso = 0.0

    if tipo != TipoDemissao.COM_JUSTA_CAUSA:
        # ── 13º proporcional ─────────────────────────────────────────────────
        # CLT: só o ano corrente da demissão entra na rescisão.
        #      13º de anos anteriores já foram pagos em dezembro de cada ano.
        # Avulso: como não há vínculo formal, a contabilidade separa por ano
        #         (ano de admissão + ano de demissão), pois não houve pagamento anual.

        if tipo == TipoDemissao.AVULSO and admissao.year != demissao.year:
            # Ano de admissão: meses trabalhados até dezembro
            avos_adm = 12 - admissao.month
            if admissao.day <= 15:
                avos_adm += 1
            avos_adm = min(avos_adm, 12)
            sal_adm = f.salario_em(admissao)
            if avos_adm > 0:
                dec3_adm = round(sal_adm / 12 * avos_adm, 2)
                decimo_terceiro += dec3_adm
                verbas.append(LinhaVerba(
                    f"13º salário proporcional ({admissao.year})",
                    dec3_adm,
                    f"{avos_adm}/12 avos",
                ))

            # Anos intermediários completos (avulso sem pagamento anual)
            for ano_inter in range(admissao.year + 1, demissao.year):
                sal_inter = f.salario_em(date(ano_inter, 6, 1))
                dec3_inter = round(sal_inter, 2)
                decimo_terceiro += dec3_inter
                verbas.append(LinhaVerba(
                    f"13º salário ({ano_inter})",
                    dec3_inter,
                    "12/12 avos",
                ))

        # Ano de demissão (todos os tipos): jan até mês da demissão
        if admissao.year == demissao.year:
            # Mesmo ano: conta da admissão
            inicio_13 = admissao
        else:
            # Anos diferentes: conta de janeiro do ano de demissão
            inicio_13 = date(demissao.year, 1, 1)

        avos_demissao = relativedelta(demissao, inicio_13).months
        if demissao.day >= 15:
            avos_demissao += 1
        avos_demissao = min(avos_demissao, 12)

        if avos_demissao > 0:
            dec3_demissao = round(salario / 12 * avos_demissao, 2)
            decimo_terceiro += dec3_demissao
            label_13 = "13º salário proporcional" if admissao.year == demissao.year else f"13º salário proporcional ({demissao.year})"
            verbas.append(LinhaVerba(
                label_13,
                dec3_demissao,
                f"{avos_demissao}/12 avos",
            ))

        # 13º do aviso prévio — usa ceil(dias/30) pois aviso parcial conta mês cheio
        if tipo in (TipoDemissao.SEM_JUSTA_CAUSA, TipoDemissao.ACORDO_MUTUO):
            meses_aviso_13 = math.ceil(dias_aviso / 30)
            decimo_terceiro_aviso = round(salario / 12 * meses_aviso_13, 2)
            verbas.append(LinhaVerba(
                "13º salário (aviso prévio indenizado)",
                decimo_terceiro_aviso,
                f"{meses_aviso_13} mês(es) do aviso",
            ))

    # ── 6. FGTS ──────────────────────────────────────────────────────────────
    resultado_fgts = calcular_fgts(f)
    resultado.resultado_fgts = resultado_fgts
    resultado.fgts_saldo = resultado_fgts.saldo_total

    # ── 7. Multa FGTS ────────────────────────────────────────────────────────
    # Multa e contribuição social ficam FORA do total bruto/líquido da rescisão
    # pois dependem do saldo real do FGTS (pode haver depósitos anteriores desconhecidos)
    multa = 0.0
    multa_gov = 0.0
    if tipo == TipoDemissao.SEM_JUSTA_CAUSA:
        multa     = round(resultado_fgts.saldo_total * 0.40, 2)
        multa_gov = round(resultado_fgts.saldo_total * 0.10, 2)
    elif tipo == TipoDemissao.ACORDO_MUTUO:
        multa = round(resultado_fgts.saldo_total * 0.20, 2)
    resultado.fgts_multa     = multa
    resultado.fgts_multa_gov = multa_gov

    # ── 8. Deduções ──────────────────────────────────────────────────────────
    deducoes: list[LinhaVerba] = []

    if tipo != TipoDemissao.AVULSO:
        # Base 1: saldo de salário (aviso isento de INSS)
        base_inss_1 = saldo_salario
        inss_1 = _calcular_inss(base_inss_1)

        # Base 2: 13º + férias do aviso (ambos com floor) + 13º aviso com floor
        # 13º aviso usa ceil para a verba, mas floor para a base INSS (método da contabilidade)
        dec3_aviso_inss = round(salario / 12 * meses_aviso_ferias, 2)
        base_inss_2 = decimo_terceiro + dec3_aviso_inss + ferias_aviso
        inss_2 = _calcular_inss(base_inss_2)

        if inss_1 > 0:
            deducoes.append(LinhaVerba(
                "Previdência Social",
                inss_1,
                f"Base: {_brl(base_inss_1)} (aviso isento)",
                eh_deducao=True,
            ))
        if inss_2 > 0:
            deducoes.append(LinhaVerba(
                "Previdência Social — 13º salário",
                inss_2,
                f"Base: {_brl(base_inss_2)}",
                eh_deducao=True,
            ))

        base_irrf = base_inss_1 - inss_1
        irrf = _calcular_irrf(base_irrf)
        if irrf > 0:
            deducoes.append(LinhaVerba(
                "IRRF (estimado)",
                irrf,
                f"Base líq.: {_brl(base_irrf)}",
                eh_deducao=True,
            ))

    # ── Totais ───────────────────────────────────────────────────────────────
    # Avulso: FGTS entra no total. Demais tipos: FGTS fica separado (saldo incerto)
    fgts_no_total = resultado_fgts.saldo_total if tipo == TipoDemissao.AVULSO else 0.0
    total_bruto = round(sum(v.valor for v in verbas) + fgts_no_total, 2)
    total_ded   = round(sum(d.valor for d in deducoes), 2)
    total_liq   = round(total_bruto - total_ded, 2)

    resultado.verbas         = verbas
    resultado.deducoes       = deducoes
    resultado.total_bruto    = total_bruto
    resultado.total_deducoes = total_ded
    resultado.total_liquido  = total_liq

    return resultado


def _brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")