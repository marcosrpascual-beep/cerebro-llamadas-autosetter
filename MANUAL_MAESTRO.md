# 🧠 EL CEREBRO DE LLAMADAS — MANUAL MAESTRO

> Manual exhaustivo para que cualquier persona monte el sistema entero
> aunque no haya tocado código en su vida.
>
> **Este documento es el texto fuente.** Está pensado para alimentar
> tu skill de manuales en Claude.ai y que ella lo eleve a un sitio HTML
> con el branding AUTOSETTER.

---

## 📋 INSTRUCCIONES PARA EL DISEÑADOR (tu skill / Claude)

Convierte este contenido en un manual HTML interactivo cumpliendo:

**BRANDING (idéntico a autosetter-lab.pages.dev):**
- Fondo: `#050505`
- Texto: `#F5F2EC`
- Acento: `#FE2E00` (naranja-rojo eléctrico)
- Dim: `#6E6A62`
- Soft: `#C9C5BD`
- Línea: `rgba(255,255,255,0.08)`
- Fuentes: Geist (display) + JetBrains Mono (técnica) + Caveat (anotaciones manuscritas)

**ESTILO:**
- Single-file HTML (CSS + JS inline)
- Dark mode estricto
- Cada gran sección ocupa ~100vh
- Numeración prominente de pasos (01, 02, 03...)
- Code snippets con botón COPY
- Checkboxes con persistencia (localStorage)
- Progress bar arriba mientras haces scroll
- FAQ accordion
- Anotaciones manuscritas en Caveat para los "tips de oro" (ej. "*ojo con esto, me costó 2 horas*")
- Avisos rojos con borde izquierdo para los gotchas críticos

**TONO:**
- Cercano pero profesional ("tú" no "usted")
- Sin tecnicismos sin explicar
- Frases cortas
- Humor sutil ("aquí Google te va a hacer dudar de la vida, tranquilo")

---

# 🎬 0. INTRO

## Lo que vas a montar

Un sistema que, una vez instalado, hace todo esto **sin que tú toques nada**:

```
Haces una llamada en Google Meet
        ↓
Fathom la graba y transcribe
        ↓
Tu servidor recibe la transcripción
        ↓
Claude detecta el tipo (VENTA / CLIENTE / EQUIPO)
        ↓
Claude analiza profundo (objeciones, mejoras, frases clave...)
        ↓
Se crea un Google Doc precioso en la carpeta correcta
        ↓
Telegram te avisa con un resumen + el link al Doc
```

**Tiempo real para instalar:** 90 minutos la primera vez. Si lo haces otra vez,
20 minutos.

**Coste mensual:** ~$10-15 (Anthropic ≈ $10 con 100 llamadas/mes + Railway $5).

**Saber programar:** CERO. Si copias y pegas, lo tienes.

---

## Resultado final · qué vas a tener

Después de las 90 minutos:

1. Una **web (en Railway)** que escucha 24/7.
2. **Cuatro carpetas** en tu Google Drive: `VENTAS`, `CLIENTES`, `EQUIPO`, `MAESTROS`.
3. Un **bot de Telegram** que te avisa cada vez que termines una llamada.
4. **Cada 30 días**, sin pedirlo, un **Doc maestro** con resumen mensual de las
   3 categorías (métricas, patrones, wins, alertas).

---

# 🛠️ 1. PRE-REQUISITOS (TIEMPO: 10 MIN)

> **Antes de empezar de verdad, abre estas pestañas y crea cuenta donde haga falta.**
> Si ya tienes alguna, mejor.

## Cuentas que necesitas

| Servicio | Para qué | Coste real | Link |
|---|---|---|---|
| **Google** | Para Drive, Cloud, Gmail | Gratis | gmail.com |
| **Anthropic (Claude)** | El cerebro que analiza | **Mete $5 mínimo** | console.anthropic.com |
| **Fathom** | Graba las llamadas | Free vale al principio | fathom.video |
| **Railway** | Hosting del servidor | Free trial $5 + **te recomiendo cargar $5 más para que no te pare** | railway.app |
| **GitHub** | Para tener el código | Gratis | github.com |
| **Telegram** | Recibir avisos | Gratis | tienes la app en el móvil |
| **Claude Code** (recomendado) | Para editar el código sin saber programar | Plan Pro $20/mes (o usa Cursor/VSCode gratis) | claude.com/code |

