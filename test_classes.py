from datetime import date, timedelta
from decimal import Decimal
import unittest

from cliente import Cliente
from conta import Conta


class TestClasses(unittest.TestCase):
    def setUp(self):
        self.cliente = Cliente("123.456.789-00", "Zion", "Rua A", "01/01/2000")
        self.conta = Conta(self.cliente, 1001)

    def test_endereco(self):
        self.assertTrue(self.cliente.modificar_endereco(" Rua B "))
        self.assertEqual(self.cliente.consultar_endereco(), "Rua B")
        for valor in (None, "", " ", 123):
            self.assertFalse(self.cliente.modificar_endereco(valor))
        self.assertEqual(self.cliente.consultar_endereco(), "Rua B")

    def test_cpf_normalizado_e_imutavel(self):
        self.assertEqual(self.cliente.cpf, "12345678900")
        self.assertEqual(self.conta.id_cliente, self.cliente.cpf)
        with self.assertRaises(AttributeError):
            self.cliente.cpf = "00000000000"
        with self.assertRaises(AttributeError):
            self.conta.id_cliente = "00000000000"

    def test_cadastros_invalidos(self):
        futuro = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")
        for cpf in (None, "", "abc", "123", "1234567890a"):
            with self.subTest(cpf=cpf), self.assertRaises(ValueError):
                Cliente(cpf, "Zion", "Rua A", "01/01/2000")
        for nascimento in (None, "", "31/02/2000", futuro):
            with self.subTest(nascimento=nascimento), self.assertRaises(ValueError):
                Cliente("12345678900", "Zion", "Rua A", nascimento)
        for nome, endereco in (("", "Rua A"), (None, "Rua A"), ("Zion", " ")):
            with self.assertRaises(ValueError):
                Cliente("12345678900", nome, endereco, "01/01/2000")

    def test_numero_invalido(self):
        for numero in (None, "", " ", "abc", -1, 0, True, 1.2, "١٢٣"):
            with self.subTest(numero=numero), self.assertRaises(ValueError):
                Conta(self.cliente, numero)

    def test_operacoes_validas_e_limites(self):
        self.assertTrue(self.conta.depositar(600))
        self.assertFalse(self.conta.sacar(501))
        self.assertTrue(self.conta.sacar(500))
        self.assertFalse(self.conta.sacar(101))
        self.assertTrue(self.conta.sacar(100))
        self.assertEqual(self.conta.consultar_saldo(), 0)
        self.assertTrue(self.conta.aumentar_limite(800))
        self.assertEqual(self.conta.consultar_limite(), 800)
        self.assertFalse(self.conta.aumentar_limite(800))
        self.assertFalse(self.conta.aumentar_limite(700))

    def test_valores_invalidos_nao_alteram_estado(self):
        invalidos = (0, -1, True, None, "10", float("nan"), float("inf"),
                     10**1000, .001, 1.999, Decimal("sNaN"), Decimal("Infinity"))
        self.conta.depositar(100)
        for valor in invalidos:
            with self.subTest(valor=repr(valor)):
                self.assertFalse(self.conta.depositar(valor))
                self.assertFalse(self.conta.sacar(valor))
                self.assertFalse(self.conta.aumentar_limite(valor))
                self.assertEqual(self.conta.consultar_saldo(), 100)
                self.assertEqual(self.conta.consultar_limite(), 500)

    def test_centavos_exatos(self):
        for _ in range(10):
            self.assertTrue(self.conta.depositar(.1))
        self.assertEqual(self.conta.consultar_saldo(), 1)
        self.assertTrue(self.conta.sacar(Decimal("1.00")))
        self.assertEqual(self.conta.consultar_saldo(), 0)

    def test_teto_de_saldo(self):
        conta = Conta(self.cliente, 2, saldo=1_000_000_000_000)
        self.assertFalse(conta.depositar(.01))
        self.assertEqual(conta.consultar_saldo(), 1_000_000_000_000)

    def test_construtor_rejeita_valores_invalidos(self):
        for valor in (-1, 1.999, True, None, float("nan"), 10**1000):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ValueError):
                    Conta(self.cliente, 2, saldo=valor)
                with self.assertRaises(ValueError):
                    Conta(self.cliente, 2, limite=valor)
        with self.assertRaises(ValueError):
            Conta(self.cliente, 2, limite=0)
        with self.assertRaises(ValueError):
            Conta(None, 2)

    def test_contas_independentes(self):
        outra = Conta(self.cliente, 2)
        self.conta.depositar(100)
        self.assertEqual(outra.consultar_saldo(), 0)


if __name__ == "__main__":
    unittest.main()
