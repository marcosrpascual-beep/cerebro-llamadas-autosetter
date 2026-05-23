"""
🧠 CEREBRO DE LLAMADAS v4 - by Nico Acero / AUTOSETTER™
- Recibe webhooks de Fathom
- Analiza con Claude según tipo (VENTA / CLIENTE / EQUIPO)
- Crea Google Doc detallado en la carpeta correcta
- Avisa por Telegram con link al Doc
"""

import os
import io
import json
import re
import html as _html
import threading
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from anthropic import Anthropic
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from apscheduler.schedulers.background import BackgroundScheduler

# ============================================================
# 🔑 LLAVES
# ============================================================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = (
    os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    or os.environ.get("GOOGLE_CREDENTIALS_JSON")
)
# OAuth de usuario (preferido sobre Service Account porque los SA en cuentas
# Gmail personales tienen 0 GB de cuota y no pueden crear archivos en Drive).
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_OAUTH_REFRESH_TOKEN = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")

# IDs de carpetas de Google Drive (las creas tú y pasas los IDs como env vars
# en Railway — ver .env.example y el paso 06 del manual).
FOLDER_VENTAS    = os.environ.get("FOLDER_VENTAS")
FOLDER_CLIENTES  = os.environ.get("FOLDER_CLIENTES")
FOLDER_EQUIPO    = os.environ.get("FOLDER_EQUIPO")
FOLDER_MAESTROS  = os.environ.get("FOLDER_MAESTROS")  # carpeta del Doc maestro mensual
FOLDER_DATOS     = os.environ.get("FOLDER_DATOS")     # carpeta oculta para los .json hermanos
CRON_TOKEN       = os.environ.get("CRON_TOKEN")       # protege el endpoint /cron/maestro
FATHOM_API_KEY   = os.environ.get("FATHOM_API_KEY")   # para el polling de fallback

claude = Anthropic(api_key=ANTHROPIC_API_KEY)
app = Flask(__name__)

