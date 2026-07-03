# Transcreve Facil Privado v8

Versao corrigida com interface premium e funcoes restauradas.

## Como atualizar

Envie para o GitHub, substituindo os arquivos antigos:

- app.py
- requirements.txt
- packages.txt
- runtime.txt
- README.md
- assets/

Depois, no Streamlit Cloud, use **Reboot app**.

## Acesso inicial

- Email: vmsoares@tre-ba.jus.br
- Senha: transcreve123

Para trocar, configure no Streamlit Secrets:

```toml
[users]
"vmsoares@tre-ba.jus.br" = "SUA_SENHA"

[profiles]
"vmsoares@tre-ba.jus.br" = "admin"
```
