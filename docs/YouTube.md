# Automatizador de YouTube Shorts

MPV2 usa una implementación similar a la de V1 (ver [MPV1](https://github.com/FujiwaraChoki/MoneyPrinter)), para generar archivos de video y subirlos a YouTube Shorts.

A diferencia de V1, V2 usa imágenes generadas por IA como los visuales del video, en lugar de usar material de archivo de stock. Esto hace que los videos sean más únicos y menos propensos a ser marcados por YouTube. V2 también soporta música desde el inicio.

## Configuración Relevante

En tu `config.json`, necesitás tener los siguientes atributos completados para que el bot funcione correctamente.

```json
{
  "firefox_profile": "La ruta a tu perfil de Firefox (usado para iniciar sesión en YouTube)",
  "headless": true,
  "llm": "El modelo de lenguaje grande que querés usar para generar el guion del video.",
  "image_model": "Qué modelo de IA querés usar para generar imágenes.",
  "threads": 4,
  "is_for_kids": true
}
```

## Hoja de Ruta

Acá hay algunas funcionalidades planeadas para el futuro:

- [ ] Subtítulos (usando AssemblyAI o ensamblándolos localmente)
