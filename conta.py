from math import isfinite

from cliente import Cliente


class Conta:
    def __init__(self, cliente, numero, saldo=0.0, limite=500.0):
        if not isinstance(cliente, Cliente):
            raise ValueError("Cliente invalido.")
        if not self.__valor_valido(saldo) or saldo < 0:
            raise ValueError("Saldo inicial invalido.")
        if not self.__valor_valido(limite) or limite <= 0:
            raise ValueError("Limite invalido.")

        self.cliente = cliente
        self.id_cliente = cliente.cpf
        self.numero = str(numero)
        self.__saldo = round(saldo, 2)
        self.__limite = round(limite, 2)
        if self.__limite <= 0:
            raise ValueError("Limite deve ser de pelo menos um centavo.")

    @staticmethod
    def __valor_valido(valor):
        return (
            type(valor) in (int, float)
            and isfinite(valor)
            and abs(valor) <= 1_000_000_000_000
        )

    def sacar(self, valor):
        if not self.__valor_valido(valor) or valor <= 0:
            return False
        valor = round(valor, 2)
        if valor <= 0 or valor > self.__saldo or valor > self.__limite:
            return False

        self.__saldo = round(self.__saldo - valor, 2)
        return True

    def depositar(self, valor):
        if not self.__valor_valido(valor) or valor <= 0:
            return False
        valor = round(valor, 2)
        novo_saldo = round(self.__saldo + valor, 2)
        if valor <= 0 or not self.__valor_valido(novo_saldo):
            return False

        self.__saldo = novo_saldo
        return True

    def consultar_saldo(self):
        return self.__saldo

    def consultar_limite(self):
        return self.__limite

    def aumentar_limite(self, novo_limite):
        if not self.__valor_valido(novo_limite):
            return False
        novo_limite = round(novo_limite, 2)
        if novo_limite <= self.__limite:
            return False

        self.__limite = novo_limite
        return True