# ============================================================
# 🔧 GOOGLE DOCS: inicializar cliente
# ============================================================
def get_google_services():
    scopes = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ]

    # 1) Preferimos OAuth de usuario (los archivos se crean en SU Drive con SU cuota).
    if GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET and GOOGLE_OAUTH_REFRESH_TOKEN:
        creds = UserCredentials(
            token=None,
            refresh_token=GOOGLE_OAUTH_REFRESH_TOKEN,
            client_id=GOOGLE_OAUTH_CLIENT_ID,
            client_secret=GOOGLE_OAUTH_CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=scopes,
        )
        docs_service  = build("docs",  "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)
        return docs_service, drive_service

    # 2) Fallback a Service Account (solo funciona con Shared Drives / Workspace).
    raw_json = (GOOGLE_SERVICE_ACCOUNT_JSON or "").strip()
    if not raw_json:
        print("❌ Error Google Docs: no hay credenciales (ni OAuth ni Service Account)")
        return None, None

    try:
        info = json.loads(raw_json)
    except Exception as e:
        print(f"❌ Error Google Docs: credenciales JSON inválidas: {e}")
        return None, None

    creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    docs_service  = build("docs",  "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    return docs_service, drive_service


def get_next_number(drive_service, folder_id, prefix):
    """Cuenta cuántos docs hay ya en la carpeta y devuelve el siguiente número."""
    if not drive_service:
        return 1
    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(name)"
        ).execute()
        files = results.get("files", [])
        nums = []
        for f in files:
            match = re.search(rf"{prefix}-(\d+)", f["name"])
            if match:
                nums.append(int(match.group(1)))
        return max(nums) + 1 if nums else 1
    except Exception:
        return 1


# ============================================================
# 🧠 PROMPTS PARA CLAUDE (uno por tipo)
# ============================================================

PROMPT_VENTA = """Eres un coach experto en ventas y analista de llamadas comerciales.

Analiza esta transcripción de llamada de VENTA y responde SOLO con JSON válido (sin markdown, sin ```).

{
  "tipo": "VENTA",
  "cliente": "nombre o empresa del prospecto",
  "closer": "nombre del vendedor",
  "cerrado": true o false,
  "importe": "cantidad con moneda o null",
  "duracion_estimada": "X minutos",
  "resumen_ejecutivo": "3-4 líneas explicando qué pasó en la llamada",
  "puntos_positivos": [
    "Cosa concreta que hizo bien el closer (sé específico, pon ejemplos de la llamada)"
  ],
  "puntos_negativos": [
    "Cosa concreta que hizo mal o pudo mejorar"
  ],
  "objeciones": [
    {"objecion": "qué dijo el cliente", "como_se_manejo": "cómo respondió el closer", "valoracion": "bien/regular/mal"}
  ],
  "mejoras_detalladas": [
    {"momento": "en qué momento de la llamada", "que_paso": "qué dijo o hizo", "como_deberia_ser": "exactamente qué debería haber dicho o hecho en su lugar"}
  ],
  "frases_clave": [
    "frase literal del cliente que revela algo importante"
  ],
  "proximos_pasos": ["acción 1", "acción 2"],
  "puntuacion_llamada": "nota del 1 al 10 con justificación breve",
  "resumen_corto_telegram": "máximo 2 líneas para el aviso de Telegram"
}

TRANSCRIPCIÓN:
"""

PROMPT_EQUIPO = """Eres un asistente ejecutivo experto en gestión de equipos.

Analiza esta transcripción de REUNIÓN DE EQUIPO y responde SOLO con JSON válido (sin markdown, sin ```).

{
  "tipo": "EQUIPO",
  "asistentes": ["nombre 1", "nombre 2"],
  "resumen_ejecutivo": "4-5 líneas con lo más importante tratado",
  "puntos_clave": [
    "punto importante 1",
    "punto importante 2"
  ],
  "decisiones_tomadas": [
    "decisión concreta 1"
  ],
  "tareas": [
    {"responsable": "nombre", "tarea": "descripción concreta de qué debe hacer", "deadline": "fecha o 'sin fecha'", "prioridad": "alta/media/baja"}
  ],
  "pendientes_proxima_reunion": [
    "tema que quedó pendiente"
  ],
  "resumen_corto_telegram": "máximo 2 líneas para el aviso de Telegram"
}

TRANSCRIPCIÓN:
"""

PROMPT_CLIENTE = """Eres un experto en customer success y gestión de clientes.

Analiza esta transcripción de LLAMADA CON CLIENTE y responde SOLO con JSON válido (sin markdown, sin ```).

{
  "tipo": "CLIENTE",
  "cliente": "nombre o empresa",
  "motivo_llamada": "por qué se hizo esta llamada",
  "resumen_ejecutivo": "4-5 líneas con lo más importante",
  "estado_cliente": "satisfecho/neutro/insatisfecho",
  "problemas_detectados": [
    "problema o queja concreta"
  ],
  "necesidades_detectadas": [
    "necesidad o deseo del cliente"
  ],
  "compromisos_adquiridos": [
    {"compromiso": "qué nos comprometemos a hacer", "responsable": "quién lo hace", "deadline": "cuándo"}
  ],
  "tareas": [
    {"responsable": "nombre", "tarea": "qué debe hacer", "deadline": "cuándo", "prioridad": "alta/media/baja"}
  ],
  "proximo_contacto": "fecha o motivo del próximo contacto",
  "resumen_corto_telegram": "máximo 2 líneas para el aviso de Telegram"
}

TRANSCRIPCIÓN:
"""


# Dual model: Haiku para deteccion (tarea trivial), Sonnet para analisis profundo.
MODEL_DETECCION = "claude-haiku-4-5-20251001"
MODEL_ANALISIS = "claude-sonnet-4-6"


def analizar_con_claude(transcripcion, tipo_prompt, model=None):
    """Llama a Claude y parsea su JSON. Con 1 reintento si viene roto."""
    model = model or MODEL_ANALISIS
    for intento in (1, 2):
        try:
            respuesta = claude.messages.create(
                model=model,
                max_tokens=8000,
                messages=[{"role": "user", "content": tipo_prompt + transcripcion}]
            )
            texto = respuesta.content[0].text.strip()
            texto = texto.replace("```json", "").replace("```", "").strip()
            # Intento parseo directo
            try:
                return json.loads(texto)
            except json.JSONDecodeError as je:
                # Recortar a {...} mas externo por si Claude antepuso/anadió texto
                primer = texto.find("{")
                ultimo = texto.rfind("}")
                if primer != -1 and ultimo > primer:
                    try:
                        return json.loads(texto[primer:ultimo + 1])
                    except json.JSONDecodeError:
                        pass
                if intento == 1:
                    print(f"⚠️ Claude ({model}) JSON malformado, reintentando: {je}")
                    continue
                print(f"❌ Claude ({model}) JSON inválido tras 2 intentos: {je}")
                print(f"   primer 500 chars de la respuesta: {texto[:500]}")
                return None
        except Exception as e:
            if intento == 1:
                print(f"⚠️ Claude ({model}) error, reintentando: {e}")
                continue
            print(f"❌ Error Claude ({model}) tras 2 intentos: {e}")
            return None
    return None


# ============================================================
# 📄 Google Doc desde HTML (Drive conversion)
# ============================================================
def crear_google_doc_desde_html(titulo, html_contenido, folder_id):
    """Sube un HTML a Drive con conversion=true para obtener un Google Doc nativo
    con estilos limpios. Mucho mas robusto que construir el doc con batchUpdate.
    """
    _, drive_service = get_google_services()
    if not drive_service:
        print("❌ Error Google Docs: sin credenciales")
        return None
    try:
        file_metadata = {
            "name": titulo,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [folder_id],
        }
        media = MediaInMemoryUpload(
            html_contenido.encode("utf-8"),
            mimetype="text/html",
            resumable=False,
        )
        doc = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
        ).execute()

        drive_service.permissions().create(
            fileId=doc["id"],
            body={"role": "reader", "type": "anyone"},
            supportsAllDrives=True,
        ).execute()

        return doc.get("webViewLink") or f"https://docs.google.com/document/d/{doc['id']}/edit"
    except Exception as e:
        print(f"❌ Error creando Doc HTML: {e}")
        return None


# ----- helpers HTML -----

_VAL_EMOJI = {"bien": "✅", "regular": "⚠️", "mal": "❌"}
_PRIO_EMOJI = {"alta": "🔴", "media": "🟡", "baja": "🟢"}


def _esc(s):
    return _html.escape(str(s if s is not None else ""))


def _val_emoji(v):
    return _VAL_EMOJI.get(v.lower(), "") if isinstance(v, str) else ""


def _prio_emoji(p):
    return _PRIO_EMOJI.get(p.lower(), "") if isinstance(p, str) else ""


def _split_puntuacion(raw):
    """Separa 'X/10 - texto' en (nota, justificacion)."""
    if not raw or not isinstance(raw, str):
        return str(raw or "?"), ""
    for sep in (" - ", " – ", " — ", ": ", " : ", "\n"):
        if sep in raw:
            nota, just = raw.split(sep, 1)
            return nota.strip(), just.strip()
    return raw.strip(), ""


def _kv_table(rows):
    inner = "\n".join(
        f"<tr><td><b>{_esc(k)}</b></td><td>&nbsp;&nbsp;{_esc(v)}</td></tr>"
        for k, v in rows
    )
    return (
        '<table cellpadding="4" style="border-collapse: collapse;">\n'
        + inner + "\n</table>"
    )


def _ul(items, check=False):
    if not items:
        return ""
    prefix = "☐ " if check else ""
    inner = "\n".join(f"<li>{prefix}{_esc(i)}</li>" for i in items)
    return f"<ul>\n{inner}\n</ul>"


