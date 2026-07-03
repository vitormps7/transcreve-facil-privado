import os
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
from faster_whisper import WhisperModel
from docx import Document
import ffmpeg

st.set_page_config(
    page_title="Transcreve Fácil Privado",
    page_icon="🎙️",
    layout="wide"
)

APP_NAME = "Transcreve Fácil"
APP_SUBTITLE = "Uso privado - transcrição de vídeos e áudios"


def get_password() -> str:
    try:
        return st.secrets.get("APP_PASSWORD", "transcreve123")
    except Exception:
        return "transcreve123"


def check_password() -> bool:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title(APP_NAME)
    st.caption(APP_SUBTITLE)
    st.subheader("Acesso restrito")
    st.write("Digite a senha para acessar o sistema.")

    password = st.text_input("Senha", type="password")

    col1, col2 = st.columns([1, 3])
    with col1:
        enter = st.button("Entrar", type="primary")

    if enter:
        if password == get_password():
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    with st.expander("Primeiro acesso"):
        st.write("A senha inicial é `transcreve123`. Troque depois no Streamlit Cloud em Settings > Secrets.")
    return False


def format_time(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def extract_audio(input_path: str) -> str:
    output_path = input_path + "_audio.wav"
    (
        ffmpeg
        .input(input_path)
        .output(output_path, acodec="pcm_s16le", ac=1, ar="16000")
        .overwrite_output()
        .run(quiet=True)
    )
    return output_path


def create_docx(title: str, lines: list[str]) -> bytes:
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    doc.add_paragraph("")

    for line in lines:
        doc.add_paragraph(line)

    temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    temp_docx.close()
    doc.save(temp_docx.name)

    with open(temp_docx.name, "rb") as f:
        data = f.read()

    os.unlink(temp_docx.name)
    return data


def build_prompt(kind: str, plain_text: str) -> str:
    base = """Você receberá abaixo a transcrição de um áudio/vídeo em português. Trabalhe apenas com o conteúdo fornecido, sem inventar informações. Quando houver trecho confuso, marque como [trecho inaudível ou incerto].\n\nTRANSCRIÇÃO:\n"""
    if kind == "revisao":
        instruction = "Revise a transcrição, corrigindo pontuação, quebras de parágrafo, concordância evidente e termos técnicos prováveis. Preserve o sentido original e não invente conteúdo."
    elif kind == "resumo":
        instruction = "Faça um resumo objetivo e organizado, destacando os pontos principais, datas, leis, decisões, tarefas e conclusões."
    elif kind == "ata":
        instruction = "Transforme a transcrição em uma ata simples, com assunto, participantes quando identificáveis, pontos discutidos, deliberações e providências."
    elif kind == "tabela":
        instruction = "Transforme o conteúdo em uma tabela prática, com situação, regra/orientação, fundamento citado e observação operacional."
    elif kind == "checklist":
        instruction = "Crie um checklist operacional com as providências em ordem lógica de execução."
    else:
        instruction = "Organize o conteúdo da forma mais útil possível."
    return f"{instruction}\n\n{base}{plain_text}"


def main():
    if not check_password():
        return

    st.title(APP_NAME)
    st.caption(APP_SUBTITLE)
    st.write("Envie um arquivo de áudio ou vídeo para gerar transcrição com marcação de tempo e download em TXT ou Word.")

    with st.sidebar:
        st.header("Configurações")
        model_size = st.selectbox(
            "Modelo de transcrição",
            ["tiny", "base", "small", "medium"],
            index=2,
            help="Na nuvem, comece com small. Em computador melhor, medium tende a acertar mais."
        )
        output_mode = st.radio(
            "Formato da transcrição",
            ["Com marcação de tempo", "Texto corrido"],
            index=0
        )
        st.divider()
        st.caption("Privacidade: os arquivos temporários são apagados ao final do processamento.")
        if st.button("Sair"):
            st.session_state.authenticated = False
            st.rerun()

    uploaded_file = st.file_uploader(
        "Escolha um arquivo",
        type=["mp4", "mp3", "wav", "m4a", "mov", "avi", "mkv", "webm", "ogg", "flac", "aac"]
    )

    if not uploaded_file:
        st.info("Envie um arquivo para começar. Para o Streamlit Cloud, prefira arquivos menores no início.")
        return

    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"Arquivo carregado: {uploaded_file.name} ({file_size_mb:.1f} MB)")

    if file_size_mb > 100:
        st.warning("Arquivo grande. No Streamlit Cloud pode demorar ou falhar. Para vídeos longos, use a versão local no computador.")

    if st.button("Transcrever arquivo", type="primary"):
        suffix = Path(uploaded_file.name).suffix.lower()
        input_path = None
        audio_path = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            input_path = temp_file.name

        try:
            with st.spinner("Extraindo áudio..."):
                if suffix in [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"]:
                    audio_path = input_path
                else:
                    audio_path = extract_audio(input_path)

            with st.spinner("Carregando modelo de transcrição..."):
                model = WhisperModel(model_size, device="cpu", compute_type="int8")

            progress = st.progress(0)
            with st.spinner("Transcrevendo. Aguarde..."):
                segments, info = model.transcribe(
                    audio_path,
                    language="pt",
                    vad_filter=True,
                    beam_size=5
                )

                lines = []
                plain_parts = []
                count = 0

                for segment in segments:
                    text = segment.text.strip()
                    if not text:
                        continue
                    plain_parts.append(text)
                    if output_mode == "Com marcação de tempo":
                        lines.append(f"[{format_time(segment.start)} - {format_time(segment.end)}] {text}")
                    else:
                        lines.append(text)
                    count += 1
                    progress.progress(min(count % 100, 99))

                progress.progress(100)
                transcript = "\n".join(lines)
                plain_text = " ".join(plain_parts)

            st.session_state["last_transcript"] = transcript
            st.session_state["last_plain_text"] = plain_text
            st.session_state["last_lines"] = lines
            st.session_state["last_file_name"] = uploaded_file.name

            st.success("Transcrição concluída.")

        except Exception as e:
            st.error("Não foi possível transcrever o arquivo.")
            st.exception(e)
        finally:
            for path in [input_path, audio_path]:
                try:
                    if path and os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass

    if "last_transcript" in st.session_state:
        transcript = st.session_state["last_transcript"]
        plain_text = st.session_state["last_plain_text"]
        lines = st.session_state["last_lines"]

        st.subheader("Transcrição")
        st.text_area("Resultado", transcript, height=450)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Baixar TXT",
                data=transcript.encode("utf-8"),
                file_name="transcricao.txt",
                mime="text/plain"
            )
        with col2:
            docx_data = create_docx("Transcrição", lines)
            st.download_button(
                "Baixar Word",
                data=docx_data,
                file_name="transcricao.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        st.subheader("Texto corrido")
        st.text_area("Texto para copiar e revisar", plain_text, height=220)

        st.subheader("Prompts prontos para usar no ChatGPT")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Revisar", "Resumo", "Ata", "Tabela", "Checklist"])
        prompts = {
            "Revisar": build_prompt("revisao", plain_text),
            "Resumo": build_prompt("resumo", plain_text),
            "Ata": build_prompt("ata", plain_text),
            "Tabela": build_prompt("tabela", plain_text),
            "Checklist": build_prompt("checklist", plain_text),
        }
        for tab, name in zip([tab1, tab2, tab3, tab4, tab5], prompts.keys()):
            with tab:
                st.text_area(f"Prompt - {name}", prompts[name], height=260)
                st.download_button(
                    f"Baixar prompt de {name.lower()}",
                    data=prompts[name].encode("utf-8"),
                    file_name=f"prompt_{name.lower()}.txt",
                    mime="text/plain",
                    key=f"download_{name}"
                )


if __name__ == "__main__":
    main()
