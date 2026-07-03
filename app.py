import os
import re
import tempfile
import subprocess
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

import streamlit as st
from faster_whisper import WhisperModel
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
import yt_dlp

st.set_page_config(page_title="Transcreve Fácil", page_icon="🎙️", layout="wide")

APP_NAME = "Transcreve Fácil"
ALLOWED_DOMAIN = "@tre-ba.jus.br"
DEFAULT_USER = "vmsoares@tre-ba.jus.br"
DEFAULT_PASSWORD = "transcreve123"

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}
SUPPORTED_EXTS = sorted(AUDIO_EXTS | VIDEO_EXTS)
SUPPORTED_URL_DOMAINS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}

# Limites conservadores para uso em Streamlit Cloud. O limite real do upload pode variar.
RECOMMENDED_MAX_MB = 150
RECOMMENDED_MAX_MINUTES = 45


# -------------------------
# Autenticação
# -------------------------
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

    if users:
        expected_password = users.get(email)
        if expected_password and password == str(expected_password):
            return True, str(profiles.get(email, "usuario"))
        return False, "E-mail ou senha inválidos."

    # Primeiro acesso/fallback. Troque por Secrets assim que o app estiver publicado.
    if email == DEFAULT_USER and password == DEFAULT_PASSWORD:
        return True, "admin"

    try:
        app_password = st.secrets.get("APP_PASSWORD", DEFAULT_PASSWORD)
    except Exception:
        app_password = DEFAULT_PASSWORD
    if email == DEFAULT_USER and password == app_password:
        return True, "admin"

    return False, "Usuário não cadastrado. Configure os usuários em Secrets."


def login_screen():
    left, right = st.columns([1.2, 1])
    with left:
        st.title("🎙️ Transcreve Fácil")
        st.subheader("Transcrição privada de vídeos e áudios")
        st.write("Uso pessoal/institucional, com acesso restrito e exportação em TXT, Word, PDF e SRT.")
        st.info("Dica: no Streamlit Cloud, use preferencialmente o modelo small e arquivos curtos ou médios.")
    with right:
        with st.form("login_form"):
            st.markdown("### Acesso institucional")
            email = st.text_input("E-mail institucional", placeholder="vmsoares@tre-ba.jus.br")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            ok, result = authenticate(email, password)
            if ok:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email.strip().lower()
                st.session_state["user_profile"] = result
                st.rerun()
            else:
                st.error(result)

        if not get_secret_dict("users"):
            with st.expander("Primeiro acesso"):
                st.write("Usuário inicial de teste:")
                st.code(f"E-mail: {DEFAULT_USER}\nSenha: {DEFAULT_PASSWORD}")
                st.write("Depois, substitua por usuários configurados em Secrets.")


def logout_button():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.caption(
            f"Usuário: {st.session_state.get('user_email', '')} | "
            f"Perfil: {st.session_state.get('user_profile', 'usuario')}"
        )
    with col2:
        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()


# -------------------------
# Utilidades
# -------------------------
def seconds_to_hhmmss(seconds: float) -> str:
    seconds = max(0, int(seconds or 0))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def safe_filename(name: str) -> str:
    stem = Path(name).stem[:80] or "transcricao"
    stem = re.sub(r"[^a-zA-Z0-9_.\-]+", "_", stem).strip("_")
    return stem or "transcricao"


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def get_duration_seconds(path: str) -> float | None:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except Exception:
        return None


def extract_audio(input_path: str, output_path: str):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path,
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2500:] if result.stderr else "Falha ao executar FFmpeg.")


def is_supported_url(url: str) -> bool:
    try:
        parsed = urlparse((url or "").strip())
        host = (parsed.netloc or "").lower()
        return parsed.scheme in {"http", "https"} and host in SUPPORTED_URL_DOMAINS
    except Exception:
        return False


