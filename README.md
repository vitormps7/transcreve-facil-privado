# Transcreve Facil Privado v17

Versao de recuperacao baseada na ultima versao funcional (v6), com ajuste leve de cabecalho e logo.

## Arquivos na raiz

- app.py
- requirements.txt
- packages.txt
- runtime.txt
- README.md
- .gitignore
- assets/

## Observacao importante sobre Streamlit Cloud

Para instalar `faster-whisper`, selecione Python 3.11 nas configuracoes avancadas do deploy do Streamlit Cloud. Se o app antigo estiver preso em Python 3.13/3.14, delete o app no Streamlit Cloud e faca novo deploy escolhendo Python 3.11.
