# ❕ Info
Есть файл uuuuh.py - тут не необходимо ввести логин и пароль для pixiv, с селениумом работаем как-никак. Данные вводятся в виде параметров
- Pixiv может выдать капчу на стадии входа, ее вы обязаные решить сами, после нажать на кнопку входа
- Кросс, теперь никаких windows-зависимых библиотек.
- Generative code included of course (4o mini)
- Сканирует папку сохраненок и скачивает только те, что еще не скачены
- Теперь есть асинхрон для curl
- Перелелано с учетом всяких там SOLID-ов
  
# 🏁 Using example
```py
python saverSaves.py --l "<login>" --p "<password>"
```

- Также можно использовать параметр --url для указания ссылки на коллекцию сохраненок
```py
python saverSaves.py --l "<login>" --p "<password>" --url "<url>"
```

## 📃TODO
- Переименовать репо

![image](https://github.com/user-attachments/assets/69bf60bb-dbdb-4804-93c5-cf6cb5b241cd)