def _html_wrap(titulo, secciones_html, share_url):
    fathom_line = (
        f'\n🎥 <a href="{_esc(share_url)}">Grabación en Fathom</a>'
        if share_url else ""
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Helvetica', 'Inter', sans-serif; font-size: 12pt; color: #222;">

<h1 style="font-size: 18pt; margin-bottom: 4px;">{_esc(titulo)}</h1>
<p style="color: #666; font-size: 11pt; margin-top: 0;">
🧠 Cerebro de Llamadas · AUTOSETTER™<br>{fathom_line}
</p>
<hr>

{secciones_html}

<hr>
<p style="color: #999; font-size: 10pt; text-align: center;">
🧠 Generado automáticamente por Cerebro de Llamadas · AUTOSETTER™
</p>

</body>
</html>"""


def build_html_venta(analisis, numero, fecha_str, share_url=""):
    cliente = analisis.get("cliente", "?")
    closer = analisis.get("closer", "?")
    cerrado_txt = "✅ Cerrada" if analisis.get("cerrado") else "❌ No cerrada"
    importe = analisis.get("importe") or "No especificado"
    nota, nota_just = _split_puntuacion(analisis.get("puntuacion_llamada", "?"))

    sec = []

    sec.append("<h2>📊 Datos clave</h2>\n" + _kv_table([
        ("Cliente", cliente),
        ("Closer", closer),
        ("Estado", cerrado_txt),
        ("Importe", importe),
        ("Puntuación", nota),
    ]))

    sec.append(
        "<h2>📋 Resumen ejecutivo</h2>\n"
        f"<p>{_esc(analisis.get('resumen_ejecutivo', ''))}</p>"
    )

    if nota_just:
        sec.append(
            f'<p style="color: #666;"><i>Justificación de la puntuación:</i> {_esc(nota_just)}</p>'
        )

    sec.append("<h2>✅ Puntos positivos</h2>\n" + _ul(analisis.get("puntos_positivos", [])))
    sec.append("<h2>❌ Errores cometidos</h2>\n" + _ul(analisis.get("puntos_negativos", [])))

    obj_parts = ["<h2>🛑 Objeciones</h2>"]
    for i, o in enumerate(analisis.get("objeciones", []), 1):
        val = o.get("valoracion", "?")
        obj_parts.extend([
            f"<h3>Objeción {i}</h3>",
            f'<p><b>Qué dijo:</b> "{_esc(o.get("objecion", "?"))}"</p>',
            f"<p><b>Cómo se respondió:</b> {_esc(o.get('como_se_manejo', '?'))}</p>",
            f"<p><b>Valoración:</b> {_val_emoji(val)} {_esc(val)}</p>",
        ])
    sec.append("\n".join(obj_parts))

    mej_parts = ["<h2>🎯 Mejoras detalladas</h2>"]
    for i, m in enumerate(analisis.get("mejoras_detalladas", []), 1):
        mej_parts.extend([
            f"<h3>Momento {i} · {_esc(m.get('momento', '?'))}</h3>",
            f"<p><b>Qué pasó:</b> {_esc(m.get('que_paso', '?'))}</p>",
            f"<p><b>Cómo debería ser:</b> {_esc(m.get('como_deberia_ser', '?'))}</p>",
        ])
    sec.append("\n".join(mej_parts))

    if analisis.get("frases_clave"):
        frases_parts = ["<h2>💬 Frases clave del cliente</h2>", "<blockquote>"]
        for f in analisis.get("frases_clave", []):
            frases_parts.append(f'<p>"{_esc(f)}"</p>')
        frases_parts.append("</blockquote>")
        sec.append("\n".join(frases_parts))

    sec.append(
        "<h2>📌 Próximos pasos</h2>\n"
        + _ul(analisis.get("proximos_pasos", []), check=True)
    )

    titulo = f"VENTA-{numero:03d} · {cliente} · {fecha_str}"
    return titulo, _html_wrap(titulo, "\n\n".join(sec), share_url)


def build_html_equipo(analisis, numero, fecha_str, share_url=""):
    asistentes = analisis.get("asistentes", [])
    tareas = analisis.get("tareas", [])
    decisiones = analisis.get("decisiones_tomadas", [])

    sec = []
    sec.append("<h2>📊 Datos clave</h2>\n" + _kv_table([
        ("Asistentes", ", ".join(asistentes) if asistentes else "?"),
        ("Nº tareas", str(len(tareas))),
        ("Nº decisiones", str(len(decisiones))),
    ]))

    sec.append(
        "<h2>📋 Resumen ejecutivo</h2>\n"
        f"<p>{_esc(analisis.get('resumen_ejecutivo', ''))}</p>"
    )

    sec.append("<h2>🔑 Puntos clave</h2>\n" + _ul(analisis.get("puntos_clave", [])))
    sec.append("<h2>✅ Decisiones tomadas</h2>\n" + _ul(decisiones))

    tareas_parts = ["<h2>📝 Tareas asignadas</h2>"]
    for i, t in enumerate(tareas, 1):
        prio = t.get("prioridad", "?")
        tareas_parts.extend([
            f"<h3>Tarea {i} · {_esc(t.get('tarea', '?'))}</h3>",
            f"<p><b>Responsable:</b> {_esc(t.get('responsable', '?'))}</p>",
            f"<p><b>Deadline:</b> {_esc(t.get('deadline', 'sin fecha'))}</p>",
            f"<p><b>Prioridad:</b> {_prio_emoji(prio)} {_esc(prio)}</p>",
        ])
    sec.append("\n".join(tareas_parts))

    sec.append(
        "<h2>⏭️ Pendientes próxima reunión</h2>\n"
        + _ul(analisis.get("pendientes_proxima_reunion", []))
    )

    titulo = f"EQUIPO-{numero:03d} · Reunión de equipo · {fecha_str}"
    return titulo, _html_wrap(titulo, "\n\n".join(sec), share_url)


def build_html_cliente(analisis, numero, fecha_str, share_url=""):
    cliente = analisis.get("cliente", "?")
    estado = analisis.get("estado_cliente", "?")
    motivo = analisis.get("motivo_llamada", "?")
    estado_low = estado.lower() if isinstance(estado, str) else ""
    riesgo = {
        "satisfecho": "🟢 Bajo",
        "neutro": "🟡 Medio",
        "insatisfecho": "🔴 Alto",
    }.get(estado_low, "?")

    sec = []
    sec.append("<h2>📊 Datos clave</h2>\n" + _kv_table([
        ("Cliente", cliente),
        ("Estado", estado),
        ("Riesgo de churn", riesgo),
        ("Motivo llamada", motivo),
    ]))

    sec.append(
        "<h2>📋 Resumen ejecutivo</h2>\n"
        f"<p>{_esc(analisis.get('resumen_ejecutivo', ''))}</p>"
    )

    sec.append("<h2>🚨 Problemas detectados</h2>\n" + _ul(analisis.get("problemas_detectados", [])))
    sec.append("<h2>💡 Necesidades detectadas</h2>\n" + _ul(analisis.get("necesidades_detectadas", [])))

    comp_parts = ["<h2>🤝 Compromisos adquiridos</h2>"]
    for i, c in enumerate(analisis.get("compromisos_adquiridos", []), 1):
        comp_parts.extend([
            f"<h3>Compromiso {i}</h3>",
            f"<p><b>Qué:</b> {_esc(c.get('compromiso', '?'))}</p>",
            f"<p><b>Responsable:</b> {_esc(c.get('responsable', '?'))}</p>",
            f"<p><b>Deadline:</b> {_esc(c.get('deadline', '?'))}</p>",
        ])
    sec.append("\n".join(comp_parts))

    tareas_parts = ["<h2>📝 Tareas</h2>"]
    for i, t in enumerate(analisis.get("tareas", []), 1):
        prio = t.get("prioridad", "?")
        tareas_parts.extend([
            f"<h3>Tarea {i} · {_esc(t.get('tarea', '?'))}</h3>",
            f"<p><b>Responsable:</b> {_esc(t.get('responsable', '?'))}</p>",
            f"<p><b>Deadline:</b> {_esc(t.get('deadline', 'sin fecha'))}</p>",
            f"<p><b>Prioridad:</b> {_prio_emoji(prio)} {_esc(prio)}</p>",
        ])
    sec.append("\n".join(tareas_parts))

    sec.append(
        "<h2>📅 Próximo contacto</h2>\n"
        f"<p>{_esc(analisis.get('proximo_contacto', 'No definido'))}</p>"
    )

    titulo = f"CLIENTE-{numero:03d} · {cliente} · {fecha_str}"
    return titulo, _html_wrap(titulo, "\n\n".join(sec), share_url)


# ============================================================
# 📚 DOC MAESTRO MENSUAL (cada 30 dias)
# ============================================================

def guardar_analisis_json(titulo_doc, analisis, folder_id, share_url, tipo, numero):
    """Guarda el JSON del analisis en la carpeta oculta FOLDER_DATOS (no en la
    carpeta del Doc) para mantener limpias las 3 carpetas principales del
    cliente. Usado luego por el doc maestro mensual.
    `folder_id` (carpeta original del Doc) se ignora — solo lo mantenemos en
    la firma por compatibilidad y se guarda en el JSON para trazabilidad.
    """
    if not FOLDER_DATOS:
        print("⚠️ FOLDER_DATOS no configurado — no se guarda JSON. El maestro no podrá agregar.")
        return
    _, drive_service = get_google_services()
    if not drive_service:
        return
    try:
        payload = {
            "tipo": tipo,
            "numero": numero,
            "titulo_doc": titulo_doc,
            "share_url": share_url,
            "folder_origen": folder_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "analisis": analisis,
        }
        media = MediaInMemoryUpload(
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            mimetype="application/json",
            resumable=False,
        )
        drive_service.files().create(
            body={
                "name": f"{titulo_doc}.json",
                "mimeType": "application/json",
                "parents": [FOLDER_DATOS],
            },
            media_body=media,
            fields="id",
            supportsAllDrives=True,
        ).execute()
    except Exception as e:
        print(f"⚠️ No se pudo guardar JSON oculto: {e}")


def leer_analisis_de_carpeta(folder_id, desde_dt, tipo_filter=None):
    """Lee todos los .json (creados desde desde_dt) de la carpeta FOLDER_DATOS,
    filtrando opcionalmente por tipo (VENTA/CLIENTE/EQUIPO).

    El parametro folder_id se mantiene por compatibilidad pero ahora todos los
    JSON estan en FOLDER_DATOS (carpeta oculta). El filtrado por tipo se hace
    leyendo el campo "tipo" o "folder_origen" del JSON.
    """
    _, drive_service = get_google_services()
    if not drive_service:
        return []
    target_folder = FOLDER_DATOS or folder_id  # fallback al folder_id viejo si no hay FOLDER_DATOS
    if not target_folder:
        return []
    desde_iso = desde_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    q = (
        f"'{target_folder}' in parents and trashed=false "
        f"and mimeType='application/json' and createdTime > '{desde_iso}'"
    )
    try:
        results = drive_service.files().list(
            q=q,
            fields="files(id, name, createdTime)",
            orderBy="createdTime",
            pageSize=200,
            supportsAllDrives=True,
        ).execute()
    except Exception as e:
        print(f"⚠️ No pude listar JSONs de carpeta {target_folder}: {e}")
        return []

    # Si llamaron con folder_id especifico, inferimos el tipo para filtrar.
    # Mapeo: folder_id → tipo del JSON
    if tipo_filter is None and folder_id:
        if folder_id == FOLDER_VENTAS:    tipo_filter = "VENTA"
        elif folder_id == FOLDER_CLIENTES: tipo_filter = "CLIENTE"
        elif folder_id == FOLDER_EQUIPO:   tipo_filter = "EQUIPO"

    out = []
    for f in results.get("files", []):
        try:
            req = drive_service.files().get_media(fileId=f["id"], supportsAllDrives=True)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, req)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            data = json.loads(buf.getvalue().decode("utf-8"))
            if tipo_filter and data.get("tipo") != tipo_filter:
                continue
            out.append(data)
        except Exception as e:
            print(f"⚠️ No pude leer {f['name']}: {e}")
    return out


PROMPT_MAESTRO = """Eres un analista senior. Te paso una lista de análisis de llamadas de tipo {tipo} de los últimos 30 días.

Sintetiza un resumen ejecutivo del mes en JSON válido (sin markdown), con esta estructura:

{{
  "headline": "1 línea con la conclusión más importante del mes",
  "metricas_clave": [
    "métrica concreta con número, ej: '12 llamadas totales · 4 cerradas (33%)'",
    "otra métrica relevante"
  ],
  "patrones_detectados": [
    "patrón recurrente que se repite en varias llamadas"
  ],
  "wins_del_mes": [
    "logro o llamada destacable POSITIVA, con cliente y razón"
  ],
  "alertas": [
    "problema, riesgo o llamada destacable NEGATIVA"
  ],
  "recomendaciones": [
    "acción concreta y accionable para el próximo mes"
  ]
}}

ANÁLISIS DE LLAMADAS DE LOS ÚLTIMOS 30 DÍAS:
"""


def resumir_bloque_con_claude(tipo, analisis_list):
    """Resume un bloque de analisis con Claude. Si no hay datos devuelve estructura vacia."""
    if not analisis_list:
        return {
            "headline": "Sin llamadas registradas este periodo.",
            "metricas_clave": [],
            "patrones_detectados": [],
            "wins_del_mes": [],
            "alertas": [],
            "recomendaciones": [],
        }
    # Compactar para no mandar el JSON entero — solo lo relevante.
    compact = []
    for item in analisis_list:
        a = item.get("analisis", {})
        compact.append({
            "fecha": item.get("created_at", "")[:10],
            "titulo": item.get("titulo_doc", ""),
            "datos": a,
        })
    prompt = PROMPT_MAESTRO.format(tipo=tipo)
    return analizar_con_claude(json.dumps(compact, ensure_ascii=False), prompt) or {
        "headline": "(Claude no pudo procesar este bloque)",
        "metricas_clave": [],
        "patrones_detectados": [],
        "wins_del_mes": [],
        "alertas": [],
        "recomendaciones": [],
    }


def _seccion_maestro_html(emoji, nombre, num_llamadas, resumen):
    """Construye el HTML de una seccion del maestro (VENTAS/CLIENTES/EQUIPO)."""
    def _ul_clean(items):
        if not items:
            return "<p style='color:#999;'><i>(sin datos)</i></p>"
        return "<ul>\n" + "\n".join(f"<li>{_esc(i)}</li>" for i in items) + "\n</ul>"

    return f"""<h2>{emoji} {nombre}  <span style="color:#999; font-weight:normal; font-size:11pt;">· {num_llamadas} llamadas</span></h2>

<p style="font-size:13pt;"><b>{_esc(resumen.get('headline', ''))}</b></p>

<h3>📈 Métricas clave</h3>
{_ul_clean(resumen.get('metricas_clave', []))}

<h3>🔁 Patrones detectados</h3>
{_ul_clean(resumen.get('patrones_detectados', []))}

<h3>🏆 Wins del mes</h3>
{_ul_clean(resumen.get('wins_del_mes', []))}

<h3>⚠️ Alertas</h3>
{_ul_clean(resumen.get('alertas', []))}

<h3>🎯 Recomendaciones para el próximo mes</h3>
{_ul_clean(resumen.get('recomendaciones', []))}
"""


def build_html_maestro(titulo, fecha_desde, fecha_hasta, ventas_data, clientes_data, equipo_data):
    """Genera el HTML del Doc maestro mensual con 3 secciones grandes."""
    ventas_n, ventas_resumen = ventas_data
    clientes_n, clientes_resumen = clientes_data
    equipo_n, equipo_resumen = equipo_data

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Helvetica', 'Inter', sans-serif; font-size: 12pt; color: #222;">

<h1 style="font-size: 20pt; margin-bottom: 4px;">{_esc(titulo)}</h1>
<p style="color: #666; font-size: 11pt; margin-top: 0;">
🧠 Cerebro de Llamadas · AUTOSETTER™<br>
📅 Periodo: {_esc(fecha_desde)} → {_esc(fecha_hasta)}<br>
📊 Total: {ventas_n + clientes_n + equipo_n} llamadas analizadas
</p>
<hr>

{_seccion_maestro_html("💼", "VENTAS", ventas_n, ventas_resumen)}
<hr>
{_seccion_maestro_html("🤝", "CLIENTES", clientes_n, clientes_resumen)}
<hr>
{_seccion_maestro_html("👥", "EQUIPO", equipo_n, equipo_resumen)}

<hr>
<p style="color: #999; font-size: 10pt; text-align: center;">
🧠 Generado automáticamente por Cerebro de Llamadas · AUTOSETTER™
</p>

</body>
</html>"""


def generar_maestro():
    """Lee los .json de los ultimos 30 dias en las 3 carpetas y genera el Doc maestro."""
    if not FOLDER_MAESTROS:
        print("⚠️ FOLDER_MAESTROS no configurado — no genero maestro")
        return None

    ahora = datetime.now(timezone.utc)
    hace_30 = ahora - timedelta(days=30)

    print(f"📚 Generando maestro · periodo {hace_30.date()} → {ahora.date()}")

    ventas = leer_analisis_de_carpeta(FOLDER_VENTAS, hace_30)
    clientes = leer_analisis_de_carpeta(FOLDER_CLIENTES, hace_30)
    equipos = leer_analisis_de_carpeta(FOLDER_EQUIPO, hace_30)

    print(f"   · Ventas: {len(ventas)} · Clientes: {len(clientes)} · Equipo: {len(equipos)}")

    resumen_ventas = resumir_bloque_con_claude("VENTAS", ventas)
    resumen_clientes = resumir_bloque_con_claude("CLIENTES", clientes)
    resumen_equipo = resumir_bloque_con_claude("EQUIPO", equipos)

    fecha_desde = hace_30.strftime("%d %b %Y")
    fecha_hasta = ahora.strftime("%d %b %Y")
    titulo = f"MAESTRO · {fecha_desde} → {fecha_hasta}"

    html = build_html_maestro(
        titulo,
        fecha_desde,
        fecha_hasta,
        (len(ventas), resumen_ventas),
        (len(clientes), resumen_clientes),
        (len(equipos), resumen_equipo),
    )

    url = crear_google_doc_desde_html(titulo, html, FOLDER_MAESTROS)
    if url:
        print(f"✅ Maestro creado: {url}")
        mandar_telegram(
            f"📚 <b>Doc maestro generado</b>\n"
            f"📅 {fecha_desde} → {fecha_hasta}\n"
            f"📊 {len(ventas)} ventas · {len(clientes)} clientes · {len(equipos)} reuniones\n"
            f"📄 <a href='{url}'>Ver maestro</a>"
        )
    return url


def maestro_si_toca():
    """Chequea si el ultimo maestro tiene >= 30 dias. Si si, dispara generar_maestro."""
    if not FOLDER_MAESTROS:
        return
    try:
        _, drive_service = get_google_services()
        if not drive_service:
            return
        results = drive_service.files().list(
            q=(
                f"'{FOLDER_MAESTROS}' in parents and trashed=false "
                f"and mimeType='application/vnd.google-apps.document'"
            ),
            fields="files(id, name, createdTime)",
            orderBy="createdTime desc",
            pageSize=1,
            supportsAllDrives=True,
        ).execute()
        files = results.get("files", [])
        if files:
            ultimo = datetime.fromisoformat(files[0]["createdTime"].replace("Z", "+00:00"))
            dias = (datetime.now(timezone.utc) - ultimo).days
            if dias < 30:
                print(f"📚 Aun no toca maestro (ultimo hace {dias}d)")
                return
        generar_maestro()
    except Exception as e:
        print(f"❌ Error en maestro_si_toca: {e}")


# ============================================================
# 📱 Telegram
# ============================================================
def mandar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"❌ Error Telegram: {e}")


