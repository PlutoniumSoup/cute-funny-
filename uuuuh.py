import argparse
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import pyautogui
import keyboard
import sys
import threading


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

        # Проверка длины путей
        if len(self.absolute_path) < len(self.output_folder):
            raise Exception("Что-то пошло не так")

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

    def download_image(self, url):
        if self.stop_flag:
            return
        try:
            # Открываем ссылку
            self.driver.get(url)

            # Ожидаем, пока изображение станет доступным
            image_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.gtm-medium-work-expanded-view div img'))
            )

            # Печатаем найденный элемент
            print(f"Найден элемент: {image_element}")

            # Имитация скачивания изображения через контекстное меню
            time.sleep(3)
            action = ActionChains(self.driver)
            action.context_click(image_element).perform()

            # Навигация в меню с помощью pyautogui
            [pyautogui.press('down') for _ in range(8 if self.username and self.password else 2)]
            pyautogui.press('enter')

            if self.firstT_flag:
                time.sleep(2)

                # Ввод пути для сохранения изображения
                [pyautogui.hotkey('shift', 'tab') for _ in range(5)]
                pyautogui.press('enter')
                time.sleep(1)
                pyautogui.write(self.absolute_path)
                time.sleep(1)
                pyautogui.press('enter')

                # Завершающие действия
                [pyautogui.press('tab') for _ in range(8)]
                time.sleep(1)
                self.firstT_flag = False
            else:
                time.sleep(1.5)
            pyautogui.press('enter')

            print(f"Скачано изображение с {url}")
        except Exception as e:
            print(f"Не удалось найти изображение на странице {url}: {e}")

    def download_images_from_urls(self, urls):
        for url in urls:
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
    parser.add_argument('--param1', type=str, help='Логин', default=None)
    parser.add_argument('--param2', type=str, help='Пароль', default=None)
    args = parser.parse_args()

    username = args.param1
    password = args.param2

    # Чтение ссылок из файла
    with open('urls.txt', 'r') as file:
        links = [line.strip() for line in file]

    # Инициализация загрузчика
    downloader = PixivDownloader(username, password)

    # Загрузка изображений по ссылкам
    downloader.download_images_from_urls(links)

    # Завершение работы
    downloader.close()
