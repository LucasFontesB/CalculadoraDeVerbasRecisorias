from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class TipoDemissao(Enum):
    SEM_JUSTA_CAUSA   = "Sem justa causa"
    COM_JUSTA_CAUSA   = "Com justa causa"
    PEDIDO_DEMISSAO   = "Pedido de demissão"
    ACORDO_MUTUO      = "Acordo mútuo (§ 484-A)"
    AVULSO            = "Rescisão avulsa (sem vínculo CLT)"


@dataclass
class PeriodoSalarial:
    """Período em que o funcionário recebeu um salário fixo."""
    data_inicio: date
    data_fim: date | None   # None = ainda vigente
    valor: float

    def vigente_em(self, data: date) -> bool:
        fim = self.data_fim or date.today()
        return self.data_inicio <= data <= fim


@dataclass
class Funcionario:
    nome: str
    data_admissao: date
    data_demissao: date
    tipo_demissao: TipoDemissao
    periodos_salariais: list[PeriodoSalarial]
    ferias_vencidas_periodos: int = 0   # ajustável pelo usuário (auto-calculado como base)
    ferias_proporcionais_meses: int = 0 # ajustável pelo usuário (auto-calculado como base)

    def salario_em(self, data: date) -> float:
        """Retorna o salário vigente em uma data específica."""
        for p in sorted(self.periodos_salariais, key=lambda p: p.data_inicio, reverse=True):
            if p.vigente_em(data):
                return p.valor
        return sorted(self.periodos_salariais, key=lambda p: p.data_inicio)[0].valor

    @property
    def salario_atual(self) -> float:
        return self.salario_em(self.data_demissao)