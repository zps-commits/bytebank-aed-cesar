from decimal import Decimal, ROUND_HALF_UP
from math import isfinite


contas = [
    {
        "numero": "1001",
        "nome": "Ana",
        "cpf": "11111111111",
        "chave_pix": "ana@email.com",
        "saldo": 1000.0,
        "historico": [],
        "cofrinhos": {},
        "limite_credito": 1000.0,
        "limite_disponivel": 1000.0,
        "saldo_fatura": 0.0,
        "compras_credito": [],
    },
    {
        "numero": "1002",
        "nome": "Bruno",
        "cpf": "22222222222",
        "chave_pix": "81999990000",
        "saldo": 750.0,
        "historico": [],
        "cofrinhos": {},
        "limite_credito": 1000.0,
        "limite_disponivel": 1000.0,
        "saldo_fatura": 0.0,
        "compras_credito": [],
    },
]

LIMITE_SAQUE = 500.0
TAXA_RENDIMENTO = 0.005


def arredondar_valor(valor):
    return float(
        Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def ler_valor(mensagem):
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))
            if not isfinite(valor) or valor <= 0:
                print("O valor precisa ser maior que zero.")
            else:
                return arredondar_valor(valor)
        except ValueError:
            print("Digite um valor numerico valido.")


def formatar_moeda(valor):
    valor_formatado = f"{valor:,.2f}"
    valor_formatado = valor_formatado.replace(",", "X").replace(".", ",")
    return "R$ " + valor_formatado.replace("X", ".")


def normalizar_cpf(cpf):
    return "".join(caractere for caractere in cpf if caractere.isdigit())


def registrar_transacao(conta, tipo, valor, movimento, descricao):
    conta["historico"].append(
        {
            "tipo": tipo,
            "valor": arredondar_valor(valor),
            "movimento": movimento,
            "descricao": descricao,
            "saldo_apos": arredondar_valor(conta["saldo"]),
        }
    )


def depositar(conta, valor):
    if not isfinite(valor):
        return False

    valor = arredondar_valor(valor)
    if valor <= 0:
        return False

    conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
    registrar_transacao(conta, "Deposito", valor, "entrada", "Deposito em conta")
    return True


def sacar(conta, valor):
    if not isfinite(valor):
        return False

    valor = arredondar_valor(valor)
    if valor <= 0 or valor > LIMITE_SAQUE or valor > conta["saldo"]:
        return False

    conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
    registrar_transacao(conta, "Saque", valor, "saida", "Saque em conta")
    return True


def buscar_conta(identificador):
    cpf = normalizar_cpf(identificador)

    for conta in contas:
        if conta["numero"] == identificador or conta["cpf"] == cpf:
            return conta
    return None


def buscar_por_pix(chave_pix):
    for conta in contas:
        if conta["chave_pix"] == chave_pix:
            return conta
    return None


def cadastrar_conta(nome, cpf, chave_pix):
    nome = nome.strip()
    cpf = normalizar_cpf(cpf)
    chave_pix = chave_pix.strip()

    if not nome or len(cpf) != 11 or not chave_pix:
        return None

    if buscar_conta(cpf) is not None or buscar_por_pix(chave_pix) is not None:
        return None

    maior_numero = max((int(conta["numero"]) for conta in contas), default=1000)
    conta = {
        "numero": str(maior_numero + 1),
        "nome": nome,
        "cpf": cpf,
        "chave_pix": chave_pix,
        "saldo": 0.0,
        "historico": [],
        "cofrinhos": {},
        "limite_credito": 500.0,
        "limite_disponivel": 500.0,
        "saldo_fatura": 0.0,
        "compras_credito": [],
    }
    contas.append(conta)
    return conta


def transferir_pix(origem, chave_destino, valor):
    destino = buscar_por_pix(chave_destino)

    if not isfinite(valor):
        return False

    valor = arredondar_valor(valor)
    if destino is None or destino is origem or valor <= 0 or valor > origem["saldo"]:
        return False

    origem["saldo"] = arredondar_valor(origem["saldo"] - valor)
    destino["saldo"] = arredondar_valor(destino["saldo"] + valor)
    registrar_transacao(
        origem,
        "PIX enviado",
        valor,
        "saida",
        f"PIX para a conta {destino['numero']}",
    )
    registrar_transacao(
        destino,
        "PIX recebido",
        valor,
        "entrada",
        f"PIX recebido da conta {origem['numero']}",
    )
    return True