## ⚠️ Lo que TIENES que tener cargado en saldo

- **Anthropic: $5 mínimo.** Sin saldo, las llamadas a Claude fallan.
  Ve a `console.anthropic.com → Plans & Billing → Add credits`.
- **Railway: te recomiendo $5 extra al free trial.** El free trial son
  $5 que duran ≈ 1 mes con uso bajo. Si se acaba sin tener saldo, tu
  servidor se apaga y deja de funcionar.

## Lo que tienes que tener INSTALADO en tu Mac/PC

**Mínimo:**
- Un navegador (Chrome, Safari, Firefox).
- Acceso a tu terminal (en Mac: Cmd+Espacio → escribe "Terminal").

**Recomendado fuerte (te ahorra horas):**
- **Claude Code** instalado. Es una app de Anthropic que te deja chatear
  con Claude para que él edite tu código por ti. Si te atascas con algo,
  Claude te lo arregla.
  - Descarga: `claude.com/code`
  - Una vez instalada, login con tu cuenta Anthropic.

**Si prefieres no usar Claude Code:**
- **Cursor** (cursor.com) o **VSCode** (code.visualstudio.com) — son
  editores gratuitos que también funcionan. Si nunca has usado ninguno,
  Claude Code es más fácil porque puedes hablarle en español.

---

# 💻 2. DESCARGAR EL CÓDIGO (TIEMPO: 5 MIN)

> **El código del Cerebro está público en GitHub. Hay dos formas de
> traértelo a tu Mac/PC. Elige la que te dé menos pereza.**

## Opción A · Con Claude Code (recomendada, sin tocar comandos raros)

1. Abre **Claude Code**.
2. Pulsa `Cmd+K` o el botón **Open Folder** y crea una carpeta nueva
   en tu Escritorio llamada `cerebro-llamadas`.
3. Una vez dentro, abre el chat y pega esto:

   > *"Clona el repositorio https://github.com/azerorisk-ui/cerebro-llamadas-autosetter
   > en esta carpeta y enséñame los archivos."*

4. Claude lo hace por ti. Cuando termine, verás en la barra lateral
   los archivos del proyecto (main.py, README.md, etc.).
5. **Ya está.** No tienes que tocar nada. Sigue al paso 3.

## Opción B · Descargar como ZIP (sin instalar nada)

1. Abre en el navegador: `github.com/azerorisk-ui/cerebro-llamadas-autosetter`
2. Botón verde **Code** → **Download ZIP**.
3. Se descarga `cerebro-llamadas-autosetter-main.zip`.
4. Doble click para descomprimirlo en tu Escritorio.
5. Listo. Tienes la carpeta con el código.

## Opción C · Con git (si ya sabes)

```bash
cd ~/Desktop
git clone https://github.com/azerorisk-ui/cerebro-llamadas-autosetter.git
cd cerebro-llamadas-autosetter
```

## El archivo `.env` (importante)

Dentro de la carpeta verás un archivo llamado `.env.example`. **Cópialo y
renómbralo a `.env`** (sin la palabra example).

- En Mac/Linux terminal: `cp .env.example .env`
- En Finder: click derecho → Duplicar → renombrar el copia.

Ese `.env` es donde vas a ir pegando todas las claves que generes en los
siguientes pasos. **Téngalo abierto en tu editor todo el rato.**

> *📌 Nota: el .env nunca se sube al repo. Es solo tuyo, local. Es donde
> guardas tus claves antes de copiarlas a Railway.*

---

# 📱 3. CREAR EL BOT DE TELEGRAM (TIEMPO: 5 MIN)

> **Necesitas dos cosas: el TOKEN del bot y tu CHAT_ID (a quién avisa).**

## 3.1 Crear el bot

1. Abre Telegram en tu móvil.
2. En la barra de búsqueda, busca **@BotFather** (es el bot oficial de Telegram).
3. Dale click → **Iniciar / Start**.
4. Escribe: `/newbot` → enviar.
5. BotFather te pide un **nombre** (visible). Pon lo que quieras, ej:
   `Cerebro de Llamadas Bot`.
6. Te pide un **username** (único). Tiene que **acabar en `bot`**. Ej:
   `cerebrollamadas_nico_bot`. Si está cogido, prueba otro.
7. BotFather te devuelve un mensaje con tu **TOKEN**, algo así:
   ```
   1234567890:AAAAxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
8. **Copia ese token entero y pégalo en tu `.env`**:
   ```
   TELEGRAM_TOKEN=1234567890:AAAAxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

