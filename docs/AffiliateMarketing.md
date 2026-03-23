# AFM

Esta clase es responsable de la parte de Marketing de Afiliados de MPV2. Usa Ollama (como todas las demás clases) como su forma de aprovechar el poder de los LLMs, en este caso, para generar tweets basados en información sobre un **Producto de Amazon**. MPV2 hará scraping de la página del producto y guardará el **título del producto** y las **características del producto**, teniendo así suficiente información para poder crear un pitch del producto y publicarlo en Twitter.

## Configuración Relevante

En tu `config.json`, necesitás tener los siguientes atributos completados para que el bot funcione correctamente.

```json
{
  "firefox_profile": "La ruta a tu perfil de Firefox (usado para iniciar sesión en Twitter)",
  "headless": true,
  "ollama_base_url": "http://127.0.0.1:11434",
  "threads": 4
}
```

## Hoja de Ruta

Acá hay algunas funcionalidades planeadas para el futuro:

- [ ] Hacer scraping de más información sobre el producto, para poder crear un pitch más detallado.
- [ ] Unirse a comunidades online relacionadas con el producto y publicar un pitch (con un link al producto) ahí.
- [ ] Responder a tweets relacionados con el producto, con un pitch del producto.
