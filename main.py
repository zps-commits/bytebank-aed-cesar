from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from calendar import monthrange
from datetime import date, datetime, timedelta
import re


contas = []

LIMITE_SAQUE = 500.0
TAXA_RENDIMENTO = 0.005
TAXAS_CAMBIO = {"USD": 5.50, "EUR": 6.00, "BTC": 350000.0}
CATEGORIAS = ["Alimentacao", "Transporte", "Lazer", "Contas", "Educacao", "Saude", "Outros"]
GASTOS = {"Saque", "PIX enviado", "Compra no credito", "Pagamento agendado", "Pagamento de parcela"}


def normalizar_cpf(cpf):
    return "".join(caractere for caractere in str(cpf) if caractere.isdigit())


def arredondar_valor(valor):
    return float(
        Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def senha_valida(pin):
    return isinstance(pin, str) and len(pin) == 4 and pin.isascii() and pin.isdigit()


def hash_pin(pin):
    return sha256(pin.encode("utf-8")).hexdigest()


def criar_conta(numero, nome, cpf, chave_pix, saldo=0.0, limite_credito=1000.0, pin=None):
    return {
        "numero": str(numero),
        "nome": nome,
        "cpf": normalizar_cpf(cpf),
        "chave_pix": chave_pix,
        "pin_hash": hash_pin(pin) if senha_valida(pin) else None,
        "saldo": arredondar_valor(saldo),
        "historico": [],
        "pilha_estornos": [],
        "fila_pagamentos": [],
        "cofrinhos": {},
        "limite_credito": arredondar_valor(limite_credito),
        "limite_disponivel": arredondar_valor(limite_credito),
        "saldo_fatura": 0.0,
        "compras_credito": [],
        "saldos_moedas": {moeda: 0.0 for moeda in TAXAS_CAMBIO},
        "bytepoints": 0,
        "emprestimos": [],
        "orcamento_mensal": 2000.0,
    }


def preparar_conta(conta):
    conta.setdefault("pilha_estornos", [])
    conta.setdefault("fila_pagamentos", [])
    conta.setdefault("cofrinhos", {})
    conta.setdefault("limite_credito", 500.0)
    conta.setdefault("limite_disponivel", conta["limite_credito"])
    conta.setdefault("saldo_fatura", 0.0)
    conta.setdefault("compras_credito", [])
    conta.setdefault("saldos_moedas", {moeda: 0.0 for moeda in TAXAS_CAMBIO})
    conta.setdefault("bytepoints", 0)
    conta.setdefault("emprestimos", [])
    conta.setdefault("orcamento_mensal", 2000.0)
    return conta


contas.extend(
    [
        criar_conta("1001", "Ana", "11111111111", "ana@email.com", 1000.0, pin="1234"),
        criar_conta("1002", "Bruno", "22222222222", "81999990000", 750.0, pin="4321"),
    ]
)


def normalizar_categoria(categoria):
    categoria = str(categoria or "Outros").strip().title()
    return categoria if categoria in CATEGORIAS else "Outros"


def validar_valor(valor):
    try:
        texto = str(valor).strip()
        if "," in texto:
            if "." in texto and not re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d{1,2}", texto):
                return None
            texto = texto.replace(".", "").replace(",", ".")
        elif (isinstance(valor, str) and re.fullmatch(r"[1-9]\d{0,2}(?:\.\d{3})+", texto)):
            texto = texto.replace(".", "")
        valor = Decimal(texto)
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not valor.is_finite() or not Decimal("0.01") <= valor <= Decimal("1000000000000"):
        return None
    if valor != valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):
        return None
    return float(valor) if valor > 0 else None


def validar_quantidade(valor):
    try:
        quantidade = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not quantidade.is_finite() or not Decimal("0.00000001") <= quantidade <= Decimal("1000000000000"):
        return None
    quantidade = quantidade.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    return float(quantidade)


def formatar_moeda(valor):
    valor_formatado = f"{valor:,.2f}"
    valor_formatado = valor_formatado.replace(",", "X").replace(".", ",")
    return "R$ " + valor_formatado.replace("X", ".")


def ler_valor(mensagem):
    while True:
        valor = validar_valor(input(mensagem))
        if valor is not None:
            return valor
        print("Valor invalido. Digite de R$ 0,01 ate R$ 1.000.000.000.000,00, com no maximo 2 casas decimais.")


def ler_quantidade(mensagem):
    while True:
        quantidade = validar_quantidade(input(mensagem))
        if quantidade is not None:
            return quantidade
        print("Digite uma quantidade maior que zero.")


def ler_categoria():
    while True:
        print("Escolha uma categoria:")
        for indice, categoria in enumerate(CATEGORIAS, start=1):
            print(f"{indice} - {categoria}")
        opcao = input("Numero da categoria: ").strip()
        if opcao in [str(indice) for indice in range(1, len(CATEGORIAS) + 1)]:
            return CATEGORIAS[int(opcao) - 1]
        print("Categoria invalida. Digite um numero da lista.")


def buscar_conta(identificador):
    identificador = str(identificador).strip()
    cpf = normalizar_cpf(identificador)
    for conta in contas:
        preparar_conta(conta)
        if conta["numero"] == identificador or conta["cpf"] == cpf:
            return conta
    return None


def buscar_por_pix(chave_pix):
    chave_pix = str(chave_pix).strip()
    for conta in contas:
        preparar_conta(conta)
        if conta["chave_pix"] == chave_pix:
            return conta
    return None


def autenticar_conta(identificador, pin):
    conta = buscar_conta(identificador)
    if conta is None or not senha_valida(pin):
        return None
    return conta if conta["pin_hash"] == hash_pin(pin) else None


def erro_cadastro(nome, cpf, chave_pix, pin):
    if not str(nome).strip():
        return "Digite seu nome para criar a conta."
    cpf = str(cpf).strip()
    if not (re.fullmatch(r"[0-9]{11}", cpf) or re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf)):
        return "CPF invalido. Digite 11 numeros ou use o formato 000.000.000-00."
    if not str(chave_pix).strip():
        return "Digite uma chave PIX para criar a conta."
    if not senha_valida(pin):
        return "PIN invalido. Digite exatamente 4 numeros."
    if buscar_conta(normalizar_cpf(cpf)) is not None:
        return "CPF ja cadastrado. Entre na conta existente."
    if buscar_por_pix(chave_pix) is not None:
        return "Chave PIX ja cadastrada. Escolha outra chave."
    return None