# ============================================================
# 🎯 WEBHOOK PRINCIPAL
# ============================================================
@app.route("/webhook/fathom", methods=["POST"])
def recibir_fathom():
    data = request.json or {}
    print(f"📨 Webhook recibido: {list(data.keys())}")
    # Responder a Fathom YA y procesar el analisis en background.
    # Claude + Google Docs tardan >30s y mataban el worker por timeout.
    threading.Thread(target=procesar_webhook, args=(data,), daemon=True).start()
    return jsonify({"status": "accepted"}), 200


def procesar_webhook(data):
    titulo = "Sin título"
    share_url = ""
    try:
        # === DEDUPLICACION (webhook vs polling) ===
        # Si esta llamada ya esta en el cache (la cogio el polling o un webhook
        # anterior), no la procesamos de nuevo. Marcamos AHORA, no al final.
        recording_id = data.get("recording_id")
        if recording_id is not None:
            with _processed_ids_lock:
                global _processed_ids_cache
                if _processed_ids_cache is None:
                    # Inicializar cache leyendo .json de Drive (primera vez).
                    pass  # se inicializa fuera del lock abajo
            if _processed_ids_cache is None:
                _get_processed_ids()
            with _processed_ids_lock:
                if str(recording_id) in _processed_ids_cache:
                    print(f"⏭️  Recording {recording_id} ya procesada, saltando duplicado.")
                    return
                _processed_ids_cache.add(str(recording_id))

        titulo        = data.get("title") or data.get("meeting_title") or "Sin título"
        share_url     = data.get("share_url", "")
        transcript    = data.get("transcript")
        summary       = data.get("default_summary")
        invitees      = data.get("calendar_invitees", [])
        recorded_by   = data.get("recorded_by", {})
        fecha_str     = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Sin transcripción → aviso y salir
        if not transcript or not isinstance(transcript, list) or len(transcript) == 0:
            mandar_telegram(f"⚠️ Llegó llamada sin transcripción\n📌 {titulo}\n🔗 {share_url}")
            return

        # Convertir transcripción a texto plano
        lineas = []
        for entry in transcript:
            speaker   = entry.get("speaker", {}).get("display_name", "?")
            texto     = entry.get("text", "")
            timestamp = entry.get("timestamp", "")
            lineas.append(f"[{timestamp}] {speaker}: {texto}")
        transcripcion_texto = "\n".join(lineas)

        resumen_fathom = "(sin resumen)"
        if summary and isinstance(summary, dict):
            resumen_fathom = summary.get("markdown_formatted", "(sin resumen)")

        datos_completos = f"""TÍTULO: {titulo}
GRABADO POR: {recorded_by.get('name','?')} ({recorded_by.get('email','')})
PARTICIPANTES: {', '.join([i.get('name','?') for i in invitees])}
RESUMEN AUTO FATHOM: {resumen_fathom}

TRANSCRIPCIÓN:
{transcripcion_texto}
"""

        # ── Detectar tipo con Claude (primer análisis ligero) → Haiku ──
        deteccion = analizar_con_claude(
            datos_completos,
            """Lee esta info de llamada y responde SOLO con un JSON así (sin markdown):
{"tipo": "VENTA" o "EQUIPO" o "CLIENTE"}

INFO:
""",
            model=MODEL_DETECCION,
        )

        tipo = deteccion.get("tipo", "EQUIPO") if deteccion else "EQUIPO"
        print(f"🔍 Tipo detectado: {tipo}")

        # ── Análisis profundo según tipo ──
        if tipo == "VENTA":
            analisis = analizar_con_claude(datos_completos, PROMPT_VENTA)
            folder_id = FOLDER_VENTAS
            prefix = "VENTA"
        elif tipo == "CLIENTE":
            analisis = analizar_con_claude(datos_completos, PROMPT_CLIENTE)
            folder_id = FOLDER_CLIENTES
            prefix = "CLIENTE"
        else:
            analisis = analizar_con_claude(datos_completos, PROMPT_EQUIPO)
            folder_id = FOLDER_EQUIPO
            prefix = "EQUIPO"
            tipo = "EQUIPO"

        if not analisis:
            mandar_telegram(f"⚠️ Llamada llegó pero Claude no la pudo analizar\n📌 {titulo}\n🔗 {share_url}")
            return

        # ── Crear Google Doc ──
        numero = 1
        try:
            _, drive_service = get_google_services()
            numero = get_next_number(drive_service, folder_id, prefix)

            if tipo == "VENTA":
                titulo_doc, html = build_html_venta(analisis, numero, fecha_str, share_url)
            elif tipo == "CLIENTE":
                titulo_doc, html = build_html_cliente(analisis, numero, fecha_str, share_url)
            else:
                titulo_doc, html = build_html_equipo(analisis, numero, fecha_str, share_url)

            doc_url = crear_google_doc_desde_html(titulo_doc, html, folder_id)
            print(f"✅ Doc creado: {doc_url}")
            # Guardar JSON hermano para el maestro mensual (invisible al cliente).
            guardar_analisis_json(titulo_doc, analisis, folder_id, share_url, tipo, numero)
        except Exception as e:
            print(f"❌ Error Google Docs: {e}")
            doc_url = share_url  # Si falla Drive, el link es el de Fathom

        # ── Mensaje de Telegram (solo aviso) ──
        resumen_tg = analisis.get("resumen_corto_telegram", "Nueva llamada analizada")

        if tipo == "VENTA":
            cerrado = "✅ CERRADA" if analisis.get("cerrado") else "❌ No cerrada"
            importe = analisis.get("importe") or ""
            importe_txt = f" · {importe}" if importe and importe != "null" else ""
            msg = "\n".join([
                f"📞 <b>VENTA-{numero:03d}</b> | {analisis.get('cliente','?')}",
                f"{cerrado}{importe_txt}",
                f"{resumen_tg}",
                f"📄 <a href='{doc_url}'>Ver análisis completo</a>"
            ])
        elif tipo == "CLIENTE":
            msg = "\n".join([
                f"🤝 <b>CLIENTE-{numero:03d}</b> | {analisis.get('cliente','?')}",
                f"Estado: {analisis.get('estado_cliente','?')}",
                f"{resumen_tg}",
                f"📄 <a href='{doc_url}'>Ver análisis completo</a>"
            ])
        else:
            tareas = analisis.get("tareas", [])
            msg = "\n".join([
                f"👥 <b>EQUIPO-{numero:03d}</b>",
                f"{resumen_tg}",
                f"✅ {len(tareas)} tareas asignadas",
                f"📄 <a href='{doc_url}'>Ver acta completa</a>"
            ])

        mandar_telegram(msg)
        print(f"📱 Telegram enviado")

    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        mandar_telegram(f"⚠️ Error procesando webhook de Fathom: {e}\n📌 {titulo}\n🔗 {share_url}")