## 3.2 Conseguir tu CHAT_ID

> El TOKEN dice "qué bot escribe". El CHAT_ID dice "a quién escribe".

1. En Telegram, **busca tu nuevo bot por su username** (`cerebrollamadas_nico_bot`).
2. Ábrelo y mándale cualquier mensaje, por ejemplo `hola`.
   (Importante: el bot no responde, no pasa nada. Solo necesitamos
   que exista la conversación.)
3. **Abre esta URL en tu navegador**, reemplazando `TU_TOKEN` por el token
   del paso anterior:
   ```
   https://api.telegram.org/botTU_TOKEN/getUpdates
   ```
4. Verás un JSON con texto. Busca algo así:
   ```
   "chat":{"id": 123456789, "first_name":...
   ```
5. **Ese número (123456789) es tu CHAT_ID.** Cópialo a tu `.env`:
   ```
   TELEGRAM_CHAT_ID=123456789
   ```

### ⚠️ Si NO ves nada en el JSON

Te aparece `{"ok":true,"result":[]}` → significa que no mandaste el
mensaje al bot todavía. Vuelve al paso 2 y mándale un mensaje.

### ✅ Cómo verificar que funciona ahora mismo

Abre esta URL (cambiando TU_TOKEN y TU_CHAT_ID):
```
https://api.telegram.org/botTU_TOKEN/sendMessage?chat_id=TU_CHAT_ID&text=hola
```
Si te llega un "hola" en Telegram del bot → **perfecto**, sigues.

---

# 🤖 4. API KEY DE CLAUDE (TIEMPO: 3 MIN)

> **El cerebro de verdad. Usamos dos modelos: Haiku (barato) para
> detectar el tipo, y Sonnet (mejor) para el análisis profundo.**

