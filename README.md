# Transcreve Fácil Privado v7

Versão privada para GitHub + Streamlit Cloud, com nova identidade visual, logo, interface com cards, botões arredondados, ícones coloridos em estilo flat e ferramentas integradas.

## Recursos principais

- Login institucional com e-mail `@tre-ba.jus.br`.
- Interface visual premium com logo do Transcreve Fácil.
- Upload de áudio e vídeo.
- Transcrição com Faster-Whisper.
- Exportação em TXT, Word, PDF e SRT.
- URL do YouTube como recurso experimental.
- Modo YouTube local recomendado.
- Fragmentador de mídia por duração.
- Fragmentador de qualquer arquivo por tamanho.
- Compactador ZIP.
- Compactador de áudio/vídeo por reencodação.
- Prompts prontos para revisão, resumo, ata, tabela prática, checklist e material de estudo.

## Arquivos do repositório

A estrutura deve ficar assim na raiz do GitHub:

```text
app.py
requirements.txt
packages.txt
README.md
assets/
  logo_full.png
  logo_icon.png
  ui_concept.png
```

## Atualização no GitHub

1. Extraia o ZIP.
2. Substitua no repositório os arquivos `app.py`, `requirements.txt`, `packages.txt` e `README.md`.
3. Envie também a pasta `assets` completa.
4. Faça `Commit changes`.
5. No Streamlit Cloud, clique em `Manage app` > `Reboot app`.

## Acesso inicial

```text
E-mail: vmsoares@tre-ba.jus.br
Senha: transcreve123
```

Depois, configure usuários no `Secrets` do Streamlit:

```toml
[users]
"vmsoares@tre-ba.jus.br" = "SUA_SENHA_FORTE"

[profiles]
"vmsoares@tre-ba.jus.br" = "admin"
```

## Observação sobre ícones

A interface usa ícones próprios/emoji e elementos visuais em estilo flat, evitando dependência externa de bibliotecas de ícones e problemas de licença. Caso deseje usar ícones oficiais do Flaticon, baixe-os com a licença adequada e substitua os arquivos na pasta `assets`.