# ============================================================
# 📚 Endpoint manual para disparar el maestro (protegido con token)
# ============================================================
@app.route("/cron/maestro", methods=["POST", "GET"])
def cron_maestro():
    token = request.args.get("token") or (request.json or {}).get("token") if request.is_json else request.args.get("token")
    if not CRON_TOKEN or token != CRON_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    forzar = request.args.get("force") == "1"
    threading.Thread(
        target=(generar_maestro if forzar else maestro_si_toca),
        daemon=True,
    ).start()
    return jsonify({"status": "accepted", "forzado": forzar}), 200


# ============================================================
# 🏠 Health check
# ============================================================
@app.route("/", methods=["GET"])
def home():
    return "🧠 Cerebro de Llamadas v4 activo - by AUTOSETTER™"


# ============================================================
# 🔄 POLLING FATHOM (fallback al webhook que a veces no dispara)
# ============================================================
FATHOM_API_BASE = "https://api.fathom.ai/external/v1"


def fathom_list_recent_meetings(limit=20):
    """Lista las ultimas N llamadas del usuario via API externa de Fathom.
    Con retries + backoff exponencial para resistir caídas/timeouts puntuales.
    """
    if not FATHOM_API_KEY:
        return []
    import time as _t
    delays = [0, 2, 5, 10]  # 4 intentos: inmediato, +2s, +5s, +10s
    last_err = None
    for intento, espera in enumerate(delays, 1):
        if espera:
            _t.sleep(espera)
        try:
            r = requests.get(
                f"{FATHOM_API_BASE}/meetings",
                headers={"X-Api-Key": FATHOM_API_KEY},
                params={"limit": limit, "include_transcript": "true", "include_summary": "true"},
                timeout=30,
            )
            if r.status_code == 200:
                data = r.json()
                if intento > 1:
                    print(f"✅ Fathom OK al intento {intento}/{len(delays)}")
                return data.get("items") or data.get("data") or data.get("meetings") or []
            # 5xx → reintentamos; 4xx → fallo permanente
            if 500 <= r.status_code < 600:
                last_err = f"HTTP {r.status_code}"
                print(f"⚠️ Fathom {r.status_code} (intento {intento}/{len(delays)}), reintentando...")
                continue
            else:
                print(f"⚠️ Fathom HTTP {r.status_code}: {r.text[:200]}")
                return []
        except requests.exceptions.Timeout:
            last_err = "timeout"
            print(f"⚠️ Fathom timeout (intento {intento}/{len(delays)}), reintentando...")
            continue
        except Exception as e:
            last_err = str(e)[:120]
            print(f"⚠️ Fathom error (intento {intento}/{len(delays)}): {last_err}")
            continue
    print(f"❌ Fathom no respondio tras {len(delays)} intentos. Ultimo error: {last_err}")
    return []


