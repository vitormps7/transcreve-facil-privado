# -*- coding: utf-8 -*-
"""Transcreve Facil Privado v8.
Interface premium com funcoes principais restauradas.
"""

import base64
import os
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

APP_NAME = "Transcreve Fácil"
APP_VERSION = "v8 - interface premium com funções restauradas"
ALLOWED_DOMAIN = "@tre-ba.jus.br"
DEFAULT_USER = "vmsoares@tre-ba.jus.br"
DEFAULT_PASSWORD = "transcreve123"

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".webm"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}
SUPPORTED_EXTS = sorted(AUDIO_EXTS | VIDEO_EXTS)
RECOMMENDED_MAX_MB = 150
RECOMMENDED_MAX_MINUTES = 45

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_FULL_PATH = ASSETS_DIR / "logo_full.png"
LOGO_ICON_PATH = ASSETS_DIR / "logo_icon.png"

st.set_page_config(page_title=APP_NAME, page_icon=str(LOGO_ICON_PATH) if LOGO_ICON_PATH.exists() else "🎙️", layout="wide")


def b64(path: Path) -> str:
    try:
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception:
        return ""


def logo_html(width: int = 230) -> str:
    logo = b64(LOGO_FULL_PATH)
    if logo:
        return f'<img src="data:image/png;base64,{logo}" style="width:{width}px;max-width:100%;height:auto;display:block;" />'
    return '<div class="tf-logo-text">Transcreve<br><span>Fácil</span></div>'


