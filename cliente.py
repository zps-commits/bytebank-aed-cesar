class Cliente:
    def __init__(self, cpf, nome, endereco, nascimento):
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Nome invalido.")
        if not isinstance(endereco, str) or not endereco.strip():
            raise ValueError("Endereco invalido.")

        self.cpf = str(cpf)
        self.nome = nome.strip()
        self.__endereco = endereco.strip()
        self.nascimento = nascimento

    def consultar_endereco(self):
        return self.__endereco

    def modificar_endereco(self, novo_endereco):
        if not isinstance(novo_endereco, str) or not novo_endereco.strip():
            return False

        self.__endereco = novo_endereco.strip()
        return True
