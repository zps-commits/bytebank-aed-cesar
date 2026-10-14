# Módulos de Persistência TXT e Log HTTP

## Executar o ByteBank

```bash
python main.py
```

Na primeira execução, as contas de demonstração são disponibilizadas. Ao sair ou navegar pelos menus, o programa salva a lista de contas em `contas.txt`; em execuções posteriores, os dados são restaurados automaticamente.

A persistência mantém as referências entre contas, histórico e pilha de estornos (incluindo PIX). O arquivo é escrito de forma atômica e não é sobrescrito se estiver ilegível/corrompido. Interrupções abruptas antes do próximo salvamento podem perder as alterações mais recentes.

**Atenção:** `contas.txt` guarda dados pessoais e financeiros em texto claro para fins didáticos. Não utilize informações bancárias reais e não publique esse arquivo no GitHub.

## Analisar log HTTP

```bash
python analisador_log_http.py servidor.log
```

Reconhece linhas simples no formato `IP METODO CAMINHO STATUS` ou Apache/Nginx Common/Combined, contabilizando respostas HTTP 200 e 404 e linhas inválidas ignoradas.

## Testes

```bash
python testar_modulos.py
```

Verifica os vínculos da pilha de estornos de PIX após restauração, tratamento de arquivo ausente/inválido e contagem do log.