def inject_css() -> None:
    icon = b64(LOGO_ICON_PATH)
    icon_url = f"data:image/png;base64,{icon}" if icon else ""
    st.markdown(
        f"""
        <style>
        :root {{
            --tf-blue:#0b3b91; --tf-blue2:#1368f2; --tf-cyan:#08b7c9;
            --tf-teal:#11b7a8; --tf-orange:#ff7a1a; --tf-bg:#f7fbff;
            --tf-card:#fff; --tf-text:#10233f; --tf-muted:#6b7890;
            --tf-border:#dfe9f7; --tf-shadow:0 14px 35px rgba(15,61,145,.10);
        }}
        .stApp {{
            background: radial-gradient(circle at 0% 0%, rgba(8,183,201,.12), transparent 28%),
                        radial-gradient(circle at 100% 0%, rgba(19,104,242,.10), transparent 30%),
                        linear-gradient(180deg,#fbfdff 0%,#f5faff 100%);
            color:var(--tf-text);
        }}
        .block-container {{padding-top:1rem; max-width:1550px;}}
        [data-testid="stSidebar"] {{
            background:linear-gradient(180deg,#fff 0%,#f3f9ff 100%);
            border-right:1px solid var(--tf-border);
        }}
        h1,h2,h3 {{color:var(--tf-blue); letter-spacing:-.025em;}}
        .tf-logo-text {{font-size:1.6rem;line-height:1.0;font-weight:900;color:var(--tf-blue);}}
        .tf-logo-text span {{color:var(--tf-cyan);}}
        .tf-topbar {{
            display:flex; align-items:center; justify-content:space-between; gap:1rem;
            padding:.9rem 1rem; margin-bottom:1rem; background:rgba(255,255,255,.78);
            border:1px solid var(--tf-border); border-radius:24px; box-shadow:var(--tf-shadow);
            backdrop-filter: blur(10px);
        }}
        .tf-search {{flex:1; border:1px solid var(--tf-border); background:#fff; border-radius:18px; min-height:44px; display:flex; align-items:center; padding:0 .9rem; color:#8a97aa;}}
        .tf-user {{display:flex; align-items:center; gap:.65rem; color:var(--tf-blue);font-weight:800;}}
        .tf-avatar {{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--tf-blue2),var(--tf-cyan));color:#fff;font-weight:900;}}
        .tf-hero {{
            border:1px solid #cfe0f7; border-radius:28px; padding:1.6rem 1.75rem; margin-bottom:1rem;
            background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(235,248,255,.88));
            box-shadow:var(--tf-shadow); position:relative; overflow:hidden;
        }}
        .tf-hero:after {{
            content:""; position:absolute; right:28px; top:24px; width:150px; height:150px; opacity:.13;
            background-image:url('{icon_url}'); background-size:contain; background-repeat:no-repeat;
        }}
        .tf-muted {{color:var(--tf-muted);}}
        .tf-pill-row {{display:flex; gap:.6rem; flex-wrap:wrap; margin-top:.8rem;}}
        .tf-pill {{display:inline-flex;align-items:center;gap:.4rem;padding:.42rem .75rem;border-radius:999px;font-weight:800;font-size:.84rem;background:#e9f9fb;color:#027c91;border:1px solid #c8f0f4;}}
        .tf-pill.blue {{background:#edf4ff;color:#1368f2;border-color:#d4e5ff;}}
        .tf-pill.orange {{background:#fff3e9;color:#d96b00;border-color:#ffe0c4;}}
        .tf-card {{background:#fff;border:1px solid var(--tf-border);border-radius:24px;padding:1.1rem;box-shadow:var(--tf-shadow);height:100%;}}
        .tf-card p {{color:var(--tf-muted); margin:0; line-height:1.45;}}
        .tf-icon {{width:50px;height:50px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:1.45rem;margin-bottom:.8rem;color:#fff;box-shadow:0 10px 20px rgba(0,0,0,.11);}}
        .tf-icon.teal {{background:linear-gradient(135deg,#06c6b3,#1bd3e8);}}
        .tf-icon.blue {{background:linear-gradient(135deg,#1268f2,#57a6ff);}}
        .tf-icon.orange {{background:linear-gradient(135deg,#ff7a1a,#ffb15c);}}
        .tf-icon.purple {{background:linear-gradient(135deg,#7657e8,#aa7cff);}}
        .tf-file-row {{display:flex;align-items:center;justify-content:space-between;gap:.75rem;padding:.75rem;border:1px solid var(--tf-border);border-radius:18px;background:#fff;margin-bottom:.65rem;}}
        .tf-file-name {{font-weight:900;color:var(--tf-blue);}}
        .tf-status {{padding:.28rem .6rem;border-radius:999px;font-weight:800;font-size:.78rem;background:#eaf9ef;color:#188038;white-space:nowrap;}}
        .tf-status.blue {{background:#eef6ff;color:#1268f2;}}
        .tf-status.teal {{background:#e9fbfb;color:#058191;}}
        .tf-sidebar-note {{border:1px solid var(--tf-border);border-radius:22px;padding:1rem;background:linear-gradient(180deg,#fff,#edfaff);color:var(--tf-blue);font-weight:800;}}
        .tf-upload-box {{border:2px dashed #b8d0f3;border-radius:22px;background:linear-gradient(180deg,#fff,#edf8ff);padding:1.2rem;text-align:center;margin:.4rem 0 1rem;}}
        div[data-testid="stButton"] > button, div[data-testid="stDownloadButton"] > button {{border-radius:16px !important; font-weight:800 !important; min-height:42px;}}
        div[data-testid="stButton"] > button[kind="primary"] {{background:linear-gradient(135deg,var(--tf-blue2),var(--tf-cyan)) !important; color:#fff !important; border:0 !important;}}
        [data-testid="stFileUploader"] section {{border-radius:20px !important; border:2px dashed #b8d0f3 !important; background:#fff !important;}}
        .tf-nav-title {{font-weight:900;color:var(--tf-blue);font-size:1.05rem;margin:.8rem 0 .35rem;}}
        .tf-small {{font-size:.86rem;color:var(--tf-muted);}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    user = st.session_state.get("user_email", DEFAULT_USER)
    initial = (user[:1] or "V").upper()
    st.markdown(
        f"""
        <div class="tf-topbar">
            <div class="tf-search">🔎 Buscar transcrições, arquivos ou ferramentas...</div>
            <div class="tf-user"><span>🔔</span><div class="tf-avatar">{initial}</div><div>{user}<br><span style="font-size:.78rem;color:#08a9b7;font-weight:700;">Uso privado</span></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="tf-hero">
            <h1>Transcritor de Vídeos e Áudios</h1>
            <div class="tf-muted">Envie arquivos, fragmente mídias, compacte documentos e gere transcrições em TXT, Word, PDF e SRT.</div>
            <div class="tf-pill-row">
                <span class="tf-pill">✅ Recomendado: upload manual</span>
                <span class="tf-pill blue">🧪 YouTube: recurso experimental</span>
                <span class="tf-pill orange">⚡ Modelo online sugerido: small</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(logo_html(250), unsafe_allow_html=True)
        st.markdown('<div class="tf-nav-title">Navegação</div>', unsafe_allow_html=True)
        page = st.radio(
            "",
            ["Início", "Transcrever", "Resultado", "Prompts", "Ferramentas", "YouTube Local", "Ajuda"],
            label_visibility="collapsed",
        )
        st.markdown('<div class="tf-sidebar-note">🚀 Transcreva mais, organize melhor e economize tempo.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Configurações")
        st.session_state["model_size"] = st.selectbox("Modelo", ["small", "medium", "large-v3"], index=0)
        st.session_state["timestamps"] = st.checkbox("Incluir marcação de tempo", value=True)
        st.session_state["beam_size"] = st.slider("Precisão", 1, 5, 1)
        st.caption("Use small e precisão 1 no Streamlit Cloud.")
        if st.button("Limpar resultado atual", use_container_width=True):
            for key in ["last_transcription", "last_plain_text", "last_segments", "last_metadata"]:
                st.session_state.pop(key, None)
            st.success("Resultado limpo.")
    return page


# ---------------- Auth ----------------
def get_secret_dict(section_name: str) -> dict:
    try:
        return dict(st.secrets.get(section_name, {}))
    except Exception:
        return {}


def valid_institutional_email(email: str) -> bool:
    email = (email or "").strip().lower()
    return email.endswith(ALLOWED_DOMAIN) and re.match(r"^[a-z0-9._%+\-]+@tre-ba\.jus\.br$", email) is not None


def authenticate(email: str, password: str) -> tuple[bool, str]:
    email = (email or "").strip().lower()
    if not valid_institutional_email(email):
        return False, "Use um e-mail institucional @tre-ba.jus.br."
    users = get_secret_dict("users")
    profiles = get_secret_dict("profiles")
    if users:
        if password == str(users.get(email, "")):
            return True, str(profiles.get(email, "usuario"))
        return False, "E-mail ou senha inválidos."
    if email == DEFAULT_USER and password == DEFAULT_PASSWORD:
        return True, "admin"
    try:
        app_password = st.secrets.get("APP_PASSWORD", DEFAULT_PASSWORD)
    except Exception:
        app_password = DEFAULT_PASSWORD
    if email == DEFAULT_USER and password == app_password:
        return True, "admin"
    return False, "Usuário não cadastrado. Configure os usuários em Secrets."


def login_screen() -> None:
    inject_css()
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(logo_html(420), unsafe_allow_html=True)
        render_hero()
        c1, c2, c3 = st.columns(3)
        for col, icon, title, desc, color in [
            (c1, "🎙️", "Transcrição", "Áudios e vídeos em português.", "teal"),
            (c2, "🧰", "Ferramentas", "Fragmentador, compactador e downloads.", "blue"),
            (c3, "🔒", "Privado", "Acesso institucional com senha.", "orange"),
        ]:
            with col:
                st.markdown(f'<div class="tf-card"><div class="tf-icon {color}">{icon}</div><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="tf-card">', unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("### Acesso institucional")
            email = st.text_input("E-mail institucional", placeholder=DEFAULT_USER)
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
        if submitted:
            ok, result = authenticate(email, password)
            if ok:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email.strip().lower()
                st.session_state["user_profile"] = result
                st.rerun()
            st.error(result)
        if not get_secret_dict("users"):
            with st.expander("Primeiro acesso"):
                st.code(f"E-mail: {DEFAULT_USER}\nSenha: {DEFAULT_PASSWORD}")
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------- Helpers ----------------
def safe_filename(name: str) -> str:
    stem = Path(name or "arquivo").stem[:80]
    stem = re.sub(r"[^a-zA-Z0-9_.\-]+", "_", stem).strip("_")
    return stem or "arquivo"


def seconds_to_hhmmss(seconds: float | None) -> str:
    seconds = max(0, int(seconds or 0))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def get_duration_seconds(path: str) -> float | None:
    result = run_command(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path])
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except Exception:
        return None


def extract_audio(input_path: str, output_path: str) -> None:
    result = run_command(["ffmpeg", "-y", "-i", input_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_path])
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2500:] or "Falha ao executar FFmpeg.")


