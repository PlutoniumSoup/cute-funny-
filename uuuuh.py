import argparse
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import keyboard
import sys
import threading
import subprocess

class PixivDownloader:
    def __init__(self, username=None, password=None, output_folder='downloaded_images'):
        self.username = username
        self.password = password
        self.output_folder = output_folder
        self.driver = None
        self.firstT_flag = True
        self.setup_driver()
        self.login()
        # Поток для отслеживания клавиши экстренной остановки
        self.stop_flag = False
        self.monitor_stop_key()

    def setup_driver(self):
        # Установка параметров Chrome
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Настройка драйвера
        self.driver = uc.Chrome(options=options)

        # Создание папки для изображений
        os.makedirs(self.output_folder, exist_ok=True)
        self.absolute_path = os.path.abspath(self.output_folder)  # Преобразуем в полный путь
        os.chdir(self.output_folder)

    def login(self):
        # Открываем главную страницу для установки куков
        if not (self.username and self.password):
            return
        self.driver.get("https://accounts.pixiv.net/login")

        # Вводим учетные данные
        self.driver.find_element(By.XPATH, "//input[@placeholder='E-mail address or pixiv ID']").send_keys(self.username)
        self.driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(self.password)
        time.sleep(2)

        # Нажимаем кнопку входа
        self.driver.find_element(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/button[1]').click()
        time.sleep(2)
        if self.driver.find_elements(By.XPATH, '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/div[3]'): time.sleep(40)

    def download_image(self, url):
        if self.stop_flag:
            return
        try:
            # Открываем ссылку
            self.driver.get(url)
            time.sleep(4)

            # Ожидаем, пока изображение станет доступным
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li > div > div:first-child > div > a img'))
            )

            elements = self.driver.find_elements(By.CSS_SELECTOR, 'li > div > div:first-child > div > a')
            time.sleep(2)
            
            # Сохраняем ссылки на арты на странице
            pageHrefs = []
            for element in elements:
                pageHrefs.append(element.get_attribute('href'))

            for art in pageHrefs:
                try:
                    self.driver.get(art)
                    time.sleep(3)

                    showAllButtons = self.driver.find_elements(By.CSS_SELECTOR, '.sc-ye57th-1 > button')
                    if showAllButtons: showAllButtons[0].click()

                    highRef = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.gtm-medium-work-expanded-view div a'))
                    )

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
                except Exception as e:
                    print(f"Что пошло не так - art: {e}")
                
        except Exception as e:
            print(f"Что пошло не так - page: {e}")

    def download_images_from_urls(self):
        for url in [f"https://www.pixiv.net/en/users/95678549/bookmarks/artworks?p={i}" for i in range(1, 25)]:
            if self.stop_flag:  # Проверка флага остановки
                print("Процесс был остановлен.")
                break
            self.download_image(url)

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

    def monitor_stop_key(self):
        # Создаем поток для отслеживания клавиши экстренной остановки
        def check_stop_key():
            print("Для экстренной остановки программы нажмите '-' на NumPad.")
            keyboard.wait('num -')  # Ожидание нажатия клавиши "minus" на цифровой клавиатуре
            self.stop_flag = True
            print("Экстренная остановка программы...")
            self.close()
            sys.exit()

        threading.Thread(target=check_stop_key, daemon=True).start()


if __name__ == "__main__":
    # Данные для входа
    # Создаем парсер
    parser = argparse.ArgumentParser()
    parser.add_argument('--l', type=str, help='Логин', default=None)
    parser.add_argument('--p', type=str, help='Пароль', default=None)
    args = parser.parse_args()

    username = args.l
    password = args.p

    # Инициализация загрузчика
    downloader = PixivDownloader(username, password)

    # Загрузка изображений по ссылкам
    downloader.download_images_from_urls()

    # Завершение работы
    downloader.close()