def criar_cofrinho(conta, nome):
    nome = nome.strip()

    if not nome or nome in conta["cofrinhos"]:
        return False

    conta["cofrinhos"][nome] = 0.0
    return True


def guardar_no_cofrinho(conta, nome, valor):
    if not isfinite(valor):
        return False

    valor = arredondar_valor(valor)
    if nome not in conta["cofrinhos"] or valor <= 0 or valor > conta["saldo"]:
        return False

    conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
    conta["cofrinhos"][nome] = arredondar_valor(
        conta["cofrinhos"][nome] + valor
    )
    registrar_transacao(
        conta,
        "Valor guardado",
        valor,
        "saida",
        f"Transferencia para o cofrinho {nome}",
    )
    return True


def resgatar_do_cofrinho(conta, nome, valor):
    if not isfinite(valor):
        return False

    valor = arredondar_valor(valor)
    if nome not in conta["cofrinhos"] or valor <= 0:
        return False
    if valor > conta["cofrinhos"][nome]:
        return False

    conta["cofrinhos"][nome] = arredondar_valor(
        conta["cofrinhos"][nome] - valor
    )
    conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
    registrar_transacao(
        conta,
        "Resgate de cofrinho",
        valor,
        "entrada",
        f"Resgate do cofrinho {nome}",
    )
    return True


def simular_rendimento(conta, meses):
    if meses <= 0 or not conta["cofrinhos"]:
        return False

    for nome, saldo_cofrinho in conta["cofrinhos"].items():
        rendimento = arredondar_valor(
            saldo_cofrinho * TAXA_RENDIMENTO * meses
        )
        if rendimento > 0:
            conta["cofrinhos"][nome] = arredondar_valor(
                saldo_cofrinho + rendimento
            )
            registrar_transacao(
                conta,
                "Rendimento de cofrinho",
                rendimento,
                "entrada",
                f"Rendimento simulado no cofrinho {nome}",
            )
    return True


def mostrar_cofrinhos(conta):
    print("\n=== Cofrinhos ===")

    if not conta["cofrinhos"]:
        print("Nenhum cofrinho criado.")
        return

    total = 0.0
    for nome, valor in conta["cofrinhos"].items():
        print(f"{nome}: {formatar_moeda(valor)}")
        total += valor
    print(f"Total guardado: {formatar_moeda(total)}")


def comprar_no_credito(conta, valor, estabelecimento):
    estabelecimento = estabelecimento.strip()

    if not isfinite(valor):
        return False

    valor = arredondar_valor(valor)
    if not estabelecimento or valor <= 0 or valor > conta["limite_disponivel"]:
        return False

    conta["limite_disponivel"] = arredondar_valor(
        conta["limite_disponivel"] - valor
    )
    conta["saldo_fatura"] = arredondar_valor(conta["saldo_fatura"] + valor)
    conta["compras_credito"].append(
        {"estabelecimento": estabelecimento, "valor": valor}
    )
    registrar_transacao(
        conta,
        "Compra no credito",
        valor,
        "credito",
        f"Compra em {estabelecimento}",
    )
    return True


def pagar_fatura(conta):
    valor = arredondar_valor(conta["saldo_fatura"])

    if valor <= 0 or valor > conta["saldo"]:
        return False

    conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
    conta["limite_disponivel"] = min(
        conta["limite_credito"],
        arredondar_valor(conta["limite_disponivel"] + valor),
    )
    conta["saldo_fatura"] = 0.0
    conta["compras_credito"].clear()
    registrar_transacao(
        conta,
        "Pagamento de fatura",
        valor,
        "saida",
        "Pagamento integral da fatura do cartao",
    )
    return True


def mostrar_fatura(conta):
    print("\n=== Fatura do cartao ===")

    if not conta["compras_credito"]:
        print("Nenhuma compra no credito.")
    else:
        for indice, compra in enumerate(conta["compras_credito"], start=1):
            print(
                f"{indice}. {compra['estabelecimento']}: "
                f"{formatar_moeda(compra['valor'])}"
            )

    print(f"Total da fatura: {formatar_moeda(conta['saldo_fatura'])}")
    print(f"Limite total: {formatar_moeda(conta['limite_credito'])}")
    print(f"Limite disponivel: {formatar_moeda(conta['limite_disponivel'])}")


