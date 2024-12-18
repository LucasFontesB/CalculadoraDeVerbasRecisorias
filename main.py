from datetime import *
from bs4 import BeautifulSoup
import pandas as pd
from dateutil.relativedelta import relativedelta
import lxml

def Calcular_Rendimento(mes, fgts):
    tabelas_tr = pd.read_html("https://brasilindicadores.com.br/tr")
    tabela_selecionada = tabelas_tr[0]
    tabela_filtrada = tabela_selecionada[["Mês de referência", "TR no mês"]]
    taxa_rendimento = 0.0025
    taxa_tr = None
    taxa_tr_float = 0

    if mes == "JANEIRO":
        taxa_tr = tabela_filtrada.loc[0, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "FEVEREIRO":
        taxa_tr = tabela_filtrada.loc[1, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "MARÇO":
        taxa_tr = tabela_filtrada.loc[2, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "ABRIL":
        taxa_tr = tabela_filtrada.loc[3, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "MAIO":
        taxa_tr = tabela_filtrada.loc[4, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "JUNHO":
        taxa_tr = tabela_filtrada.loc[5, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "JULHO":
        taxa_tr = tabela_filtrada.loc[6, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "AGOSTO":
        taxa_tr = tabela_filtrada.loc[7, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "SETEMBRO":
        taxa_tr = tabela_filtrada.loc[8, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "OUTUBRO":
        taxa_tr = tabela_filtrada.loc[9, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "NOVEMBRO":
        taxa_tr = tabela_filtrada.loc[10, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    if mes == "DEZEMBRO":
        taxa_tr = tabela_filtrada.loc[11, "TR no mês"]
        taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100

    return (fgts * taxa_tr_float) + (fgts * taxa_rendimento)

def Calcular_FGTS(periodo_inicial, periodo_final):
    meses = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    #meses_trabalhados = ((periodo_final - periodo_inicial) / 30).days#
    diferença = relativedelta(periodo_final, periodo_inicial)
    meses_trabalhados = (diferença.years * 12) + diferença.months
    print(f"Meses Trabalhados: {meses_trabalhados}")

    fgts = 0
    contador_meses = 1

    while contador_meses <= meses_trabalhados:
        mes = None
        print(f"Data: {periodo_inicial}\n")
        pular_mes = timedelta(31)
        mes = meses[periodo_inicial.month - 1]
        fgts = (0.08 * salario) + fgts
        credito_jam = Calcular_Rendimento(mes, fgts)
        print(f"Crédito de JAM: R$ {round(credito_jam, 2)}")
        print(f"Rendimento: R$ {round(fgts*0.0025, 2)}")
        print(f"Rendimento total: R$ {round(credito_jam + (fgts * 0.0025), 2)}")
        fgts = (fgts + credito_jam) - 0.33
        print(f"Valor do FGTS no mês de {mes}: R$ {round(fgts, 2)}\n")
        contador_meses = contador_meses + 1
        periodo_inicial = periodo_inicial + relativedelta(months=+1)
    print(f"O valor total acumulado no FGTS é de: R$ {round(fgts, 2)}")

print("=============== Calculadora De Recisão ===============")

salario = float(input("Informe Seu Salário (utilizando . para separar casa decial): "))
periodo_inicial = input("Informe Sua Data De Admissão: ")
periodo_final = input("Informe Sua Data De Demissão: ")

periodo_inicial_formatado = datetime.strptime(periodo_inicial, "%d/%m/%Y")
periodo_final_formatado = datetime.strptime(periodo_final, "%d/%m/%Y")

Calcular_FGTS(periodo_inicial_formatado, periodo_final_formatado)