"""Persistência TXT do ByteBank, preservando referências entre objetos."""
import json
import os
from pathlib import Path
import tempfile

ARQUIVO = Path(__file__).resolve().parent / "contas.txt"


def _codificar(raiz):
    objetos, indices = [], {}

    def visitar(valor):
        if isinstance(valor, (dict, list)):
            identidade = id(valor)
            if identidade in indices:
                return {"ref": indices[identidade]}
            indice = len(objetos)
            indices[identidade] = indice
            objetos.append(None)
            if isinstance(valor, dict):
                if not all(isinstance(chave, str) for chave in valor):
                    raise ValueError("Chaves devem ser texto")
                objetos[indice] = {"tipo": "dict", "dados": {k: visitar(v) for k, v in valor.items()}}
            else:
                objetos[indice] = {"tipo": "list", "dados": [visitar(v) for v in valor]}
            return {"ref": indice}
        if valor is None or type(valor) in (str, int, float, bool):
            return {"valor": valor}
        raise TypeError(f"Tipo não suportado: {type(valor).__name__}")

    return {"versao": 1, "raiz": visitar(raiz), "objetos": objetos}


def _decodificar(documento):
    if not isinstance(documento, dict) or documento.get("versao") != 1:
        raise ValueError("Formato de arquivo incompatível")
    nos = documento["objetos"]
    if not isinstance(nos, list):
        raise ValueError("Dados inválidos")
    instancias = []
    for no in nos:
        if no["tipo"] == "dict" and isinstance(no["dados"], dict):
            instancias.append({})
        elif no["tipo"] == "list" and isinstance(no["dados"], list):
            instancias.append([])
        else:
            raise ValueError("Tipo de objeto inválido")

    def resolver(item):
        if not isinstance(item, dict):
            raise ValueError("Referência inválida")
        if set(item) == {"ref"}:
            indice = item["ref"]
            if type(indice) is not int or indice < 0 or indice >= len(instancias):
                raise ValueError("Referência fora do intervalo")
            return instancias[indice]
        if set(item) == {"valor"}:
            valor = item["valor"]
            if valor is None or type(valor) in (str, int, float, bool):
                return valor
        raise ValueError("Valor inválido")

    for indice, no in enumerate(nos):
        if no["tipo"] == "dict":
            instancias[indice].update({chave: resolver(v) for chave, v in no["dados"].items()})
        else:
            instancias[indice].extend(resolver(v) for v in no["dados"])
    return resolver(documento["raiz"])


def salvar_contas_txt(contas, caminho=ARQUIVO):
    """Grava atomicamente para não corromper o arquivo anterior."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = json.dumps(_codificar(contas), ensure_ascii=False, indent=2, allow_nan=False)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=caminho.parent, prefix=".contas-", suffix=".tmp", delete=False) as arquivo:
            temporario = arquivo.name
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario and os.path.exists(temporario):
            os.unlink(temporario)


def carregar_contas_txt(caminho=ARQUIVO):
    """Retorna None na primeira execução; não silencia arquivos corrompidos."""
    caminho = Path(caminho)
    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            contas = _decodificar(json.load(arquivo))
    except FileNotFoundError:
        return None
    if not isinstance(contas, list) or not all(isinstance(conta, dict) for conta in contas):
        raise ValueError("Base de contas inválida")
    return contas
