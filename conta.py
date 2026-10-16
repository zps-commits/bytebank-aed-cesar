from decimal import Decimal

from cliente import Cliente


class Conta:
    def __init__(self, cliente, numero, saldo=0.0, limite=500.0):
        if not isinstance(cliente, Cliente):
            raise ValueError("Cliente invalido.")
        if type(numero) not in (str, int):
            raise ValueError("Numero da conta invalido.")
        numero = str(numero).strip()
        if not numero.isascii() or not numero.isdigit() or int(numero) <= 0:
            raise ValueError("Numero da conta deve ser um inteiro positivo.")

        saldo = self.__converter_valor(saldo)
        limite = self.__converter_valor(limite)
        if saldo is None:
            raise ValueError("Saldo inicial invalido.")
        if limite is None or limite <= 0:
            raise ValueError("Limite invalido.")

        self.__cliente = cliente
        self.numero = numero
        self.__saldo = saldo
        self.__limite = limite

    @property
    def cliente(self):
        return self.__cliente

    @property
    def id_cliente(self):
        return self.__cliente.cpf

    @staticmethod
    def __converter_valor(valor):
        if type(valor) not in (int, float, Decimal):
            return None
        if isinstance(valor, Decimal) and not valor.is_finite():
            return None
        if not 0 <= valor <= 1_000_000_000_000:
            return None
        valor = Decimal(str(valor))
        if valor != valor.quantize(Decimal("0.01")):
            return None
        return valor.quantize(Decimal("0.01"))

    def sacar(self, valor):
        valor = self.__converter_valor(valor)
        if valor is None or valor <= 0:
            return False
        if valor > self.__saldo or valor > self.__limite:
            return False

        self.__saldo -= valor
        return True

    def depositar(self, valor):
        valor = self.__converter_valor(valor)
        if valor is None or valor <= 0:
            return False
        novo_saldo = self.__saldo + valor
        if novo_saldo > 1_000_000_000_000:
            return False

        self.__saldo = novo_saldo
        return True

    def consultar_saldo(self):
        return float(self.__saldo)

    def consultar_limite(self):
        return float(self.__limite)

    def aumentar_limite(self, novo_limite):
        novo_limite = self.__converter_valor(novo_limite)
        if novo_limite is None or novo_limite <= self.__limite:
            return False

        self.__limite = novo_limite
        return True
