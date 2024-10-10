import argparse
import os
import time
import subprocess
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# 1. Ответственность за настройку драйвера
class WebDriverManager:
    def __init__(self):
        self.driver = self.setup_driver()

    def setup_driver(self):
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return uc.Chrome(options=options)

    def get_driver(self):
        return self.driver

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                print("Браузер закрыт.")
            except Exception as e:
                print(f"Ошибка при закрытии браузера: {e}")

# 2. Ответственность за авторизацию
class PixivAuthenticator:
    def __init__(self, driver, username, password):
        self.driver = driver
        self.username = username
        self.password = password

    def login(self):
        self.driver.get("https://accounts.pixiv.net/login")
        self.driver.find_element(By.XPATH, "//input[@placeholder='E-mail address or pixiv ID']").send_keys(self.username)
        self.driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(self.password)
        time.sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/button[1]').click()
        time.sleep(2)

        # Проверка на капчу
        if self.driver.find_elements(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/div[3]'):
            print("Пройдите капчу и нажмите на кнопку входа")
        while self.driver.find_elements(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/div[3]'):
            time.sleep(5)

# 3. Ответственность за работу с файловой системой
class FileManager:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        self.existing_files = set()
        self.scan_directory()

    def scan_directory(self):
        os.makedirs(self.output_folder, exist_ok=True)
        absolute_path = os.path.abspath(self.output_folder)
        os.chdir(absolute_path)
        for root, dirs, files in os.walk(f"../{self.output_folder}"):
            for file_name in files:
                self.existing_files.add(file_name.split("_")[0])

    def file_exists(self, filename):
        return filename in self.existing_files

# 4. Ответственность за скачивание изображений
class ImageDownloader:
    def __init__(self, driver, file_manager):
        self.driver = driver
        self.file_manager = file_manager

    async def download_image(self, art_url):
        try:
            self.driver.get(art_url)
            time.sleep(3)

            # Кликаем на кнопку Show all, если она есть
            show_all_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.sc-ye57th-1 > button')
            if show_all_buttons:
                show_all_buttons[0].click()

            # Находим ссылку на full quality изображение
            high_res_link = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.gtm-medium-work-expanded-view div a'))
            )

            download_url = high_res_link.get_attribute('href')
            curl_command = [
                "curl", download_url,
                "-H", "referer: https://www.pixiv.net/",
                "-O",
            ]

            print(f"{download_url}")

            # Асинхронный вызов команды curl для скачивания изображения
            process = await asyncio.create_subprocess_exec(
                *curl_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                print(f"Изображение {art_url} успешно загружено.")
                print(f"stdout: {stdout.decode().strip()}")  # Явный вывод stdout
            else:
                print(f"Ошибка загрузки {art_url}: {stderr.decode().strip()}")  # Явный вывод stderr

        except Exception as e:
            print(f"Ошибка при загрузке изображения {art_url}: {e}")


# 5. Главный класс для управления процессом
class PixivDownloader:
    def __init__(self, username, password, url, output_folder='downloaded_images'):
        self.url = url
        self.output_folder = output_folder
        self.file_manager = FileManager(output_folder)
        self.driver_manager = WebDriverManager()
        self.authenticator = PixivAuthenticator(self.driver_manager.get_driver(), username, password)
        self.image_downloader = ImageDownloader(self.driver_manager.get_driver(), self.file_manager)

    def login(self):
        self.authenticator.login()

    def download_images_from_page(self, page_url):
        # Открываем страницу
        self.driver_manager.get_driver().get(page_url)
        
        try:
            # Ожидаем загрузки элементов с изображениями
            elements = WebDriverWait(self.driver_manager.get_driver(), 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li > div > div:first-child > div > a'))
            )

            # Собираем ссылки на изображения с текущей страницы
            page_hrefs = [el.get_attribute('href') for el in elements]
            
            # Асинхронно загружаем изображения
            asyncio.run(self.async_download_images(page_hrefs))
        except Exception as e:
            print(f"Ошибка при обработке страницы {page_url}: {e}")

    async def async_download_images(self, page_hrefs):
        tasks = []
        for href in page_hrefs:
            # Проверяем, если изображение уже загружено, пропускаем
            if not self.file_manager.file_exists(href.split("/")[-1]):
                tasks.append(self.image_downloader.download_image(href))
        
        # Ожидаем выполнения всех задач
        await asyncio.gather(*tasks)

    def download_images_from_urls(self):
        # Определяем максимальную страницу, чтобы понять сколько страниц есть на сайте
        try:
            # Идем на страницу с самым высоким номером
            self.driver_manager.get_driver().get(f"{self.url}?p=999")
            time.sleep(5)
            
            # Извлекаем реальное количество страниц
            current_url = self.driver_manager.get_driver().current_url
            pages_count = int(current_url.split("p=")[-1])  # Извлекаем число страниц из URL

            # Генерируем список URL для всех страниц
            pages = [f"{self.url}?p={i+1}" for i in range(pages_count)]

            # Для каждой страницы вызываем загрузку изображений
            for page in pages:
                self.download_images_from_page(page)
        except Exception as e:
            print(f"Ошибка при загрузке страниц: {e}")

    def close(self):
        self.driver_manager.close_driver()


# Основной код программы
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--l', type=str, help='Логин', required=True)
    parser.add_argument('--p', type=str, help='Пароль', required=True)
    parser.add_argument('--url', type=str, help='Ссылка на профиль', default="https://www.pixiv.net/en/users/95678549/bookmarks/artworks")
    args = parser.parse_args()

    downloader = PixivDownloader(args.l, args.p, args.url)
    downloader.login()
    downloader.download_images_from_urls()
    downloader.close()
