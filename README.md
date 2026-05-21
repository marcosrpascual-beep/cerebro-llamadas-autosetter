# 🧠 El Cerebro de Llamadas

**Sistema automático que escucha tus llamadas y te entrega un análisis ejecutivo antes de que cierres la pestaña.**

Recibe webhooks de Fathom, analiza la transcripción con Claude según el tipo de llamada (VENTA / CLIENTE / EQUIPO), genera un Google Doc detallado en la carpeta correspondiente, y te avisa por Telegram con el link.

Además, cada 30 días genera automáticamente un **doc maestro mensual** con el resumen agregado de las 3 categorías: métricas, patrones, wins, alertas y recomendaciones.

---

## 📖 Manual de instalación

**👉 [autosetter-cerebro.pages.dev](https://autosetter-cerebro.pages.dev)**

Guía paso a paso, ≈ 90 minutos. Sin saber programar.

---

## ⚡ Stack

| Pieza | Para qué |
|---|---|
| **Fathom** | Graba y transcribe la llamada |
| **Flask + Gunicorn** | Endpoint que recibe el webhook |
| **Claude (Anthropic)** | Detecta el tipo (Haiku) + análisis profundo (Sonnet) |
| **Google Drive + Docs API** | Crea los Docs vía HTML conversion |
| **Telegram Bot** | Avisa con resumen + link al Doc |
| **APScheduler** | Cron del doc maestro cada 30 días |
| **Railway** | Hosting del backend |

---

## 🚀 Quickstart (para impacientes)

```bash
# 1. Clonar
git clone https://github.com/azerorisk-ui/cerebro-llamadas-autosetter.git
cd cerebro-llamadas-autosetter

# 2. Setup local opcional
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Crear .env
cp .env.example .env
# rellenar con tus claves (ver el manual)

# 4. Obtener refresh token OAuth de Google
python3 scripts/get_refresh_token.py

# 5. Deploy a Railway conectando este repo
# (subir las variables del .env como env vars en Railway)
```

**Pero en serio, sigue el manual entero la primera vez. Te ahorra todos los gotchas que ya están resueltos.**

---

## 📂 Estructura

```
.
├── main.py                       # Backend Flask completo
├── requirements.txt              # Dependencias Python
├── Procfile                      # Comando de arranque en Railway
├── .env.example                  # Variables de entorno necesarias
└── scripts/
    └── get_refresh_token.py      # One-shot OAuth para Google Drive
```

---

## 🔐 Endpoints

| Endpoint | Método | Para qué |
|---|---|---|
| `/` | GET | Health check |
| `/webhook/fathom` | POST | Recibe webhooks de Fathom |
| `/cron/maestro?token=XXX` | POST | Dispara el doc maestro (chequea si toca) |
| `/cron/maestro?token=XXX&force=1` | POST | Fuerza el doc maestro ya |

---

## 📜 Licencia

MIT. Haz lo que quieras con esto.

---

🧠 Hecho por [AUTOSETTER™](https://autosetter-lab.pages.dev/)
