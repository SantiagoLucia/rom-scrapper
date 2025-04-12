# Crear un nuevo archivo llamado `downloader.py` para manejar la lógica de descarga

# downloader.py
import os
import asyncio
from aiohttp import ClientSession
from urllib.parse import unquote

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

async def download_all(hrefs, semaphore):
    async with ClientSession() as session:
        tasks = [download_resource(url, session, semaphore, path) for url, path in hrefs]
        await asyncio.gather(*tasks)