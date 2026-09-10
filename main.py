saldo = 0.0


def ler_valor(mensagem):
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))
            if valor <= 0:
                print("O valor precisa ser maior que zero.")
            else:
                return valor
        except ValueError:
            print("Digite um valor numerico valido.")


def depositar(valor):
    global saldo

    if valor <= 0:
        return False

    saldo += valor
    return True


def sacar(valor):
    global saldo

    if valor <= 0 or valor > saldo:
        return False

    saldo -= valor
    return True


def mostrar_menu():
    print("\n=== ByteBank ===")
    print("1 - Consultar saldo")
    print("2 - Depositar")
    print("3 - Sacar")
    print("0 - Sair")


def main():
    while True:
        mostrar_menu()
        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "1":
            print(f"Saldo: R$ {saldo:.2f}")
        elif opcao == "2":
            valor = ler_valor("Valor do deposito: R$ ")
            if depositar(valor):
                print("Deposito realizado.")
        elif opcao == "3":
            valor = ler_valor("Valor do saque: R$ ")
            if sacar(valor):
                print("Saque realizado.")
            else:
                print("Saldo insuficiente.")
        elif opcao == "0":
            print("Sessao encerrada.")
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main()
