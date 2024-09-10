import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, quote
import asyncio
from aiohttp import ClientSession
from tqdm.asyncio import tqdm
import inquirer
import os

# Título enmarcado
def print_title():
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
    directory = input("Introduce el directorio donde se encuentran los archivos: ")
    return directory

# Función para descargar un recurso
async def download_resource(url, session, semaphore, download_path):
    async with semaphore:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    filename = unquote(url.split('/')[-1])
                    with open(os.path.join(download_path, filename), 'wb') as f:
                        f.write(content)
                else:
                    pass
        except Exception as e:
            print(f'Error downloading {url}: {str(e)}')

# Función para obtener links
def get_links(url):
    # Realiza una solicitud GET a la página web
    response = requests.get(url)

    # Verifica si la solicitud fue exitosa
    if response.status_code == 200:
        # Parsear el contenido HTML con Beautiful Soup
        soup = BeautifulSoup(response.content, 'lxml')

        # Encuentra todas las etiquetas <a>
        links = soup.find_all('a')
        return links
    
    else:
        print(f'Failed to retrieve the page. Status code: {response.status_code}')

# Función principal
async def main():
    print_title()

    # Seleccionar el directorio de búsqueda
    search_directory = select_directory()
    if not search_directory:
        print("No se seleccionó un directorio. Saliendo...")
        return

    # Obtener los nombres de los archivos en el directorio seleccionado sin las extensiones
    search_files = {os.path.splitext(file)[0] for file in os.listdir(search_directory)}

    # URL de la página web
    base_url = f'https://thumbnails.libretro.com/'

    links = get_links(base_url)

    # Definir las opciones de sistemas
    sistemas = []
    for link in links[1:-3]:
        sistema = link.text[:-1]
        if sistema:
            sistemas.append(sistema)
    sistemas.append('SALIR')
    
    # Crear el menú interactivo
    questions = [
        inquirer.List('sistema',
                      message='Selecciona el sistema',
                      choices=sistemas,
                      ),
    ]
    respuestas = inquirer.prompt(questions)
    sistema = respuestas['sistema']

    if sistema == 'SALIR':
        print('Saliendo del script...')
        return

    # Crear la estructura de directorios
    os.makedirs(sistema, exist_ok=True)
    boxarts_dir = os.path.join(sistema, 'Named_Boxarts')
    snaps_dir = os.path.join(sistema, 'Named_Snaps')
    titles_dir = os.path.join(sistema, 'Named_Titles')
    os.makedirs(boxarts_dir, exist_ok=True)
    os.makedirs(snaps_dir, exist_ok=True)
    os.makedirs(titles_dir, exist_ok=True)

    hrefs = []
    for category, download_path in zip(['Named_Boxarts', 'Named_Snaps', 'Named_Titles'], [boxarts_dir, snaps_dir, titles_dir]):

        # URL de la página web
        base_url = f'https://thumbnails.libretro.com/{quote(sistema)}/{category}/'

        links = get_links(base_url)

        # Extrae los href de cada etiqueta <a> menos el primero
        for link in links[1:]:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                filename = os.path.splitext(unquote(full_url.split('/')[-1]))[0]
                if filename in search_files:  # Descargar solo si coincide el nombre sin la extensión
                    hrefs.append((full_url, download_path))

    # Limitar el número de solicitudes simultáneas
    semaphore = asyncio.Semaphore(16)

    async with ClientSession() as session:
        tasks = [download_resource(url, session, semaphore, path) for url, path in hrefs]
        for f in tqdm.as_completed(
            tasks, desc='Downloading resources', total=len(tasks)
        ):
            await f

# Ejecutar el script
if __name__ == '__main__':
    asyncio.run(main())
