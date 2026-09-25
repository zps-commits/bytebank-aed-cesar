# ByteBank

Projeto de banco em Python para a disciplina de Algoritmos e Estruturas de Dados. O programa roda no terminal e permite gerenciar contas, fazer movimentações e consultar relatórios.

**Integrantes:** Zion e Vinicius.

## Como executar

É necessário ter Python 3 instalado. No terminal, dentro da pasta do projeto, execute:

```bash
python main.py
```

Se o comando `python` não funcionar, tente `python3 main.py`.

Na tela inicial, escolha **1** para entrar em uma conta ou **2** para criar uma. Para criar a conta, informe nome, CPF, chave PIX e um PIN de quatro números. Contas novas começam com saldo zero; você pode depositar dinheiro no menu **Conta**.

Para testar sem criar uma conta, use um dos acessos de exemplo:

| Nome | Número da conta | CPF | PIN |
| --- | --- | --- | --- |
| Ana | `1001` | `11111111111` | `1234` |
| Bruno | `1002` | `22222222222` | `4321` |

O login aceita o número da conta ou o CPF. Escolha **0** para sair da conta e voltar à tela inicial.

## Menu principal

Depois do login, as operações ficam organizadas em nove grupos:

| Opção | Grupo | O que permite fazer |
| --- | --- | --- |
| 1 | Conta | Consultar saldo e dados pessoais, depositar, sacar, ver histórico, estornar e consultar entradas e saídas. |
| 2 | PIX | Transferir para outra conta usando a chave PIX de destino. |
| 3 | Cofrinhos | Criar, guardar, resgatar e simular rendimento. |
| 4 | Cartão | Comprar no crédito, consultar e pagar a fatura. |
| 5 | Pagamentos | Agendar pagamentos e processar o primeiro da fila. |
| 6 | Gastos | Consultar gastos por categoria e definir o orçamento. |
| 7 | Moedas | Consultar, comprar e vender USD, EUR e BTC. |
| 8 | BytePoints | Consultar pontos e resgatar cashback. |
| 9 | Empréstimos | Simular, contratar, consultar e pagar parcelas. |

Em cada grupo, a opção **0** volta ao menu anterior. Uma opção inválida mostra um aviso.

## Operações principais

### Dados da conta

Entre em **Conta > Dados da conta** para ver nome, CPF, chave PIX e número da conta. É preciso confirmar o PIN antes de exibir os dados. O PIN não é listado entre as informações; por usar a entrada normal do terminal, os números digitados podem ficar visíveis durante a confirmação.

### Cofrinhos

Em **Cofrinhos > Criar cofrinho**, escolha um nome e, se quiser, um valor inicial. Pressione Enter no valor para criar o cofrinho vazio. Também é possível escolher **Depositar no cofrinho** e criar um ali mesmo, caso ainda não exista nenhum.

Para guardar ou resgatar dinheiro, selecione o cofrinho pelo **número mostrado na lista**. A lista exibe os nomes e os saldos, então não é preciso lembrar ou digitar o nome. O depósito usa o saldo da conta corrente; o resgate devolve o valor para ela.

A opção **Simular rendimento** aplica juros simples de **0,5% ao mês** aos saldos dos cofrinhos. Ela mostra o ganho de cada um e o total. **A simulação altera o saldo dos cofrinhos**; para apenas consultar o valor atual, use **Consultar cofrinhos**.

### Empréstimos

O limite para contratar é de até **três vezes o saldo atual** da conta, com parcelamento de **1 a 360 vezes**. Você pode dar um nome ao empréstimo ou deixar o campo em branco para receber um nome automático. Para pagar, escolha pelo número na lista de dívidas pendentes; o valor da próxima parcela aparece na tela. O pagamento exige saldo suficiente.

### Relatórios e outras regras

- **Conta > Entradas e saídas por período:** escolha semana, mês ou semestre e informe uma data de referência no formato `DD/MM/AAAA`. Enter usa a data atual. O relatório mostra movimentações, totais de entradas e saídas e a diferença entre eles.
- **Gastos > Relatório por categoria:** soma os gastos registrados em cada categoria e compara os totais com o orçamento informado. Esse relatório considera o histórico acumulado da conta.
- **Saque:** limite de **R$ 500,00 por operação**, respeitando o saldo disponível.
- **PIX:** exige uma chave de destino cadastrada e saldo suficiente; não transfere para a própria conta.
- **Cartão:** uma compra usa o limite disponível e aumenta a fatura; pagar a fatura usa o saldo da conta.
- **Pagamentos:** agendar apenas coloca a operação na fila. É preciso selecionar **Processar próximo pagamento** para descontar o primeiro item, desde que haja saldo.
- **BytePoints:** saques e PIX enviados rendem **1 ponto a cada R$ 10,00**; **100 pontos equivalem a R$ 5,00** em cashback.
- **Estorno:** desfaz a última transação quando ainda for possível reverter seus efeitos.

Valores em reais aceitam, por exemplo, `10,50`, `10.50` e `1.234,56`. Valores inválidos são recusados; saídas que exigem mais dinheiro do que o disponível também. Datas informadas ao programa usam o formato `DD/MM/AAAA`.

## Estruturas de dados utilizadas

- **Lista de dicionários:** contas e dados de cada cliente.
- **Dicionários:** cofrinhos, saldos em outras moedas e totais por categoria.
- **Pilha (LIFO):** estorno da última transação reversível.
- **Fila (FIFO):** ordem de processamento dos pagamentos agendados.
- **Listas de transações:** histórico, compras no crédito e parcelas de empréstimos.

## Testes

Para executar os testes automatizados, na pasta do projeto rode:

```bash
python -m unittest -v
```

Os testes cobrem operações, menus, entradas inválidas, PIN, saldo insuficiente, seleção de cofrinhos, pagamentos, empréstimos, estornos e relatórios.

## Observações

Os dados ficam **somente na memória**: ao fechar o programa, contas criadas e transações são perdidas. As contas e os PINs de exemplo servem apenas para demonstração. Este projeto é uma simulação acadêmica, não um serviço bancário real.
