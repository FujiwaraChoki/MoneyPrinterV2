# Bot de Twitter

Este bot está diseñado para automatizar el proceso de hacer crecer una cuenta de Twitter. Una vez que creaste una cuenta nueva, proporcioná la ruta al perfil de Firefox y el bot empezará a publicar tweets basados en el tema que proporcionaste durante la creación de la cuenta.

## Configuración Relevante

En tu `config.json`, necesitás tener los siguientes atributos completados para que el bot funcione correctamente.

```json
{
  "twitter_language": "Cualquier idioma, el formato no importa",
  "headless": true,
  "llm": "El modelo de lenguaje grande que querés usar, consultá Configuration.md para más información",
}
```
