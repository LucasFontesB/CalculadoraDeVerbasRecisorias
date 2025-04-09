from datetime import *

def Verificar(mes, lista_salarios):
    print("Verificando Salário...")
    salario = 0
    cont = 0
    for salarios in lista_salarios:
        print(f"Lista de Salarios {cont}:")

        data_inicio = salarios.get(f"data de inicio do salario {cont}")
        print(data_inicio)

        data_termino = salarios.get(f"data de fim do salario {cont}")
        if data_termino == None:
            data_termino = datetime.now()
            data_termino_formatada = datetime.strftime(data_termino, "%d/%m/%Y")
            print(data_termino_formatada)
        else:
            print(data_termino)

        salario_periodo = salarios.get(f"salario {cont}")
        print(salario_periodo)

        cont = cont + 1
        break

    return salario