def _recording_id_de(meeting):
    """Extrae el recording_id sin importar el shape exacto."""
    return (
        meeting.get("recording_id")
        or meeting.get("id")
        or (meeting.get("recording") or {}).get("id")
    )


_processed_ids_cache = None
_processed_ids_lock = threading.Lock()


def _get_processed_ids(force_refresh=False):
    """Set de recording_ids ya procesados, leyendo .json hermanos de las 3 carpetas.
    Cacheado en memoria, se refresca cuando procesamos algo nuevo o si force_refresh.
    """
    global _processed_ids_cache
    with _processed_ids_lock:
        if _processed_ids_cache is not None and not force_refresh:
            return _processed_ids_cache
        ids = set()
        _, drive_service = get_google_services()
        if not drive_service:
            _processed_ids_cache = ids
            return ids
        for folder_id in (FOLDER_VENTAS, FOLDER_CLIENTES, FOLDER_EQUIPO):
            if not folder_id:
                continue
            try:
                # Mira solo .json de los ultimos 7 dias para no leer todo el historico.
                desde = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
                q = (
                    f"'{folder_id}' in parents and trashed=false "
                    f"and mimeType='application/json' and createdTime > '{desde}'"
                )
                results = drive_service.files().list(
                    q=q, fields="files(id, name)", pageSize=100,
                    supportsAllDrives=True,
                ).execute()
                for f in results.get("files", []):
                    try:
                        req = drive_service.files().get_media(fileId=f["id"], supportsAllDrives=True)
                        buf = io.BytesIO()
                        downloader = MediaIoBaseDownload(buf, req)
                        done = False
                        while not done:
                            _, done = downloader.next_chunk()
                        data = json.loads(buf.getvalue().decode("utf-8"))
                        rid = data.get("recording_id") or data.get("analisis", {}).get("recording_id")
                        if rid is not None:
                            ids.add(str(rid))
                    except Exception:
                        pass
            except Exception as e:
                print(f"⚠️ No pude listar .json de {folder_id}: {e}")
        _processed_ids_cache = ids
        return ids


