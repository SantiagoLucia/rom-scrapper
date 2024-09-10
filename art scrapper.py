import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from tqdm.asyncio import tqdm
import os

# Título enmarcado
def print_title():
    """
    Imprime el título del programa.
    """
    title = """
+----------------------------------------------------+
|                   Art Scrapper                     |
|       Descarga de Imágenes de Videojuegos          |
|           desde Thumbnails.Libretro.Com            |
+----------------------------------------------------+
    """
    print(title)

# Función para seleccionar el directorio
def select_directory():
    """
    Solicita al usuario que introduzca el directorio donde se encuentran los archivos.
    """
    directory = input("Introduce el directorio donde se encuentran los archivos: ")
    return directory

# Función para descargar un recurso
async def download_resource(url, session, semaphore, download_path):
    """
    Descarga un recurso desde una URL utilizando una sesión aiohttp.
    """
    async with semaphore:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    filename = unquote(url.split('/')[-1])
                    with open(os.path.join(download_path, filename), 'wb') as f:
                        f.write(content)
                else:
                    print(f'Error: {url} devolvió el código de estado {response.status}')
        except Exception as e:
            print(f'Error descargando {url}: {str(e)}')

# Función para obtener links
async def get_links(url):
    """
    Obtiene todos los enlaces de una página web.
    """
    async with ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
                    return links
                else:
                    print(f'Error: {url} devolvió el código de estado {response.status}')
                    return []
        except Exception as e:
            print(f'Error obteniendo enlaces de {url}: {str(e)}')
            return []

# Función principal para ejecutar el scrapper
async def main():
    print_title()
    directory = select_directory()
    url = input("Introduce la URL de la página web: ")
    links = await get_links(url)
    
    semaphore = asyncio.Semaphore(10)  # Limitar el número de descargas concurrentes
    async with ClientSession() as session:
        tasks = [download_resource(link, session, semaphore, directory) for link in links]
        await tqdm.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())