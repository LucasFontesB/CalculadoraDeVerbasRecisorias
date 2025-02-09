from datetime import *
from bs4 import BeautifulSoup
import pandas as pd
from dateutil.relativedelta import relativedelta
import lxml

def Calcular_Rendimento(mes, fgts, data_para_tabela):
    tabelas_tr = pd.read_html("https://brasilindicadores.com.br/tr")
    tabela_selecionada = None
    #if data_para_tabela.year == 2025:
        #tabela_selecionada = tabelas_tr[0]
        #print("Utilizando Tabela de 2025")
    #elif data_para_tabela.year == 2024:
        #tabela_selecionada = tabelas_tr[1]
        #print("Utilizando Tabela de 2024")
    #elif data_para_tabela.year == 2024:
        #tabela_selecionada = tabelas_tr[1]

    tabela_selecionada = tabelas_tr[2]

    tabela_selecionada.set_index("Ano", inplace=True)

    tabela_selecionada.index = tabela_selecionada.index.astype(str)

    ano = str(data_para_tabela.year)

    tabela_selecionada = tabela_selecionada.iloc[:, :-1]
    taxa_rendimento = 0.0025
    taxa_tr = None
    taxa_tr_float = 0

    #meses = {"Jan": 0, "Fev": 1, "Mar": 2, "Abr": 3, "Mai": 4, "Jun": 5, "Jul": 6, "Ago": 7, "Set": 8, "Out": 9, "Nov": 10, "Dez": 11}
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    taxa_tr = tabela_selecionada.loc[ano, mes]
    taxa_tr_float = float(taxa_tr.replace("%", "").replace(",", ".")) / 100
    #print(f"Taxa TR do mês de {mes} foi de: {taxa_tr}")

    #print(f"Rendimento Da Taxa TR: R$ {round(fgts * taxa_tr_float, 2)}")
    #print(f"Rendimento Do Salário: R$ {round(fgts * taxa_rendimento, 2)}")

    return (fgts * taxa_tr_float) + (fgts * taxa_rendimento)

def Calcular_FGTS(periodo_inicial, periodo_final):
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    #meses_trabalhados = ((periodo_final - periodo_inicial) / 30).days
    diferença = relativedelta(periodo_final, periodo_inicial)
    meses_trabalhados = (diferença.years * 12) + diferença.months
    #print(f"Meses Trabalhados: {meses_trabalhados}")

    fgts = 0
    contador_meses = 0

    while meses_trabalhados >= contador_meses:
        #print(f"Data: {periodo_inicial}")
        mes = meses[periodo_inicial.month - 1]
        data_para_tabela = periodo_inicial

        if periodo_inicial.day > 1 and contador_meses == 0:
            fgts_diario = (salario * 0.08) / 30
            diferenca_dias = 31 - periodo_inicial.day
            #print(f"Diferença de: {diferenca_dias} dias")
            fgts = fgts_diario * diferenca_dias
            #print(f"O valor da diferença de {diferenca_dias} dias é de R$ {round(fgts, 2)}")
        else:
            fgts = (0.08 * salario) + fgts

        if contador_meses == 0:
            pass
        else:
            credito_jam = Calcular_Rendimento(mes, fgts, data_para_tabela)
            #print(f"Rendimento total: R$ {round(credito_jam, 2)}")
            fgts = (fgts + credito_jam) - 0.50

        #print(f"Valor do FGTS no mês de {mes}: R$ {round(fgts, 2)}\n")
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