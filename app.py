# -*- coding: utf-8 -*-
"""Transcreve Facil Privado v11.
Stable UI + functional pages. Source kept ASCII-safe.
"""

import io
import os
import zipfile
import tempfile
import subprocess
from pathlib import Path

import streamlit as st

APP_TITLE = "Transcreve Facil"
APP_VERSION = "v11 - funcional com interface premium"
BASE_DIR = Path(__file__).parent
ASSET_DIR = BASE_DIR / "assets"
LOGO_FULL = ASSET_DIR / "logo_full.png"
LOGO_ICON = ASSET_DIR / "logo_icon.png"

st.set_page_config(page_title=APP_TITLE, page_icon="🎙️", layout="wide")

CSS = """
<style>
:root{--blue:#073b91;--cyan:#05b9c8;--ink:#13233f;--muted:#6b7a99;--orange:#ff7a1a;}
html,body,[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#f7fbff 0%,#edf6ff 100%);}
[data-testid="stSidebar"]{background:#f8fbff;border-right:1px solid #dbe9fb;}
.block-container{padding-top:1.1rem;max-width:1320px;}
.tf-card{background:rgba(255,255,255,.94);border:1px solid #dbe8fb;border-radius:24px;padding:26px;box-shadow:0 18px 45px rgba(31,81,143,.10);margin-bottom:18px;}
.tf-hero{background:linear-gradient(135deg,#fff 0%,#eaf8ff 100%);border:1px solid #d3e6ff;border-radius:28px;padding:32px;box-shadow:0 18px 45px rgba(31,81,143,.12);margin-bottom:18px;}
.tf-title{font-size:42px;line-height:1.05;font-weight:850;color:var(--ink);margin:0 0 12px 0;}
.tf-sub{color:var(--muted);font-size:17px;}
.tf-pill{display:inline-block;padding:9px 14px;margin:4px 8px 4px 0;border-radius:999px;font-weight:750;font-size:14px;border:1px solid #cfe2fb;}
.tf-pill.teal{background:#e8fbfd;color:#007c88;}.tf-pill.blue{background:#eef5ff;color:#0b62e5;}.tf-pill.orange{background:#fff4e9;color:#c75500;border-color:#ffd9b7;}
.tf-iconbox{width:58px;height:58px;border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:26px;color:white;font-weight:800;margin-bottom:18px;box-shadow:0 12px 28px rgba(0,0,0,.10);}
.tf-bg-teal{background:linear-gradient(135deg,#05c9c8,#0798da);}.tf-bg-blue{background:linear-gradient(135deg,#1a73ff,#0f5bd7);}.tf-bg-orange{background:linear-gradient(135deg,#ff8a28,#ff6b00);}.tf-bg-purple{background:linear-gradient(135deg,#855cf5,#6b43db);}
.tf-topbar{background:#fff;border:1px solid #e1ebf7;border-radius:22px;padding:13px 17px;box-shadow:0 12px 30px rgba(31,81,143,.08);margin-bottom:16px;}
.tf-note{background:#ecfbff;border:1px solid #bdeff6;color:#006d78;padding:12px 14px;border-radius:16px;font-weight:650;}
.tf-warn{background:#fff4e9;border:1px solid #ffd9b7;color:#a24800;padding:12px 14px;border-radius:16px;font-weight:650;}
.tf-error{background:#fff2f2;border:1px solid #ffd0d0;color:#a31515;padding:12px 14px;border-radius:16px;font-weight:650;}
.stButton>button{border-radius:16px!important;min-height:44px!important;font-weight:750!important;border:1px solid #d9e6f6!important;}
.stDownloadButton>button{border-radius:16px!important;min-height:44px!important;font-weight:750!important;}
button[kind="primary"]{background:linear-gradient(135deg,#0b73ff,#05b9c8)!important;border:0!important;color:white!important;}
[data-testid="stFileUploaderDropzone"]{border:2px dashed #a9caf5;border-radius:24px;background:#fbfdff;}
hr{border-color:#e5eefb;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def safe_logo(width=280):
    try:
        if LOGO_FULL.exists():
            st.image(str(LOGO_FULL), width=width)
        else:
            st.markdown('<h1 style="color:#073b91;margin:0">Transcreve<br><span style="color:#05b9c8">Facil</span></h1>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<h1 style="color:#073b91;margin:0">Transcreve<br><span style="color:#05b9c8">Facil</span></h1>', unsafe_allow_html=True)


def init_state():
    defaults = {
        "logged_in": False,
        "user_email": "",
        "page": "Inicio",
        "transcript": "",
        "segments": [],
        "last_file_name": "",
        "last_error": "",
        "model_size": "small",
        "with_timestamps": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_users():
    try:
        users = dict(st.secrets.get("users", {}))
    except Exception:
        users = {}
    if not users:
        users = {"vmsoares@tre-ba.jus.br": "transcreve123"}
    return users


def login_screen():
    c1, c2, c3 = st.columns([1, 1.15, 1])
    with c2:
        st.markdown('<div class="tf-card" style="text-align:center;margin-top:34px">', unsafe_allow_html=True)
        safe_logo(width=300)
        st.markdown(f'<p class="tf-sub">Acesso privado - {APP_VERSION}</p>', unsafe_allow_html=True)
        email = st.text_input("E-mail institucional", value="vmsoares@tre-ba.jus.br")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary", use_container_width=True):
            users = get_users()
            if email in users and password == users[email] and email.endswith("@tre-ba.jus.br"):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.page = "Inicio"
                st.rerun()
            else:
                st.error("E-mail ou senha invalidos.")
        st.caption("Senha inicial: transcreve123. Troque depois em Streamlit Secrets.")
        st.markdown('</div>', unsafe_allow_html=True)


def go(page):
    st.session_state.page = page
    st.rerun()


def sidebar():
    with st.sidebar:
        safe_logo(width=230)
        st.markdown("### Navegacao")
        pages = [
            ("Inicio", "Inicio"),
            ("Transcrever", "Transcrever"),
            ("Resultado", "Resultado"),
            ("Prompts", "Prompts"),
            ("Ferramentas", "Ferramentas"),
            ("YouTube Local", "YouTube Local"),
            ("Ajuda", "Ajuda"),
        ]
        for label, page in pages:
            prefix = "✅ " if st.session_state.page == page else ""
            if st.button(prefix + label, key="nav_" + page, use_container_width=True):
                go(page)
        st.markdown("---")
        st.markdown('<div class="tf-note">Transcreva, organize e economize tempo.</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### Configuracoes")
        st.session_state.model_size = st.selectbox("Modelo", ["small", "medium", "large-v3"], index=["small", "medium", "large-v3"].index(st.session_state.model_size))
        st.session_state.with_timestamps = st.checkbox("Incluir marcacao de tempo", value=st.session_state.with_timestamps)
        if st.button("Sair", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()


def topbar():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="tf-topbar">🔎 Buscar transcricoes, arquivos ou ferramentas...</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="tf-topbar" style="text-align:right"><b>{st.session_state.user_email}</b><br><span style="color:#0094a6">Uso privado</span></div>', unsafe_allow_html=True)


def page_inicio():
    topbar()
    st.markdown('<div class="tf-hero"><div class="tf-title">Transcritor de Videos e Audios</div><div class="tf-sub">Envie arquivos, fragmente midias, compacte documentos e gere transcricoes em TXT, Word, PDF e SRT.</div><br><span class="tf-pill teal">Recomendado: upload manual</span><span class="tf-pill blue">YouTube: recurso experimental</span><span class="tf-pill orange">Modelo online sugerido: small</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="tf-card"><div class="tf-iconbox tf-bg-teal">DOC</div><h3>Arquivos processados</h3><p class="tf-sub">Transcreva videos, audios e gere downloads editaveis.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="tf-card"><div class="tf-iconbox tf-bg-blue">CLK</div><h3>Tempo economizado</h3><p class="tf-sub">Transforme aulas, reunioes e treinamentos em texto pesquisavel.</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="tf-card"><div class="tf-iconbox tf-bg-orange">BOX</div><h3>Ferramentas integradas</h3><p class="tf-sub">Fragmentador, compactador, PDF, Word, TXT e SRT.</p></div>', unsafe_allow_html=True)
    st.markdown("## Ferramentas rapidas")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Fragmentador", use_container_width=True): go("Ferramentas")
    with b2:
        if st.button("Compactador", use_container_width=True): go("Ferramentas")
    with b3:
        if st.button("Transcrever agora", type="primary", use_container_width=True): go("Transcrever")
    with b4:
        if st.button("Ver resultado", use_container_width=True): go("Resultado")


def save_upload(uploaded):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix)
    tmp.write(uploaded.getbuffer())
    tmp.close()
    return tmp.name


def run_cmd(cmd, timeout=900):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)


def extract_audio(path):
    ext = Path(path).suffix.lower()
    if ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"]:
        return path
    out = str(Path(path).with_suffix(".wav"))
    cmd = ["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", out]
    result = run_cmd(cmd)
    if result.returncode != 0 or not Path(out).exists():
        raise RuntimeError("Falha ao extrair audio. Confirme se o arquivo e valido.")
    return out


@st.cache_resource(show_spinner=False)
def load_model(model_size):
    from faster_whisper import WhisperModel
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def fmt_time(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def transcribe_file(path):
    audio = extract_audio(path)
    model = load_model(st.session_state.get("model_size", "small"))
    segments_iter, _info = model.transcribe(audio, language="pt", vad_filter=True)
    segments = []
    lines = []
    for seg in segments_iter:
        text = (seg.text or "").strip()
        if not text:
            continue
        segments.append({"start": float(seg.start), "end": float(seg.end), "text": text})
        if st.session_state.get("with_timestamps", True):
            lines.append(f"[{fmt_time(seg.start)} - {fmt_time(seg.end)}] {text}")
        else:
            lines.append(text)
    return "\n".join(lines), segments


def page_transcrever():
    topbar()
    st.markdown("# Transcrever")
    st.markdown('<div class="tf-note">Use upload manual como caminho principal. Para YouTube, use a pagina YouTube Local.</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Escolha um video ou audio", type=["mp3","wav","m4a","ogg","flac","aac","mp4","mov","avi","mkv","webm","mpeg","mpg"])
    if uploaded:
        st.success("Arquivo carregado: " + uploaded.name)
        if st.button("Transcrever agora", type="primary", use_container_width=True):
            try:
                bar = st.progress(0)
                msg = st.empty()
                msg.info("Preparando arquivo...")
                path = save_upload(uploaded)
                bar.progress(25)
                msg.info("Extraindo audio e carregando modelo...")
                text, segments = transcribe_file(path)
                bar.progress(100)
                st.session_state.transcript = text
                st.session_state.segments = segments
                st.session_state.last_file_name = uploaded.name
                msg.success("Transcricao concluida. Abra Resultado para baixar.")
            except Exception as exc:
                st.session_state.last_error = str(exc)
                st.error("Erro na transcricao: " + str(exc))
    st.markdown("---")
    if st.button("Ir para Resultado", use_container_width=True): go("Resultado")


def make_txt(text):
    return text.encode("utf-8")


def make_docx(text):
    from docx import Document
    doc = Document()
    doc.add_heading("Transcricao", level=1)
    for line in text.splitlines():
        doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()


def make_pdf(text):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    safe = text.encode("latin-1", errors="replace").decode("latin-1")
    for line in safe.splitlines():
        pdf.multi_cell(0, 8, line)
    data = pdf.output(dest="S")
    if isinstance(data, str):
        data = data.encode("latin-1", errors="replace")
    return bytes(data)


def make_srt(segments):
    def srt_time(sec):
        ms = int((sec - int(sec)) * 1000)
        sec = int(sec)
        return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d},{ms:03d}"
    out = []
    for i, seg in enumerate(segments, 1):
        out += [str(i), f"{srt_time(seg['start'])} --> {srt_time(seg['end'])}", seg["text"], ""]
    return "\n".join(out).encode("utf-8")


def page_resultado():
    topbar()
    st.markdown("# Resultado")
    text = st.session_state.get("transcript", "")
    if not text:
        st.info("Nenhuma transcricao disponivel. Va para Transcrever.")
        return
    st.markdown("**Ultimo arquivo:** " + st.session_state.get("last_file_name", ""))
    st.text_area("Transcricao", text, height=420)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.download_button("Baixar TXT", make_txt(text), "transcricao.txt", "text/plain", use_container_width=True)
    with c2: st.download_button("Baixar Word", make_docx(text), "transcricao.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with c3: st.download_button("Baixar PDF", make_pdf(text), "transcricao.pdf", "application/pdf", use_container_width=True)
    with c4: st.download_button("Baixar SRT", make_srt(st.session_state.get("segments", [])), "legenda.srt", "text/plain", use_container_width=True)
    if st.button("Limpar resultado", use_container_width=True):
        st.session_state.transcript = ""
        st.session_state.segments = []
        st.session_state.last_file_name = ""
        st.rerun()


def page_prompts():
    topbar()
    st.markdown("# Prompts")
    text = st.session_state.get("transcript", "")
    if not text:
        st.info("Transcreva um arquivo primeiro.")
        return
    choices = {
        "Tabela pratica": "Transforme a transcricao abaixo em uma tabela pratica, com colunas de tema, orientacao, fundamento citado, providencia e observacoes:",
        "Resumo executivo": "Resuma a transcricao abaixo de forma objetiva, destacando pontos principais e conclusoes:",
        "Ata de reuniao": "Transforme a transcricao abaixo em ata formal, com pauta, deliberacoes e providencias:",
        "Checklist": "Transforme a transcricao abaixo em checklist de providencias praticas:",
        "Material de estudo": "Transforme a transcricao abaixo em material de estudo organizado:",
    }
    choice = st.selectbox("Tipo", list(choices.keys()))
    st.text_area("Prompt pronto", choices[choice] + "\n\n" + text, height=420)


def split_file(path, mb):
    size = int(mb * 1024 * 1024)
    parts = []
    with open(path, "rb") as f:
        idx = 1
        while True:
            data = f.read(size)
            if not data:
                break
            part = f"{path}.part{idx:03d}"
            with open(part, "wb") as out:
                out.write(data)
            parts.append(part)
            idx += 1
    return parts


def zip_paths(paths):
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=Path(p).name)
    bio.seek(0)
    return bio.getvalue()


def page_ferramentas():
    topbar()
    st.markdown("# Ferramentas")
    t1, t2, t3, t4 = st.tabs(["Fragmentar midia", "Fragmentar arquivo", "Compactar ZIP", "Compactar midia"])
    with t1:
        up = st.file_uploader("Video/audio para fragmentar por duracao", key="media_frag")
        minutes = st.number_input("Minutos por parte", min_value=1, max_value=120, value=10)
        if up and st.button("Fragmentar midia", type="primary"):
            try:
                path = save_upload(up)
                outdir = tempfile.mkdtemp()
                pattern = str(Path(outdir) / "parte_%03d.mp4")
                result = run_cmd(["ffmpeg", "-y", "-i", path, "-c", "copy", "-map", "0", "-segment_time", str(int(minutes*60)), "-f", "segment", pattern])
                parts = sorted(str(p) for p in Path(outdir).glob("parte_*.mp4"))
                if not parts:
                    raise RuntimeError(result.stderr[-400:] or "Nao foi possivel fragmentar.")
                st.download_button("Baixar partes em ZIP", zip_paths(parts), "partes_midia.zip", "application/zip")
            except Exception as exc:
                st.error("Erro: " + str(exc))
    with t2:
        up = st.file_uploader("Qualquer arquivo para fragmentar por tamanho", key="file_frag")
        mb = st.number_input("Tamanho de cada parte em MB", min_value=1, max_value=500, value=50)
        if up and st.button("Fragmentar arquivo", type="primary"):
            path = save_upload(up)
            st.download_button("Baixar partes em ZIP", zip_paths(split_file(path, mb)), "partes_arquivo.zip", "application/zip")
    with t3:
        ups = st.file_uploader("Arquivos para ZIP", accept_multiple_files=True, key="zip_files")
        if ups and st.button("Criar ZIP", type="primary"):
            paths = [save_upload(u) for u in ups]
            st.download_button("Baixar ZIP", zip_paths(paths), "arquivos.zip", "application/zip")
    with t4:
        up = st.file_uploader("Audio/video para compactar", key="compress_media")
        level = st.selectbox("Nivel", ["leve", "medio", "forte"])
        if up and st.button("Compactar midia", type="primary"):
            try:
                path = save_upload(up)
                out = str(Path(path).with_name("midia_compactada.mp4"))
                crf = {"leve":"28", "medio":"32", "forte":"36"}[level]
                result = run_cmd(["ffmpeg", "-y", "-i", path, "-vcodec", "libx264", "-crf", crf, "-preset", "veryfast", "-acodec", "aac", "-b:a", "96k", out])
                if result.returncode != 0 or not Path(out).exists():
                    raise RuntimeError(result.stderr[-400:] or "Falha ao compactar.")
                st.download_button("Baixar midia compactada", Path(out).read_bytes(), "midia_compactada.mp4", "video/mp4")
            except Exception as exc:
                st.error("Erro: " + str(exc))


def page_youtube_local():
    topbar()
    st.markdown("# YouTube Local")
    st.markdown('<div class="tf-warn">Use apenas em videos seus, autorizados ou permitidos. Este metodo evita bloqueios do Streamlit Cloud.</div>', unsafe_allow_html=True)
    url = st.text_input("Cole a URL")
    if url:
        st.code('yt-dlp -x --audio-format mp3 "' + url + '"', language="bash")
    st.markdown("Depois de gerar o MP3 no computador, volte em Transcrever e envie o arquivo.")


def page_ajuda():
    topbar()
    st.markdown("# Ajuda")
    st.write("Versao: " + APP_VERSION)
    st.markdown("""
Fluxo recomendado:
1. Transcrever: envie arquivo e gere texto.
2. Resultado: baixe TXT, Word, PDF ou SRT.
3. Prompts: copie prompts para organizar o conteudo.
4. Ferramentas: fragmente ou compacte arquivos.
""")


def main_app():
    sidebar()
    page = st.session_state.get("page", "Inicio")
    if page == "Inicio": page_inicio()
    elif page == "Transcrever": page_transcrever()
    elif page == "Resultado": page_resultado()
    elif page == "Prompts": page_prompts()
    elif page == "Ferramentas": page_ferramentas()
    elif page == "YouTube Local": page_youtube_local()
    elif page == "Ajuda": page_ajuda()
    else: page_inicio()


def main():
    init_state()
    try:
        if st.session_state.logged_in:
            main_app()
        else:
            login_screen()
    except Exception as exc:
        st.error("Erro interno do aplicativo: " + str(exc))
        st.info("Abra Manage app > Logs no Streamlit Cloud e envie o trecho vermelho para correcao precisa.")


if __name__ == "__main__":
    main()
