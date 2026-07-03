# Transcreve Facil Privado v10

Versao funcional estabilizada, com interface premium, menu por botoes, login com logo e codigo-fonte ASCII para evitar erros de codificacao no Streamlit Cloud.

## Atualizacao

Substitua no GitHub:

- app.py
- requirements.txt
- packages.txt
- runtime.txt
- README.md
- assets/
- .gitignore

Depois clique em Commit changes e reinicie o app no Streamlit Cloud.

## Login inicial

E-mail: vmsoares@tre-ba.jus.br  
Senha: transcreve123

Troque a senha em Streamlit Secrets:

```toml
[users]
"vmsoares@tre-ba.jus.br" = "sua_senha"
```