1. Entra a [console.anthropic.com](https://console.anthropic.com) → login.
2. ⚠️ **Antes de crear la key, asegúrate de tener saldo.**
   - Ve a **Plans & Billing** (o **Settings → Billing**).
   - Si tienes $0, click **Add credits** → mete **$5 mínimo**.
3. Ve a **Settings → API Keys** ([link directo](https://console.anthropic.com/settings/keys)).
4. **Create Key** → nombre: `cerebro-llamadas` → **Create**.
5. Te enseña la key. Empieza por `sk-ant-api03-...`.
   **⚠️ Cópiala YA. Solo se ve una vez.** Si la cierras sin copiar,
   tienes que crear otra.
6. Pégala en tu `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxx
   ```

### 💰 Cuánto vas a gastar

- Detectar tipo (Haiku): ~$0.0002 por llamada (céntimos).
- Análisis profundo (Sonnet): ~$0.10 por llamada.
- **100 llamadas al mes ≈ $10.**

---

# ☁️ 5. GOOGLE CLOUD (TIEMPO: 20 MIN — ES EL MÁS LARGO PERO LO ÚLTIMO COMPLICADO)

> **Aquí Google te va a hacer dudar de la vida. Tranquilo, hazlo
> exactamente como pone abajo y sale a la primera.**

## 5.1 Crear el proyecto

1. Entra a [console.cloud.google.com](https://console.cloud.google.com).
2. Arriba a la izquierda hay un selector de proyecto. Click → **New Project**.
3. Nombre: `cerebro-llamadas` → **Create**.
4. Espera 10 segundos. Cuando se cree, **selecciónalo** arriba (asegúrate de
   que pone "cerebro-llamadas" en la barra de arriba — todo lo que hagas
   ahora tiene que ser DENTRO de este proyecto).

## 5.2 Activar las dos APIs (Docs + Drive)

1. Abre estos dos links (asegúrate de que estás en tu proyecto) y en cada
   uno pulsa el botón azul **ENABLE / HABILITAR**:
   - [Google Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com)
   - [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
2. **Verifica:** después de pulsar, debe poner "API habilitada" con un check
   verde. Si pone "Habilitar", todavía no le diste.

## 5.3 OAuth Consent Screen (la pantalla que pedirá permiso)

> Esto le dice a Google "voy a hacer una app que pedirá acceso a Drive
> para crear Docs en mi cuenta".

1. Entra a [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).
2. **User Type**: selecciona `External` → **Create**.
3. Rellena:
   - **App name**: `cerebro-llamadas`
   - **User support email**: tu email (sale en el desplegable)
   - **App logo**: déjalo en blanco
   - **App domain**: déjalo en blanco
   - **Developer contact information**: tu email
   - **Save and continue**
4. **Scopes**: NO añadas nada. Solo **Save and continue**.
5. **Test users**: ⚠️ **AQUÍ ES SUPER IMPORTANTE.**
   - Click **+ Add Users**.
   - Añade **tu propio email de Google** (el mismo donde están las carpetas
     de Drive donde se guardarán los Docs).
   - Si planeas dejar que **otras personas usen tu sistema** (ej. tu equipo),
     añade también sus emails aquí. Si no los añades, Google les bloqueará.
   - **Save and continue**.
6. Resumen → **Back to Dashboard**.

> *💡 ¿Cuántos test users puedes tener? Hasta 100. Más que de sobra.*

## 5.4 OAuth Client ID (la "tarjeta de identidad" de la app)

1. Entra a [Credentials](https://console.cloud.google.com/apis/credentials).
2. Arriba: **+ CREATE CREDENTIALS** → **OAuth client ID**.
3. **Application type**: `Desktop app`.
4. **Name**: `cerebro-llamadas-cli`.
5. **CREATE**.
6. Te aparece un popup con:
   - **Client ID** (algo como `12345...apps.googleusercontent.com`)
   - **Client Secret** (algo como `GOCSPX-...`)
7. **Cópialos los dos a tu `.env`**:
   ```
   GOOGLE_OAUTH_CLIENT_ID=12345-xxxxxxx.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxx
   ```

> *También puedes descargar el JSON entero, pero solo necesitas esos dos.*

---

# 📁 6. CREAR LAS 4 CARPETAS EN DRIVE (TIEMPO: 5 MIN)

> **El cerebro guarda cada tipo de llamada en una carpeta distinta.
> Más el doc maestro mensual.**

1. Abre [drive.google.com](https://drive.google.com) con tu cuenta.
2. Crea una carpeta principal llamada **AUTOSETTER** (o el nombre que quieras).
3. Dentro, crea estas **4 subcarpetas**:
   - `VENTAS`
   - `CLIENTES`
   - `EQUIPO`
   - `MAESTROS`
4. Abre cada una. La URL se verá así:
   ```
   https://drive.google.com/drive/folders/1ABC...XYZ
   ```
   La parte **después de `/folders/`** es el **ID**. Cópialo.
5. Pega los 4 IDs en tu `.env`:
   ```
   FOLDER_VENTAS=1ABC...XYZ
   FOLDER_CLIENTES=1DEF...UVW
   FOLDER_EQUIPO=1GHI...RST
   FOLDER_MAESTROS=1JKL...OPQ
   ```

> *📌 No hace falta que compartas las carpetas con nadie. Como vamos a
> usar OAuth con tu cuenta personal, el sistema actuará como tú. Las
> carpetas siguen siendo solo tuyas.*

---

# 🔑 7. CONSEGUIR EL REFRESH TOKEN (TIEMPO: 5 MIN)

> **Este token permite al servidor crear Docs en TU Drive sin que tengas
> que iniciar sesión cada vez. Se hace UNA vez y dura para siempre.**

## Si usas Claude Code o tienes terminal cómodo

1. Abre Claude Code (o terminal) en la carpeta del proyecto.
2. Asegúrate de tener Python 3 instalado. En la terminal:
   ```bash
   python3 --version
   ```
   Si pone "Python 3.x.x" perfecto. Si no, instálalo en [python.org/downloads](https://python.org/downloads).
3. Instala la librería necesaria:
   ```bash
   pip3 install google-auth-oauthlib
   ```
4. Abre el archivo `scripts/get_refresh_token.py`. En las dos primeras
   líneas hay placeholders `PEGA_TU_CLIENT_ID_AQUI` y `PEGA_TU_CLIENT_SECRET_AQUI`.
   Reemplázalos con los valores del paso 5.4 (también puedes definir
   las env vars `GOOGLE_OAUTH_CLIENT_ID` y `GOOGLE_OAUTH_CLIENT_SECRET`).
5. En la terminal, dentro de la carpeta:
   ```bash
   python3 scripts/get_refresh_token.py
   ```
6. Se abre tu navegador. **Selecciona la cuenta de Google donde están
   las carpetas** (importante).
7. Te dirá **"Google no ha verificado esta app"**.
   - Click **Configuración avanzada** (abajo a la izquierda).
   - Click **Ir a cerebro-llamadas (no seguro)**.
   - Acepta los permisos (Drive + Docs).
   - **Es seguro:** es TU propia app autorizándose contra TU cuenta.
8. La terminal te imprime algo así:
   ```
   ========================================
   REFRESH TOKEN obtenido. Guárdalo en .env y Railway como
   GOOGLE_OAUTH_REFRESH_TOKEN:

   1//03xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ========================================
   ```
9. **Pégalo en tu `.env`:**
   ```
   GOOGLE_OAUTH_REFRESH_TOKEN=1//03xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Si te bloquea con "Access blocked"

Volviste al paso 5.3 y **NO añadiste tu email como Test User**. Vuelve,
añádete, y repite este paso.

---

# 🚂 8. DEPLOY EN RAILWAY (TIEMPO: 15 MIN)

> **Railway coge tu código de GitHub y lo monta en un servidor que escucha
> 24/7. Auto-redeploy cada vez que haces push.**

## 8.1 Conectar tu cuenta de GitHub con Railway

1. Entra a [railway.app](https://railway.app) → **Login with GitHub**.
2. Si es la primera vez, autoriza Railway a leer tus repos.

## 8.2 Crear el proyecto desde el repo

1. Botón **+ New Project** → **Deploy from GitHub repo**.
2. Selecciona tu repo `cerebro-llamadas-autosetter`.
   - Si NO te aparece (porque hiciste fork del original), pulsa
     **Configure GitHub App** y dale acceso al repo.
3. Railway empieza a desplegar inmediatamente. **Va a fallar al arrancar.**
   Es normal: aún no le pasamos las claves.
4. Espera a que termine (verás "Failed" o "Crashed" en rojo). No pasa nada.

## 8.3 Meter todas las variables del .env

1. Click en el servicio (la card del proyecto).
2. Arriba pestaña **Variables**.
3. **Raw Editor** (o "Bulk import") → pega TODO el contenido de tu `.env`
   de una vez. Railway parsea cada línea como variable.
   - Quita las líneas que empiezan por `#` (comentarios).
   - **Importante:** debes tener TODAS estas:
     - `ANTHROPIC_API_KEY`
     - `TELEGRAM_TOKEN`
     - `TELEGRAM_CHAT_ID`
     - `GOOGLE_OAUTH_CLIENT_ID`
     - `GOOGLE_OAUTH_CLIENT_SECRET`
     - `GOOGLE_OAUTH_REFRESH_TOKEN`
     - `FOLDER_VENTAS`
     - `FOLDER_CLIENTES`
     - `FOLDER_EQUIPO`
     - `FOLDER_MAESTROS`
     - `CRON_TOKEN`
4. Para `CRON_TOKEN`, si no lo tienes aún, genera uno aleatorio. En tu Mac:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"
   ```
   Te da algo tipo `xyzABC_123-aBc...`. Pégalo como valor.
5. **Save**. Railway redespliega automáticamente.

## 8.4 ⚠️ Cargar saldo en Railway

> **CRÍTICO:** Railway tiene un free trial de $5 que dura ≈ 1 mes con uso bajo.
> Si se acaba, tu servidor se apaga y no recibes llamadas.

1. Click tu avatar (arriba derecha) → **Account Settings → Billing**.
2. **Add Payment Method** → tarjeta.
3. **Add Credits** → mete **$5 extra**.
   - El cobro real es por uso. Con tu app pequeña, $5 te duran 2-3 meses.
   - Railway te avisa antes de que se acabe el saldo.

## 8.5 Generar el dominio público

1. En tu servicio, pestaña **Settings → Networking**.
2. **Generate Domain**.
3. Te da una URL tipo `tu-app-production-xxxx.up.railway.app`.
4. **Apuntala** — la necesitas en el siguiente paso para Fathom.

### ✅ Verificar que está vivo

Abre la URL en el navegador. Deberías ver:
```
🧠 Cerebro de Llamadas v4 activo - by AUTOSETTER™
```

Si ves esto, **el servidor está respirando**. Pasa al siguiente paso.

Si ves un error, ve a **Logs** del servicio y busca el último mensaje.
Probablemente te falta alguna variable.

---

# 🎬 9. CONECTAR FATHOM (TIEMPO: 5 MIN)

> **Fathom necesita saber dónde enviarte cada llamada. Le damos tu URL
> de Railway + el path `/webhook/fathom`.**

1. Entra a Fathom → click en tu avatar → **Settings**.
2. Busca **Integrations** o **Webhooks**.
3. **Add Webhook**:
   - **URL**: `https://tu-app-production-xxxx.up.railway.app/webhook/fathom`
     (la URL del paso 8.5 + `/webhook/fathom` al final)
   - **Trigger / Event**: `Meeting recorded` o equivalente (cuando hay
     transcripción lista)
4. **Save**.

---

# 🧪 10. TU PRIMERA LLAMADA DE PRUEBA (TIEMPO: 10 MIN)

> **El momento de la verdad. Vamos a hacer una llamada cortita y
> verificar que todo el flujo funciona end-to-end.**

## 10.1 La llamada

1. Abre Google Meet contigo mismo (link → meet.google.com → "Nueva reunión").
2. Conecta Fathom (si no se conecta solo, en la app de Fathom → "Join meeting").
3. **Empieza a grabar** (botón rojo en Fathom).
4. Habla 1-2 minutos. Para que Claude detecte el tipo correctamente, di
   frases claras:
   - Si quieres VENTA: *"te ofrezco este servicio por X euros al mes"*
   - Si quieres CLIENTE: *"hemos detectado un problema con la herramienta"*
   - Si quieres EQUIPO: *"vamos a decidir las prioridades de la próxima semana"*
5. Cuelga la llamada.

## 10.2 Esperar el ping de Telegram

- Fathom tarda **1-5 minutos** en procesar la grabación y enviar el webhook.
- Cuando lo envíe, el sistema:
  1. Recibe el webhook.
  2. Detecta el tipo con Claude.
  3. Analiza la transcripción a fondo.
  4. Crea un Google Doc en la carpeta correspondiente.
  5. **Te llega un mensaje en Telegram** con el resumen + link al Doc.

## 10.3 Si no llega en 10 minutos

Algo falló. Vamos a debuggear:

1. **Abre Railway** → tu servicio → pestaña **Logs**.
2. Busca un mensaje que empiece por `📨 Webhook recibido`.
   - **Si NO aparece:** Fathom no está enviando el webhook. Vuelve al
     paso 9 y verifica que la URL está bien.
   - **Si SÍ aparece pero seguido de `❌ Error`:** la línea del error te
     dice qué falla. Los más comunes:
     - `Drive storage quota exceeded` → algo del OAuth no está bien.
       Vuelve al paso 7.
     - `permission denied / 403` → no habilitaste las APIs en el paso 5.2.
     - `Claude Error` → falta saldo en Anthropic (paso 4).

---

# 📊 11. EL DOC MAESTRO MENSUAL (YA ESTÁ ACTIVO)

> **No tienes que hacer nada. Cada día a las 9:00 (hora Madrid) el
> sistema chequea si han pasado 30 días desde el último doc maestro.
> Si sí, lo genera automáticamente.**

## Si quieres forzar uno YA (para probar)

En tu terminal, sustituye `TU_DOMINIO_RAILWAY` y `TU_CRON_TOKEN`:

```bash
curl -X POST "https://TU_DOMINIO_RAILWAY/cron/maestro?token=TU_CRON_TOKEN&force=1"
```

En unos segundos te llega un Telegram con el link al Doc Maestro.

> *El primer maestro puede salir vacío si aún no has procesado llamadas.
> A partir de la próxima llamada real, se va guardando JSON oculto en
> cada carpeta para que el maestro siguiente lo agregue todo.*

---

# 🎨 12. PERSONALIZAR (OPCIONAL)

## Cambiar lo que Claude dice en el análisis

Los prompts de Claude están al principio de `main.py`. Búscalos:
- `PROMPT_VENTA`
- `PROMPT_CLIENTE`
- `PROMPT_EQUIPO`
- `PROMPT_MAESTRO`

Edita el texto, haz push a GitHub → Railway redespliega solo.

## Cambiar el formato del Google Doc

Los Docs se generan en HTML que luego Drive convierte a Doc nativo.
Las plantillas están en `main.py`:
- `build_html_venta`
- `build_html_cliente`
- `build_html_equipo`
- `build_html_maestro`

Edita el HTML, push, redeploy. **Tip pro:** abre `main.py` en Claude Code
y pídele en español *"cámbiame el formato del Doc de venta para que tenga
una tabla con las objeciones"*. Claude lo hace por ti.

## Cambiar quién recibe los avisos

Cambia el `TELEGRAM_CHAT_ID` en Railway por el ID de otro chat
(un grupo, otra persona, etc.). Para grupos, añade el bot al grupo y
sigue el paso 3.2 pero usando ese chat.

---

# 🚨 GOTCHAS COMUNES (los problemas que viví yo)

## "Mi servidor responde pero no llega el Doc a Drive"
- Verifica que TÚ estás como **Test User** en el OAuth consent (paso 5.3).
- Verifica que las 2 APIs (Docs + Drive) están habilitadas (paso 5.2).
- Verifica que el `GOOGLE_OAUTH_REFRESH_TOKEN` está bien copiado en Railway.

## "Telegram me llega pero sin link al Doc"
- Probablemente el Doc falló al crearse y el sistema usa el link de Fathom
  como fallback. Ve a los logs de Railway para ver el error real.

## "Mi worker se muere por timeout"
- No debería pasar, lo arreglamos haciendo procesamiento en background.
- Si pasa, revisa que no tocaste el Procfile.

## "Cada llamada se procesa 3 veces"
- Fathom reintenta el webhook si tarda en responder. Como respondemos
  en 0.2s, esto no debería pasar. Si pasa, verifica que `/webhook/fathom`
  devuelve HTTP 200 rápido.

## "Necesito rotar las claves"
- Anthropic: `console.anthropic.com → API Keys → Revoke → Create new`.
- Telegram: `@BotFather → /token → seleccionar bot → Revoke current token`.
- Google OAuth: borra el OAuth Client y crea uno nuevo. Repite el paso 7.
- Sube las nuevas en Railway → Variables.

---

# 💬 FAQ

## ¿Cuánto cuesta esto al mes de verdad?

| Servicio | Coste mensual realista |
|---|---|
| Anthropic | ~$10 con 100 llamadas/mes |
| Railway | ~$5 con uso bajo |
| Google | $0 |
| Fathom | $0 (free) o $19 si quieres ilimitado |
| Telegram | $0 |
| **TOTAL** | **~$15/mes** (ó $34 con Fathom pro) |

## ¿Mis llamadas las verá alguien?

- **Anthropic** no usa datos de API para entrenar. Tu transcripción se
  procesa y se descarta.
- **Google Drive** es tu Drive personal. Solo tú accedes.
- **Fathom** ya tiene tus llamadas porque es quien las graba.
- **El servidor (Railway)** es tuyo, solo tú puedes ver los logs.

Conclusión: nadie más que tú y los servicios que ya usabas (Fathom + Drive).

## ¿Puedo compartir mi sistema con mi equipo?

Sí, pero **cada uno necesita estar en tus Test Users** (paso 5.3) para
que el OAuth les funcione. Si vais a ser más de 10-15 personas, casi
mejor que cada uno monte su propio sistema (es lo mismo, gratis los
demás servicios).

## ¿Y si Anthropic saca un modelo mejor?

Cambia `MODEL_DETECCION` o `MODEL_ANALISIS` en `main.py` por el nuevo
nombre. Push, redeploy. Listo.

## ¿Funciona con Zoom / Microsoft Teams / etc.?

Funciona con **lo que Fathom soporte**. Hoy: Google Meet, Zoom, Teams.

## ¿Puedo conectar el análisis a Slack en vez de Telegram?

Sí, pero hay que tocar código. Pídeselo a Claude Code: *"reemplaza
mandar_telegram por mandar_slack usando un webhook de Slack"*. Necesitas
crear un Incoming Webhook en Slack y pasarle la URL.

---

# 🎬 CIERRE

Si has llegado hasta aquí, **tienes el sistema vivo**. Tus llamadas
ahora trabajan para ti, no contra ti.

Cuelgues una llamada. Vete a hacer otra cosa. En 5 minutos tienes el
Doc + el ping. Cada 30 días, sin pedirlo, un resumen ejecutivo del mes.

Si te ha gustado y quieres más sistemas así, sígueme en:
- GitHub: [@azerorisk-ui](https://github.com/azerorisk-ui)
- Web: [autosetter-lab.pages.dev](https://autosetter-lab.pages.dev)

🧠 **AUTOSETTER™** · 2026