def mostrar_extrato(conta):
    print("\n=== Historico de transacoes ===")

    if not conta["historico"]:
        print("Nenhuma transacao realizada nesta sessao.")
    else:
        for indice, transacao in enumerate(conta["historico"], start=1):
            sinal = "+" if transacao["movimento"] == "entrada" else "-"
            print(
                f"{indice}. {transacao['tipo']} | "
                f"{sinal} {formatar_moeda(transacao['valor'])} | "
                f"Saldo: {formatar_moeda(transacao['saldo_apos'])}"
            )
            print(f"   {transacao['descricao']}")

    print(f"Saldo atual: {formatar_moeda(conta['saldo'])}")


def mostrar_menu():
    print("\n=== ByteBank ===")
    print("1 - Consultar saldo")
    print("2 - Depositar")
    print("3 - Sacar")
    print("4 - Cadastrar cliente")
    print("5 - Transferir via PIX")
    print("6 - Consultar historico de transacoes")
    print("7 - Criar cofrinho")
    print("8 - Guardar no cofrinho")
    print("9 - Resgatar do cofrinho")
    print("10 - Simular rendimento")
    print("11 - Consultar cofrinhos")
    print("12 - Comprar no credito")
    print("13 - Consultar fatura")
    print("14 - Pagar fatura")
    print("0 - Sair")


def main():
    identificador = input("Numero da conta ou CPF: ").strip()
    conta = buscar_conta(identificador)

    if conta is None:
        print("Conta nao encontrada.")
        return

    while True:
        mostrar_menu()
        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "1":
            print(f"Saldo: {formatar_moeda(conta['saldo'])}")
        elif opcao == "2":
            valor = ler_valor("Valor do deposito: R$ ")
            if depositar(conta, valor):
                print("Deposito realizado.")
        elif opcao == "3":
            valor = ler_valor("Valor do saque: R$ ")
            if sacar(conta, valor):
                print("Saque realizado.")
            else:
                print(
                    "Saque nao permitido. Verifique o saldo e o limite de "
                    f"{formatar_moeda(LIMITE_SAQUE)} por operacao."
                )
        elif opcao == "4":
            nome = input("Nome: ").strip()
            cpf = input("CPF: ").strip()
            chave_pix = input("Chave PIX: ").strip()
            nova_conta = cadastrar_conta(nome, cpf, chave_pix)
            if nova_conta is None:
                print("Dados invalidos, CPF ou chave PIX ja cadastrados.")
            else:
                print(f"Conta criada: {nova_conta['numero']}")
        elif opcao == "5":
            chave_destino = input("Chave PIX de destino: ").strip()
            valor = ler_valor("Valor da transferencia: R$ ")
            if transferir_pix(conta, chave_destino, valor):
                print("PIX realizado.")
            else:
                print("Nao foi possivel realizar o PIX.")
        elif opcao == "6":
            mostrar_extrato(conta)
        elif opcao == "7":
            nome = input("Nome do cofrinho: ").strip()
            if criar_cofrinho(conta, nome):
                print("Cofrinho criado.")
            else:
                print("Nome invalido ou cofrinho ja existente.")
        elif opcao == "8":
            nome = input("Nome do cofrinho: ").strip()
            valor = ler_valor("Valor para guardar: R$ ")
            if guardar_no_cofrinho(conta, nome, valor):
                print("Valor guardado.")
            else:
                print("Cofrinho inexistente ou saldo insuficiente.")
        elif opcao == "9":
            nome = input("Nome do cofrinho: ").strip()
            valor = ler_valor("Valor para resgatar: R$ ")
            if resgatar_do_cofrinho(conta, nome, valor):
                print("Valor resgatado.")
            else:
                print("Cofrinho inexistente ou saldo insuficiente.")
        elif opcao == "10":
            try:
                meses = int(input("Quantidade de meses: "))
                if simular_rendimento(conta, meses):
                    print("Rendimento simulado com sucesso.")
                else:
                    print("Crie um cofrinho e informe uma quantidade valida.")
            except ValueError:
                print("Digite um numero inteiro de meses.")
        elif opcao == "11":
            mostrar_cofrinhos(conta)
        elif opcao == "12":
            estabelecimento = input("Estabelecimento: ").strip()
            valor = ler_valor("Valor da compra: R$ ")
            if comprar_no_credito(conta, valor, estabelecimento):
                print("Compra aprovada.")
            else:
                print("Compra recusada.")
        elif opcao == "13":
            mostrar_fatura(conta)
        elif opcao == "14":
            if pagar_fatura(conta):
                print("Fatura paga com sucesso.")
            else:
                print("Nao foi possivel pagar a fatura.")
        elif opcao == "0":
            print("Sessao encerrada.")
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main()
