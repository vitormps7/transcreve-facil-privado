# Transcreve Fácil Privado v5

Versão privada para GitHub + Streamlit Cloud.

## Recursos

- Login institucional com domínio `@tre-ba.jus.br`.
- Upload de áudio e vídeo.
- Extração de áudio com FFmpeg.
- Transcrição com Faster-Whisper.
- Exportação em TXT, Word, PDF e SRT.
- Prompts para revisão, resumo, ata, tabela, checklist e material de estudo.
- URL do YouTube mantida como recurso experimental.
- Tratamento de erro limpo, sem traceback técnico para o usuário.
- Nova aba **YouTube local**, com comandos prontos para baixar o áudio no computador quando o YouTube bloquear o Streamlit Cloud.

## Arquivos para subir no GitHub

Substitua no repositório:

- `app.py`
- `requirements.txt`
- `packages.txt`
- `README.md`

Depois faça commit e reinicie o app no Streamlit Cloud.

## Login inicial

E-mail: `vmsoares@tre-ba.jus.br`  
Senha: `transcreve123`

Recomenda-se trocar via Secrets:

```toml
[users]
"vmsoares@tre-ba.jus.br" = "SUA_SENHA_FORTE"

[profiles]
"vmsoares@tre-ba.jus.br" = "admin"
```

## Uso recomendado

No Streamlit Cloud, use preferencialmente:

- modelo `small`;
- arquivos pequenos ou médios;
- upload manual do arquivo;
- aba **YouTube local** para vídeos do YouTube que sejam seus, autorizados ou com permissão de uso.

## Observação sobre YouTube

O download direto por URL pode falhar em servidores de nuvem com erros como 403, login obrigatório ou confirmação anti-bot. Isso depende do YouTube no momento do acesso. O modo mais estável é baixar o áudio localmente com `yt-dlp` e depois enviar o MP3 pelo upload.
