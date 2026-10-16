from datetime import date, datetime
import re


class Cliente:
    def __init__(self, cpf, nome, endereco, nascimento):
        if not isinstance(cpf, str) or not re.fullmatch(
            r"[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf.strip()
        ):
            raise ValueError("CPF deve conter 11 numeros.")
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Nome invalido.")
        if not isinstance(endereco, str) or not endereco.strip():
            raise ValueError("Endereco invalido.")
        try:
            data = datetime.strptime(nascimento, "%d/%m/%Y").date()
        except (ValueError, TypeError):
            raise ValueError("Nascimento deve ser uma data valida em DD/MM/AAAA.") from None
        if data > date.today():
            raise ValueError("Nascimento nao pode estar no futuro.")

        self.__cpf = re.sub(r"\D", "", cpf)
        self.nome = nome.strip()
        self.__endereco = endereco.strip()
        self.nascimento = data.strftime("%d/%m/%Y")

    @property
    def cpf(self):
        return self.__cpf

    def consultar_endereco(self):
        return self.__endereco

    def modificar_endereco(self, novo_endereco):
        if not isinstance(novo_endereco, str) or not novo_endereco.strip():
            return False

        self.__endereco = novo_endereco.strip()
        return True
