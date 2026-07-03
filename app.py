# -*- coding: utf-8 -*-
"""Transcreve Facil Privado v14 - stable recovery build.
ASCII-only source file to avoid encoding problems on Streamlit Cloud.
"""
import os
import io
import re
import zipfile
import tempfile
import subprocess
from pathlib import Path

import streamlit as st

APP_VERSION = "v14 - estavel"
APP_NAME = "Transcreve Facil"
ASSET_DIR = Path(__file__).parent / "assets"
LOGO_FULL = ASSET_DIR / "logo_full.png"
LOGO_ICON = ASSET_DIR / "logo_icon.png"

st.set_page_config(page_title=APP_NAME, page_icon=str(LOGO_ICON) if LOGO_ICON.exists() else "TF", layout="wide")

CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: linear-gradient(135deg,#f7fbff 0%,#eef7ff 45%,#ffffff 100%);}
section[data-testid="stSidebar"] {background: #f8fbff; border-right: 1px solid #d9e8fb;}
.block-container {padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1280px;}
.tf-topbar {display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:22px;}
.tf-search {flex:1; background:white; border:1px solid #dbe8fb; border-radius:18px; padding:16px 20px; color:#6b7891; box-shadow:0 12px 32px rgba(18,72,124,.07);}
.tf-user {background:white; border-radius:18px; padding:12px 18px; min-width:220px; text-align:right; box-shadow:0 12px 32px rgba(18,72,124,.08);}
.tf-hero {background:linear-gradient(135deg,#ffffff 0%,#eef8ff 100%); border:1px solid #d4e7ff; border-radius:26px; padding:34px 38px; box-shadow:0 24px 70px rgba(18,72,124,.10); margin-bottom:22px;}
.tf-title {font-size:44px; line-height:1.1; font-weight:800; color:#102342; margin:0 0 12px 0;}
.tf-sub {font-size:17px; color:#687891; margin:0 0 20px 0;}
.tf-badge {display:inline-block; padding:10px 15px; border-radius:999px; margin-right:8px; margin-bottom:8px; font-weight:700; font-size:14px;}
.tf-badge.green {background:#e6fbfb; color:#007a85; border:1px solid #b9eeee;}
.tf-badge.blue {background:#edf4ff; color:#1266e3; border:1px solid #cde0ff;}
.tf-badge.orange {background:#fff2e5; color:#ba5800; border:1px solid #ffd7ae;}
.tf-card {background:white; border:1px solid #dfeaf7; border-radius:24px; padding:24px; box-shadow:0 18px 46px rgba(18,72,124,.08); min-height:145px; margin-bottom:16px;}
.tf-card h3 {margin-top:0; color:#102342;}
.tf-card p {color:#687891;}
.tf-icon {width:54px; height:54px; border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:27px; margin-bottom:14px; box-shadow:0 12px 25px rgba(0,0,0,.08);}
.tf-icon.teal {background:#12c7c5;}
.tf-icon.blue {background:#2f7df1;}
.tf-icon.orange {background:#ff8a2b;}
.tf-icon.purple {background:#8b5cf6;}
.tf-upload {border:2px dashed #a9c6ed; background:#fbfdff; border-radius:22px; padding:28px; text-align:center; margin:14px 0 20px 0;}
.tf-note {background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; padding:14px 16px; border-radius:16px; margin:12px 0; font-weight:650;}
.tf-ok {background:#ecfdf5; border:1px solid #bbf7d0; color:#166534; padding:14px 16px; border-radius:16px; margin:12px 0; font-weight:650;}
.tf-danger {background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:14px 16px; border-radius:16px; margin:12px 0; font-weight:650;}
.tf-small {font-size:13px; color:#7a879d;}
div.stButton > button {border-radius:16px; border:1px solid #cde0ff; padding:.65rem 1rem; font-weight:750; background:white; color:#113b74;}
div.stButton > button:hover {border-color:#16bcc3; color:#007a85; background:#f0fbff;}
div[data-testid="stDownloadButton"] button {border-radius:14px; font-weight:750;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def txt(s):
    return s


def fmt_bytes(n):
    try:
        n = float(n)
    except Exception:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = 0
    while n >= 1024 and i < len(units)-1:
        n /= 1024
        i += 1
    return f"{n:.1f} {units[i]}" if i else f"{int(n)} B"


def safe_name(name):
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "arquivo")
    return name[:90]


def sec_to_srt(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ensure_auth():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if st.session_state.auth:
        return True
    col1, col2, col3 = st.columns([1, 1.25, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if LOGO_FULL.exists():
            st.image(str(LOGO_FULL), use_container_width=True)
        else:
            st.markdown("# Transcreve Facil")
        st.markdown("<div class='tf-card'>", unsafe_allow_html=True)
        st.subheader("Acesso privado")
        email = st.text_input("E-mail institucional")
        pwd = st.text_input("Senha", type="password")
        default_user = "vmsoares@tre-ba.jus.br"
        default_pass = "transcreve123"
        users = dict(st.secrets.get("users", {})) if hasattr(st, "secrets") else {}
        if not users:
            users = {default_user: default_pass}
        if st.button("Entrar", use_container_width=True):
            if email in users and pwd == users[email] and email.endswith("@tre-ba.jus.br"):
                st.session_state.auth = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("E-mail ou senha invalidos.")
        st.caption("Acesso inicial: vmsoares@tre-ba.jus.br / transcreve123. Altere em Secrets.")
        st.markdown("</div>", unsafe_allow_html=True)
    return False


def sidebar():
    with st.sidebar:
        if LOGO_FULL.exists():
            st.image(str(LOGO_FULL), use_container_width=True)
        else:
            st.markdown("## Transcreve Facil")
        st.markdown("### Navegacao")
        pages = [
            ("Inicio", "home"),
            ("Transcrever", "transcribe"),
            ("Resultado", "result"),
            ("Prompts", "prompts"),
            ("Ferramentas", "tools"),
            ("YouTube Local", "youtube"),
            ("Ajuda", "help"),
        ]
        if "page" not in st.session_state:
            st.session_state.page = "home"
        for label, key in pages:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()
        st.markdown("<div class='tf-ok'>Transcreva mais, organize melhor e economize tempo.</div>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### Configuracoes")
        st.session_state.model_size = st.selectbox("Modelo", ["small", "medium", "large-v3"], index=0)
        st.session_state.timestamps = st.checkbox("Incluir marcacao de tempo", value=True)
        if st.button("Sair", use_container_width=True):
            st.session_state.auth = False
            st.rerun()


def topbar():
    user = st.session_state.get("user_email", "usuario")
    st.markdown(f"""
    <div class='tf-topbar'>
      <div class='tf-search'>Buscar transcricoes, arquivos ou ferramentas...</div>
      <div class='tf-user'><b>{user}</b><br><span style='color:#0097a7;font-weight:700'>Uso privado</span></div>
    </div>
    """, unsafe_allow_html=True)


def hero():
    st.markdown("""
    <div class='tf-hero'>
      <div class='tf-title'>Transcritor de Videos e Audios</div>
      <div class='tf-sub'>Envie arquivos, fragmente midias, compacte documentos e gere transcricoes em TXT, Word, PDF e SRT.</div>
      <span class='tf-badge green'>Recomendado: upload manual</span>
      <span class='tf-badge blue'>YouTube: recurso experimental</span>
      <span class='tf-badge orange'>Modelo online sugerido: small</span>
    </div>
    """, unsafe_allow_html=True)


def page_home():
    hero()
    c1, c2, c3 = st.columns(3)
    cards = [
        (c1, "teal", "Arquivos processados", "Transcreva videos, audios e gere downloads editaveis em TXT, Word, PDF e SRT."),
        (c2, "blue", "Tempo economizado", "Transforme aulas, reunioes e treinamentos em texto pesquisavel em poucos passos."),
        (c3, "orange", "Ferramentas integradas", "Fragmentador, compactador, PDF, Word, TXT e legendas SRT no mesmo ambiente."),
    ]
    for col, color, title, body in cards:
        with col:
            st.markdown(f"<div class='tf-card'><div class='tf-icon {color}'>#</div><h3>{title}</h3><p>{body}</p></div>", unsafe_allow_html=True)
    st.markdown("## Ferramentas rapidas")
    b1, b2, b3, b4 = st.columns(4)
    quicks = [(b1,"Fragmentador","tools"),(b2,"Compactador","tools"),(b3,"Exportar PDF","result"),(b4,"Legenda SRT","result")]
    for col, label, target in quicks:
        with col:
            st.markdown(f"<div class='tf-card'><h3>{label}</h3><p>Acesse pelo botao abaixo.</p></div>", unsafe_allow_html=True)
            if st.button(f"Abrir {label}", key=f"quick_{label}", use_container_width=True):
                st.session_state.page = target
                st.rerun()


def save_upload(uploaded, tmpdir):
    path = Path(tmpdir) / safe_name(uploaded.name)
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path


def is_video(path):
    return path.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"]


def extract_audio(input_path, tmpdir):
    if not is_video(input_path):
        return input_path
    out = Path(tmpdir) / "audio_extraido.wav"
    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-vn", "-ac", "1", "-ar", "16000", str(out)]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError("Nao foi possivel extrair audio. Verifique se o FFmpeg esta disponivel.")
    return out


def run_transcription(audio_path, model_size):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(audio_path), language="pt", vad_filter=True)
    data = []
    plain = []
    timed = []
    for seg in segments:
        text = (seg.text or "").strip()
        data.append({"start": float(seg.start), "end": float(seg.end), "text": text})
        plain.append(text)
        timed.append(f"[{sec_to_srt(float(seg.start))} --> {sec_to_srt(float(seg.end))}] {text}")
    return data, "\n".join(plain), "\n".join(timed)


def make_txt(text):
    return text.encode("utf-8")


def make_docx(text):
    from docx import Document
    bio = io.BytesIO()
    doc = Document()
    doc.add_heading("Transcricao", level=1)
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(bio)
    return bio.getvalue()


def make_pdf(text):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4
    y = height - 2*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, "Transcricao")
    y -= 1*cm
    c.setFont("Helvetica", 10)
    for line in text.splitlines():
        words = line.split()
        buf = ""
        for w in words:
            if len(buf + " " + w) > 92:
                c.drawString(2*cm, y, buf)
                y -= 0.5*cm
                buf = w
                if y < 2*cm:
                    c.showPage(); y = height - 2*cm; c.setFont("Helvetica", 10)
            else:
                buf = (buf + " " + w).strip()
        if buf:
            c.drawString(2*cm, y, buf)
            y -= 0.5*cm
        if y < 2*cm:
            c.showPage(); y = height - 2*cm; c.setFont("Helvetica", 10)
    c.save()
    return bio.getvalue()


def make_srt(segments):
    out = []
    for i, seg in enumerate(segments, 1):
        out.append(str(i))
        out.append(f"{sec_to_srt(seg['start'])} --> {sec_to_srt(seg['end'])}")
        out.append(seg["text"])
        out.append("")
    return "\n".join(out).encode("utf-8")


def page_transcribe():
    st.markdown("# Transcrever")
    st.markdown("<div class='tf-upload'><h3>Envie seu arquivo de audio ou video</h3><p>Formatos: MP3, MP4, WAV, M4A, MOV, AAC, WEBM e similares.</p></div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Escolha um arquivo", type=["mp3","mp4","wav","m4a","mov","aac","ogg","flac","webm","mkv","avi","mpeg","mpg"])
    if uploaded:
        st.info(f"Arquivo carregado: {uploaded.name} - {fmt_bytes(uploaded.size)}")
    if st.button("Transcrever agora", type="primary", use_container_width=True, disabled=(uploaded is None)):
        try:
            progress = st.progress(0, text="Preparando arquivo...")
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = save_upload(uploaded, tmpdir)
                progress.progress(20, text="Extraindo audio...")
                audio_path = extract_audio(input_path, tmpdir)
                progress.progress(45, text="Carregando modelo...")
                segs, plain, timed = run_transcription(audio_path, st.session_state.get("model_size", "small"))
                progress.progress(100, text="Concluido")
            st.session_state.last_segments = segs
            st.session_state.last_plain = plain
            st.session_state.last_timed = timed
            st.session_state.last_file = uploaded.name
            st.success("Transcricao concluida. Acesse a pagina Resultado.")
        except Exception as e:
            st.error(f"Erro ao transcrever: {e}")


def page_result():
    st.markdown("# Resultado")
    text = st.session_state.get("last_timed" if st.session_state.get("timestamps", True) else "last_plain", "")
    if not text:
        st.warning("Ainda nao ha transcricao. Va em Transcrever e envie um arquivo.")
        return
    st.text_area("Transcricao", text, height=420)
    name = safe_name(Path(st.session_state.get("last_file", "transcricao")).stem)
    c1,c2,c3,c4 = st.columns(4)
    c1.download_button("Baixar TXT", make_txt(text), file_name=f"{name}.txt", mime="text/plain", use_container_width=True)
    c2.download_button("Baixar Word", make_docx(text), file_name=f"{name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    c3.download_button("Baixar PDF", make_pdf(text), file_name=f"{name}.pdf", mime="application/pdf", use_container_width=True)
    c4.download_button("Baixar SRT", make_srt(st.session_state.get("last_segments", [])), file_name=f"{name}.srt", mime="text/plain", use_container_width=True)
    if st.button("Limpar resultado"):
        for k in ["last_segments","last_plain","last_timed","last_file"]:
            st.session_state.pop(k, None)
        st.rerun()


def page_prompts():
    st.markdown("# Prompts")
    base = st.session_state.get("last_plain", "")
    if not base:
        st.warning("Transcreva um arquivo primeiro para gerar prompts completos.")
    choices = {
        "Tabela pratica": "Transforme a transcricao abaixo em uma tabela pratica, com colunas de tema, orientacao, fundamento citado, providencia e observacoes.",
        "Resumo executivo": "Resuma a transcricao abaixo de forma objetiva, separando pontos principais, alertas e providencias.",
        "Ata de reuniao": "Transforme a transcricao abaixo em uma ata formal, com participantes, pauta, deliberacoes e encaminhamentos.",
        "Checklist": "Transforme a transcricao abaixo em um checklist de providencias praticas.",
        "Material de estudo": "Transforme a transcricao abaixo em material de estudo esquematizado, com conceitos, exemplos e quadro-resumo.",
    }
    opt = st.selectbox("Modelo de prompt", list(choices.keys()))
    prompt = choices[opt] + "\n\nTRANSCRICAO:\n" + (base[:12000] if base else "cole aqui a transcricao")
    st.text_area("Prompt", prompt, height=420)


def split_file_bytes(data, size_mb):
    size = int(size_mb * 1024 * 1024)
    return [data[i:i+size] for i in range(0, len(data), size)]


def page_tools():
    st.markdown("# Ferramentas")
    tabs = st.tabs(["Fragmentar arquivo", "Compactar ZIP", "Compactar midia"])
    with tabs[0]:
        f = st.file_uploader("Arquivo para fragmentar", key="frag")
        mb = st.number_input("Tamanho de cada parte em MB", min_value=1, max_value=500, value=50)
        if f and st.button("Fragmentar", use_container_width=True):
            parts = split_file_bytes(f.getvalue(), mb)
            bio = io.BytesIO()
            with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
                for i,p in enumerate(parts, 1):
                    z.writestr(f"{safe_name(f.name)}.parte_{i:03d}", p)
            st.download_button("Baixar partes em ZIP", bio.getvalue(), file_name="partes.zip", mime="application/zip")
    with tabs[1]:
        files = st.file_uploader("Arquivos para compactar em ZIP", accept_multiple_files=True, key="zip")
        if files and st.button("Gerar ZIP", use_container_width=True):
            bio = io.BytesIO()
            with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
                for f in files:
                    z.writestr(safe_name(f.name), f.getvalue())
            st.download_button("Baixar ZIP", bio.getvalue(), file_name="arquivos.zip", mime="application/zip")
    with tabs[2]:
        st.markdown("<div class='tf-note'>Para video/audio, ZIP geralmente reduz pouco. Esta opcao usa FFmpeg para gerar arquivo menor.</div>", unsafe_allow_html=True)
        media = st.file_uploader("Midia para compactar", type=["mp4","mov","avi","mkv","webm","mp3","wav","m4a"], key="media_comp")
        if media and st.button("Compactar midia", use_container_width=True):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    inp = save_upload(media, tmpdir)
                    out = Path(tmpdir) / (Path(safe_name(media.name)).stem + "_compactado.mp4")
                    cmd = ["ffmpeg", "-y", "-i", str(inp), "-vcodec", "libx264", "-crf", "28", "-preset", "veryfast", "-acodec", "aac", "-b:a", "96k", str(out)]
                    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if p.returncode != 0:
                        raise RuntimeError("Falha ao compactar midia com FFmpeg.")
                    data = out.read_bytes()
                st.download_button("Baixar midia compactada", data, file_name=out.name, mime="video/mp4")
            except Exception as e:
                st.error(str(e))


def page_youtube():
    st.markdown("# YouTube Local")
    st.markdown("<div class='tf-note'>Use apenas em videos seus, autorizados ou permitidos. Este metodo evita bloqueios do Streamlit Cloud.</div>", unsafe_allow_html=True)
    url = st.text_input("Cole a URL")
    if url:
        cmd = f'yt-dlp -x --audio-format mp3 "{url}"'
        st.code(cmd, language="bash")
        st.markdown("Depois de gerar o MP3 no computador, volte em Transcrever e envie o arquivo.")


def page_help():
    st.markdown("# Ajuda")
    st.markdown("""
    1. Use Transcrever para enviar audio ou video.
    2. Use Resultado para baixar TXT, Word, PDF ou SRT.
    3. Use Prompts para transformar a transcricao em resumo, ata, tabela ou checklist.
    4. Use Ferramentas para fragmentar ou compactar arquivos.
    5. Use YouTube Local quando o YouTube bloquear downloads no Streamlit Cloud.
    """)


def main():
    if not ensure_auth():
        return
    sidebar()
    topbar()
    page = st.session_state.get("page", "home")
    if page == "home":
        page_home()
    elif page == "transcribe":
        page_transcribe()
    elif page == "result":
        page_result()
    elif page == "prompts":
        page_prompts()
    elif page == "tools":
        page_tools()
    elif page == "youtube":
        page_youtube()
    else:
        page_help()
    st.caption(f"Transcreve Facil Privado - {APP_VERSION}")


if __name__ == "__main__":
    main()
