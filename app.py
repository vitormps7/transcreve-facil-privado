import os
import re
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

import streamlit as st
from faster_whisper import WhisperModel
from docx import Document

st.set_page_config(page_title="Transcreve Fácil", page_icon="🎙️", layout="wide")

APP_NAME = "Transcreve Fácil"
ALLOWED_DOMAIN = "@tre-ba.jus.br"
DEFAULT_USER = "vmsoares@tre-ba.jus.br"
DEFAULT_PASSWORD = "transcreve123"

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}


def get_secret_dict(section_name: str) -> dict:
    try:
        section = st.secrets.get(section_name, {})
        return dict(section)
    except Exception:
        return {}


def valid_institutional_email(email: str) -> bool:
    email = (email or "").strip().lower()
    if not email.endswith(ALLOWED_DOMAIN):
        return False
    return re.match(r"^[a-z0-9._%+\-]+@tre-ba\.jus\.br$", email) is not None


def authenticate(email: str, password: str) -> tuple[bool, str]:
    email = (email or "").strip().lower()
    password = password or ""

    if not valid_institutional_email(email):
        return False, "Use um e-mail institucional @tre-ba.jus.br."

    users = get_secret_dict("users")
    profiles = get_secret_dict("profiles")

    # Modo recomendado: usuários definidos nos Secrets do Streamlit Cloud.
    # Exemplo:
    # [users]
    # "vmsoares@tre-ba.jus.br" = "senha"
    # [profiles]
    # "vmsoares@tre-ba.jus.br" = "admin"
    if users:
        expected_password = users.get(email)
        if expected_password and password == str(expected_password):
            return True, str(profiles.get(email, "usuario"))
        return False, "E-mail ou senha inválidos."

    # Modo inicial/fallback para o primeiro acesso.
    if email == DEFAULT_USER and password == DEFAULT_PASSWORD:
        return True, "admin"

    # Também aceita APP_PASSWORD antigo apenas para o usuário padrão.
    try:
        app_password = st.secrets.get("APP_PASSWORD", DEFAULT_PASSWORD)
    except Exception:
        app_password = DEFAULT_PASSWORD
    if email == DEFAULT_USER and password == app_password:
        return True, "admin"

    return False, "Usuário não cadastrado. Configure os usuários em Secrets."


def login_screen():
    st.title(APP_NAME)
    st.subheader("Acesso institucional")
    st.caption("Uso privado. Acesso restrito a e-mails institucionais @tre-ba.jus.br.")

    with st.form("login_form"):
        email = st.text_input("E-mail institucional", placeholder="vmsoares@tre-ba.jus.br")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        ok, result = authenticate(email, password)
        if ok:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email.strip().lower()
            st.session_state["user_profile"] = result
            st.rerun()
        else:
            st.error(result)

    with st.expander("Primeiro acesso"):
        st.write("Usuário inicial de teste:")
        st.code(f"E-mail: {DEFAULT_USER}\nSenha: {DEFAULT_PASSWORD}")
        st.write("Depois troque pelos Secrets do Streamlit Cloud.")


def logout_button():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption(f"Usuário: {st.session_state.get('user_email', '')} | Perfil: {st.session_state.get('user_profile', 'usuario')}")
    with col2:
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()


def seconds_to_hhmmss(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def extract_audio(input_path: str, output_path: str):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] if result.stderr else "Falha ao executar FFmpeg.")


def save_docx(lines: list[str], plain_text: str) -> bytes:
    doc = Document()
    doc.add_heading("Transcrição", level=1)
    doc.add_paragraph(f"Gerada em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    doc.add_paragraph(f"Sistema: {APP_NAME}")
    doc.add_paragraph("")
    for line in lines:
        doc.add_paragraph(line)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.close()
    doc.save(tmp.name)
    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)
    return data