def download_audio_from_url(url: str, output_dir: str) -> tuple[str, dict]:
    """Baixa apenas o áudio de uma URL compatível e converte para WAV mono 16kHz."""
    url = (url or "").strip()
    if not is_supported_url(url):
        raise ValueError("URL não suportada. Use uma URL do YouTube, como youtube.com ou youtu.be.")

    base = os.path.join(output_dir, "audio_youtube")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": base + ".%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "postprocessor_args": ["-ar", "16000", "-ac", "1"],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    wav_path = base + ".wav"
    if not os.path.exists(wav_path):
        # Fallback: procura qualquer WAV gerado pelo yt-dlp.
        matches = list(Path(output_dir).glob("audio_youtube*.wav"))
        if matches:
            wav_path = str(matches[0])
        else:
            raise RuntimeError("O áudio foi baixado, mas o arquivo WAV convertido não foi encontrado.")

    metadata = {
        "title": info.get("title") or "video_youtube",
        "duration": info.get("duration"),
        "webpage_url": info.get("webpage_url") or url,
        "uploader": info.get("uploader") or "",
    }
    return wav_path, metadata


@st.cache_resource(show_spinner=False)
def load_model(model_size: str):
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def save_docx(lines: list[str], metadata: dict) -> bytes:
    doc = Document()
    doc.add_heading("Transcrição", level=1)
    doc.add_paragraph(f"Sistema: {APP_NAME}")
    doc.add_paragraph(f"Gerada em: {metadata.get('generated_at', '')}")
    if metadata.get("filename"):
        doc.add_paragraph(f"Arquivo: {metadata['filename']}")
    if metadata.get("duration"):
        doc.add_paragraph(f"Duração estimada: {metadata['duration']}")
    doc.add_paragraph("")

    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(11)

    for line in lines:
        doc.add_paragraph(line)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.close()
    doc.save(tmp.name)
    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)
    return data


def save_pdf(lines: list[str], metadata: dict) -> bytes:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "NormalWrapped",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    story = []
    story.append(Paragraph("Transcrição", styles["Title"]))
    story.append(Paragraph(f"Sistema: {APP_NAME}", normal))
    story.append(Paragraph(f"Gerada em: {metadata.get('generated_at', '')}", normal))
    if metadata.get("filename"):
        story.append(Paragraph(f"Arquivo: {metadata['filename']}", normal))
    if metadata.get("duration"):
        story.append(Paragraph(f"Duração estimada: {metadata['duration']}", normal))
    story.append(Spacer(1, 12))

    for line in lines:
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe_line, normal))

    doc.build(story)
    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)
    return data


def build_srt(segments_data: list[dict]) -> str:
    def srt_time(seconds: float) -> str:
        seconds = max(0, float(seconds or 0))
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    blocks = []
    for i, seg in enumerate(segments_data, start=1):
        blocks.append(
            f"{i}\n{srt_time(seg['start'])} --> {srt_time(seg['end'])}\n{seg['text']}"
        )
    return "\n\n".join(blocks)


def build_prompts(plain_text: str) -> dict:
    return {
        "Revisar transcrição": (
            "Revise a transcrição abaixo, corrigindo pontuação, quebras de parágrafo "
            "e termos evidentemente incorretos, sem alterar o sentido. Preserve datas, números, "
            "nomes próprios e fundamentos citados:\n\n" + plain_text
        ),
        "Resumo objetivo": (
            "Faça um resumo objetivo da transcrição abaixo, destacando os principais pontos, "
            "decisões, orientações, datas relevantes e eventuais ressalvas:\n\n" + plain_text
        ),
        "Ata de reunião": (
            "Transforme a transcrição abaixo em uma ata formal, com pauta, participantes quando "
            "identificáveis, deliberações, encaminhamentos, pendências e observações finais:\n\n" + plain_text
        ),
        "Tabela prática": (
            "Transforme a transcrição abaixo em uma tabela prática, com colunas de tema, orientação, "
            "fundamento citado, providência e observações:\n\n" + plain_text
        ),
        "Checklist": (
            "Transforme a transcrição abaixo em um checklist de providências, separando o que deve ser feito, "
            "responsável sugerido, prazo se houver e observações:\n\n" + plain_text
        ),
        "Material de estudo": (
            "Transforme a transcrição abaixo em material de estudo, com tópicos, explicações, conceitos-chave, "
            "quadros comparativos e pontos de atenção para prova ou aplicação prática:\n\n" + plain_text
        ),
    }


