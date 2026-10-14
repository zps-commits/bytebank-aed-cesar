import tempfile
import unittest
from pathlib import Path
from persistencia_txt import salvar_contas_txt, carregar_contas_txt
from analisador_log_http import analisar_log


class TesteModulos(unittest.TestCase):
    def test_preserva_referencias_pix(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "contas.txt"
            recebimento = {"tipo": "PIX recebido", "estornado": False}
            destino = {"numero": "1002", "historico": [recebimento]}
            envio = {"tipo": "PIX enviado", "estornado": False}
            origem = {"numero": "1001", "historico": [envio], "pilha_estornos": [
                {"transacao": envio, "acao": {"tipo": "pix_enviado", "destino": destino, "recebimento": recebimento}}
            ]}
            salvar_contas_txt([origem, destino], caminho)
            contas = carregar_contas_txt(caminho)
            self.assertIs(contas[0]["pilha_estornos"][0]["acao"]["destino"], contas[1])
            self.assertIs(contas[0]["pilha_estornos"][0]["transacao"], contas[0]["historico"][0])
            self.assertIs(contas[0]["pilha_estornos"][0]["acao"]["recebimento"], contas[1]["historico"][0])

    def test_ausencia_e_corrupcao(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "contas.txt"
            self.assertIsNone(carregar_contas_txt(caminho))
            caminho.write_text("erro", encoding="utf-8")
            with self.assertRaises(ValueError):
                carregar_contas_txt(caminho)

    def test_log(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "servidor.log"
            caminho.write_text(
                '1.1.1.1 GET / 200\n'
                '1.1.1.2 GET /erro 404\n'
                '127.0.0.1 - - [01/Jan/2026:00:00:00 +0000] "GET /teste HTTP/1.1" 200 123\n'
                'linha invalida 200\n', encoding="utf-8")
            self.assertEqual(analisar_log(caminho), {"200": 2, "404": 1, "ignoradas": 1})


if __name__ == "__main__":
    unittest.main()
