import argparse
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import subprocess

class PixivDownloader:
    def __init__(self, username=None, password=None, output_folder='downloaded_images', url="https://www.pixiv.net/en/users/95678549/bookmarks/artworks"):
        self.username = username
        self.password = password
        self.output_folder = output_folder
        self.driver = None
        self.firstT_flag = True
        self.root_url = url
        self.existing_files = set()

        self.setup_driver()
        self.login()
        self.scan_directory()

    def setup_driver(self):
        # Установка параметров Chrome
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Настройка драйвера
        self.driver = uc.Chrome(options=options)

        # Создание папки для изображений
        os.makedirs(self.output_folder, exist_ok=True)
        self.absolute_path = os.path.abspath(self.output_folder) 

        # Переход в папку для изображений
        os.chdir(self.absolute_path)

    def login(self):
        self.driver.get("https://accounts.pixiv.net/login")

        # Вводим учетные данные
        self.driver.find_element(By.XPATH, "//input[@placeholder='E-mail address or pixiv ID']").send_keys(self.username)
        self.driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(self.password)
        time.sleep(2)

        # Нажимаем кнопку входа
        self.driver.find_element(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/button[1]').click()
        time.sleep(2)

        # Проверка на капчу
        if self.driver.find_elements(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/div[3]'): print("Пройдите капчу и нажмите на кнопку входа")
        while self.driver.find_elements(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/div[3]'):
            time.sleep(5)

    def scan_directory(self):
        for root, dirs, files in os.walk(f"../{self.output_folder}"):
            for file_name in files:
                self.existing_files.add(file_name.split("_")[0])
                
    def download_images_from_page(self, url):
        try:
            # Открываем ссылку
            self.driver.get(url)

            # Ожидаем, пока ссылки станут доступными
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li > div > div:first-child > div > a'))
            )

            # Находим сслыки на арты
            elements = self.driver.find_elements(By.CSS_SELECTOR, 'li > div > div:first-child > div > a')
            
            # Сохраняем ссылки на арты на текущей странице
            pageHrefs = []
            for element in elements:
                pageHrefs.append(element.get_attribute('href'))

            for artHref in pageHrefs:
                try:
                    if artHref.split("/")[-1] in self.existing_files: continue
                    self.download_image(artHref)
                except Exception as e:
                    print(f"Что пошло не так - art: {e}")
                
        except Exception as e:
            print(f"Что пошло не так - page: {e}")

    def download_image(self, art):
        self.driver.get(art)
        time.sleep(3)

        # Кликаем на кнопку Show all, если она есть
        showAllButtons = self.driver.find_elements(By.CSS_SELECTOR, '.sc-ye57th-1 > button')
        if showAllButtons: showAllButtons[0].click()

        # Находим ссылку на full quality изображение
        highRef = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.gtm-medium-work-expanded-view div a'))
        )

        # Через curl скачиваем изображение
        curl_command = [
            "curl", highRef.get_attribute('href'),
            "-H", "referer: https://www.pixiv.net/",
            "-O", 
        ]
        print(highRef.get_attribute('href'))
        result = subprocess.run(curl_command, capture_output=True, text=True)
        print("Return Code:", result.returncode)
        if result.returncode == 0:
            print("Команда успешно выполнена")
        else:
            print("Ошибка выполнения команды")
            print("Ошибка:", result.stderr)

    def download_images_from_urls(self):
        max_page = 999
        url = f"{self.root_url}?p={max_page}"

        # Переходим на последнюю страницу
        self.driver.get(url)
        time.sleep(5)
        pagesCount = int(self.driver.current_url.split("p=")[-1])

        pages = [f"{self.root_url}?p={i+1}" for i in range(pagesCount)]

        for page in pages:
            self.download_images_from_page(page)

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                print("Браузер закрыт.")
            except Exception as e:
                print(f"Ошибка при закрытии браузера: {e}")

    def __del__(self):
        # Закрываем драйвер при удалении объекта
        self.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--l', type=str, help='Логин', default=None)
    parser.add_argument('--p', type=str, help='Пароль', default=None)
    parser.add_argument('--url', type=str, help='Ссылка на профиль', default=None)
    args = parser.parse_args()

    username = args.l
    password = args.p
    url = args.url

    if not (username and password):
        print("Auth required: Для загрузки в высоком качестве нужна авторизация.")
        print("Auth required: Use \"python --l '<login>' --p '<password>'\"")
        quit()

    downloader = PixivDownloader(username, password, url=url or "https://www.pixiv.net/en/users/95678549/bookmarks/artworks")

    downloader.download_images_from_urls()

    downloader.close()
