# Configuración

Todas tus configuraciones estarán en un archivo en el directorio raíz, llamado `config.json`, que es una copia de `config.example.json`. Podés cambiar los valores en `config.json` a tu gusto.

## Valores

- `verbose`: `boolean` - Si es `true`, la aplicación imprimirá más información.
- `firefox_profile`: `string` - La ruta a tu perfil de Firefox. Se usa para utilizar tus cuentas de redes sociales sin tener que iniciar sesión cada vez que ejecutás la aplicación.
- `headless`: `boolean` - Si es `true`, la aplicación se ejecutará en modo headless. Esto significa que el navegador no será visible.
- `ollama_base_url`: `string` - URL base de tu servidor Ollama local (por defecto: `http://127.0.0.1:11434`).
- `ollama_model`: `string` - Modelo de Ollama a usar para la generación de texto (ej. `llama3.2:3b`). Si está vacío, la app consulta a Ollama al iniciar y te permite elegir interactivamente entre los modelos disponibles.
- `twitter_language`: `string` - El idioma que se usará para generar y publicar tweets.
- `nanobanana2_api_base_url`: `string` - URL base de la API de Nano Banana 2 (por defecto: `https://generativelanguage.googleapis.com/v1beta`).
- `nanobanana2_api_key`: `string` - Clave de API para Nano Banana 2 (API de imágenes de Gemini). Si está vacía, MPV2 recurre a la variable de entorno `GEMINI_API_KEY`.
- `nanobanana2_model`: `string` - Nombre del modelo de Nano Banana 2 (por defecto: `gemini-3.1-flash-image-preview`).
- `nanobanana2_aspect_ratio`: `string` - Relación de aspecto para las imágenes generadas (por defecto: `9:16`).
- `threads`: `number` - La cantidad de hilos que se usarán para ejecutar operaciones, ej. escritura a un archivo usando MoviePy.
- `is_for_kids`: `boolean` - Si es `true`, la aplicación subirá el video a YouTube Shorts como un video para niños.
- `google_maps_scraper`: `string` - La URL del scraper de Google Maps. Se usará para hacer scraping de Google Maps en busca de negocios locales. Se recomienda usar el valor por defecto.
- `zip_url`: `string` - La URL del archivo ZIP que contiene las canciones a utilizar para el automatizador de YouTube Shorts.
- `email`: `object`:
    - `smtp_server`: `string` - Tu servidor SMTP.
    - `smtp_port`: `number` - El puerto de tu servidor SMTP.
    - `username`: `string` - Tu dirección de correo electrónico.
    - `password`: `string` - Tu contraseña de correo electrónico.
- `google_maps_scraper_niche`: `string` - El nicho para el cual querés hacer scraping en Google Maps.
- `scraper_timeout`: `number` - El tiempo de espera para el scraper de Google Maps.
- `outreach_message_subject`: `string` - El asunto de tu mensaje de contacto. `{{COMPANY_NAME}}` será reemplazado por el nombre de la empresa.
- `outreach_message_body_file`: `string` - El archivo que contiene el cuerpo de tu mensaje de contacto, debe ser HTML. `{{COMPANY_NAME}}` será reemplazado por el nombre de la empresa.
- `stt_provider`: `string` - Proveedor para la transcripción de subtítulos. Por defecto es `local_whisper`. Opciones:
    * `local_whisper`
    * `third_party_assemblyai`
- `whisper_model`: `string` - Modelo de Whisper para transcripción local (por ejemplo `base`, `small`, `medium`, `large-v3`).
- `whisper_device`: `string` - Dispositivo para Whisper local (`auto`, `cpu`, `cuda`).
- `whisper_compute_type`: `string` - Tipo de cómputo para Whisper local (`int8`, `float16`, etc.).
- `assembly_ai_api_key`: `string` - Tu clave de API de Assembly AI. Obtené la tuya desde [acá](https://www.assemblyai.com/app/).
- `tts_voice`: `string` - Voz para text-to-speech de KittenTTS. Por defecto es `Jasper`. Opciones: `Bella`, `Jasper`, `Luna`, `Bruno`, `Rosie`, `Hugo`, `Kiki`, `Leo`.
- `font`: `string` - La fuente que se usará para generar imágenes. Debe ser un archivo `.ttf` en el directorio `fonts/`.
- `imagemagick_path`: `string` - La ruta al binario de ImageMagick. Lo usa MoviePy para manipular imágenes. Instalá ImageMagick desde [acá](https://imagemagick.org/script/download.php) y configurá la ruta a `magick.exe` en Windows, o en Linux/macOS la ruta a `convert` (generalmente /usr/bin/convert).
- `script_sentence_length`: `number` - La cantidad de oraciones en el guion de video generado (por defecto: `4`).

## Ejemplo

```json
{
  "verbose": true,
  "firefox_profile": "",
  "headless": false,
  "ollama_base_url": "http://127.0.0.1:11434",
  "ollama_model": "",
  "twitter_language": "English",
  "nanobanana2_api_base_url": "https://generativelanguage.googleapis.com/v1beta",
  "nanobanana2_api_key": "",
  "nanobanana2_model": "gemini-3.1-flash-image-preview",
  "nanobanana2_aspect_ratio": "9:16",
  "threads": 2,
  "zip_url": "",
  "is_for_kids": false,
  "google_maps_scraper": "https://github.com/gosom/google-maps-scraper/archive/refs/tags/v0.9.7.zip",
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "",
    "password": ""
  },
  "google_maps_scraper_niche": "",
  "scraper_timeout": 300,
  "outreach_message_subject": "I have a question...",
  "outreach_message_body_file": "outreach_message.html",
  "stt_provider": "local_whisper",
  "whisper_model": "base",
  "whisper_device": "auto",
  "whisper_compute_type": "int8",
  "assembly_ai_api_key": "",
  "tts_voice": "Jasper",
  "font": "bold_font.ttf",
  "imagemagick_path": "Path to magick.exe or on linux/macOS just /usr/bin/convert",
  "script_sentence_length": 4
}
```

## Variables de Entorno Alternativas

- `GEMINI_API_KEY`: se usa cuando `nanobanana2_api_key` está vacío.

Ejemplo:

```bash
export GEMINI_API_KEY="tu_clave_de_api_acá"
```
