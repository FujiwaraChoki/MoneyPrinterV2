# MoneyPrinter V2

> ♥︎ **Sponsor**: La Mejor App de Chat con IA: [shiori.ai](https://www.shiori.ai). Usá el código **MPV2** para un 20% de descuento.

---

> 𝕏 Seguime en X: [@DevBySami](https://x.com/DevBySami).

[![madewithlove](https://img.shields.io/badge/made_with-%E2%9D%A4-red?style=for-the-badge&labelColor=orange)](https://github.com/FujiwaraChoki/MoneyPrinterV2)

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donar-brightgreen?logo=buymeacoffee)](https://www.buymeacoffee.com/fujicodes)
[![GitHub license](https://img.shields.io/github/license/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/issues)
[![GitHub stars](https://img.shields.io/github/stars/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/stargazers)
[![Discord](https://img.shields.io/discord/1134848537704804432?style=for-the-badge)](https://dsc.gg/fuji-community)

Una aplicación que automatiza el proceso de generar dinero en línea.
MPV2 (MoneyPrinter Versión 2) es, como su nombre indica, la segunda versión del proyecto MoneyPrinter. Es una reescritura completa del proyecto original, con enfoque en una mayor variedad de funcionalidades y una arquitectura más modular.

> **Nota:** MPV2 necesita Python 3.12 para funcionar correctamente.
> Mirá el video de YouTube [acá](https://youtu.be/wAZ_ZSuIqfk)

## Funcionalidades

- [x] Bot de Twitter (con tareas CRON => `scheduler`)
- [x] Automatización de YouTube Shorts (con tareas CRON => `scheduler`)
- [x] Marketing de Afiliados (Amazon + Twitter)
- [x] Búsqueda de negocios locales y contacto en frío

## Versiones

MoneyPrinter tiene diferentes versiones en varios idiomas, desarrolladas por la comunidad para la comunidad. Estas son algunas versiones conocidas:

- Chino: [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)
- Español: [MoneyPrinterV2 (Español)](https://github.com/fdfretes/MoneyPrinterV2)

Si querés enviar tu propia versión/fork de MoneyPrinter, por favor abrí un issue describiendo los cambios que hiciste en el fork.

## Instalación

> ⚠️ Si planeás contactar negocios por correo electrónico, primero instalá el [Lenguaje de Programación Go](https://golang.org/).

```bash
git clone https://github.com/fdfretes/MoneyPrinterV2.git

cd MoneyPrinterV2
# Copiar la configuración de ejemplo y completar los valores en config.json
cp config.example.json config.json

# Crear un entorno virtual
python -m venv venv

# Activar el entorno virtual - Windows
.\venv\Scripts\activate

# Activar el entorno virtual - Unix
source venv/bin/activate

# Instalar las dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Ejecutar la aplicación
python src/main.py
```

## Documentación

Toda la documentación relevante se encuentra [acá](docs/).

## Scripts

Para un uso más sencillo, hay algunos scripts en el directorio `scripts` que se pueden usar para acceder directamente a la funcionalidad principal de MPV2, sin necesidad de interacción del usuario.

Todos los scripts deben ejecutarse desde el directorio raíz del proyecto, por ejemplo: `bash scripts/upload_video.sh`.

## Contribuir

Por favor leé [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles sobre nuestro código de conducta y el proceso para enviar pull requests. Consultá [docs/Roadmap.md](docs/Roadmap.md) para una lista de funcionalidades pendientes de implementar.

## Código de Conducta

Por favor leé [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) para más detalles sobre nuestro código de conducta y el proceso para enviar pull requests.

## Licencia

MoneyPrinterV2 está licenciado bajo `Affero General Public License v3.0`. Consultá [LICENSE](LICENSE) para más información.

## Agradecimientos

- [KittenTTS](https://github.com/KittenML/KittenTTS)
- [gpt4free](https://github.com/xtekky/gpt4free)

## Aviso Legal

Este proyecto es solo con fines educativos. El autor no se hace responsable por ningún uso indebido de la información proporcionada. Toda la información en este sitio web se publica de buena fe y con fines informativos generales. El autor no ofrece garantías sobre la integridad, confiabilidad y exactitud de esta información. Cualquier acción que tomes basándote en la información que encontrás en este sitio web (FujiwaraChoki/MoneyPrinterV2) es estrictamente bajo tu propio riesgo. El autor no será responsable por ninguna pérdida y/o daño en conexión con el uso de nuestro sitio web.
