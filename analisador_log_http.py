"""Conta respostas HTTP 200 e 404 em logs simples ou Apache/Nginx."""
import re
from pathlib import Path

PADRAO = re.compile(r'"(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|TRACE|CONNECT)\s+[^"\r\n]*"\s+(\d{3})\b', re.IGNORECASE)


def analisar_log(caminho):
    contagem = {200: 0, 404: 0}
    ignoradas = 0
    with Path(caminho).open("r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            correspondencia = PADRAO.search(linha)
            if correspondencia:
                codigo = int(correspondencia.group(1))
            else:
                partes = linha.split()
                if len(partes) != 4 or partes[1].upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} or not re.fullmatch(r"\d{3}", partes[3]):
                    ignoradas += 1
                    continue
                codigo = int(partes[3])
            if codigo in contagem:
                contagem[codigo] += 1
    return {"200": contagem[200], "404": contagem[404], "ignoradas": ignoradas}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analisar respostas HTTP 200 e 404")
    parser.add_argument("arquivo", help="Caminho do arquivo .log")
    args = parser.parse_args()
    try:
        resultado = analisar_log(args.arquivo)
        print(f"200 (Sucesso): {resultado['200']}")
        print(f"404 (Não Encontrado): {resultado['404']}")
        print(f"Linhas ignoradas: {resultado['ignoradas']}")
    except (OSError, UnicodeError) as erro:
        parser.exit(1, f"Erro ao ler log: {erro}\n")
