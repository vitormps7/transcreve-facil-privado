# Transcreve Fácil Privado

Sistema privado em Streamlit para transcrever vídeos e áudios em português.

## Recursos

- Upload de vídeo ou áudio.
- Extração automática do áudio com FFmpeg.
- Transcrição com Faster-Whisper.
- Marcação de tempo.
- Download em TXT e Word.
- Senha de acesso.
- Prompts prontos para revisão, resumo, ata, tabela e checklist no ChatGPT.

## Senha inicial

A senha inicial é:

```text
transcreve123
```

Troque a senha no Streamlit Cloud em `Settings > Secrets`.

## Rodar no computador

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar no Streamlit Cloud

1. Crie um repositório privado no GitHub chamado `transcreve-facil-privado`.
2. Envie estes arquivos para o repositório:
   - `app.py`
   - `requirements.txt`
   - `packages.txt`
   - `README.md`
   - `.gitignore`
3. Entre no Streamlit Cloud.
4. Clique em `New app`.
5. Escolha o repositório.
6. Em `Main file path`, coloque:

```text
app.py
```

7. Clique em `Deploy`.

## Trocar a senha no Streamlit Cloud

No app publicado:

1. Acesse `Settings`.
2. Entre em `Secrets`.
3. Cole:

```toml
APP_PASSWORD = "sua_senha_segura_aqui"
```

4. Salve.
5. Reinicie o app.

## Observações

- No Streamlit Cloud, comece usando o modelo `small`.
- Arquivos grandes podem demorar ou falhar na nuvem.
- Para vídeos longos, prefira rodar no computador.
- O app apaga arquivos temporários ao final do processamento.