def make_zip_from_paths(paths: list[str], zip_path: str) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in paths:
            if os.path.exists(file_path):
                zf.write(file_path, arcname=os.path.basename(file_path))


def bytes_from_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def is_supported_url(url: str) -> bool:
    try:
        parsed = urlparse((url or "").strip())
        host = (parsed.netloc or "").lower()
        return parsed.scheme in {"http", "https"} and host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
    except Exception:
        return False


def friendly_youtube_error(error: Exception) -> str:
    msg = str(error).lower()
    if "403" in msg or "forbidden" in msg:
        return "O YouTube bloqueou o servidor do Streamlit Cloud com erro 403. Use a aba YouTube Local ou envie o arquivo manualmente."
    if "not a bot" in msg or "sign in" in msg or "cookies" in msg:
        return "O YouTube pediu login ou confirmação anti-robô. Use a aba YouTube Local ou envie o arquivo manualmente."
    if "private" in msg:
        return "O vídeo parece ser privado. Use apenas conteúdo público/autorizado ou envie o arquivo manualmente."
    return "Não foi possível baixar o áudio automaticamente. Use upload manual ou a aba YouTube Local."


def download_audio_from_youtube(url: str, output_dir: str, mode: str = "auto") -> tuple[str, dict]:
    if not is_supported_url(url):
        raise ValueError("URL não suportada. Use link do YouTube.")
    try:
        import yt_dlp
    except Exception as exc:
        raise RuntimeError("yt-dlp não foi carregado. Confira requirements.txt.") from exc

    strategies = ["default", "web", "android", "ios"] if mode == "compatibilidade" else ["default", "web"]
    last_error = None
    for idx, strategy in enumerate(strategies, start=1):
        base = os.path.join(output_dir, f"youtube_{idx}_{strategy}")
        opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": base + ".%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 2,
            "forceipv4": True,
            "geo_bypass": True,
            "http_headers": {"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"},
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
            "postprocessor_args": ["-ar", "16000", "-ac", "1"],
        }
        if strategy != "default":
            opts["extractor_args"] = {"youtube": {"player_client": [strategy]}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            matches = list(Path(output_dir).glob(f"youtube_{idx}_{strategy}*.wav"))
            if not matches:
                raise RuntimeError("Áudio convertido não encontrado.")
            return str(matches[0]), {"title": info.get("title") or "youtube", "duration": info.get("duration"), "url": info.get("webpage_url") or url}
        except Exception as exc:
            last_error = exc
    raise RuntimeError(friendly_youtube_error(last_error or RuntimeError("Falha desconhecida")))


@st.cache_resource(show_spinner=False)
def load_model(model_size: str):
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError("Não foi possível carregar faster-whisper.") from exc
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def build_srt(segments: list[dict]) -> str:
    def fmt(sec: float) -> str:
        sec = max(0, float(sec or 0))
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int((sec - int(sec)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    blocks = []
    for i, seg in enumerate(segments, start=1):
        blocks.append(f"{i}\n{fmt(seg['start'])} --> {fmt(seg['end'])}\n{seg['text']}")
    return "\n\n".join(blocks) + "\n"


def save_docx(lines: list[str], metadata: dict) -> bytes:
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.add_heading("Transcrição", level=1)
    doc.add_paragraph(f"Sistema: {APP_NAME}")
    doc.add_paragraph(f"Gerada em: {metadata.get('generated_at', '')}")
    doc.add_paragraph(f"Arquivo: {metadata.get('filename', '')}")
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(11)
    for line in lines:
        doc.add_paragraph(line)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.close()
    doc.save(tmp.name)
    data = bytes_from_file(tmp.name)
    os.unlink(tmp.name)
    return data


def save_pdf(lines: list[str], metadata: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import cm
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    doc = SimpleDocTemplate(tmp.name, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("TFNormal", parent=styles["Normal"], fontName="Helvetica", fontSize=10.5, leading=14)
    story = [Paragraph("Transcrição", styles["Title"]), Paragraph(f"Arquivo: {metadata.get('filename','')}", normal), Spacer(1, 10)]
    for line in lines:
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe_line, normal))
        story.append(Spacer(1, 4))
    doc.build(story)
    data = bytes_from_file(tmp.name)
    os.unlink(tmp.name)
    return data


def build_prompts(text: str) -> dict[str, str]:
    return {
        "Revisar transcrição": "Revise a transcrição abaixo, corrigindo pontuação, quebras de parágrafo e termos evidentes, sem alterar o sentido:\n\n" + text,
        "Resumo executivo": "Faça um resumo executivo da transcrição abaixo, com pontos principais e observações relevantes:\n\n" + text,
        "Ata de reunião": "Transforme a transcrição abaixo em ata objetiva, com participantes se identificados, pauta, deliberações e providências:\n\n" + text,
        "Tabela prática": "Transforme a transcrição abaixo em tabela prática com colunas: tema, orientação, fundamento citado, providência e observações:\n\n" + text,
        "Checklist": "Transforme a transcrição abaixo em checklist de providências, separando ações imediatas, pontos de atenção e pendências:\n\n" + text,
        "Material de estudo": "Transforme a transcrição abaixo em material de estudo, com tópicos, conceitos-chave, quadro-resumo e possíveis questões:\n\n" + text,
    }


# ---------------- Pages ----------------
def page_home() -> None:
    render_hero()
    c1, c2, c3 = st.columns(3)
    cards = [
        (c1, "📄", "Arquivos processados", "Transcreva vídeos, áudios e gere downloads editáveis em TXT, Word, PDF e SRT.", "teal"),
        (c2, "⏱️", "Tempo economizado", "Transforme aulas, reuniões e treinamentos em texto pesquisável em poucos passos.", "blue"),
        (c3, "🗂️", "Ferramentas integradas", "Fragmentador, compactador, PDF, Word, TXT e legendas no mesmo ambiente.", "orange"),
    ]
    for col, icon, title, desc, color in cards:
        with col:
            st.markdown(f'<div class="tf-card"><div class="tf-icon {color}">{icon}</div><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.markdown("### Ferramentas rápidas")
    t1, t2, t3, t4 = st.columns(4)
    for col, icon, title, desc, color in [
        (t1, "✂️", "Fragmentador", "Divida arquivos grandes.", "teal"),
        (t2, "🗜️", "Compactador", "Reduza tamanho de mídia.", "purple"),
        (t3, "📕", "Exportar PDF", "Gere documento completo.", "orange"),
        (t4, "💬", "Legenda SRT", "Crie legendas com tempo.", "blue"),
    ]:
        with col:
            st.markdown(f'<div class="tf-card"><div class="tf-icon {color}">{icon}</div><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.markdown("### Arquivos recentes")
    for icon, name, meta, status, color in [
        ("🎬", "reuniao_projeto.mp4", "MP4 • 52:13 • 48 MB", "Concluído", ""),
        ("🎵", "entrevista_cliente.m4a", "M4A • 23:45 • 22 MB", "Pronto para baixar", "teal"),
        ("🎥", "aula_marketing.mp4", "MP4 • 1:15:30 • 105 MB", "Processando", "blue"),
    ]:
        cls = "tf-status " + color if color else "tf-status"
        st.markdown(f'<div class="tf-file-row"><div><span style="font-size:1.4rem;">{icon}</span> <span class="tf-file-name">{name}</span><br><span class="tf-muted">{meta}</span></div><span class="{cls}">{status}</span></div>', unsafe_allow_html=True)


def page_transcribe() -> None:
    st.markdown('<div class="tf-upload-box"><h2>🎙️ Transcrever arquivo ou URL</h2><p class="tf-muted">Para maior estabilidade no Streamlit Cloud, prefira upload manual e modelo small.</p></div>', unsafe_allow_html=True)
    st.warning("Use URLs apenas para vídeos seus, autorizados ou com permissão de uso. YouTube direto no Streamlit Cloud pode falhar por bloqueio 403.")
    origem = st.radio("Fonte do conteúdo", ["Enviar arquivo", "URL do YouTube"], horizontal=True)
    uploaded = None
    youtube_url = ""
    yt_mode = "auto"
    if origem == "Enviar arquivo":
        uploaded = st.file_uploader("Escolha um arquivo", type=[x.replace(".", "") for x in SUPPORTED_EXTS])
        ready = uploaded is not None
    else:
        youtube_url = st.text_input("Cole a URL do YouTube", placeholder="https://www.youtube.com/watch?v=...")
        yt_mode = st.selectbox("Modo", ["auto", "compatibilidade"], index=0)
        st.info("Se falhar, use a aba YouTube Local para baixar no computador e depois envie o áudio por upload.")
        ready = bool(youtube_url.strip())
    if not ready:
        st.info("Envie um arquivo ou cole uma URL para começar.")
        return

    if st.button("Transcrever agora", type="primary", use_container_width=True):
        model_size = st.session_state.get("model_size", "small")
        include_timestamps = st.session_state.get("timestamps", True)
        beam_size = st.session_state.get("beam_size", 1)
        progress = st.progress(0, text="Preparando...")
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                if origem == "Enviar arquivo":
                    suffix = Path(uploaded.name).suffix.lower()
                    if suffix not in SUPPORTED_EXTS:
                        st.error("Formato não suportado.")
                        return
                    file_mb = uploaded.size / (1024 * 1024)
                    if file_mb > RECOMMENDED_MAX_MB:
                        st.warning(f"Arquivo com {file_mb:.1f} MB. Pode demorar ou falhar no Streamlit Cloud.")
                    input_path = os.path.join(tmpdir, safe_filename(uploaded.name) + suffix)
                    with open(input_path, "wb") as f:
                        f.write(uploaded.getbuffer())
                    duration = get_duration_seconds(input_path)
                    if duration and duration / 60 > RECOMMENDED_MAX_MINUTES:
                        st.warning(f"Duração estimada: {duration/60:.1f} min. Para arquivos longos, prefira fragmentar.")
                    source_title = uploaded.name
                    audio_path = input_path
                    if suffix in VIDEO_EXTS:
                        progress.progress(25, text="Extraindo áudio do vídeo...")
                        audio_path = os.path.join(tmpdir, "audio.wav")
                        extract_audio(input_path, audio_path)
                    else:
                        progress.progress(25, text="Áudio identificado...")
                else:
                    if not is_supported_url(youtube_url):
                        st.error("URL não suportada.")
                        return
                    progress.progress(20, text="Tentando baixar áudio da URL...")
                    audio_path, yt_meta = download_audio_from_youtube(youtube_url, tmpdir, mode=yt_mode)
                    source_title = yt_meta.get("title", "youtube")
                    duration = yt_meta.get("duration") or get_duration_seconds(audio_path)
                    file_mb = 0.0
                progress.progress(40, text="Carregando modelo...")
                model = load_model(model_size)
                progress.progress(55, text="Transcrevendo...")
                segments, info = model.transcribe(audio_path, language="pt", vad_filter=True, beam_size=beam_size)
                lines, plain_parts, segs = [], [], []
                for seg in segments:
                    text = (seg.text or "").strip()
                    if not text:
                        continue
                    segs.append({"start": seg.start, "end": seg.end, "text": text})
                    plain_parts.append(text)
                    if include_timestamps:
                        lines.append(f"[{seconds_to_hhmmss(seg.start)} - {seconds_to_hhmmss(seg.end)}] {text}")
                    else:
                        lines.append(text)
                if not lines:
                    st.warning("Nenhuma fala foi identificada.")
                    return
                metadata = {
                    "filename": source_title,
                    "duration": seconds_to_hhmmss(duration) if duration else "não identificada",
                    "model": model_size,
                    "source": origem,
                    "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                st.session_state["last_transcription"] = "\n".join(lines)
                st.session_state["last_plain_text"] = "\n".join(plain_parts)
                st.session_state["last_segments"] = segs
                st.session_state["last_metadata"] = metadata
                progress.progress(100, text="Transcrição concluída.")
                st.success("Transcrição concluída. Acesse a página Resultado para baixar TXT, Word, PDF ou SRT.")
            except Exception as exc:
                st.error("Não foi possível concluir a transcrição.")
                st.warning(str(exc))


def page_result() -> None:
    if not st.session_state.get("last_transcription"):
        st.info("Nenhuma transcrição concluída nesta sessão.")
        return
    final_text = st.session_state["last_transcription"]
    metadata = st.session_state.get("last_metadata", {})
    segments = st.session_state.get("last_segments", [])
    lines = final_text.splitlines()
    base_name = safe_filename(metadata.get("filename", "transcricao"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Arquivo", metadata.get("filename", "-")[:24])
    c2.metric("Duração", metadata.get("duration", "-"))
    c3.metric("Modelo", metadata.get("model", "-"))
    c4.metric("Trechos", str(len(segments)))
    st.text_area("Transcrição", final_text, height=440)
    d1, d2, d3, d4 = st.columns(4)
    d1.download_button("Baixar TXT", final_text.encode("utf-8"), file_name=f"{base_name}_transcricao.txt", mime="text/plain", use_container_width=True)
    d2.download_button("Baixar Word", save_docx(lines, metadata), file_name=f"{base_name}_transcricao.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    d3.download_button("Baixar PDF", save_pdf(lines, metadata), file_name=f"{base_name}_transcricao.pdf", mime="application/pdf", use_container_width=True)
    d4.download_button("Baixar SRT", build_srt(segments).encode("utf-8"), file_name=f"{base_name}_legenda.srt", mime="text/plain", use_container_width=True)


def page_prompts() -> None:
    text = st.session_state.get("last_plain_text")
    if not text:
        st.info("Conclua uma transcrição para gerar prompts.")
        return
    for title, prompt in build_prompts(text).items():
        with st.expander(title):
            st.text_area(title, prompt, height=230)
            st.download_button(f"Baixar prompt - {title}", prompt.encode("utf-8"), file_name=f"prompt_{safe_filename(title)}.txt", mime="text/plain")


def fragment_media(input_path: str, output_dir: str, segment_seconds: int, suffix: str) -> list[str]:
    pattern = os.path.join(output_dir, f"parte_%03d{suffix}")
    result = run_command(["ffmpeg", "-y", "-i", input_path, "-map", "0", "-c", "copy", "-f", "segment", "-segment_time", str(segment_seconds), "-reset_timestamps", "1", pattern])
    if result.returncode != 0:
        pattern = os.path.join(output_dir, "parte_%03d.mp4")
        result = run_command(["ffmpeg", "-y", "-i", input_path, "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-b:a", "96k", "-f", "segment", "-segment_time", str(segment_seconds), "-reset_timestamps", "1", pattern])
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-2000:] or "Falha ao fragmentar mídia.")
    return sorted(str(x) for x in Path(output_dir).glob("parte_*.*"))


def split_file_by_size(input_path: str, output_dir: str, chunk_mb: int, original_name: str) -> list[str]:
    chunk_size = int(chunk_mb * 1024 * 1024)
    parts = []
    with open(input_path, "rb") as src:
        index = 1
        while True:
            data = src.read(chunk_size)
            if not data:
                break
            part_path = os.path.join(output_dir, f"{safe_filename(original_name)}.part{index:03d}")
            with open(part_path, "wb") as dst:
                dst.write(data)
            parts.append(part_path)
            index += 1
    return parts


def compress_media(input_path: str, output_path: str, suffix: str, preset: str) -> None:
    if preset == "Alta qualidade":
        crf, bitrate = "26", "128k"
    elif preset == "Equilibrado":
        crf, bitrate = "30", "96k"
    else:
        crf, bitrate = "34", "64k"
    if suffix in VIDEO_EXTS:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-c:v", "libx264", "-preset", "veryfast", "-crf", crf, "-c:a", "aac", "-b:a", bitrate, "-movflags", "+faststart", output_path]
    elif suffix in AUDIO_EXTS:
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-codec:a", "libmp3lame", "-b:a", bitrate, output_path]
    else:
        raise ValueError("Formato não suportado para compactação.")
    result = run_command(cmd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or "Falha ao compactar mídia.")


def page_tools() -> None:
    st.header("🛠️ Ferramentas")
    tool = st.radio("Escolha a ferramenta", ["Fragmentar mídia por duração", "Fragmentar qualquer arquivo por tamanho", "Compactar arquivos em ZIP", "Compactar áudio/vídeo"])
    if tool == "Fragmentar mídia por duração":
        media = st.file_uploader("Escolha áudio ou vídeo", type=[x.replace(".", "") for x in SUPPORTED_EXTS], key="frag")
        minutes = st.number_input("Duração de cada parte em minutos", 1, 60, 10)
        if media and st.button("Fragmentar mídia", type="primary", use_container_width=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                suffix = Path(media.name).suffix.lower()
                input_path = os.path.join(tmpdir, safe_filename(media.name) + suffix)
                Path(input_path).write_bytes(media.getbuffer())
                out_dir = os.path.join(tmpdir, "partes")
                os.makedirs(out_dir, exist_ok=True)
                try:
                    parts = fragment_media(input_path, out_dir, int(minutes * 60), suffix)
                    zip_path = os.path.join(tmpdir, "partes.zip")
                    make_zip_from_paths(parts, zip_path)
                    st.success(f"Geradas {len(parts)} parte(s).")
                    st.download_button("Baixar partes em ZIP", bytes_from_file(zip_path), file_name=f"{safe_filename(media.name)}_partes.zip", mime="application/zip", use_container_width=True)
                except Exception as exc:
                    st.error("Falha ao fragmentar mídia.")
                    st.warning(str(exc))
    elif tool == "Fragmentar qualquer arquivo por tamanho":
        f = st.file_uploader("Escolha qualquer arquivo", key="split")
        mb = st.number_input("Tamanho de cada parte em MB", 1, 100, 50)
        if f and st.button("Fragmentar por tamanho", type="primary", use_container_width=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = os.path.join(tmpdir, safe_filename(f.name) + Path(f.name).suffix)
                Path(input_path).write_bytes(f.getbuffer())
                out_dir = os.path.join(tmpdir, "partes")
                os.makedirs(out_dir, exist_ok=True)
                parts = split_file_by_size(input_path, out_dir, int(mb), f.name)
                zip_path = os.path.join(tmpdir, "partes_binarias.zip")
                make_zip_from_paths(parts, zip_path)
                st.success(f"Geradas {len(parts)} parte(s).")
                st.download_button("Baixar partes em ZIP", bytes_from_file(zip_path), file_name=f"{safe_filename(f.name)}_partes_binarias.zip", mime="application/zip", use_container_width=True)
    elif tool == "Compactar arquivos em ZIP":
        files = st.file_uploader("Escolha um ou mais arquivos", accept_multiple_files=True, key="zip")
        if files and st.button("Gerar ZIP", type="primary", use_container_width=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                paths = []
                for file in files:
                    p = os.path.join(tmpdir, safe_filename(file.name) + Path(file.name).suffix)
                    Path(p).write_bytes(file.getbuffer())
                    paths.append(p)
                zip_path = os.path.join(tmpdir, "arquivos.zip")
                make_zip_from_paths(paths, zip_path)
                st.success("ZIP gerado.")
                st.download_button("Baixar ZIP", bytes_from_file(zip_path), file_name="arquivos_compactados.zip", mime="application/zip", use_container_width=True)
    else:
        media = st.file_uploader("Escolha áudio ou vídeo", type=[x.replace(".", "") for x in SUPPORTED_EXTS], key="compress")
        preset = st.selectbox("Nível de compactação", ["Alta qualidade", "Equilibrado", "Menor tamanho"], index=1)
        if media and st.button("Compactar mídia", type="primary", use_container_width=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                suffix = Path(media.name).suffix.lower()
                input_path = os.path.join(tmpdir, safe_filename(media.name) + suffix)
                Path(input_path).write_bytes(media.getbuffer())
                output_ext = ".mp4" if suffix in VIDEO_EXTS else ".mp3"
                output_path = os.path.join(tmpdir, safe_filename(media.name) + "_compactado" + output_ext)
                try:
                    compress_media(input_path, output_path, suffix, preset)
                    st.success("Mídia compactada.")
                    st.download_button("Baixar compactado", bytes_from_file(output_path), file_name=os.path.basename(output_path), mime="video/mp4" if output_ext == ".mp4" else "audio/mpeg", use_container_width=True)
                except Exception as exc:
                    st.error("Falha ao compactar mídia.")
                    st.warning(str(exc))


def page_youtube_local() -> None:
    st.header("▶️ YouTube Local")
    st.info("Quando o YouTube bloquear o Streamlit Cloud, baixe o áudio no seu computador e envie o MP3 pelo upload.")
    st.markdown("### Passo a passo")
    st.write("1. Instale o yt-dlp uma única vez:")
    st.code("python -m pip install -U yt-dlp", language="bash")
    st.write("2. Instale o FFmpeg, se necessário:")
    st.code("winget install Gyan.FFmpeg", language="bash")
    st.write("3. Baixe o áudio autorizado:")
    st.code('yt-dlp -x --audio-format mp3 --audio-quality 0 "COLE_A_URL_DO_YOUTUBE_AQUI"', language="bash")
    url = st.text_input("URL para gerar comando", placeholder="https://www.youtube.com/watch?v=...")
    if url:
        st.code(f'yt-dlp -x --audio-format mp3 --audio-quality 0 "{url.strip()}"', language="bash")


def page_help() -> None:
    st.header("❓ Ajuda")
    st.write("Use o menu lateral para acessar cada função. Na versão v8, as funcionalidades voltaram a ficar separadas em páginas, em vez de ficarem escondidas abaixo do dashboard.")
    st.markdown("### Configuração de usuários em Secrets")
    st.code('[users]\n"vmsoares@tre-ba.jus.br" = "SUA_SENHA"\n\n[profiles]\n"vmsoares@tre-ba.jus.br" = "admin"', language="toml")
    st.markdown("### Observações")
    st.write("No Streamlit Cloud, use arquivos pequenos ou médios e modelo small. Para vídeos longos, fragmente ou rode localmente.")


def app_screen() -> None:
    inject_css()
    page = render_sidebar()
    render_topbar()
    if page == "Início":
        page_home()
    elif page == "Transcrever":
        page_transcribe()
    elif page == "Resultado":
        page_result()
    elif page == "Prompts":
        page_prompts()
    elif page == "Ferramentas":
        page_tools()
    elif page == "YouTube Local":
        page_youtube_local()
    else:
        page_help()
    st.caption(APP_VERSION)
    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
else:
    app_screen()