def estimate_warning(file_mb: float, duration: float | None, model_size: str):
    if file_mb > RECOMMENDED_MAX_MB:
        st.warning(
            f"Arquivo com {file_mb:.1f} MB. No Streamlit Cloud, arquivos acima de "
            f"{RECOMMENDED_MAX_MB} MB podem demorar ou falhar."
        )
    if duration and duration / 60 > RECOMMENDED_MAX_MINUTES:
        st.warning(
            f"Duração estimada de {duration / 60:.1f} min. Para arquivos longos, a versão local tende a ser melhor."
        )
    if model_size != "small":
        st.warning("No Streamlit Cloud, o modelo small é o mais estável. Medium/large podem ficar lentos ou travar.")


# -------------------------
# Tela principal
# -------------------------
def app_screen():
    logout_button()
    st.title("🎙️ Transcreve Fácil")
    st.write("Transcrição privada de vídeos e áudios com exportação em TXT, Word, PDF e legenda SRT.")

    with st.sidebar:
        st.header("Configurações")
        model_size = st.selectbox("Modelo", ["small", "medium", "large-v3"], index=0)
        include_timestamps = st.checkbox("Incluir marcação de tempo no texto", value=True)
        beam_size = st.slider("Precisão da busca", min_value=1, max_value=5, value=1)
        st.caption("Use 1 para mais velocidade. Use 5 para tentar melhorar a qualidade, com mais demora.")

        st.divider()
        st.header("Limites recomendados")
        st.write(f"Arquivo: até {RECOMMENDED_MAX_MB} MB")
        st.write(f"Duração: até {RECOMMENDED_MAX_MINUTES} min")
        st.write("Modelo online: small")

        if st.button("Limpar resultado atual"):
            for key in ["last_transcription", "last_plain_text", "last_segments", "last_metadata"]:
                st.session_state.pop(key, None)
            st.success("Resultado limpo.")

    tab_transcrever, tab_resultado, tab_prompts, tab_ajuda = st.tabs(
        ["1. Transcrever", "2. Resultado", "3. Prompts", "Ajuda"]
    )

    with tab_transcrever:
        st.warning(
            "Use URLs apenas para vídeos seus, autorizados ou com permissão de uso. "
            "O recurso baixa somente o áudio para fins de transcrição privada."
        )
        origem = st.radio(
            "Fonte do conteúdo",
            ["Enviar arquivo", "URL do YouTube"],
            horizontal=True,
        )

        uploaded = None
        youtube_url = ""
        if origem == "Enviar arquivo":
            uploaded = st.file_uploader(
                "Escolha um arquivo",
                type=[ext.replace(".", "") for ext in SUPPORTED_EXTS],
                help="Formatos aceitos: áudio e vídeo. Para vídeos, o sistema extrai o áudio automaticamente.",
            )
            ready_to_transcribe = uploaded is not None
        else:
            youtube_url = st.text_input(
                "Cole a URL do YouTube",
                placeholder="https://www.youtube.com/watch?v=... ou https://youtu.be/...",
            )
            st.caption("O sistema tentará baixar somente o áudio. Vídeos privados, protegidos ou indisponíveis podem falhar.")
            ready_to_transcribe = bool(youtube_url.strip())

        if not ready_to_transcribe:
            st.info("Envie um arquivo ou cole uma URL do YouTube para começar.")
        else:
            if origem == "Enviar arquivo":
                file_mb = uploaded.size / (1024 * 1024)
                suffix = Path(uploaded.name).suffix.lower()
                display_name = uploaded.name
                display_type = "Vídeo" if suffix in VIDEO_EXTS else "Áudio"
                st.success(f"Arquivo carregado: {uploaded.name} ({file_mb:.1f} MB)")
            else:
                file_mb = 0.0
                suffix = ".url"
                display_name = youtube_url.strip()
                display_type = "YouTube"
                st.success("URL informada. O áudio será baixado ao iniciar a transcrição.")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Tamanho", f"{file_mb:.1f} MB" if origem == "Enviar arquivo" else "URL")
            with col_b:
                st.metric("Tipo", display_type)
            with col_c:
                st.metric("Modelo", model_size)

            if origem == "Enviar arquivo" and suffix not in AUDIO_EXTS and suffix not in VIDEO_EXTS:
                st.error("Formato não suportado.")
                return
            if origem == "URL do YouTube" and not is_supported_url(youtube_url):
                st.error("URL não suportada. Use uma URL do YouTube, como youtube.com ou youtu.be.")
                return

            if st.button("Transcrever", type="primary", use_container_width=True):
                progress = st.progress(0, text="Preparando...")
                status_box = st.empty()

                with tempfile.TemporaryDirectory() as tmpdir:
                    source_title = display_name
                    yt_meta = {}
                    if origem == "Enviar arquivo":
                        input_path = os.path.join(tmpdir, safe_filename(uploaded.name) + suffix)
                        with open(input_path, "wb") as f:
                            f.write(uploaded.getbuffer())

                        progress.progress(10, text="Arquivo salvo temporariamente.")
                        duration = get_duration_seconds(input_path)
                        if duration:
                            status_box.info(f"Duração estimada: {seconds_to_hhmmss(duration)}")
                        estimate_warning(file_mb, duration, model_size)

                        audio_path = input_path
                        try:
                            if suffix in VIDEO_EXTS:
                                progress.progress(25, text="Extraindo áudio do vídeo...")
                                audio_path = os.path.join(tmpdir, "audio_extraido.wav")
                                extract_audio(input_path, audio_path)
                            else:
                                progress.progress(25, text="Arquivo de áudio identificado.")
                        except Exception as e:
                            st.error("Não foi possível extrair o áudio. Confira se o FFmpeg foi instalado pelo packages.txt no Streamlit Cloud.")
                            st.exception(e)
                            return
                    else:
                        try:
                            progress.progress(15, text="Baixando áudio da URL...")
                            audio_path, yt_meta = download_audio_from_url(youtube_url, tmpdir)
                            source_title = yt_meta.get("title") or "video_youtube"
                            duration = yt_meta.get("duration") or get_duration_seconds(audio_path)
                            if duration:
                                status_box.info(f"Duração estimada: {seconds_to_hhmmss(duration)}")
                            estimate_warning(file_mb, duration, model_size)
                            progress.progress(30, text="Áudio baixado e convertido.")
                        except Exception as e:
                            st.error("Não foi possível baixar o áudio da URL. Confira se o vídeo é público, autorizado e está disponível.")
                            st.exception(e)
                            return

                    try:
                        progress.progress(40, text="Carregando modelo de transcrição...")
                        model = load_model(model_size)

                        progress.progress(55, text="Transcrevendo. Aguarde...")
                        segments, info = model.transcribe(
                            audio_path,
                            language="pt",
                            vad_filter=True,
                            beam_size=beam_size,
                        )

                        lines = []
                        plain_parts = []
                        segments_data = []
                        last_progress = 55

                        for seg in segments:
                            text = (seg.text or "").strip()
                            if not text:
                                continue
                            segments_data.append({"start": seg.start, "end": seg.end, "text": text})
                            plain_parts.append(text)
                            if include_timestamps:
                                lines.append(f"[{seconds_to_hhmmss(seg.start)} - {seconds_to_hhmmss(seg.end)}] {text}")
                            else:
                                lines.append(text)

                            if duration and duration > 0:
                                pct = 55 + min(40, int((seg.end / duration) * 40))
                                if pct > last_progress:
                                    progress.progress(pct, text=f"Transcrevendo... {min(100, int((seg.end / duration) * 100))}%")
                                    last_progress = pct

                        if not lines:
                            st.warning("Nenhuma fala foi identificada no arquivo.")
                            return

                        plain_text = "\n".join(plain_parts)
                        final_text = "\n".join(lines)
                        generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
                        metadata = {
                            "filename": source_title,
                            "file_mb": f"{file_mb:.1f} MB" if origem == "Enviar arquivo" else "URL",
                            "duration": seconds_to_hhmmss(duration) if duration else "não identificada",
                            "model": model_size,
                            "source": origem,
                            "url": yt_meta.get("webpage_url", "") if origem == "URL do YouTube" else "",
                            "uploader": yt_meta.get("uploader", "") if origem == "URL do YouTube" else "",
                            "generated_at": generated_at,
                            "language_probability": getattr(info, "language_probability", None),
                        }

                        st.session_state["last_transcription"] = final_text
                        st.session_state["last_plain_text"] = plain_text
                        st.session_state["last_segments"] = segments_data
                        st.session_state["last_metadata"] = metadata

                        progress.progress(100, text="Transcrição concluída.")
                        status_box.success("Transcrição concluída. Abra a aba Resultado para baixar os arquivos.")
                    except Exception as e:
                        st.error("Erro durante a transcrição.")
                        st.exception(e)
                        return

    with tab_resultado:
        if not st.session_state.get("last_transcription"):
            st.info("Nenhuma transcrição concluída nesta sessão.")
        else:
            final_text = st.session_state["last_transcription"]
            plain_text = st.session_state.get("last_plain_text", final_text)
            lines = final_text.splitlines()
            metadata = st.session_state.get("last_metadata", {})
            segments_data = st.session_state.get("last_segments", [])
            base_name = safe_filename(metadata.get("filename", "transcricao"))

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Arquivo", metadata.get("filename", "-")[:24])
            col2.metric("Duração", metadata.get("duration", "-"))
            col3.metric("Modelo", metadata.get("model", "-"))
            col4.metric("Trechos", str(len(segments_data)))

            st.subheader("Transcrição")
            st.text_area("Resultado", final_text, height=440)

            st.subheader("Downloads")
            dl1, dl2, dl3, dl4 = st.columns(4)
            with dl1:
                st.download_button(
                    "TXT",
                    final_text.encode("utf-8"),
                    file_name=f"{base_name}_transcricao.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with dl2:
                docx_bytes = save_docx(lines, metadata)
                st.download_button(
                    "Word",
                    docx_bytes,
                    file_name=f"{base_name}_transcricao.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            with dl3:
                pdf_bytes = save_pdf(lines, metadata)
                st.download_button(
                    "PDF",
                    pdf_bytes,
                    file_name=f"{base_name}_transcricao.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with dl4:
                srt_text = build_srt(segments_data)
                st.download_button(
                    "SRT",
                    srt_text.encode("utf-8"),
                    file_name=f"{base_name}_legenda.srt",
                    mime="text/plain",
                    use_container_width=True,
                )

    with tab_prompts:
        if not st.session_state.get("last_plain_text"):
            st.info("Conclua uma transcrição para gerar os prompts.")
        else:
            plain_text = st.session_state["last_plain_text"]
            st.write("Copie o prompt desejado e cole no ChatGPT para transformar a transcrição.")
            prompts = build_prompts(plain_text)
            for title, prompt in prompts.items():
                with st.expander(title):
                    st.text_area(title, prompt, height=220)
                    st.download_button(
                        f"Baixar prompt - {title}",
                        prompt.encode("utf-8"),
                        file_name=f"prompt_{safe_filename(title)}.txt",
                        mime="text/plain",
                    )

    with tab_ajuda:
        st.subheader("Como usar bem no Streamlit Cloud")
        st.write(
            "1. Comece com arquivos curtos.\n\n"
            "2. Use o modelo small para maior estabilidade.\n\n"
            "3. Para vídeos longos, prefira rodar a versão local no computador.\n\n"
            "4. O resultado não fica salvo permanentemente. Baixe TXT, Word ou PDF assim que terminar."
        )
        st.subheader("Configuração de usuários em Secrets")
        st.code(
            '[users]\n'
            '"vmsoares@tre-ba.jus.br" = "SUA_SENHA_FORTE"\n\n'
            '[profiles]\n'
            '"vmsoares@tre-ba.jus.br" = "admin"',
            language="toml",
        )


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
else:
    app_screen()
