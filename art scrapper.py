import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, quote
import asyncio
from aiohttp import ClientSession
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QWidget, QMessageBox, QProgressBar, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import json

# Ruta del archivo de configuración
CONFIG_FILE = "config.json"

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

# Crear una clase para manejar las descargas en un hilo separado
class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    completed_signal = pyqtSignal()

    def __init__(self, hrefs, semaphore):
        super().__init__()
        self.hrefs = hrefs
        self.semaphore = semaphore

    async def download_all_with_progress(self):
        async with ClientSession() as session:
            tasks = [download_resource(url, session, self.semaphore, path) for url, path in self.hrefs]
            total_tasks = len(tasks)
            completed_tasks = 0

            for task in asyncio.as_completed(tasks):
                await task
                completed_tasks += 1
                progress = int((completed_tasks / total_tasks) * 100)
                self.progress_signal.emit(progress)

    def run(self):
        asyncio.run(self.download_all_with_progress())
        self.completed_signal.emit()

class ArtScrapperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Art Scrapper")
        self.setGeometry(100, 100, 400, 400)  # Reducir el alto de la aplicación a un tercio menos

        # Variables
        self.search_directory = ""
        self.selected_system = ""

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Mejorar el atractivo visual con colores y tipografía
        self.setStyleSheet("background-color: #2c3e50; color: white;")

        # Title
        self.title_label = QLabel("Art Scrapper\nDescarga de Imágenes de Videojuegos\ndesde Thumbnails.Libretro.Com")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ecf0f1; text-align: center;")
        self.layout.addWidget(self.title_label)

        # Select directory button
        self.select_dir_button = QPushButton("Seleccionar Directorio")
        self.select_dir_button.setStyleSheet("background-color: #3498db; color: white; font-size: 14px; padding: 8px; border-radius: 5px;")
        self.select_dir_button.clicked.connect(self.select_directory)
        self.layout.addWidget(self.select_dir_button)

        # Directory label
        self.directory_label = QLabel("Directorio seleccionado: Ninguno")
        self.directory_label.setStyleSheet("font-size: 14px; color: #bdc3c7;")
        self.layout.addWidget(self.directory_label)

        # System selection dropdown
        self.system_label = QLabel("Selecciona el sistema:")
        self.system_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ecf0f1;")
        self.layout.addWidget(self.system_label)

        self.system_dropdown = QComboBox()
        self.system_dropdown.setStyleSheet("background-color: #34495e; color: white; font-size: 14px; padding: 5px; border-radius: 5px;")
        self.layout.addWidget(self.system_dropdown)

        # Ajustar el espacio entre el listado de sistemas y la barra de progreso
        self.layout.addStretch()

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { border: 2px solid #34495e; border-radius: 5px; text-align: center; } QProgressBar::chunk { background-color: #1abc9c; width: 20px; }")
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # Start button
        self.start_button = QPushButton("Iniciar")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71; color: white; font-size: 14px; padding: 8px; border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        # Botón de salir
        self.exit_button = QPushButton("Salir")
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white; font-size: 14px; padding: 8px; border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        # Crear un contenedor horizontal para los botones de iniciar y salir
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)  # Cambiar a QHBoxLayout para alinearlos horizontalmente
        self.button_layout.setSpacing(10)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.button_container)

        # Añadir los botones al contenedor horizontal
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.exit_button)

        # Ajustar el alto de la ventana para cubrir los elementos sin dejar espacios vacíos
        self.adjustSize()

        # Load systems
        self.load_systems()

        # Cargar configuración al iniciar
        self.load_config()

        # Guardar configuración al cerrar
        self.closeEvent = self.save_config

        self.download_thread = None

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecciona el directorio donde se encuentran los archivos")
        if directory:
            self.search_directory = directory
            self.directory_label.setText(f"Directorio seleccionado: {directory}")
        else:
            QMessageBox.warning(self, "Advertencia", "No se seleccionó un directorio.")

    def load_systems(self):
        base_url = f'https://thumbnails.libretro.com/'
        links = get_links(base_url)

        sistemas = []
        for link in links[4:-3]:  # Excluir los primeros tres elementos
            sistema = link.text[:-1]
            if sistema:
                sistemas.append(sistema)

        self.system_dropdown.addItems(sistemas)

    def start_process(self):
        directory = self.search_directory
        sistema = self.system_dropdown.currentText()

        if not directory:
            QMessageBox.critical(self, "Error", "Por favor selecciona un directorio primero.")
            return

        if not sistema:
            QMessageBox.critical(self, "Error", "Por favor selecciona un sistema.")
            return

        QMessageBox.information(self, "Información", f"Iniciando proceso para el sistema: {sistema}")

        # Obtener los nombres de los archivos en el directorio seleccionado sin las extensiones
        search_files = {os.path.splitext(file)[0] for file in os.listdir(directory)}

        # Crear la estructura de directorios dentro de "resources" en el directorio seleccionado
        resources_dir = os.path.join(directory, "resources")
        os.makedirs(resources_dir, exist_ok=True)

        boxarts_dir = os.path.join(resources_dir, 'Named_Boxarts')
        snaps_dir = os.path.join(resources_dir, 'Named_Snaps')
        titles_dir = os.path.join(resources_dir, 'Named_Titles')
        os.makedirs(boxarts_dir, exist_ok=True)
        os.makedirs(snaps_dir, exist_ok=True)
        os.makedirs(titles_dir, exist_ok=True)

        # Descargar imágenes
        hrefs = []
        for category, download_path in zip(['Named_Boxarts', 'Named_Snaps', 'Named_Titles'], [boxarts_dir, snaps_dir, titles_dir]):
            base_url = f'https://thumbnails.libretro.com/{quote(sistema)}/{category}/'
            links = get_links(base_url)

            for link in links[1:]:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    filename = os.path.splitext(unquote(full_url.split('/')[-1]))[0]
                    if filename in search_files:
                        hrefs.append((full_url, download_path))

        self.semaphore = asyncio.Semaphore(16)

        # Configurar el hilo de descargas
        self.download_thread = DownloadThread(hrefs, self.semaphore)
        self.download_thread.progress_signal.connect(self.progress_bar.setValue)
        self.download_thread.completed_signal.connect(self.on_download_complete)
        self.download_thread.start()

    def on_download_complete(self):
        QMessageBox.information(self, "Información", "Descarga completada.")
        self.progress_bar.setValue(0)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.search_directory = config.get("last_directory", "")
                self.selected_system = config.get("last_system", "")

                if self.search_directory:
                    self.directory_label.setText(f"Directorio seleccionado: {self.search_directory}")

                if self.selected_system:
                    index = self.system_dropdown.findText(self.selected_system)
                    if index != -1:
                        self.system_dropdown.setCurrentIndex(index)

    def save_config(self, event):
        config = {
            "last_directory": self.search_directory,
            "last_system": self.system_dropdown.currentText()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArtScrapperApp()
    window.show()
    sys.exit(app.exec_())