def _mark_processed(recording_id):
    """Añade un recording_id al cache."""
    with _processed_ids_lock:
        if _processed_ids_cache is not None and recording_id is not None:
            _processed_ids_cache.add(str(recording_id))


def _meeting_a_webhook_payload(meeting):
    """Transforma un meeting de la API externa al shape que espera procesar_webhook()."""
    transcript = meeting.get("transcript") or meeting.get("transcript_plaintext_segments") or []
    # Si transcript viene como string, lo envolvemos
    if isinstance(transcript, str):
        transcript = [{"speaker": {"display_name": "?"}, "text": transcript, "timestamp": "00:00"}]
    return {
        "title": meeting.get("title") or meeting.get("meeting_title") or "Sin título",
        "meeting_title": meeting.get("meeting_title") or meeting.get("title") or "Sin título",
        "share_url": meeting.get("share_url") or meeting.get("url") or "",
        "url": meeting.get("url") or meeting.get("share_url") or "",
        "recording_id": _recording_id_de(meeting),
        "recorded_by": meeting.get("recorded_by") or {},
        "calendar_invitees": meeting.get("calendar_invitees") or meeting.get("invitees") or [],
        "default_summary": meeting.get("default_summary") or meeting.get("summary") or {},
        "transcript": transcript,
        "transcript_language": meeting.get("transcript_language") or "es",
    }


