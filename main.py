from datetime import *
import pandas as pd
import Verificador_Salario
from dateutil.relativedelta import relativedelta


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
    print(f"Taxa TR do mês de {mes} foi de: {taxa_tr}")

    print(f"Rendimento Da Taxa TR: R$ {round(fgts * taxa_tr_float, 2)}")
    print(f"Rendimento Do Salário: R$ {round(fgts * taxa_rendimento, 2)}")

    return (fgts * taxa_tr_float) + (fgts * taxa_rendimento)

def Calcular_FGTS(periodo_inicial, periodo_final, lista_salarios):
    salario_utilizado = Verificador_Salario.Verificar(periodo_inicial, lista_salarios)
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    #meses_trabalhados = ((periodo_final - periodo_inicial) / 30).days
    diferença = relativedelta(periodo_final, periodo_inicial)
    meses_trabalhados = (diferença.years * 12) + diferença.months
    print(f"Meses Trabalhados: {meses_trabalhados}\n")

    fgts = 0
    contador_meses = 0

    while meses_trabalhados >= contador_meses:
        print(f"Data: {periodo_inicial}")
        mes = meses[periodo_inicial.month - 1]
        data_para_tabela = periodo_inicial

        if periodo_inicial.day > 1 and contador_meses == 0:
            print("Iniciando Calculo para dias quebrados no periodo inicial")
            fgts_diario = (salario_utilizado * 0.08) / 30
            diferenca_dias = 31 - periodo_inicial.day
            print(f"Diferença INICIAL de: {diferenca_dias} dias")
            fgts = fgts_diario * diferenca_dias
            print(f"O valor da diferença INICIAL de {diferenca_dias} dias é de R$ {round(fgts, 2)}")
        else:
            if meses_trabalhados == contador_meses:
                if periodo_final.day > 1:
                    print("Iniciando Calculo para dias quebrados no periodo FINAL\n")
                    print(f"Valor do fgts para o ultimo mês: R$ {round(fgts, 2)}")
                    fgts_diario = 0
                    diferenca_dias = 0
                    fgts_diario = (salario_utilizado * 0.08) / 30
                    diferenca_dias = 31 - periodo_final.day
                    print(f"Diferença de fianal: {diferenca_dias} dias")
                    fgts = fgts + (fgts_diario * diferenca_dias)
                    print(f"O valor da diferença FINAL de {diferenca_dias} dias é de R$ {round(fgts_diario * diferenca_dias, 2)}")
                    print(f"Valor do fgts para o apos o ultimo mês: R$ {round(fgts, 2)}")
                else:
                    fgts = (0.08 * salario_utilizado) + fgts
            else:
                fgts = (0.08 * salario_utilizado) + fgts

        if mes == "Nov" or mes == "Dez":
            if contador_meses == 0:
                pass
            else:
                fgts_13 = 0
                fgts_13 = (salario_utilizado * 0.08) / 2
                print(f"Adicional do 13 salario sob o FGTS: R$ {round(fgts_13, 2)}")
                fgts = fgts + fgts_13


        if contador_meses == 0:
            pass
        else:
            credito_jam = Calcular_Rendimento(mes, fgts, data_para_tabela)
            print(f"Rendimento total: R$ {round(credito_jam, 2)}")
            fgts = (fgts + credito_jam) - 0.50

        print(f"Valor do FGTS no mês de {mes}: R$ {round(fgts, 2)}\n")
        contador_meses = contador_meses + 1
        periodo_inicial = periodo_inicial + relativedelta(months=+1)
    print(f"O valor total acumulado no FGTS é de: R$ {round(fgts, 2)}")




print("=============== Calculadora De Recisão ===============")


mes = "05/07/2024"
contador_salarios = 1
lista_salarios = []
quant_salarios = int(input("Quantidade de salários diferentes que já teve: "))

if quant_salarios == 0:
    lista_salarios = [
        {f"data de inicio do salario 0": "12/07/2024", f"data de fim do salario 0": "12/09/2024", f"salario 0": 1412},
        {f"data de inicio do salario 1": "12/09/2024", f"data de fim do salario 1": None, f"salario 1": 1510}]
    mes_formatado = datetime.strptime(mes, "%d/%m/%Y")

    Verificador_Salario.Verificar(mes_formatado, lista_salarios)

else:

    while quant_salarios >= contador_salarios:
        valor_salario = float(input(f"Digite o valor do salario {contador_salarios}: " ))
        data_inicio_salario = input("Informe a data que começou a receber este salário: ")
        data_fim_salario = input("Informe a data que terminou de receber este salário: ")

        data_inicio_salario_formatado = datetime.strptime(data_inicio_salario, "%d/%m/%Y")
        data_fim_salario_formatado = datetime.strptime(data_fim_salario, "%d/%m/%Y")

        lista_salarios.append({f"data de inicio do salario {quant_salarios}": data_inicio_salario_formatado, f"data de fim do salario {quant_salarios}": data_fim_salario_formatado, f"salario {quant_salarios}": valor_salario})

        contador_salarios = contador_salarios + 1

    Verificador_Salario.Verificar(mes, lista_salarios)

#print(lista_salarios)



#salario = float(input("Informe Seu Salário (utilizando . para separar casa decial): "))
#periodo_inicial = input("Informe Sua Data De Admissão: ")
#periodo_final = input("Informe Sua Data De Demissão: ")

#periodo_inicial_formatado = datetime.strptime(periodo_inicial, "%d/%m/%Y")
#periodo_final_formatado = datetime.strptime(periodo_final, "%d/%m/%Y")

#Calcular_FGTS(periodo_inicial_formatado, periodo_final_formatado, lista_salarios)