def build_prompts(plain_text: str) -> dict:
    return {
        "Revisar transcrição": "Revise a transcrição abaixo, corrigindo pontuação, quebras de parágrafo e termos evidentemente incorretos, sem alterar o sentido:\n\n" + plain_text,
        "Resumo objetivo": "Faça um resumo objetivo da transcrição abaixo, destacando os principais pontos, decisões, orientações e datas relevantes:\n\n" + plain_text,
        "Ata de reunião": "Transforme a transcrição abaixo em uma ata formal, com pauta, participantes quando identificáveis, deliberações, encaminhamentos e pendências:\n\n" + plain_text,
        "Tabela prática": "Transforme a transcrição abaixo em uma tabela prática, com colunas de tema, orientação, fundamento citado, providência e observações:\n\n" + plain_text,
        "Checklist": "Transforme a transcrição abaixo em um checklist de providências, separando o que deve ser feito, responsável sugerido, prazo se houver e observações:\n\n" + plain_text,
    }


def app_screen():
    logout_button()
    st.title("🎙️ Transcreve Fácil")
    st.write("Transcrição privada de vídeos e áudios, com acesso institucional e exportação em TXT/Word.")

    with st.sidebar:
        st.header("Configurações")
        model_size = st.selectbox("Modelo", ["small", "medium", "large-v3"], index=0)
        st.caption("No Streamlit Cloud, prefira small. Para arquivos longos, use a versão local.")
        include_timestamps = st.checkbox("Incluir marcação de tempo", value=True)

    uploaded = st.file_uploader(
        "Escolha um arquivo",
        type=["mp3", "wav", "m4a", "ogg", "flac", "aac", "mp4", "mov", "avi", "mkv", "webm", "mpeg", "mpg"],
    )

    if not uploaded:
        st.info("Envie um arquivo para começar.")
        return

    st.success(f"Arquivo carregado: {uploaded.name} ({uploaded.size / (1024*1024):.1f} MB)")

    if st.button("Transcrever arquivo", type="primary"):
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in AUDIO_EXTS and suffix not in VIDEO_EXTS:
            st.error("Formato não suportado.")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, uploaded.name)
            with open(input_path, "wb") as f:
                f.write(uploaded.read())

            audio_path = input_path
            try:
                if suffix in VIDEO_EXTS:
                    st.info("Extraindo áudio do vídeo...")
                    audio_path = os.path.join(tmpdir, "audio_extraido.wav")
                    extract_audio(input_path, audio_path)
            except Exception as e:
                st.error("Não foi possível extrair o áudio. Confira se o FFmpeg foi instalado pelo packages.txt no Streamlit Cloud.")
                st.exception(e)
                return

            try:
                st.info("Carregando modelo de transcrição...")
                model = WhisperModel(model_size, device="cpu", compute_type="int8")

                st.info("Transcrevendo. Aguarde...")
                segments, info = model.transcribe(audio_path, language="pt", vad_filter=True)

                lines = []
                plain_parts = []
                for seg in segments:
                    text = seg.text.strip()
                    if not text:
                        continue
                    plain_parts.append(text)
                    if include_timestamps:
                        lines.append(f"[{seconds_to_hhmmss(seg.start)} - {seconds_to_hhmmss(seg.end)}] {text}")
                    else:
                        lines.append(text)

                if not lines:
                    st.warning("Nenhuma fala foi identificada no arquivo.")
                    return

                plain_text = "\n".join(plain_parts)
                final_text = "\n".join(lines)
                st.session_state["last_transcription"] = final_text
                st.session_state["last_plain_text"] = plain_text

                st.success("Transcrição concluída.")
            except Exception as e:
                st.error("Erro durante a transcrição.")
                st.exception(e)
                return

    if st.session_state.get("last_transcription"):
        final_text = st.session_state["last_transcription"]
        plain_text = st.session_state.get("last_plain_text", final_text)

        st.subheader("Resultado")
        st.text_area("Transcrição", final_text, height=420)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Baixar TXT", final_text.encode("utf-8"), file_name="transcricao.txt", mime="text/plain")
        with col2:
            docx_bytes = save_docx(final_text.splitlines(), plain_text)
            st.download_button("Baixar Word", docx_bytes, file_name="transcricao.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        st.subheader("Prompts para usar no ChatGPT")
        prompts = build_prompts(plain_text)
        for title, prompt in prompts.items():
            with st.expander(title):
                st.text_area(title, prompt, height=180)


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
else:
    app_screen()
