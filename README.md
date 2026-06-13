# Calculadora de Verbas Rescisórias

Ferramenta desktop para cálculo **aproximado** de verbas rescisórias, desenvolvida para dar uma base rápida antes de acionar a contabilidade.

> ⚠️ Os valores gerados são estimativas. Consulte sempre um contador para rescisões reais.

---

## Tipos de rescisão suportados

| Verba | Sem justa causa | Com justa causa | Pedido de demissão | Acordo mútuo | Avulsa |
|---|:---:|:---:|:---:|:---:|:---:|
| Saldo de salário | ✅ | ✅ | ✅ | ✅ | ✅ divisor 30 |
| Aviso prévio (Lei 12.506/2011) | ✅ indenizado | ❌ | ⚠️ deve ao emp. | ✅ 50% | ❌ |
| Férias vencidas + 1/3 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Férias proporcionais + 1/3 | ✅ | ❌ | ✅ | ✅ | ✅ |
| Férias do aviso prévio | ✅ | ❌ | ❌ | ✅ | ❌ |
| 13º proporcional (ano corrente) | ✅ | ❌ | ✅ | ✅ | ✅ por ano |
| 13º do aviso prévio | ✅ | ❌ | ❌ | ✅ | ❌ |
| FGTS acumulado (c/ TR mensal) | ✅ sep. | ✅ sep. | ✅ sep. | ✅ sep. | ✅ no total |
| Multa FGTS | ✅ 40% | ❌ | ❌ | ✅ 20% | ❌ |
| Deduções INSS + IRRF (estimado) | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## Detalhes do cálculo

- **Aviso prévio**: 30 dias + 3 por ano completo trabalhado, máximo 90 dias (Lei 12.506/2011)
- **13º do aviso**: usa `ceil(dias_aviso / 30)` para a verba; base do INSS usa `floor`
- **INSS**: calculado em duas bases separadas — saldo de salário e 13º (aviso prévio é isento)
- **FGTS**: calculado mês a mês com TR real via [brasilindicadores.com.br](https://brasilindicadores.com.br/tr). Exibido separadamente pois o saldo real pode incluir depósitos anteriores desconhecidos
- **Férias**: calculadas automaticamente pelas datas de admissão e demissão, mas ajustáveis manualmente (ex: funcionário tirou férias no período)
- **Rescisão avulsa**: sem deduções, FGTS incluído no total, 13º separado por ano

---

## Estrutura do projeto

```
CalculadoraDeVerbasRecisorias/
├── main.py                  # Entry point — interface PyQt6
├── requirements.txt
├── core/
│   ├── models.py            # Dataclasses: Funcionario, PeriodoSalarial, TipoDemissao
│   ├── rescisao.py          # Orquestrador: todas as verbas rescisórias
│   ├── fgts.py              # Cálculo do FGTS mês a mês com TR real
│   └── tr.py                # Busca da taxa TR via brasilindicadores.com.br
└── ui/                      # Reservado para componentes reutilizáveis
```

---

## Como rodar

```bash
# 1. Clone o repositório
git clone https://github.com/LucasFontesB/CalculadoraDeVerbasRecisorias.git
cd CalculadoraDeVerbasRecisorias

# 2. Crie um ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute
python main.py
```

---

## Dependências

| Biblioteca | Uso |
|---|---|
| PyQt6 | Interface gráfica |
| pandas | Leitura da tabela de TR |
| lxml / html5lib | Parser HTML para `pd.read_html` |
| python-dateutil | Cálculo de meses com `relativedelta` |

---

## Roadmap

- [x] Interface gráfica (PyQt6) com abas
- [x] Múltiplos períodos salariais por funcionário
- [x] FGTS mês a mês com TR real (brasilindicadores.com.br)
- [x] Aviso prévio proporcional (Lei 12.506/2011)
- [x] Férias vencidas e proporcionais com 1/3
- [x] 13º proporcional por ano (separado quando cruza dois anos)
- [x] Multa FGTS (40% sem justa causa / 20% acordo mútuo)
- [x] Deduções INSS e IRRF estimados (bases separadas)
- [x] Rescisão avulsa (sem vínculo CLT)
- [x] Cálculo automático de férias pelas datas, ajustável manualmente
- [ ] Exportar rescisão para PDF
- [ ] Persistência em SQLite (histórico de cálculos)