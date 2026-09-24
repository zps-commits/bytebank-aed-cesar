import unittest
from datetime import date
from io import StringIO
from unittest.mock import patch

import main


class ByteBankTestes(unittest.TestCase):
    def setUp(self):
        self.conta = main.criar_conta("9001", "Teste A", "99999999991", "teste-a@email.com", 1000.0)
        self.destino = main.criar_conta("9002", "Teste B", "99999999992", "teste-b@email.com", 300.0)
        main.contas.extend([self.conta, self.destino])

    def tearDown(self):
        main.contas.remove(self.conta)
        main.contas.remove(self.destino)

    def test_saque_pontos_e_estorno(self):
        self.assertTrue(main.sacar(self.conta, 100.0, "Alimentacao"))
        self.assertEqual(self.conta["bytepoints"], 10)
        self.assertEqual(self.conta["saldo"], 900.0)
        self.assertTrue(main.estornar_ultima_transacao(self.conta))
        self.assertEqual(self.conta["saldo"], 1000.0)
        self.assertEqual(self.conta["bytepoints"], 0)

    def test_pix_com_chave_e_estorno(self):
        self.assertTrue(main.transferir_pix(self.conta, self.destino["chave_pix"], 150.0, "Contas"))
        self.assertEqual(self.conta["saldo"], 850.0)
        self.assertEqual(self.destino["saldo"], 450.0)
        self.assertTrue(main.estornar_ultima_transacao(self.conta))
        self.assertEqual(self.conta["saldo"], 1000.0)
        self.assertEqual(self.destino["saldo"], 300.0)
        self.assertFalse(self.destino["pilha_estornos"])
        self.assertTrue(self.destino["historico"][0]["estornado"])
        self.assertEqual(main.relatorio_categoria(self.conta), {})

    def test_cofrinho_e_rendimento(self):
        self.assertTrue(main.criar_cofrinho(self.conta, "Viagem"))
        self.assertTrue(main.guardar_no_cofrinho(self.conta, "Viagem", 200.0))
        self.assertTrue(main.simular_rendimento(self.conta, 1))
        self.assertEqual(self.conta["cofrinhos"]["Viagem"], 201.0)
        self.assertTrue(main.resgatar_do_cofrinho(self.conta, "Viagem", 50.0))
        self.assertEqual(self.conta["saldo"], 850.0)

    def test_cartao_e_relatorio(self):
        self.assertTrue(main.comprar_no_credito(self.conta, 200.0, "Mercado", "Alimentacao"))
        self.assertEqual(self.conta["saldo_fatura"], 200.0)
        relatorio = main.relatorio_categoria(self.conta)
        self.assertEqual(relatorio["Alimentacao"]["total"], 200.0)
        self.assertTrue(main.pagar_fatura(self.conta))
        self.assertEqual(self.conta["saldo"], 800.0)
        self.assertEqual(self.conta["limite_disponivel"], self.conta["limite_credito"])

    def test_moedas(self):
        self.assertTrue(main.comprar_moeda_estrangeira(self.conta, "USD", 55.0))
        self.assertEqual(self.conta["saldos_moedas"]["USD"], 10.0)
        self.assertTrue(main.vender_moeda_estrangeira(self.conta, "USD", 5.0))
        self.assertEqual(self.conta["saldos_moedas"]["USD"], 5.0)
        self.assertEqual(self.conta["saldo"], 972.5)

    def test_cashback(self):
        self.assertTrue(main.sacar(self.conta, 300.0))
        self.assertEqual(main.consultar_pontos(self.conta), 30)
        self.assertTrue(main.resgatar_cashback(self.conta, 20))
        self.assertEqual(self.conta["bytepoints"], 10)
        self.assertEqual(self.conta["saldo"], 701.0)

    def test_emprestimo(self):
        simulacao = main.simular_emprestimo(self.conta, 600.0, 3)
        self.assertEqual(simulacao["valor_parcela"], 200.0)
        self.assertTrue(main.contratar_emprestimo(self.conta, 600.0, 3))
        self.assertEqual(self.conta["saldo"], 1600.0)
        self.assertTrue(main.pagar_parcela_emprestimo(self.conta))
        self.assertEqual(self.conta["saldo"], 1400.0)

    def test_fila_fifo(self):
        self.assertTrue(main.agendar_pagamento(self.conta, "Agua", 40.0, "Contas", "10/10/2026"))
        self.assertTrue(main.agendar_pagamento(self.conta, "Internet", 60.0, "Contas", "11/10/2026"))
        self.assertEqual(self.conta["fila_pagamentos"][0]["descricao"], "Agua")
        self.assertTrue(main.processar_proximo_pagamento(self.conta))
        self.assertEqual(self.conta["historico"][-1]["descricao"], "Agua")
        self.assertEqual(self.conta["fila_pagamentos"][0]["descricao"], "Internet")
        self.assertTrue(main.estornar_ultima_transacao(self.conta))
        self.assertEqual(self.conta["fila_pagamentos"][0]["descricao"], "Agua")

    def test_login_cadastro_e_sessao(self):
        self.assertIs(main.autenticar_conta("1001", "1234"), main.contas[0])
        self.assertIsNone(main.autenticar_conta("1001", "0000"))
        self.assertIsNone(main.cadastrar_conta("Maria", "88888888888", "maria@email.com", "12"))
        nova = main.cadastrar_conta("Maria", "88888888888", "maria@email.com", "9876")
        try:
            self.assertIsNotNone(nova)
            self.assertIs(main.autenticar_conta(nova["numero"], "9876"), nova)
            self.assertIs(main.autenticar_conta("888.888.888-88", "9876"), nova)
            self.assertNotIn("9876", str(nova))
            self.assertIsNone(main.cadastrar_conta("Outra", "88888888888", "outra@email.com", "1234"))
        finally:
            main.contas.remove(nova)

    def test_cadastro_mostra_erro_correto_e_nao_cria_conta_invalida(self):
        casos = [
            ("", "77777777777", "novo@email.com", "1234", "Digite seu nome"),
            ("Carla", "abc77777777777", "novo@email.com", "1234", "CPF invalido"),
            ("Carla", "77777777777", "", "1234", "Digite uma chave PIX"),
            ("Carla", "77777777777", "novo@email.com", "12a4", "PIN invalido"),
            ("Carla", "99999999991", "novo@email.com", "1234", "CPF ja cadastrado"),
            ("Carla", "77777777777", "teste-a@email.com", "1234", "Chave PIX ja cadastrada"),
        ]
        for nome, cpf, chave, pin, mensagem in casos:
            with self.subTest(mensagem=mensagem):
                total_contas = len(main.contas)
                self.assertIn(mensagem, main.erro_cadastro(nome, cpf, chave, pin))
                self.assertIsNone(main.cadastrar_conta(nome, cpf, chave, pin))
                self.assertEqual(len(main.contas), total_contas)
        entradas = iter(["2", "Carla", "77777777777", "novo@email.com", "12a4",
                         "2", "Carla", "99999999991", "novo@email.com", "1234", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.main()
        self.assertIn("PIN invalido. Digite exatamente 4 numeros.", saida.getvalue())
        self.assertIn("CPF ja cadastrado. Entre na conta existente.", saida.getvalue())
        self.assertIsNone(main.buscar_conta("77777777777"))

    def test_selecao_com_numero_excessivo_avisa_e_aceita_tentativa_seguinte(self):
        numero_excessivo = "9" * 5000
        self.assertTrue(main.criar_cofrinho(self.conta, "Reserva"))
        with patch("builtins.input", side_effect=[numero_excessivo, "1"]), patch("sys.stdout", new_callable=StringIO) as saida:
            self.assertEqual(main.selecionar_cofrinho(self.conta), "Reserva")
        self.assertIn("Opcao invalida", saida.getvalue())
        with patch("builtins.input", side_effect=[numero_excessivo, "1"]), patch("sys.stdout", new_callable=StringIO) as saida:
            self.assertEqual(main.ler_categoria(), main.CATEGORIAS[0])
        self.assertIn("Categoria invalida", saida.getvalue())

    def test_menu_criar_entrar_sair_e_entrar_novamente(self):
        entradas = iter([
            "2", "Carla", "77777777777", "carla@email.com", "7890",
            "1", "77777777777", "0000",
            "1", "77777777777", "7890", "1", "2", "50", "0", "0",
            "1", "77777777777", "7890", "1", "1", "0", "0", "0",
        ])
        try:
            with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
                main.main()
            self.assertIn("Conta ou PIN incorreto.", saida.getvalue())
            self.assertIn("Saldo: R$ 50,00", saida.getvalue())
            self.assertIn("Programa encerrado.", saida.getvalue())
        finally:
            main.contas.remove(main.buscar_conta("77777777777"))

    def test_dados_da_conta_exigem_pin_e_mostram_conta_certa(self):
        conta = main.contas[0]
        with patch("builtins.input", side_effect=["7", "0000", "7", "", "0"]), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_movimentacoes(conta)
        self.assertEqual(saida.getvalue().count("PIN incorreto. Dados da conta nao exibidos."), 2)
        self.assertNotIn("CPF: 11111111111", saida.getvalue())
        self.assertNotIn("Chave PIX: ana@email.com", saida.getvalue())

        with patch("builtins.input", side_effect=["7", "1234", "0"]), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_movimentacoes(conta)
        self.assertIn("Nome: Ana", saida.getvalue())
        self.assertIn("CPF: 11111111111", saida.getvalue())
        self.assertIn("Chave PIX: ana@email.com", saida.getvalue())
        self.assertIn("Numero da conta: 1001", saida.getvalue())
        self.assertNotIn("1234", saida.getvalue())

    def test_dados_de_conta_criada_so_abrem_com_o_proprio_pin(self):
        nova = main.cadastrar_conta("Julia", "44444444444", "julia@email.com", "5678")
        try:
            with patch("builtins.input", side_effect=["7", "1234", "7", "5678", "0"]), patch("sys.stdout", new_callable=StringIO) as saida:
                main.menu_movimentacoes(nova)
            texto = saida.getvalue()
            self.assertEqual(texto.count("CPF: 44444444444"), 1)
            self.assertIn("PIN incorreto. Dados da conta nao exibidos.", texto)
            self.assertIn("Nome: Julia", texto)
            self.assertIn("Chave PIX: julia@email.com", texto)
        finally:
            main.contas.remove(nova)

    def test_submenu_cofrinho_mostra_rendimento(self):
        entradas = iter(["2", "Viagem", "", "3", "1", "200", "5", "1", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_cofrinhos(self.conta)
        self.assertIn("Rendimento total: R$ 1,00", saida.getvalue())
        self.assertIn("Viagem: +R$ 1,00 | Saldo: R$ 201,00", saida.getvalue())

    def test_rendimento_zero_centavos_ainda_mostra_resultado(self):
        entradas = iter(["2", "Troco", "", "3", "1", "0.01", "5", "1", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_cofrinhos(self.conta)
        self.assertIn("Rendimento total: R$ 0,00", saida.getvalue())
        self.assertEqual(self.conta["cofrinhos"]["Troco"], 0.01)

    def test_criacao_com_valor_inicial_debita_saldo_e_registra(self):
        self.assertTrue(main.criar_cofrinho(self.conta, "Viagem", 200))
        self.assertEqual(self.conta["saldo"], 800.0)
        self.assertEqual(self.conta["cofrinhos"]["Viagem"], 200.0)
        self.assertEqual(self.conta["historico"][-1]["tipo"], "Valor guardado")
        self.assertFalse(main.criar_cofrinho(self.conta, "viagem", 10))
        self.assertTrue(main.guardar_no_cofrinho(self.conta, " VIAGEM ", 50))
        self.assertEqual(self.conta["cofrinhos"]["Viagem"], 250.0)
        self.assertTrue(main.resgatar_do_cofrinho(self.conta, " viagem", 25))
        self.assertEqual(self.conta["saldo"], 775.0)

    def test_criacao_sem_saldo_ou_valor_invalido_nao_cria(self):
        self.assertFalse(main.criar_cofrinho(self.conta, "Viagem", 1001))
        self.assertFalse(main.criar_cofrinho(self.conta, "Viagem", -10))
        self.assertEqual(self.conta["cofrinhos"], {})
        self.assertEqual(self.conta["saldo"], 1000.0)
        self.assertEqual(self.conta["historico"], [])

    def test_menu_cria_e_deposita_no_cofrinho_com_mensagem_de_saldo(self):
        entradas = iter(["2", "Viagem", "250", "3", "1", "50", "3", "1", "701", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_cofrinhos(self.conta)
        self.assertIn("Cofrinho Viagem criado com R$ 250,00.", saida.getvalue())
        self.assertIn("Deposito no cofrinho realizado: R$ 50,00.", saida.getvalue())
        self.assertIn("Saldo insuficiente.", saida.getvalue())
        self.assertEqual(self.conta["saldo"], 700.0)
        self.assertEqual(self.conta["cofrinhos"]["Viagem"], 300.0)

    def test_selecao_cofrinho_vazio_oferece_criar_com_valor_inicial(self):
        entradas = iter(["3", "abc", "1", "Reserva", "150", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_cofrinhos(self.conta)
        texto = saida.getvalue()
        self.assertIn("Nenhum cofrinho cadastrado.", texto)
        self.assertIn("1 - Criar cofrinho", texto)
        self.assertIn("Opcao invalida.", texto)
        self.assertEqual(self.conta["cofrinhos"], {"Reserva": 150.0})
        self.assertEqual(self.conta["saldo"], 850.0)

    def test_cofrinhos_lista_seleciona_segundo_e_cancela_sem_alterar(self):
        main.criar_cofrinho(self.conta, "Casa", 100)
        main.criar_cofrinho(self.conta, "Viagem", 200)
        entradas = iter(["3", "9", "x", "2", "50", "4", "2", "30", "3", "0", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_cofrinhos(self.conta)
        texto = saida.getvalue()
        self.assertIn("1 - Casa | R$ 100,00", texto)
        self.assertIn("2 - Viagem | R$ 200,00", texto)
        self.assertGreaterEqual(texto.count("Opcao invalida."), 2)
        self.assertEqual(self.conta["cofrinhos"], {"Casa": 100.0, "Viagem": 220.0})
        self.assertEqual(self.conta["saldo"], 680.0)

    def test_cofrinho_nome_repetido_e_valor_inicial_ruim(self):
        entradas = iter(["2", "Casa", "10", "2", "casa", "2", "Reserva", "abc", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_cofrinhos(self.conta)
        self.assertIn("Ja existe um cofrinho com esse nome.", saida.getvalue())
        self.assertIn("Valor inicial invalido.", saida.getvalue())
        self.assertEqual(self.conta["cofrinhos"], {"Casa": 10.0})

    def test_emprestimos_nomeados_selecao_e_parcela_correta(self):
        self.assertTrue(main.contratar_emprestimo(self.conta, 120, 2, "Notebook"))
        self.assertTrue(main.contratar_emprestimo(self.conta, 90, 3, "Reforma"))
        entradas = iter(["4", "99", "x", "2", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_emprestimos(self.conta)
        self.assertIn("1 - Notebook", saida.getvalue())
        self.assertIn("2 - Reforma", saida.getvalue())
        self.assertIn("Parcela paga: Reforma.", saida.getvalue())
        self.assertEqual(self.conta["emprestimos"][0]["parcelas_restantes"], 2)
        self.assertEqual(self.conta["emprestimos"][1]["parcelas_restantes"], 2)

    def test_emprestimo_quitado_nao_pode_receber_mais_parcela(self):
        self.assertTrue(main.contratar_emprestimo(self.conta, 20, 1, "Curso"))
        emprestimo = self.conta["emprestimos"][0]
        self.assertTrue(main.pagar_parcela_emprestimo(self.conta, emprestimo))
        self.assertFalse(main.pagar_parcela_emprestimo(self.conta, emprestimo))
        with patch("builtins.input", side_effect=["4", "0"]), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_emprestimos(self.conta)
        self.assertIn("Nenhum emprestimo com parcelas a pagar.", saida.getvalue())

    def test_estorno_de_emprestimos_identicos_remove_ultimo(self):
        self.assertTrue(main.contratar_emprestimo(self.conta, 50, 1, "Curso"))
        primeiro = self.conta["emprestimos"][0]
        self.assertTrue(main.contratar_emprestimo(self.conta, 50, 1, "Curso"))
        self.assertTrue(main.estornar_ultima_transacao(self.conta))
        self.assertEqual(len(self.conta["emprestimos"]), 1)
        self.assertIs(self.conta["emprestimos"][0], primeiro)

    def test_jornada_completa_cadastro_cofrinho_emprestimo_saldo(self):
        entradas = iter([
            "2", "Carla", "77777777777", "carla@email.com", "7890",
            "1", "77777777777", "7890",
            "1", "2", "1000", "0",
            "3", "3", "1", "Viagem", "200", "3", "1", "50", "4", "1", "20", "0",
            "9", "3", "100", "2", "Curso", "4", "1", "0",
            "1", "1", "0", "0", "0",
        ])
        try:
            with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
                main.main()
            texto = saida.getvalue()
            self.assertIn("Cofrinho Viagem criado com R$ 200,00.", texto)
            self.assertIn("Parcela paga: Curso.", texto)
            self.assertIn("Saldo: R$ 820,00", texto)
            self.assertIn("Programa encerrado.", texto)
        finally:
            conta = main.buscar_conta("77777777777")
            if conta is not None:
                main.contas.remove(conta)

    def test_categoria_numerica_apos_erro(self):
        with patch("builtins.input", side_effect=["abc", "99", "2"]), patch("sys.stdout", new_callable=StringIO) as saida:
            categoria = main.ler_categoria()
        self.assertEqual(categoria, "Transporte")
        self.assertEqual(saida.getvalue().count("Categoria invalida."), 2)

    def test_valores_invalidos_e_datas_invalidas(self):
        for valor in ("abc", "", "-1", "0", "0.001", "nan", "inf", "1e100000", "1..2,3", "1.23.456,00", None):
            self.assertIsNone(main.validar_valor(valor))
        self.assertEqual(main.validar_valor("1.234,56"), 1234.56)
        self.assertEqual(main.validar_valor("1.000"), 1000.0)
        self.assertEqual(main.validar_valor("1.000.000,00"), 1000000.0)
        self.assertIsNone(main.validar_valor(1.234))
        self.assertIsNone(main.simular_emprestimo(self.conta, 100, 100000000))
        self.assertFalse(main.agendar_pagamento(self.conta, "Agua", 10, data="31/02/2026"))
        self.assertFalse(main.agendar_pagamento(self.conta, "", 10, data="20/09/2026"))
        self.assertEqual(self.conta["fila_pagamentos"], [])

    def test_moeda_selecionada_por_numero_apos_erro(self):
        entradas = iter(["2", "x", "9", "1", "55", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_moedas(self.conta)
        self.assertGreaterEqual(saida.getvalue().count("Opcao invalida."), 2)
        self.assertEqual(self.conta["saldos_moedas"]["USD"], 10.0)

    def test_pix_chave_invalida_e_saldo_insuficiente_no_menu(self):
        entradas = iter(["1", "nao-existe", "1", self.destino["chave_pix"], "1001", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_pix(self.conta)
        self.assertIn("Chave PIX nao encontrada.", saida.getvalue())
        self.assertIn("Saldo insuficiente", saida.getvalue())
        self.assertEqual(self.conta["saldo"], 1000.0)
        self.assertEqual(self.destino["saldo"], 300.0)

    def test_pagamento_invalido_no_menu_nao_cria_fila(self):
        entradas = iter(["2", "Agua", "31/02/2026", "3", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_pagamentos(self.conta)
        self.assertIn("Data invalida.", saida.getvalue())
        self.assertIn("Fila vazia.", saida.getvalue())
        self.assertEqual(self.conta["fila_pagamentos"], [])

    def test_menu_principal_agrupado(self):
        entradas = iter(["9", "1", "0", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_conta(self.conta)
        self.assertIn("9 - Emprestimos", saida.getvalue())
        self.assertIn("1 - Consultar emprestimos", saida.getvalue())
        self.assertNotIn("29 -", saida.getvalue())

    def test_valores_pequenos_e_emprestimo_em_centavos(self):
        self.assertIsNone(main.validar_valor("0.004"))
        self.assertFalse(main.depositar(self.conta, "0.004"))
        self.assertFalse(main.sacar(self.conta, float("nan")))
        emprestimo = main.simular_emprestimo(self.conta, 0.05, 2)
        self.assertEqual(sum(emprestimo["valores_parcelas"]), 0.05)
        self.assertTrue(main.contratar_emprestimo(self.conta, 0.05, 2))
        self.assertTrue(main.pagar_parcela_emprestimo(self.conta))
        self.assertEqual(self.conta["emprestimos"][0]["saldo_devedor"], 0.02)
        self.assertTrue(main.pagar_parcela_emprestimo(self.conta))
        self.assertEqual(self.conta["emprestimos"][0]["saldo_devedor"], 0.0)

    def test_cambio_btc_com_precisao(self):
        self.assertTrue(main.comprar_moeda_estrangeira(self.conta, "BTC", 35.0))
        self.assertEqual(self.conta["saldos_moedas"]["BTC"], 0.0001)
        self.assertTrue(main.vender_moeda_estrangeira(self.conta, "BTC", 0.00005))
        self.assertEqual(self.conta["saldos_moedas"]["BTC"], 0.00005)

    def test_relatorio_sem_movimentacoes_internas(self):
        main.criar_cofrinho(self.conta, "Viagem")
        main.guardar_no_cofrinho(self.conta, "Viagem", 100.0)
        main.comprar_moeda_estrangeira(self.conta, "USD", 55.0)
        main.sacar(self.conta, 20.0, "Lazer")
        self.assertEqual(main.relatorio_categoria(self.conta)["Lazer"]["total"], 20.0)
        self.assertEqual(len(main.relatorio_categoria(self.conta)), 1)
        main.estornar_ultima_transacao(self.conta)
        self.assertEqual(main.relatorio_categoria(self.conta), {})

    def test_estorno_pagamento_da_fatura_restaura_limite(self):
        self.assertTrue(main.comprar_no_credito(self.conta, 200, "Farmacia", "Saude"))
        self.assertTrue(main.pagar_fatura(self.conta))
        self.conta["saldo"] = 0.0
        self.assertTrue(main.estornar_ultima_transacao(self.conta))
        self.assertEqual(self.conta["saldo_fatura"], 200.0)
        self.assertEqual(self.conta["limite_disponivel"], 800.0)
        self.assertEqual(self.conta["saldo"], 200.0)

    def test_pagamento_sem_saldo_mantem_primeiro_na_fila(self):
        main.agendar_pagamento(self.conta, "Aluguel", 2000.0)
        main.agendar_pagamento(self.conta, "Agua", 10.0)
        self.assertFalse(main.processar_proximo_pagamento(self.conta))
        self.assertEqual(self.conta["fila_pagamentos"][0]["descricao"], "Aluguel")
        self.assertEqual(self.conta["saldo"], 1000.0)

    def test_pontos_resgatados_impedem_estorno_inconsistente(self):
        main.sacar(self.conta, 100)
        self.conta["bytepoints"] = 0
        self.assertFalse(main.estornar_ultima_transacao(self.conta))
        self.assertEqual(self.conta["saldo"], 900.0)
        self.assertEqual(len(self.conta["pilha_estornos"]), 1)

    def test_debitos_sem_saldo_nao_deixam_conta_negativa(self):
        conta = main.criar_conta("9301", "Zero", "33333333333", "zero@email.com")
        main.contas.append(conta)
        try:
            self.assertFalse(main.sacar(conta, 1))
            self.assertFalse(main.transferir_pix(conta, self.destino["chave_pix"], 1))
            self.assertTrue(main.criar_cofrinho(conta, "Viagem"))
            self.assertFalse(main.guardar_no_cofrinho(conta, "Viagem", 1))
            self.assertFalse(main.resgatar_do_cofrinho(conta, "Viagem", 1))
            self.assertFalse(main.comprar_moeda_estrangeira(conta, "USD", 1))
            self.assertFalse(main.pagar_fatura(conta))
            self.assertFalse(main.contratar_emprestimo(conta, 1, 1))
            self.assertTrue(main.agendar_pagamento(conta, "Agua", 1))
            self.assertFalse(main.processar_proximo_pagamento(conta))
            self.assertEqual(conta["saldo"], 0.0)
            self.assertEqual(self.destino["saldo"], 300.0)
            self.assertEqual(len(conta["historico"]), 0)
        finally:
            main.contas.remove(conta)

    def test_fluxo_semana_mes_semestre_e_estornos(self):
        self.assertTrue(main.depositar(self.conta, 100))
        self.conta["historico"][-1]["data"] = "2026-01-31T12:00:00-03:00"
        self.assertTrue(main.sacar(self.conta, 30, "Lazer"))
        self.conta["historico"][-1]["data"] = "2026-02-01T12:00:00-03:00"
        self.assertTrue(main.comprar_no_credito(self.conta, 200, "Mercado"))
        self.conta["historico"][-1]["data"] = "2026-02-02T12:00:00-03:00"
        self.assertTrue(main.depositar(self.conta, 20))
        self.conta["historico"][-1]["data"] = "2026-07-01T12:00:00-03:00"

        semana = main.relatorio_fluxo(self.conta, "semana", date(2026, 2, 1))
        self.assertEqual((semana["inicio"], semana["fim"]), (date(2026, 1, 26), date(2026, 2, 1)))
        self.assertEqual((semana["entradas"], semana["saidas"], semana["resultado"]), (100, 30, 70))
        mes = main.relatorio_fluxo(self.conta, "mes", date(2026, 2, 10))
        self.assertEqual((mes["entradas"], mes["saidas"]), (0, 30))
        semestre = main.relatorio_fluxo(self.conta, "semestre", date(2026, 6, 30))
        self.assertEqual((semestre["inicio"], semestre["fim"]), (date(2026, 1, 1), date(2026, 6, 30)))
        self.assertEqual((semestre["entradas"], semestre["saidas"]), (100, 30))
        segundo = main.relatorio_fluxo(self.conta, "semestre", date(2026, 7, 1))
        self.assertEqual((segundo["entradas"], segundo["saidas"]), (20, 0))

        self.assertTrue(main.estornar_ultima_transacao(self.conta))
        self.conta["historico"][-1]["data"] = "2026-07-02T12:00:00-03:00"
        segundo = main.relatorio_fluxo(self.conta, "semestre", date(2026, 7, 1))
        self.assertEqual((segundo["entradas"], segundo["saidas"], segundo["resultado"]), (20, 20, 0))

    def test_menu_fluxo_exibe_totais(self):
        main.depositar(self.conta, 75)
        self.conta["historico"][-1]["data"] = "2026-09-24T10:00:00-03:00"
        entradas = iter(["2", "24/09/2026", "0"])
        with patch("builtins.input", side_effect=entradas), patch("sys.stdout", new_callable=StringIO) as saida:
            main.menu_fluxo(self.conta)
        self.assertIn("01/09/2026 a 30/09/2026", saida.getvalue())
        self.assertIn("Total de entradas: R$ 75,00", saida.getvalue())
        self.assertIn("Total de saidas: R$ 0,00", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
