# Transcreve Facil Privado v18

Versao de recuperacao estavel para Streamlit Cloud.

## Arquivos na raiz

- app.py
- requirements.txt
- packages.txt
- runtime.txt
- README.md
- .gitignore
- assets/

## Importante

O `requirements.txt` nao instala o faster-whisper no deploy inicial. O app instala/carrega o motor de transcricao somente quando voce clicar em transcrever. Isso evita falha de deploy por dependencia pesada.

O `runtime.txt` usa `python-3.11`.

Depois de atualizar o GitHub, use Clear cache e Reboot app no Streamlit Cloud.
