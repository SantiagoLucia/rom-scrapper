# Art Scrapper

**Art Scrapper** es una herramienta de línea de comandos para descargar imágenes de videojuegos desde Thumbnails.Libretro.Com. Permite al usuario seleccionar un directorio local donde se encuentran los nombres de los archivos y luego elegir un sistema para descargar las imágenes correspondientes.

## Características

- **Selección de Directorio**: El usuario selecciona un directorio local que contiene los nombres de los archivos (sin extensiones).
- **Selección de Sistema**: El usuario elige el sistema de videojuegos desde el cual se desean descargar las imágenes.
- **Descarga Concurrente**: Utiliza descargas concurrentes para acelerar el proceso de obtención de imágenes.

## Instalación

Para ejecutar esta aplicación, necesitarás tener Python 3.7 o superior. Además, asegúrate de instalar las dependencias necesarias. Puedes instalar las dependencias utilizando `pip`:

```bash
pip install requests beautifulsoup4 aiohttp tqdm inquirer
