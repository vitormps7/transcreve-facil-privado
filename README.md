# Transcreve Fácil - acesso institucional

Sistema privado em Streamlit para transcrição de vídeos e áudios.

## Acesso inicial

E-mail: `vmsoares@tre-ba.jus.br`
Senha: `transcreve123`

## Secrets recomendados no Streamlit Cloud

Em **Manage app > Settings > Secrets**, use:

```toml
[users]
"vmsoares@tre-ba.jus.br" = "SUA_SENHA_FORTE"

[profiles]
"vmsoares@tre-ba.jus.br" = "admin"
```

Para adicionar outro usuário:

```toml
[users]
"outro.usuario@tre-ba.jus.br" = "senha_do_usuario"

[profiles]
"outro.usuario@tre-ba.jus.br" = "usuario"
```

O sistema só aceita e-mails `@tre-ba.jus.br`.

## Arquivos importantes

- `app.py`: sistema principal
- `requirements.txt`: bibliotecas Python
- `packages.txt`: instala FFmpeg no Streamlit Cloud