def _meeting_es_reciente(meeting, horas=6):
    """True si la llamada empezó hace menos de N horas. Defensivo: si no hay
    fecha parseable, devuelve False (no procesar — mejor perder un webhook
    raro que spammear el historico)."""
    candidatos = (
        meeting.get("recording_start_time")
        or meeting.get("started_at")
        or meeting.get("created_at")
        or (meeting.get("recording") or {}).get("started_at")
    )
    if not candidatos:
        return False
    try:
        # ISO 8601 (con o sin Z)
        dt = datetime.fromisoformat(str(candidatos).replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt) < timedelta(hours=horas)
    except Exception:
        return False


def polling_fathom():
    """Cada minuto: lista meetings recientes y procesa los que aun no han pasado.
    Solo procesa llamadas de las ultimas 6h para no spammear el historico al
    arrancar (deploys nuevos, reinicios, etc)."""
    if not FATHOM_API_KEY:
        return
    try:
        meetings = fathom_list_recent_meetings(limit=20)
        if not meetings:
            return
        ya_procesados = _get_processed_ids()
        nuevos = []
        for m in meetings:
            rid = _recording_id_de(m)
            if rid is None:
                continue
            if str(rid) in ya_procesados:
                continue
            # No procesar si no tiene transcript todavia (Fathom aún procesando).
            if not (m.get("transcript") or m.get("transcript_plaintext_segments")):
                continue
            # No procesar llamadas viejas (>6h) para no spammear historico.
            if not _meeting_es_reciente(m, horas=6):
                continue
            nuevos.append(m)

        if not nuevos:
            return
        print(f"🔄 Polling Fathom: {len(nuevos)} llamada(s) nueva(s) detectada(s) — procesando...")
        for m in nuevos:
            rid = _recording_id_de(m)
            try:
                payload = _meeting_a_webhook_payload(m)
                # NO marcamos aqui — procesar_webhook hace el dedup atomicamente
                # al inicio (chequea + marca dentro del mismo lock). Si marcamos
                # antes, procesar_webhook ve el ID en cache y aborta por dedup.
                procesar_webhook(payload)
            except Exception as e:
                print(f"⚠️ Polling: fallo procesando recording {rid}: {e}")
    except Exception as e:
        print(f"❌ Error en polling_fathom: {e}")


# ============================================================
# ⏰ Scheduler: maestro diario + polling Fathom cada minuto
# ============================================================
_scheduler = BackgroundScheduler(daemon=True, timezone="Europe/Madrid")
_scheduler.add_job(maestro_si_toca, "cron", hour=9, minute=0, id="maestro_daily")
_scheduler.add_job(polling_fathom, "interval", minutes=1, id="fathom_polling",
                   max_instances=1, coalesce=True)
_scheduler.start()
print("⏰ Scheduler arrancado · maestro_si_toca diario 09:00 + polling_fathom cada 1min")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
