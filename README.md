# Transcreve Fácil Privado v3

Sistema privado para transcrição de vídeos, áudios e URLs do YouTube, com login institucional e exportação em TXT, Word, PDF e SRT.

## Recursos

- Login com e-mail `@tre-ba.jus.br`.
- Upload de arquivos de áudio e vídeo.
- Campo para URL do YouTube, baixando somente o áudio para transcrição.
- Transcrição em português com Faster-Whisper.
- Barra de progresso por etapa.
- Exportação em TXT, Word, PDF e SRT.
- Prompts prontos para revisão, resumo, ata, tabela prática, checklist e material de estudo.

## Atenção sobre URLs do YouTube

Use essa função apenas para vídeos seus, autorizados ou com permissão de uso. Vídeos privados, protegidos, removidos, indisponíveis ou bloqueados podem falhar. O sistema baixa apenas o áudio temporariamente para fins de transcrição privada.

## Arquivos do repositório

- `app.py`
- `requirements.txt`
- `packages.txt`
- `README.md`

## Usuário inicial

E-mail: `vmsoares@tre-ba.jus.br`  
Senha: `transcreve123`

Troque a senha no Streamlit Cloud em **Settings > Secrets**:

```toml
[users]
"vmsoares@tre-ba.jus.br" = "SUA_SENHA_FORTE"

[profiles]
"vmsoares@tre-ba.jus.br" = "admin"
```

## Observação

No Streamlit Cloud, use preferencialmente o modelo `small`. Para arquivos longos, a versão local no computador tende a ser mais estável.