def cadastrar_conta(nome, cpf, chave_pix, pin=None):
    if erro_cadastro(nome, cpf, chave_pix, pin) is not None:
        return None
    nome = str(nome).strip()
    cpf = normalizar_cpf(cpf)
    chave_pix = str(chave_pix).strip()
    maior_numero = max((int(conta["numero"]) for conta in contas), default=1000)
    conta = criar_conta(maior_numero + 1, nome, cpf, chave_pix, pin=pin)
    contas.append(conta)
    return conta


def registrar_transacao(
    conta,
    tipo,
    valor,
    movimento,
    descricao,
    categoria="Outros",
    estorno=None,
    fluxo_brl=True,
):
    transacao = {
        "tipo": tipo,
        "valor": arredondar_valor(valor),
        "movimento": movimento,
        "descricao": descricao,
        "categoria": normalizar_categoria(categoria),
        "saldo_apos": arredondar_valor(conta["saldo"]),
        "estornado": False,
        "data": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fluxo_brl": fluxo_brl,
    }
    conta["historico"].append(transacao)
    if estorno is not None:
        conta["pilha_estornos"].append({"transacao": transacao, "acao": estorno})
    return transacao


def depositar(conta, valor):
    valor = validar_valor(valor)
    if valor is None:
        return False
    conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
    registrar_transacao(
        conta,
        "Deposito",
        valor,
        "entrada",
        "Deposito em conta",
        estorno={"tipo": "deposito", "valor": valor},
    )
    return True


