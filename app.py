# Паресер работает на основе библиотеки BeautifulSoup4. Среднее время выполнения: 02:58 минут.

# Здесь мы импортируем необходимые библиотеки (все, кроме bs4 и lxml встроенные)
from bs4 import BeautifulSoup  # (библиотека bs4 устанавливается при помощи команды 'pip install bs4', а также требует установку библиотеки lxml ('pip install lxml'))
import requests # для работы с запросами
from datetime import datetime # для работ с датами и временем
import csv # для работы с таблицами
import os.path # библиотека для работы с системой

start = datetime.now()

# Получение папки с файлом
pat = os.path.dirname(os.path.abspath(__file__))

# url-адрес основной страницы
url = 'https://volkswohl.tools.factsheetslive.com/'

# Параметры UserAgent. Можно поменять на любые другие из интернета
headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'}

# Создание папки tables при её отсутствии
if not os.path.exists(f"{pat}/tables/"):
    os.mkdir(f"{pat}/tables/")

# Делаем запрос и получаем html страницы
main_page = requests.get(url, headers=headers).text

# Используем парсер lxml
soup = BeautifulSoup(main_page, 'lxml')

# Делаем поиск тега 'tbody' на странице (основной таблицы без заголовков) (метод find_all ищет первое совпадение)
table = soup.find('tbody')

# Делаем поиск заголовков таблицы
heads = soup.find("table", id="fundtable").find_all('th')

# Поиск всех строк (метод find_all ищет все совпадения)
rows = table.find_all('tr')

# Многострочная константа, необходимая для правильного запроса, которая меняется при добавлении отступа, поэтому записана вне цикла
NEED = ''',
			"compared"'''

# Открытие файла основной таблицы в режиме переписывания (при повторном открытии старые данные стираются)
# f'{datetime.now().strftime('%d-%m-%Y')}.csv' - отформатированная строка, которая заполняется в зависимости от текущей даты
with open(f'{pat}/{datetime.now().strftime('%d-%m-%Y')}.csv', mode='w', encoding='utf-8') as w_file:
    # Создание объекта csv, работающего с файлом для записи
    first_writer = csv.writer(w_file, delimiter = ";", lineterminator="\r")

    # Запись заголовков таблицы (индексы взяты с сайта)
    first_writer.writerow([
        heads[1].text, heads[2].text, heads[3].text, heads[4].text, 
        heads[5].text, heads[6].text, heads[7].text, heads[8].text, 
        'link', '1 jahr', '3 jahre', '5 jahre'
        ])

    # Цикл перебора строк основной таблицы
    for i in range(len(rows)):
        row = rows[i]
        # Получение всех столбцов одной строки
        settings = row.find_all('td')

        # Запись столбцов по переменным через индексы
        num = settings[1].text.strip()
        name = settings[2].text.replace(" *", '').replace("/", '').strip()
        isin = settings[3].text.strip()
        efficiency = settings[4].text.strip()
        expenses = settings[5].text.strip()
        area = settings[6].text.strip()
        focus = settings[7].text.strip()
        rating = settings[8].text.strip()
        # Отформатированная строка, как ссылка на вторую страницу
        link = f'https://volkswohl.tools.factsheetslive.com/produkt/{isin}/1/'


        # Открытие второй страницы
        b_page = requests.get(link).text

        # ↓ Блок получения Sharp Ratio ↓
        second_soup = BeautifulSoup(b_page, 'lxml')
        # Попытка получить данные, в случае ошибки, будет пустой список
        try:
            ratio_rows = second_soup.find('div', id='performance', class_='table-holder').find_all('tr')[2].find_all(class_='align-right valign-top')
        except:
            ratio_rows = []        
        # ↑ Блок получения Sharp Ratio ↑

        # Переменная для удобной записи данных Sharp Ratio
        ratio_data = []

        # Добавление элементов в виде текста из ratio_rows в массив ratio_data
        for elem in ratio_rows:
            ratio_data.append(elem.text)
        
        # При пустов ratio_rows, элементы будут равны '-'
        if len(ratio_data) == 0:
            ratio_data = ['–', '–', '–']

        # Запись всех переменных в файл
        first_writer.writerow([
            num, name, isin, efficiency,expenses, area, focus, rating, link, ratio_data[0], ratio_data[1], ratio_data[2]
            ])
        
        # При правильной второй странице, выполняется подхадача Б
        if len(ratio_rows) > 0:
            # Создаётся файл на инструмент в папке tables
            with open(f'{pat}/tables/{num}_{name}_{datetime.now().strftime('%d-%m-%Y')}.csv', mode='w', encoding='utf-8') as file:
                # Второй объект записи в csv
                second_writer = csv.writer(file, delimiter = ";", lineterminator="\r")

                # Запись Заголовков
                second_writer.writerow(['Date', 'Value'])

                # Второй объект bs4
                second_soup = BeautifulSoup(b_page, 'lxml')

                # Поиск скрипта JS в файле
                second_table = second_soup.find('div', id='performanceLineChart').find('script')

                # Преобразование текста скрипта в словарь при помощи метода eval (здесь важен отступ, поэтому создана константа NEED)
                diction = eval(str(second_table.text[second_table.text.find('"dataProvider":') + len('"dataProvider": '):second_table.text.find(NEED)].replace('new Date(', '"').replace('),"value', '","value')))

                # Перебор всех пар в словаре
                for elem in diction:
                    # Приведение даты в более привычный вид
                    date = elem['date'].split(',')
                    true_date = f"{date[2].strip().rjust(2, '0')}.{str(int(date[1].strip()) + 1).rjust(2, '0')}.{date[0].strip()}"

                    # Запись во второй файл
                    second_writer.writerow([true_date, elem['value']])
 
print(datetime.now() - start)
            