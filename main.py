import sys
from datetime import date

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea, QFrame,
    QMessageBox, QGroupBox, QFormLayout, QComboBox,
    QSpinBox, QTabWidget, QSizePolicy, QGridLayout,
)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.models import Funcionario, PeriodoSalarial, TipoDemissao
from core.fgts import calcular_fgts
from core.rescisao import calcular_rescisao, ResultadoRescisao

# QApplication precisa existir antes de qualquer definição de widget no Windows
_app = QApplication.instance() or QApplication(sys.argv)
_app.setStyle("Fusion")

# ── Paleta ───────────────────────────────────────────────────────────────────
C = {
    "bg":       "#0F1117",
    "panel":    "#1A1D27",
    "border":   "#2A2D3A",
    "blue":     "#2563EB",
    "green":    "#10B981",
    "red":      "#EF4444",
    "amber":    "#F59E0B",
    "text":     "#E2E8F0",
    "muted":    "#64748B",
    "input":    "#252836",
    "rowalt":   "#111827",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}
QGroupBox {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 12px 10px 12px;
    font-weight: 600;
    color: {C['muted']};
    font-size: 11px;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
}}
QLineEdit, QDateEdit, QComboBox, QSpinBox {{
    background-color: {C['input']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 7px 10px;
    color: {C['text']};
    font-size: 13px;
}}
QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {C['blue']};
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    selection-background-color: {C['blue']};
    color: {C['text']};
}}
QPushButton {{
    background-color: {C['blue']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover  {{ background-color: #1D4ED8; }}
QPushButton:pressed {{ background-color: #1E40AF; }}
QPushButton#sec {{
    background-color: {C['border']};
    color: {C['text']};
}}
QPushButton#sec:hover {{ background-color: #3A3D4A; }}
QPushButton#danger {{
    background-color: transparent;
    color: {C['red']};
    border: 1px solid {C['red']};
    padding: 4px 10px;
    font-size: 12px;
}}
QPushButton#danger:hover {{ background-color: #EF444420; }}
QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    background: {C['panel']};
}}
QTabBar::tab {{
    background: {C['border']};
    color: {C['muted']};
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: 600;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background: {C['blue']};
    color: white;
}}
QTableWidget {{
    background-color: {C['panel']};
    border: none;
    gridline-color: {C['border']};
    color: {C['text']};
}}
QTableWidget::item {{ padding: 8px; }}
QTableWidget::item:selected {{
    background-color: {C['blue']}40;
    color: {C['text']};
}}
QHeaderView::section {{
    background-color: {C['rowalt']};
    color: {C['muted']};
    border: none;
    border-bottom: 1px solid {C['border']};
    padding: 8px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QScrollBar:vertical {{
    background: {C['bg']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 4px;
    min-height: 20px;
}}
"""


# ── Helpers ──────────────────────────────────────────────────────────────────
def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cell(text: str, align=Qt.AlignmentFlag.AlignCenter, bold=False, color: str | None = None) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(align)
    if bold:
        item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
    if color:
        item.setForeground(QColor(color))
    return item


# ── Worker ───────────────────────────────────────────────────────────────────
class Worker(QThread):
    concluido = pyqtSignal(object)
    erro      = pyqtSignal(str)

    def __init__(self, funcionario: Funcionario):
        super().__init__()
        self.funcionario = funcionario

    def run(self):
        try:
            self.concluido.emit(calcular_rescisao(self.funcionario))
        except Exception as e:
            self.erro.emit(str(e))


# ── Widget de períodos salariais ──────────────────────────────────────────────
class PeriodosSalariais(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = QVBoxLayout(self)
        self._lay.setSpacing(6)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._rows: list[tuple] = []
        self.adicionar()

    def adicionar(self):
        row = QWidget()
        rl  = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        inp_val = QLineEdit()
        inp_val.setPlaceholderText("Salário (R$)")
        inp_val.setMinimumHeight(36)
        inp_val.setMinimumWidth(110)

        inp_ini = QDateEdit()
        inp_ini.setDisplayFormat("dd/MM/yyyy")
        inp_ini.setCalendarPopup(True)
        inp_ini.setDate(QDate.currentDate())
        inp_ini.setMinimumHeight(36)
        inp_ini.setMinimumWidth(120)
        inp_ini.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        inp_fim = QDateEdit()
        inp_fim.setDisplayFormat("dd/MM/yyyy")
        inp_fim.setCalendarPopup(True)
        inp_fim.setDate(QDate.currentDate())
        inp_fim.setMinimumHeight(36)
        inp_fim.setMinimumWidth(120)
        inp_fim.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        btn_atual = QPushButton("Atual")
        btn_atual.setCheckable(True)
        btn_atual.setObjectName("sec")
        btn_atual.setFixedWidth(60)
        btn_atual.setMinimumHeight(36)
        btn_atual.toggled.connect(inp_fim.setDisabled)

        btn_rm = QPushButton("✕")
        btn_rm.setObjectName("danger")
        btn_rm.setFixedWidth(36)
        btn_rm.setMinimumHeight(36)
        btn_rm.clicked.connect(lambda: self._remover(row))

        rl.addWidget(inp_val, 2)
        rl.addWidget(inp_ini, 2)
        rl.addWidget(inp_fim, 2)
        rl.addWidget(btn_atual)
        rl.addWidget(btn_rm)

        self._lay.addWidget(row)
        self._rows.append((row, inp_val, inp_ini, inp_fim, btn_atual))

    def _remover(self, row):
        self._rows = [(r, *rest) for r, *rest in self._rows if r is not row]
        row.setParent(None); row.deleteLater()

    def get_periodos(self) -> list[PeriodoSalarial]:
        out = []
        for _, iv, ii, fi, ba in self._rows:
            try:
                valor = float(iv.text().replace(",", "."))
            except ValueError:
                raise ValueError("Valor de salário inválido. Use apenas números.")
            inicio = ii.date().toPyDate()
            fim    = None if ba.isChecked() else fi.date().toPyDate()
            if fim and fim < inicio:
                raise ValueError("Data fim do salário anterior ao início.")
            out.append(PeriodoSalarial(data_inicio=inicio, data_fim=fim, valor=valor))
        return out


# ── Card de resumo ────────────────────────────────────────────────────────────
class CardResumo(QWidget):
    def __init__(self, titulo: str, cor: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)
        self.setStyleSheet(f"""
            CardResumo {{
                background: {C['panel']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        lbl_t = QLabel(titulo.upper())
        lbl_t.setStyleSheet(f"color: {C['muted']}; font-size: 11px; letter-spacing: 1px; font-weight: 600;")
        self.lbl_v = QLabel("R$ —")
        self.lbl_v.setStyleSheet(f"color: {cor}; font-size: 26px; font-weight: 700;")
        lay.addWidget(lbl_t)
        lay.addWidget(self.lbl_v)

    def set_valor(self, v: float):
        self.lbl_v.setText(brl(v))


# ── Janela principal ──────────────────────────────────────────────────────────
class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora de Verbas Rescisórias")
        self.setMinimumSize(1200, 740)
        self.setStyleSheet(STYLESHEET)
        self._worker = None
        self._build()

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Coluna esquerda com scroll ────────────────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setFixedWidth(540)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        left = QWidget()
        left_scroll.setWidget(left)
        ll = QVBoxLayout(left)
        ll.setSpacing(12)
        ll.setContentsMargins(4, 4, 12, 4)

        lbl_t = QLabel("Rescisão Trabalhista")
        lbl_t.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl_sub = QLabel("Estimativa completa de verbas rescisórias")
        lbl_sub.setStyleSheet(f"color: {C['muted']}; font-size: 12px;")
        ll.addWidget(lbl_t)
        ll.addWidget(lbl_sub)

        def campo(label_txt, widget):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(10)
            lbl = QLabel(label_txt)
            lbl.setFixedWidth(100)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(f"color: {C['muted']}; font-size: 12px;")
            widget.setMinimumHeight(36)
            h.addWidget(lbl)
            h.addWidget(widget, 1)
            return w

        # ── Dados do Funcionário ──────────────────────────────────────────
        grp_dados = QGroupBox("DADOS DO FUNCIONÁRIO")
        gd = QVBoxLayout(grp_dados)
        gd.setSpacing(8)
        gd.setContentsMargins(12, 20, 12, 12)

        self.inp_nome = QLineEdit()
        self.inp_nome.setPlaceholderText("Nome do funcionário")

        self.inp_admissao = QDateEdit()
        self.inp_admissao.setDisplayFormat("dd/MM/yyyy")
        self.inp_admissao.setCalendarPopup(True)
        self.inp_admissao.setDate(QDate.currentDate().addYears(-1))

        self.inp_demissao = QDateEdit()
        self.inp_demissao.setDisplayFormat("dd/MM/yyyy")
        self.inp_demissao.setCalendarPopup(True)
        self.inp_demissao.setDate(QDate.currentDate())

        self.cmb_tipo = QComboBox()
        for t in TipoDemissao:
            self.cmb_tipo.addItem(t.value, t)

        gd.addWidget(campo("Nome:", self.inp_nome))
        gd.addWidget(campo("Admissão:", self.inp_admissao))
        gd.addWidget(campo("Demissão:", self.inp_demissao))
        gd.addWidget(campo("Tipo:", self.cmb_tipo))
        ll.addWidget(grp_dados)

        # ── Férias (auto-calculado, ajustável) ───────────────────────────
        grp_fer = QGroupBox("FÉRIAS")
        gfer = QVBoxLayout(grp_fer)
        gfer.setSpacing(8)
        gfer.setContentsMargins(12, 20, 12, 12)

        self.spn_fer_venc = QSpinBox()
        self.spn_fer_venc.setRange(0, 20)
        self.spn_fer_venc.setSuffix(" período(s)")

        self.spn_fer_prop = QSpinBox()
        self.spn_fer_prop.setRange(0, 11)
        self.spn_fer_prop.setSuffix(" meses")

        lbl_auto = QLabel("✦ Calculado automaticamente — ajuste se o funcionário tirou férias")
        lbl_auto.setWordWrap(True)
        lbl_auto.setStyleSheet(f"color: {C['muted']}; font-size: 11px; font-style: italic;")
        gfer.addWidget(lbl_auto)

        def campo_largo(label_txt, widget):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(10)
            lbl = QLabel(label_txt)
            lbl.setFixedWidth(230)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(f"color: {C['muted']}; font-size: 12px;")
            widget.setMinimumHeight(36)
            h.addWidget(lbl)
            h.addWidget(widget, 1)
            return w

        gfer.addWidget(campo_largo("Períodos vencidos não tirados:", self.spn_fer_venc))
        gfer.addWidget(campo_largo("Meses do período em curso:", self.spn_fer_prop))
        ll.addWidget(grp_fer)

        # Atualiza férias automaticamente quando datas mudam
        self.inp_admissao.dateChanged.connect(self._atualizar_ferias)
        self.inp_demissao.dateChanged.connect(self._atualizar_ferias)
        self._atualizar_ferias()  # popula com os valores iniciais

        # ── Histórico Salarial ────────────────────────────────────────────
        grp_sal = QGroupBox("HISTÓRICO SALARIAL")
        gsal = QVBoxLayout(grp_sal)
        gsal.setSpacing(8)
        gsal.setContentsMargins(12, 20, 12, 12)

        cab = QWidget()
        cl = QHBoxLayout(cab)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)
        for txt, stretch in [("Valor (R$)", 3), ("Início", 3), ("Fim", 3), ("", 2)]:
            l = QLabel(txt)
            l.setStyleSheet(f"color: {C['muted']}; font-size: 11px; font-weight: 600;")
            cl.addWidget(l, stretch)
        gsal.addWidget(cab)

        self.periodos = PeriodosSalariais()
        gsal.addWidget(self.periodos)

        btn_add = QPushButton("+ Adicionar período salarial")
        btn_add.setObjectName("sec")
        btn_add.clicked.connect(self.periodos.adicionar)
        gsal.addWidget(btn_add)
        ll.addWidget(grp_sal)

        # ── Botão calcular ────────────────────────────────────────────────
        self.btn_calc = QPushButton("Calcular Rescisão")
        self.btn_calc.setFixedHeight(44)
        self.btn_calc.clicked.connect(self._calcular)
        ll.addWidget(self.btn_calc)

        # ── Cards de resumo ───────────────────────────────────────────────
        # ── Resumo da rescisão ────────────────────────────────────────────
        grp_res = QGroupBox("RESUMO DA RESCISÃO")
        gres = QVBoxLayout(grp_res)
        gres.setSpacing(8)
        gres.setContentsMargins(12, 20, 12, 12)

        self.card_bruto = CardResumo("Total Bruto",   C['text'])
        self.card_ded   = CardResumo("Deduções",      C['red'])
        self.card_liq   = CardResumo("Total Líquido", C['green'])

        row1 = QHBoxLayout()
        row1.addWidget(self.card_bruto)
        row1.addWidget(self.card_ded)
        row1.addWidget(self.card_liq)
        gres.addLayout(row1)
        ll.addWidget(grp_res)

        # ── FGTS separado (saldo pode ser desconhecido) ───────────────────
        grp_fgts = QGroupBox("FGTS — ESTIMATIVA")
        gfgts = QVBoxLayout(grp_fgts)
        gfgts.setSpacing(8)
        gfgts.setContentsMargins(12, 20, 12, 12)

        lbl_aviso_fgts = QLabel("⚠ Calculado apenas sobre o período deste contrato. Verifique o saldo real na Caixa.")
        lbl_aviso_fgts.setWordWrap(True)
        lbl_aviso_fgts.setStyleSheet(f"color: {C['amber']}; font-size: 11px;")
        gfgts.addWidget(lbl_aviso_fgts)

        self.card_fgts  = CardResumo("Saldo FGTS",    C['blue'])
        self.card_multa = CardResumo("Multa (40%)",    C['amber'])
        self.card_multa_gov = CardResumo("Contrib. Gov (10%)", C['muted'])

        row2 = QHBoxLayout()
        row2.addWidget(self.card_fgts)
        row2.addWidget(self.card_multa)
        row2.addWidget(self.card_multa_gov)
        gfgts.addLayout(row2)
        ll.addWidget(grp_fgts)
        ll.addStretch()

        # ── Coluna direita: abas ───────────────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(0,0,0,0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Aba verbas
        tab_verbas = QWidget()
        tvl = QVBoxLayout(tab_verbas); tvl.setContentsMargins(10,10,10,10)
        self.tbl_verbas = self._make_table(["Verba", "Valor", "Observação"])
        tvl.addWidget(self.tbl_verbas)
        self.tabs.addTab(tab_verbas, "Verbas Rescisórias")

        # Aba deduções
        tab_ded = QWidget()
        tdl = QVBoxLayout(tab_ded); tdl.setContentsMargins(10,10,10,10)
        self.tbl_ded = self._make_table(["Dedução", "Valor", "Base de cálculo"])
        tdl.addWidget(self.tbl_ded)
        self.tabs.addTab(tab_ded, "Deduções")

        # Aba extrato FGTS
        tab_fgts = QWidget()
        tfl = QVBoxLayout(tab_fgts); tfl.setContentsMargins(10,10,10,10)
        self.tbl_fgts = self._make_table(["Mês/Ano", "Salário", "Depósito (8%)", "Rendimento", "Saldo", "Obs."])
        tfl.addWidget(self.tbl_fgts)
        self.tabs.addTab(tab_fgts, "Extrato FGTS")

        rl.addWidget(self.tabs)

        root.addWidget(left_scroll)
        root.addWidget(right, 1)

    def _make_table(self, headers: list[str]) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.horizontalHeader().setSectionResizeMode(len(headers)-1, QHeaderView.ResizeMode.ResizeToContents)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(f"QTableWidget {{ alternate-background-color: {C['rowalt']}; }}")
        return t

    # ── Calcular ──────────────────────────────────────────────────────────────
    def _atualizar_ferias(self):
        """Recalcula os campos de férias automaticamente ao mudar as datas."""
        try:
            from core.rescisao import calcular_ferias_automatico
            admissao = self.inp_admissao.date().toPyDate()
            demissao = self.inp_demissao.date().toPyDate()
            if demissao <= admissao:
                return
            periodos, meses = calcular_ferias_automatico(admissao, demissao)
            # Bloqueia sinais para não disparar eventos desnecessários
            self.spn_fer_venc.blockSignals(True)
            self.spn_fer_prop.blockSignals(True)
            self.spn_fer_venc.setValue(periodos)
            self.spn_fer_prop.setValue(meses)
            self.spn_fer_venc.blockSignals(False)
            self.spn_fer_prop.blockSignals(False)
        except Exception:
            pass

    def _calcular(self):
        try:
            nome     = self.inp_nome.text().strip() or "Funcionário"
            admissao = self.inp_admissao.date().toPyDate()
            demissao = self.inp_demissao.date().toPyDate()
            tipo     = self.cmb_tipo.currentData()

            if demissao <= admissao:
                raise ValueError("Data de demissão deve ser posterior à admissão.")

            periodos = self.periodos.get_periodos()
            if not periodos:
                raise ValueError("Adicione pelo menos um período salarial.")

            func = Funcionario(
                nome=nome,
                data_admissao=admissao,
                data_demissao=demissao,
                tipo_demissao=tipo,
                periodos_salariais=periodos,
                ferias_vencidas_periodos=self.spn_fer_venc.value(),
                ferias_proporcionais_meses=self.spn_fer_prop.value(),
            )
        except ValueError as e:
            QMessageBox.warning(self, "Dados inválidos", str(e))
            return

        self.btn_calc.setText("Calculando...")
        self.btn_calc.setDisabled(True)
        for t in (self.tbl_verbas, self.tbl_ded, self.tbl_fgts):
            t.setRowCount(0)

        self._worker = Worker(func)
        self._worker.concluido.connect(self._exibir)
        self._worker.erro.connect(self._erro)
        self._worker.start()

    def _exibir(self, r: ResultadoRescisao):
        self.btn_calc.setText("Calcular Rescisão")
        self.btn_calc.setDisabled(False)

        # Cards rescisão
        self.card_bruto.set_valor(r.total_bruto)
        self.card_ded.set_valor(r.total_deducoes)
        self.card_liq.set_valor(r.total_liquido)
        # Cards FGTS (estimativa separada)
        self.card_fgts.set_valor(r.fgts_saldo)
        self.card_multa.set_valor(r.fgts_multa)
        self.card_multa_gov.set_valor(r.fgts_multa_gov)

        # Tabela verbas
        self.tbl_verbas.setRowCount(len(r.verbas))
        for i, v in enumerate(r.verbas):
            cor = C['amber'] if v.valor == 0 else (C['green'] if v.valor > 0 else C['red'])
            self.tbl_verbas.setItem(i, 0, cell(v.descricao, Qt.AlignmentFlag.AlignLeft))
            self.tbl_verbas.setItem(i, 1, cell(brl(v.valor), bold=True, color=cor))
            self.tbl_verbas.setItem(i, 2, cell(v.observacao, Qt.AlignmentFlag.AlignLeft, color=C['muted']))

        # Linha de total bruto
        row_tot = self.tbl_verbas.rowCount()
        self.tbl_verbas.insertRow(row_tot)
        item_tot = cell("TOTAL BRUTO", Qt.AlignmentFlag.AlignLeft, bold=True)
        item_tot.setBackground(QColor(C['border']))
        item_val = cell(brl(r.total_bruto), bold=True, color=C['text'])
        item_val.setBackground(QColor(C['border']))
        item_obs = cell("", color=C['muted'])
        item_obs.setBackground(QColor(C['border']))
        self.tbl_verbas.setItem(row_tot, 0, item_tot)
        self.tbl_verbas.setItem(row_tot, 1, item_val)
        self.tbl_verbas.setItem(row_tot, 2, item_obs)

        # Tabela deduções
        self.tbl_ded.setRowCount(len(r.deducoes))
        for i, d in enumerate(r.deducoes):
            self.tbl_ded.setItem(i, 0, cell(d.descricao, Qt.AlignmentFlag.AlignLeft))
            self.tbl_ded.setItem(i, 1, cell(brl(d.valor), bold=True, color=C['red']))
            self.tbl_ded.setItem(i, 2, cell(d.observacao, Qt.AlignmentFlag.AlignLeft, color=C['muted']))

        # Tabela FGTS
        if r.resultado_fgts:
            dets = r.resultado_fgts.detalhes_por_mes
            self.tbl_fgts.setRowCount(len(dets))
            for i, det in enumerate(dets):
                self.tbl_fgts.setItem(i, 0, cell(det.data.strftime("%b/%Y")))
                self.tbl_fgts.setItem(i, 1, cell(brl(det.salario)))
                self.tbl_fgts.setItem(i, 2, cell(brl(det.deposito)))
                self.tbl_fgts.setItem(i, 3, cell(brl(det.rendimento), color=C['green'] if det.rendimento > 0 else None))
                self.tbl_fgts.setItem(i, 4, cell(brl(det.saldo_final), bold=True))
                self.tbl_fgts.setItem(i, 5, cell(det.observacao, Qt.AlignmentFlag.AlignLeft, color=C['muted']))

        self.tabs.setCurrentIndex(0)

    def _erro(self, msg: str):
        self.btn_calc.setText("Calcular Rescisão")
        self.btn_calc.setDisabled(False)
        QMessageBox.critical(self, "Erro no cálculo", f"Ocorreu um erro:\n\n{msg}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    janela = Janela()
    janela.show()
    sys.exit(_app.exec())