def sacar(conta, valor, categoria="Outros"):
    valor = validar_valor(valor)
    if valor is None or valor > LIMITE_SAQUE or valor > conta["saldo"]:
        return False
    pontos = int(valor // 10)
    conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
    conta["bytepoints"] += pontos
    registrar_transacao(
        conta,
        "Saque",
        valor,
        "saida",
        "Saque em conta",
        categoria,
        estorno={"tipo": "saque", "valor": valor, "pontos": pontos},
    )
    return True


def transferir_pix(origem, chave_destino, valor, categoria="Outros"):
    destino = buscar_por_pix(chave_destino)
    valor = validar_valor(valor)
    if destino is None or destino is origem or valor is None or valor > origem["saldo"]:
        return False
    pontos = int(valor // 10)
    origem["saldo"] = arredondar_valor(origem["saldo"] - valor)
    destino["saldo"] = arredondar_valor(destino["saldo"] + valor)
    origem["bytepoints"] += pontos
    registrar_transacao(
        origem,
        "PIX enviado",
        valor,
        "saida",
        f"PIX para a conta {destino['numero']}",
        categoria,
        estorno={
            "tipo": "pix_enviado",
            "valor": valor,
            "pontos": pontos,
            "destino": destino,
        },
    )
    recebido = registrar_transacao(
        destino,
        "PIX recebido",
        valor,
        "entrada",
        f"PIX recebido da conta {origem['numero']}",
        "Outros",
    )
    origem["pilha_estornos"][-1]["acao"]["recebimento"] = recebido
    return True


def buscar_nome_cofrinho(conta, nome):
    nome = str(nome).strip().casefold()
    return next((chave for chave in conta["cofrinhos"] if chave.casefold() == nome), None)


def criar_cofrinho(conta, nome, valor_inicial=0):
    nome = str(nome).strip()
    if not nome or buscar_nome_cofrinho(conta, nome) is not None:
        return False
    if valor_inicial != 0:
        valor_inicial = validar_valor(valor_inicial)
        if valor_inicial is None or valor_inicial > conta["saldo"]:
            return False
    conta["cofrinhos"][nome] = 0.0
    if valor_inicial and not guardar_no_cofrinho(conta, nome, valor_inicial):
        del conta["cofrinhos"][nome]
        return False
    return True


def guardar_no_cofrinho(conta, nome, valor):
    nome = buscar_nome_cofrinho(conta, nome)
    valor = validar_valor(valor)
    if nome is None or valor is None or valor > conta["saldo"]:
        return False
    conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
    conta["cofrinhos"][nome] = arredondar_valor(conta["cofrinhos"][nome] + valor)
    registrar_transacao(
        conta,
        "Valor guardado",
        valor,
        "saida",
        f"Transferencia para o cofrinho {nome}",
        "Outros",
        estorno={"tipo": "guardar_cofrinho", "nome": nome, "valor": valor},
    )
    return True


def resgatar_do_cofrinho(conta, nome, valor):
    nome = buscar_nome_cofrinho(conta, nome)
    valor = validar_valor(valor)
    if nome is None or valor is None:
        return False
    if valor > conta["cofrinhos"][nome]:
        return False
    conta["cofrinhos"][nome] = arredondar_valor(conta["cofrinhos"][nome] - valor)
    conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
    registrar_transacao(
        conta,
        "Resgate de cofrinho",
        valor,
        "entrada",
        f"Resgate do cofrinho {nome}",
        "Outros",
        estorno={"tipo": "resgatar_cofrinho", "nome": nome, "valor": valor},
    )
    return True


def simular_rendimento(conta, meses):
    try:
        if isinstance(meses, float) and not meses.is_integer():
            return None
        meses = int(meses)
    except (TypeError, ValueError, OverflowError):
        return None
    if meses <= 0 or not conta["cofrinhos"]:
        return None
    total = 0.0
    for nome, saldo_cofrinho in list(conta["cofrinhos"].items()):
        rendimento = arredondar_valor(saldo_cofrinho * TAXA_RENDIMENTO * meses)
        if rendimento > 0:
            total = arredondar_valor(total + rendimento)
            conta["cofrinhos"][nome] = arredondar_valor(saldo_cofrinho + rendimento)
            registrar_transacao(
                conta,
                "Rendimento de cofrinho",
                rendimento,
                "entrada",
                f"Rendimento simulado no cofrinho {nome}",
                "Outros",
                estorno={"tipo": "rendimento", "nome": nome, "valor": rendimento},
                fluxo_brl=False,
            )
    return total


def comprar_no_credito(conta, valor, estabelecimento, categoria="Outros"):
    valor = validar_valor(valor)
    estabelecimento = str(estabelecimento).strip()
    if valor is None or not estabelecimento or valor > conta["limite_disponivel"]:
        return False
    conta["limite_disponivel"] = arredondar_valor(conta["limite_disponivel"] - valor)
    conta["saldo_fatura"] = arredondar_valor(conta["saldo_fatura"] + valor)
    compra = {"estabelecimento": estabelecimento, "valor": valor, "categoria": normalizar_categoria(categoria)}
    conta["compras_credito"].append(compra)
    registrar_transacao(
        conta,
        "Compra no credito",
        valor,
        "credito",
        f"Compra em {estabelecimento}",
        categoria,
        estorno={"tipo": "compra_credito", "valor": valor, "compra": compra},
        fluxo_brl=False,
    )
    return True


def pagar_fatura(conta, categoria="Contas"):
    valor = arredondar_valor(conta["saldo_fatura"])
    if valor <= 0 or valor > conta["saldo"]:
        return False
    compras_anteriores = list(conta["compras_credito"])
    limite_anterior = conta["limite_disponivel"]
    conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
    conta["limite_disponivel"] = min(
        conta["limite_credito"], arredondar_valor(conta["limite_disponivel"] + valor)
    )
    conta["saldo_fatura"] = 0.0
    conta["compras_credito"].clear()
    registrar_transacao(
        conta,
        "Pagamento de fatura",
        valor,
        "saida",
        "Pagamento integral da fatura do cartao",
        categoria,
        estorno={
            "tipo": "pagar_fatura",
            "valor": valor,
            "compras": compras_anteriores,
            "limite": limite_anterior,
        },
    )
    return True


def comprar_moeda_estrangeira(conta, moeda, valor_brl):
    moeda = str(moeda).upper().strip()
    valor_brl = validar_valor(valor_brl)
    if moeda not in TAXAS_CAMBIO or valor_brl is None or valor_brl > conta["saldo"]:
        return False
    quantidade = validar_quantidade(Decimal(str(valor_brl)) / Decimal(str(TAXAS_CAMBIO[moeda])))
    if quantidade is None:
        return False
    conta["saldo"] = arredondar_valor(conta["saldo"] - valor_brl)
    conta["saldos_moedas"][moeda] = round(conta["saldos_moedas"][moeda] + quantidade, 8)
    registrar_transacao(
        conta,
        f"Compra de {moeda}",
        valor_brl,
        "saida",
        f"Compra de {quantidade} {moeda}",
        "Outros",
        estorno={"tipo": "compra_moeda", "moeda": moeda, "brl": valor_brl, "quantidade": quantidade},
    )
    return True


def vender_moeda_estrangeira(conta, moeda, quantidade):
    moeda = str(moeda).upper().strip()
    quantidade = validar_quantidade(quantidade)
    if moeda not in TAXAS_CAMBIO or quantidade is None or quantidade > conta["saldos_moedas"][moeda]:
        return False
    valor_brl = arredondar_valor(quantidade * TAXAS_CAMBIO[moeda])
    if valor_brl <= 0:
        return False
    conta["saldos_moedas"][moeda] = round(conta["saldos_moedas"][moeda] - quantidade, 8)
    conta["saldo"] = arredondar_valor(conta["saldo"] + valor_brl)
    registrar_transacao(
        conta,
        f"Venda de {moeda}",
        valor_brl,
        "entrada",
        f"Venda de {quantidade} {moeda}",
        "Outros",
        estorno={"tipo": "venda_moeda", "moeda": moeda, "brl": valor_brl, "quantidade": quantidade},
    )
    return True


def consultar_pontos(conta):
    return conta["bytepoints"]


def resgatar_cashback(conta, pontos):
    try:
        pontos = int(pontos)
    except (TypeError, ValueError, OverflowError):
        return False
    if pontos <= 0 or pontos > conta["bytepoints"]:
        return False
    valor = arredondar_valor(pontos * 5 / 100)
    conta["bytepoints"] -= pontos
    conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
    registrar_transacao(
        conta,
        "Resgate de cashback",
        valor,
        "entrada",
        f"Resgate de {pontos} BytePoints",
        "Outros",
        estorno={"tipo": "cashback", "pontos": pontos, "valor": valor},
    )
    return True


def simular_emprestimo(conta, valor, parcelas):
    valor = validar_valor(valor)
    try:
        if isinstance(parcelas, float) and not parcelas.is_integer():
            return None
        parcelas = int(parcelas)
    except (TypeError, ValueError, OverflowError):
        return None
    limite = arredondar_valor(conta["saldo"] * 3)
    if valor is None or not 1 <= parcelas <= 360 or valor > limite:
        return None
    centavos = round(valor * 100)
    base, resto = divmod(centavos, parcelas)
    if base == 0:
        return None
    valores = [(base + (1 if indice < resto else 0)) / 100 for indice in range(parcelas)]
    valor_parcela = valores[0]
    return {
        "valor": valor,
        "parcelas": parcelas,
        "valor_parcela": valor_parcela,
        "limite_disponivel": limite,
        "valores_parcelas": valores,
    }


def contratar_emprestimo(conta, valor, parcelas, nome=""):
    simulacao = simular_emprestimo(conta, valor, parcelas)
    if simulacao is None:
        return False
    nome = str(nome).strip() or f"Emprestimo {len(conta['emprestimos']) + 1}"
    emprestimo = {
        "nome": nome,
        "valor_original": simulacao["valor"],
        "saldo_devedor": simulacao["valor"],
        "parcelas_restantes": simulacao["parcelas"],
        "valor_parcela": simulacao["valor_parcela"],
        "valores_parcelas": list(simulacao["valores_parcelas"]),
        "status": "aberto",
    }
    conta["emprestimos"].append(emprestimo)
    conta["saldo"] = arredondar_valor(conta["saldo"] + simulacao["valor"])
    registrar_transacao(
        conta,
        "Emprestimo contratado",
        simulacao["valor"],
        "entrada",
        f"{nome} em {simulacao['parcelas']} parcelas",
        "Outros",
        estorno={"tipo": "contratar_emprestimo", "emprestimo": emprestimo, "valor": simulacao["valor"]},
    )
    return True


def pagar_parcela_emprestimo(conta, emprestimo=None):
    if emprestimo is None:
        emprestimo = next(
            (item for item in conta["emprestimos"] if item["parcelas_restantes"] > 0), None
        )
    elif not any(item is emprestimo for item in conta["emprestimos"]):
        return False
    if emprestimo is None or emprestimo["parcelas_restantes"] <= 0:
        return False
    if emprestimo["valores_parcelas"][0] > conta["saldo"]:
        return False
    valor = emprestimo["valores_parcelas"][0]
    estado_anterior = {
        "saldo_devedor": emprestimo["saldo_devedor"],
        "parcelas_restantes": emprestimo["parcelas_restantes"],
        "status": emprestimo["status"],
        "valores_parcelas": list(emprestimo["valores_parcelas"]),
    }
    conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
    emprestimo["saldo_devedor"] = arredondar_valor(emprestimo["saldo_devedor"] - valor)
    emprestimo["parcelas_restantes"] -= 1
    emprestimo["valores_parcelas"].pop(0)
    if emprestimo["parcelas_restantes"] == 0:
        emprestimo["status"] = "quitado"
    registrar_transacao(
        conta,
        "Pagamento de parcela",
        valor,
        "saida",
        f"Pagamento de parcela: {emprestimo['nome']}",
        "Contas",
        estorno={"tipo": "pagar_parcela", "emprestimo": emprestimo, "estado": estado_anterior, "valor": valor},
    )
    return True


def agendar_pagamento(conta, descricao, valor, categoria="Contas", data=""):
    valor = validar_valor(valor)
    descricao = str(descricao).strip()
    data = str(data).strip()
    if valor is None or not descricao:
        return False
    if data:
        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            return False
    conta["fila_pagamentos"].append(
        {"descricao": descricao, "valor": valor, "categoria": normalizar_categoria(categoria), "data": data}
    )
    return True


def processar_proximo_pagamento(conta):
    if not conta["fila_pagamentos"]:
        return False
    pagamento = conta["fila_pagamentos"].pop(0)
    if pagamento["valor"] > conta["saldo"]:
        conta["fila_pagamentos"].insert(0, pagamento)
        return False
    conta["saldo"] = arredondar_valor(conta["saldo"] - pagamento["valor"])
    registrar_transacao(
        conta,
        "Pagamento agendado",
        pagamento["valor"],
        "saida",
        pagamento["descricao"],
        pagamento["categoria"],
        estorno={"tipo": "pagamento_agendado", "valor": pagamento["valor"], "pagamento": pagamento},
    )
    return True


def _desfazer_acao(conta, acao):
    tipo = acao["tipo"]
    valor = acao.get("valor", 0.0)
    if tipo == "deposito":
        if valor > conta["saldo"]:
            return False
        conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
        return True
    if tipo == "saque":
        if conta["bytepoints"] < acao["pontos"]:
            return False
        conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
        conta["bytepoints"] -= acao["pontos"]
        return True
    if tipo == "pix_enviado":
        destino = acao["destino"]
        if valor > destino["saldo"] or conta["bytepoints"] < acao["pontos"]:
            return False
        conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
        destino["saldo"] = arredondar_valor(destino["saldo"] - valor)
        conta["bytepoints"] -= acao["pontos"]
        acao["recebimento"]["estornado"] = True
        registrar_transacao(destino, "PIX estornado", valor, "saida", "PIX devolvido ao remetente")
        return True
    if tipo == "guardar_cofrinho":
        if valor > conta["cofrinhos"][acao["nome"]]:
            return False
        conta["cofrinhos"][acao["nome"]] = arredondar_valor(conta["cofrinhos"][acao["nome"]] - valor)
        conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
        return True
    if tipo == "resgatar_cofrinho":
        if valor > conta["saldo"]:
            return False
        conta["cofrinhos"][acao["nome"]] = arredondar_valor(conta["cofrinhos"][acao["nome"]] + valor)
        conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
        return True
    if tipo == "rendimento":
        if valor > conta["cofrinhos"][acao["nome"]]:
            return False
        conta["cofrinhos"][acao["nome"]] = arredondar_valor(conta["cofrinhos"][acao["nome"]] - valor)
        return True
    if tipo == "compra_credito":
        compra = acao["compra"]
        if compra not in conta["compras_credito"]:
            return False
        conta["compras_credito"].remove(compra)
        conta["saldo_fatura"] = arredondar_valor(conta["saldo_fatura"] - valor)
        conta["limite_disponivel"] = arredondar_valor(conta["limite_disponivel"] + valor)
        return True
    if tipo == "pagar_fatura":
        conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
        conta["saldo_fatura"] = valor
        conta["limite_disponivel"] = acao["limite"]
        conta["compras_credito"] = list(acao["compras"])
        return True
    if tipo == "compra_moeda":
        moeda = acao["moeda"]
        if acao["quantidade"] > conta["saldos_moedas"][moeda]:
            return False
        conta["saldo"] = arredondar_valor(conta["saldo"] + acao["brl"])
        conta["saldos_moedas"][moeda] = round(conta["saldos_moedas"][moeda] - acao["quantidade"], 8)
        return True
    if tipo == "venda_moeda":
        moeda = acao["moeda"]
        if acao["brl"] > conta["saldo"]:
            return False
        conta["saldo"] = arredondar_valor(conta["saldo"] - acao["brl"])
        conta["saldos_moedas"][moeda] = round(conta["saldos_moedas"][moeda] + acao["quantidade"], 8)
        return True
    if tipo == "cashback":
        if valor > conta["saldo"]:
            return False
        conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
        conta["bytepoints"] += acao["pontos"]
        return True
    if tipo == "contratar_emprestimo":
        if valor > conta["saldo"] or not any(item is acao["emprestimo"] for item in conta["emprestimos"]):
            return False
        conta["saldo"] = arredondar_valor(conta["saldo"] - valor)
        conta["emprestimos"] = [item for item in conta["emprestimos"] if item is not acao["emprestimo"]]
        return True
    if tipo == "pagar_parcela":
        emprestimo = acao["emprestimo"]
        estado = acao["estado"]
        conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
        emprestimo.update(estado)
        return True
    if tipo == "pagamento_agendado":
        conta["saldo"] = arredondar_valor(conta["saldo"] + valor)
        conta["fila_pagamentos"].insert(0, acao["pagamento"])
        return True
    return False


def estornar_ultima_transacao(conta):
    if not conta["pilha_estornos"]:
        return False
    registro = conta["pilha_estornos"].pop()
    if not _desfazer_acao(conta, registro["acao"]):
        conta["pilha_estornos"].append(registro)
        return False
    original = registro["transacao"]
    original["estornado"] = True
    movimento = "entrada" if original["movimento"] == "saida" else "saida"
    registrar_transacao(
        conta,
        "Estorno",
        original["valor"],
        movimento,
        f"Estorno de {original['tipo']}",
        original["categoria"],
        fluxo_brl=original["fluxo_brl"],
    )
    return True


def relatorio_categoria(conta, orcamento=None):
    orcamento = validar_valor(orcamento) if orcamento is not None else conta["orcamento_mensal"]
    if orcamento is None or orcamento <= 0:
        orcamento = 0.0
    totais = {}
    for transacao in conta["historico"]:
        if transacao["estornado"] or transacao["tipo"] not in GASTOS:
            continue
        categoria = normalizar_categoria(transacao["categoria"])
        totais[categoria] = arredondar_valor(totais.get(categoria, 0.0) + transacao["valor"])
    return {
        categoria: {
            "total": total,
            "percentual_orcamento": arredondar_valor(total * 100 / orcamento) if orcamento else 0.0,
        }
        for categoria, total in totais.items()
    }


def relatorio_fluxo(conta, periodo, referencia=None):
    referencia = referencia or datetime.now().astimezone().date()
    if periodo == "semana":
        inicio = referencia - timedelta(days=referencia.weekday())
        fim = inicio + timedelta(days=6)
    elif periodo == "mes":
        inicio = referencia.replace(day=1)
        fim = referencia.replace(day=monthrange(referencia.year, referencia.month)[1])
    elif periodo == "semestre":
        mes_inicial = 1 if referencia.month <= 6 else 7
        inicio = referencia.replace(month=mes_inicial, day=1)
        fim = referencia.replace(month=mes_inicial + 5, day=monthrange(referencia.year, mes_inicial + 5)[1])
    else:
        raise ValueError("Periodo invalido")

    entradas = 0.0
    saidas = 0.0
    movimentacoes = []
    for transacao in conta["historico"]:
        if not transacao.get("fluxo_brl", True) or transacao["movimento"] not in ("entrada", "saida"):
            continue
        dia = date.fromisoformat(transacao["data"][:10])
        if not inicio <= dia <= fim:
            continue
        movimentacoes.append(transacao)
        if transacao["movimento"] == "entrada":
            entradas = arredondar_valor(entradas + transacao["valor"])
        else:
            saidas = arredondar_valor(saidas + transacao["valor"])
    return {
        "inicio": inicio,
        "fim": fim,
        "entradas": entradas,
        "saidas": saidas,
        "resultado": arredondar_valor(entradas - saidas),
        "movimentacoes": movimentacoes,
    }


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


def mostrar_fatura(conta):
    print("\n=== Fatura do cartao ===")
    if not conta["compras_credito"]:
        print("Nenhuma compra no credito.")
    for compra in conta["compras_credito"]:
        print(f"{compra['estabelecimento']}: {formatar_moeda(compra['valor'])}")
    print(f"Total: {formatar_moeda(conta['saldo_fatura'])}")
    print(f"Limite disponivel: {formatar_moeda(conta['limite_disponivel'])}")


def mostrar_moedas(conta):
    print("\n=== Carteira de moedas ===")
    for moeda, quantidade in conta["saldos_moedas"].items():
        print(f"{moeda}: {quantidade:.8f} | Taxa: {formatar_moeda(TAXAS_CAMBIO[moeda])}")


def mostrar_extrato(conta):
    print("\n=== Historico de transacoes ===")
    if not conta["historico"]:
        print("Nenhuma transacao realizada nesta sessao.")
    for indice, transacao in enumerate(conta["historico"], start=1):
        sinal = "+" if transacao["movimento"] == "entrada" else "-"
        if not transacao.get("fluxo_brl", True):
            sinal = "(sem alteracao no saldo)"
        print(
            f"{indice}. {transacao['data'][:10]} | {transacao['tipo']} | {sinal} {formatar_moeda(transacao['valor'])} | "
            f"{transacao['categoria']} | Saldo: {formatar_moeda(transacao['saldo_apos'])}"
        )
        print(f"   {transacao['descricao']}")


def mostrar_fluxo(conta, periodo, referencia=None):
    dados = relatorio_fluxo(conta, periodo, referencia)
    print(f"\n=== Entradas e saidas: {periodo} ===")
    print(f"Periodo: {dados['inicio']:%d/%m/%Y} a {dados['fim']:%d/%m/%Y}")
    if not dados["movimentacoes"]:
        print("Nenhuma movimentacao registrada no periodo.")
    for transacao in dados["movimentacoes"]:
        sinal = "+" if transacao["movimento"] == "entrada" else "-"
        dia = date.fromisoformat(transacao["data"][:10])
        print(f"{dia:%d/%m/%Y} | {transacao['tipo']} | {sinal}{formatar_moeda(transacao['valor'])}")
    print(f"Total de entradas: {formatar_moeda(dados['entradas'])}")
    print(f"Total de saidas: {formatar_moeda(dados['saidas'])}")
    print(f"Resultado do periodo: {formatar_moeda(dados['resultado'])}")


def escolher(titulo, opcoes):
    print(f"\n=== {titulo} ===")
    for indice, descricao in opcoes:
        print(f"{indice} - {descricao}")
    return input("Escolha uma opcao: ").strip()


def mostrar_relatorio(conta):
    relatorio = relatorio_categoria(conta)
    print("\n=== Relatorio por categoria ===")
    if not relatorio:
        print("Nenhum gasto categorizado.")
        return
    for categoria, dados in relatorio.items():
        print(f"{categoria}: {formatar_moeda(dados['total'])} | {dados['percentual_orcamento']:.2f}% do orcamento")


def mostrar_emprestimos(conta):
    print("\n=== Emprestimos ===")
    if not conta["emprestimos"]:
        print("Nenhum emprestimo contratado.")
        return
    for indice, emprestimo in enumerate(conta["emprestimos"], start=1):
        print(
            f"{indice}. {emprestimo.get('nome', f'Emprestimo {indice}')} | Saldo devedor: {formatar_moeda(emprestimo['saldo_devedor'])} | "
            f"Parcelas restantes: {emprestimo['parcelas_restantes']} | {emprestimo['status']}"
        )


def criar_cofrinho_interativo(conta):
    nome = input("Nome do novo cofrinho: ").strip()
    if not nome:
        print("Digite um nome para o cofrinho.")
        return False
    if buscar_nome_cofrinho(conta, nome) is not None:
        print("Ja existe um cofrinho com esse nome.")
        return False
    print(f"Saldo disponivel na conta: {formatar_moeda(conta['saldo'])}")
    texto = input("Valor inicial (Enter para comecar vazio): R$ ").strip()
    valor_inicial = 0 if not texto else validar_valor(texto)
    if valor_inicial is None:
        print("Valor inicial invalido. Digite um valor positivo ou pressione Enter.")
        return False
    if valor_inicial > conta["saldo"]:
        print("Saldo insuficiente. Deposite na conta antes de guardar dinheiro.")
        return False
    if not criar_cofrinho(conta, nome, valor_inicial):
        print("Nao foi possivel criar o cofrinho.")
        return False
    print(f"Cofrinho {nome} criado com {formatar_moeda(valor_inicial)}.")
    return True


def selecionar_cofrinho(conta, permitir_criar=False):
    while True:
        nomes = list(conta["cofrinhos"])
        print("\nCofrinhos disponiveis:")
        if not nomes:
            print("Nenhum cofrinho cadastrado.")
        for indice, nome in enumerate(nomes, start=1):
            print(f"{indice} - {nome} | {formatar_moeda(conta['cofrinhos'][nome])}")
        if permitir_criar:
            print(f"{len(nomes) + 1} - Criar cofrinho")
        print("0 - Voltar")
        opcao = input("Escolha o numero do cofrinho: ").strip()
        if opcao == "0":
            return None
        if opcao in [str(indice) for indice in range(1, len(nomes) + 1)]:
            return nomes[int(opcao) - 1]
        if permitir_criar and opcao == str(len(nomes) + 1):
            criar_cofrinho_interativo(conta)
            return None
        print("Opcao invalida. Escolha um numero exibido na lista.")


def selecionar_emprestimo(conta):
    disponiveis = [item for item in conta["emprestimos"] if item["parcelas_restantes"] > 0]
    if not disponiveis:
        print("Nenhum emprestimo com parcelas a pagar.")
        return None
    while True:
        print("\nEmprestimos com parcelas pendentes:")
        for indice, item in enumerate(disponiveis, start=1):
            print(f"{indice} - {item['nome']} | Proxima parcela: {formatar_moeda(item['valores_parcelas'][0])} | Restantes: {item['parcelas_restantes']}")
        print("0 - Voltar")
        opcao = input("Escolha o numero do emprestimo: ").strip()
        if opcao == "0":
            return None
        if opcao in [str(indice) for indice in range(1, len(disponiveis) + 1)]:
            return disponiveis[int(opcao) - 1]
        print("Opcao invalida. Escolha um numero exibido na lista.")


def selecionar_moeda(conta):
    moedas = list(TAXAS_CAMBIO)
    while True:
        print("\nMoedas disponiveis:")
        for indice, moeda in enumerate(moedas, start=1):
            print(f"{indice} - {moeda} | Saldo: {conta['saldos_moedas'][moeda]:.8f}")
        print("0 - Voltar")
        opcao = input("Escolha o numero da moeda: ").strip()
        if opcao == "0":
            return None
        if opcao in [str(indice) for indice in range(1, len(moedas) + 1)]:
            return moedas[int(opcao) - 1]
        print("Opcao invalida. Escolha um numero exibido na lista.")


def menu_fluxo(conta):
    while True:
        opcao = escolher("Entradas e saidas", [(1, "Semana"), (2, "Mes"),
                                               (3, "Semestre"), (0, "Voltar")])
        if opcao == "0":
            return
        if opcao not in ("1", "2", "3"):
            print("Opcao invalida.")
            continue
        texto = input("Data de referencia (DD/MM/AAAA; Enter para hoje): ").strip()
        try:
            referencia = datetime.strptime(texto, "%d/%m/%Y").date() if texto else None
        except ValueError:
            print("Data invalida. Use DD/MM/AAAA.")
            continue
        mostrar_fluxo(conta, {"1": "semana", "2": "mes", "3": "semestre"}[opcao], referencia)


def menu_movimentacoes(conta):
    while True:
        opcao = escolher("Conta", [(1, "Consultar saldo"), (2, "Depositar"),
                                   (3, "Sacar"), (4, "Historico"), (5, "Estornar ultima transacao"),
                                   (6, "Entradas e saidas por periodo"),
                                   (7, "Dados da conta"),
                                   (0, "Voltar")])
        if opcao == "1":
            print(f"Saldo: {formatar_moeda(conta['saldo'])}")
        elif opcao == "2":
            if depositar(conta, ler_valor("Valor do deposito: R$ ")):
                print("Deposito realizado.")
        elif opcao == "3":
            if sacar(conta, ler_valor("Valor do saque: R$ "), ler_categoria()):
                print("Saque realizado.")
            else:
                print("Saque nao permitido. Verifique o saldo e o limite por operacao.")
        elif opcao == "4":
            mostrar_extrato(conta)
        elif opcao == "5":
            print("Ultima transacao estornada." if estornar_ultima_transacao(conta) else "Nao foi possivel estornar.")
        elif opcao == "6":
            menu_fluxo(conta)
        elif opcao == "7":
            pin = input("Confirme seu PIN de 4 digitos: ").strip()
            if autenticar_conta(conta["numero"], pin) is not conta:
                print("PIN incorreto. Dados da conta nao exibidos.")
                continue
            print("\n=== Dados da conta ===")
            print(f"Nome: {conta['nome']}")
            print(f"CPF: {conta['cpf']}")
            print(f"Chave PIX: {conta['chave_pix']}")
            print(f"Numero da conta: {conta['numero']}")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_pix(conta):
    while True:
        opcao = escolher("PIX", [(1, "Transferir"), (0, "Voltar")])
        if opcao == "1":
            chave = input("Chave PIX de destino: ").strip()
            destino = buscar_por_pix(chave)
            if destino is None:
                print("Chave PIX nao encontrada.")
                continue
            if destino is conta:
                print("Nao e possivel enviar PIX para sua propria conta.")
                continue
            print(f"Destino: {destino['nome']} | Conta: {destino['numero']}")
            valor = ler_valor("Valor: R$ ")
            if valor > conta["saldo"]:
                print("Saldo insuficiente para realizar o PIX.")
                continue
            print("PIX realizado." if transferir_pix(conta, chave, valor, ler_categoria()) else "Nao foi possivel realizar o PIX.")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_cofrinhos(conta):
    while True:
        opcao = escolher("Cofrinhos", [(1, "Consultar cofrinhos"), (2, "Criar cofrinho"),
                                       (3, "Depositar no cofrinho"), (4, "Resgatar dinheiro"),
                                       (5, "Simular rendimento"), (0, "Voltar")])
        if opcao == "1":
            mostrar_cofrinhos(conta)
        elif opcao == "2":
            criar_cofrinho_interativo(conta)
        elif opcao == "3":
            nome = selecionar_cofrinho(conta, permitir_criar=True)
            if nome is None:
                continue
            print(f"Saldo disponivel na conta: {formatar_moeda(conta['saldo'])}")
            valor = ler_valor("Valor para depositar no cofrinho: R$ ")
            if valor > conta["saldo"]:
                print("Saldo insuficiente. Deposite na conta antes de guardar dinheiro.")
            elif guardar_no_cofrinho(conta, nome, valor):
                print(f"Deposito no cofrinho realizado: {formatar_moeda(valor)}.")
        elif opcao == "4":
            nome = selecionar_cofrinho(conta)
            if nome is None:
                continue
            print(f"Disponivel no cofrinho: {formatar_moeda(conta['cofrinhos'][nome])}")
            valor = ler_valor("Valor para resgatar: R$ ")
            if resgatar_do_cofrinho(conta, nome, valor):
                print(f"Valor resgatado: {formatar_moeda(valor)}.")
            else:
                print("Saldo insuficiente no cofrinho para esse resgate.")
        elif opcao == "5":
            anteriores = dict(conta["cofrinhos"])
            rendimento = simular_rendimento(conta, input("Quantidade de meses: "))
            if rendimento is None:
                print("Informe meses validos e crie um cofrinho antes.")
            else:
                print(f"Rendimento total: {formatar_moeda(rendimento)}")
                for nome, saldo_anterior in anteriores.items():
                    ganho = arredondar_valor(conta["cofrinhos"][nome] - saldo_anterior)
                    print(f"{nome}: +{formatar_moeda(ganho)} | Saldo: {formatar_moeda(conta['cofrinhos'][nome])}")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_cartao(conta):
    while True:
        opcao = escolher("Cartao", [(1, "Consultar fatura"), (2, "Comprar no credito"),
                                    (3, "Pagar fatura"), (0, "Voltar")])
        if opcao == "1":
            mostrar_fatura(conta)
        elif opcao == "2":
            estabelecimento = input("Estabelecimento: ").strip()
            if not estabelecimento:
                print("Digite o nome do estabelecimento.")
                continue
            valor = ler_valor("Valor: R$ ")
            if valor > conta["limite_disponivel"]:
                print("Limite do cartao insuficiente.")
                continue
            print("Compra aprovada." if comprar_no_credito(conta, valor, estabelecimento, ler_categoria()) else "Compra recusada.")
        elif opcao == "3":
            if conta["saldo_fatura"] <= 0:
                print("Nao ha fatura para pagar.")
            elif conta["saldo_fatura"] > conta["saldo"]:
                print("Saldo insuficiente para pagar a fatura.")
            else:
                print("Fatura paga." if pagar_fatura(conta) else "Nao foi possivel pagar a fatura.")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_pagamentos(conta):
    while True:
        opcao = escolher("Pagamentos", [(1, "Consultar fila"), (2, "Agendar pagamento"),
                                        (3, "Processar proximo pagamento"), (0, "Voltar")])
        if opcao == "1":
            if not conta["fila_pagamentos"]:
                print("Fila vazia.")
            for indice, pagamento in enumerate(conta["fila_pagamentos"], start=1):
                print(f"{indice}. {pagamento['descricao']} | {formatar_moeda(pagamento['valor'])} | {pagamento['data']}")
        elif opcao == "2":
            descricao = input("Descricao: ")
            data = input("Data (DD/MM/AAAA, opcional): ").strip()
            if not descricao.strip():
                print("Digite uma descricao para o pagamento.")
                continue
            if data:
                try:
                    datetime.strptime(data, "%d/%m/%Y")
                except ValueError:
                    print("Data invalida. Use DD/MM/AAAA.")
                    continue
            print("Pagamento agendado." if agendar_pagamento(conta, descricao, ler_valor("Valor: R$ "), ler_categoria(), data) else "Descricao ou data invalida. Use DD/MM/AAAA.")
        elif opcao == "3":
            if not conta["fila_pagamentos"]:
                print("Fila vazia. Agende um pagamento antes.")
            elif conta["fila_pagamentos"][0]["valor"] > conta["saldo"]:
                print("Saldo insuficiente para o primeiro pagamento da fila.")
            else:
                print("Pagamento processado." if processar_proximo_pagamento(conta) else "Nao foi possivel processar o pagamento.")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_gastos(conta):
    while True:
        opcao = escolher("Gastos", [(1, "Relatorio por categoria"),
                                   (2, "Definir orcamento"), (0, "Voltar")])
        if opcao == "1":
            mostrar_relatorio(conta)
        elif opcao == "2":
            orcamento = validar_valor(input("Orcamento mensal: R$ "))
            if orcamento is not None:
                conta["orcamento_mensal"] = orcamento
                print("Orcamento atualizado.")
            else:
                print("Valor invalido.")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_moedas(conta):
    while True:
        opcao = escolher("Moedas", [(1, "Consultar carteira"), (2, "Comprar moeda"),
                                    (3, "Vender moeda"), (0, "Voltar")])
        if opcao == "1":
            mostrar_moedas(conta)
        elif opcao == "2":
            moeda = selecionar_moeda(conta)
            if moeda is None:
                continue
            valor = ler_valor("Valor em reais: R$ ")
            if valor > conta["saldo"]:
                print("Saldo em reais insuficiente para comprar essa moeda.")
            else:
                print("Compra realizada." if comprar_moeda_estrangeira(conta, moeda, valor) else "Valor muito baixo para comprar essa moeda.")
        elif opcao == "3":
            moeda = selecionar_moeda(conta)
            if moeda is None:
                continue
            quantidade = ler_quantidade("Quantidade: ")
            if quantidade > conta["saldos_moedas"][moeda]:
                print(f"Saldo de {moeda} insuficiente para vender essa quantidade.")
            else:
                print("Venda realizada." if vender_moeda_estrangeira(conta, moeda, quantidade) else "Valor convertido muito baixo para vender.")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_pontos(conta):
    while True:
        opcao = escolher("BytePoints", [(1, "Consultar pontos"), (2, "Resgatar cashback"),
                                        (0, "Voltar")])
        if opcao == "1":
            print(f"BytePoints: {consultar_pontos(conta)}")
        elif opcao == "2":
            print("Cashback resgatado." if resgatar_cashback(conta, input("Pontos: ")) else "Pontos insuficientes ou invalidos.")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_emprestimos(conta):
    while True:
        opcao = escolher("Emprestimos", [(1, "Consultar emprestimos"), (2, "Simular emprestimo"),
                                        (3, "Contratar emprestimo"), (4, "Pagar parcela"),
                                        (0, "Voltar")])
        if opcao == "1":
            mostrar_emprestimos(conta)
        elif opcao == "2":
            simulacao = simular_emprestimo(conta, ler_valor("Valor: R$ "), input("Parcelas: "))
            if simulacao:
                print(f"Valor: {formatar_moeda(simulacao['valor'])} em {simulacao['parcelas']} parcelas")
                print("Parcelas: " + ", ".join(formatar_moeda(valor) for valor in simulacao["valores_parcelas"]))
            else:
                print("Emprestimo nao aprovado.")
        elif opcao == "3":
            valor = ler_valor("Valor: R$ ")
            parcelas = input("Parcelas: ")
            nome = input("Nome do emprestimo (Enter para nome automatico): ").strip()
            print("Emprestimo contratado." if contratar_emprestimo(conta, valor, parcelas, nome) else "Emprestimo nao aprovado. Verifique saldo, limite e numero de parcelas.")
        elif opcao == "4":
            emprestimo = selecionar_emprestimo(conta)
            if emprestimo is None:
                continue
            print(f"Parcela paga: {emprestimo['nome']}." if pagar_parcela_emprestimo(conta, emprestimo) else "Saldo insuficiente para pagar a parcela.")
        elif opcao == "0":
            return
        else:
            print("Opcao invalida.")


def menu_conta(conta):
    secoes = {
        "1": menu_movimentacoes,
        "2": menu_pix,
        "3": menu_cofrinhos,
        "4": menu_cartao,
        "5": menu_pagamentos,
        "6": menu_gastos,
        "7": menu_moedas,
        "8": menu_pontos,
        "9": menu_emprestimos,
    }
    while True:
        opcao = escolher("ByteBank", [(1, "Conta"), (2, "PIX"), (3, "Cofrinhos"),
                                     (4, "Cartao"), (5, "Pagamentos"), (6, "Gastos"),
                                     (7, "Moedas"), (8, "BytePoints"), (9, "Emprestimos"),
                                     (0, "Sair da conta")])
        if opcao == "0":
            print("Voce saiu da conta.")
            return
        if opcao in secoes:
            secoes[opcao](conta)
        else:
            print("Opcao invalida.")


def main():
    while True:
        print("\n=== Acesso ao ByteBank ===")
        print("1 - Entrar na conta")
        print("2 - Criar conta")
        print("0 - Sair do programa")
        opcao = input("Escolha uma opcao: ").strip()
        if opcao == "1":
            identificador = input("Numero da conta ou CPF: ").strip()
            pin = input("PIN de 4 digitos: ").strip()
            conta = autenticar_conta(identificador, pin)
            if conta is None:
                print("Conta ou PIN incorreto.")
            else:
                print(f"Bem-vindo(a), {conta['nome']}!")
                menu_conta(conta)
        elif opcao == "2":
            nome = input("Nome: ")
            cpf = input("CPF: ")
            chave_pix = input("Chave PIX: ")
            pin = input("Crie um PIN de 4 digitos: ").strip()
            erro = erro_cadastro(nome, cpf, chave_pix, pin)
            if erro is not None:
                print(erro)
                continue
            conta = cadastrar_conta(nome, cpf, chave_pix, pin)
            print(f"Conta criada: {conta['numero']}. Entre com seu numero e PIN.")
        elif opcao == "0":
            print("Programa encerrado.")
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main()
