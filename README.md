# Achtung - теперь понадёжнее #
Итак, есть файл urls - хранит ссылки на все сохраненки в pixiv - по факту уже не нужен.
Есть файл uuuuh.py - тут не необходимо ввести логин и пароль для pixiv, с селениумом работаем как-никак. Данные вводятся в виде параметров
- Рассчитано только для винды (11, ибо это то, на чем я сидел, когда писал это).
- В процессе используются методы из pyautogui, что теоретически может начать вытворять хаос на компе.
- Использовать символ '-' на numPad для экстренной остановки - как раз, чтобы не допустить хаос на компе.
- Generative code included of course (4o mini)

# Using example
python --l "\<login\>" --p "\<password\>"
