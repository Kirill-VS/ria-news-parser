import requests



headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36',
    # 'cookie': 'fb_check5=1; _pk_ref.ria.ddd3=%5B%22%22%2C%22%22%2C1794055221%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_ses.ria.ddd3=%7B%22depth%22%3A0%7D; _ym_uid=1794055221316562420; _ym_d=1794055221; _ym_isad=1; _ymab_param=e51t9NykTZrV3o2MCdWTzRJDzEPlcB7emWTJ674z27qlKoSoOpL0CbXSsBa2Lnd0nOQaMIBWYftjvJFzwcvqtzbkjLM; mdd=0; ispwa-user-visits=3; _pk_id.ria.ddd3=644eb8ad8c890a14.1794055221.1.1794055532.1794055221.',
}


import re
import sqlite3
# формирую бд
con = sqlite3.connect("News.db")
cursor = con.cursor()
###################

# создание таблицы с новостями
cursor.execute("""
    CREATE TABLE IF NOT EXISTS News (
        time TEXT, 
        clu_word TEXT, 
        title TEXT, 
        link TEXT,
        article TEXT
        )
""")
#######################


# Создание и заполнение таблицы с ключевыми словами
cursor.execute("""
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT UNIQUE
    )
""")

# Массив ключевых слов
words_to_add = ['спорт', 'косметика', 'туризм', 'наводнение']
#заполняю базу ключами
for word in words_to_add:
    cursor.execute(""" INSERT OR IGNORE INTO keywords (keyword) VALUES (?)""", (word,))

print("Таблица keywords создана и заполнена словами:", words_to_add)
##############################

cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_news_link ON News(link)")
con.commit()

# откуда раньше брали первую пачку новостей
#new_link = 'https://ria.ru/lenta/'

PAGES = 1 # параметр отвечает за количество статей вызванных


# достаю слова из базенки
cursor.execute("SELECT keyword FROM keywords", )
keywords = [row[0] for row in cursor.fetchall()]
print(keywords)
print("Количество запросов на одно ключевое слово", PAGES, "Тоесть всего будет выданно", len(keywords)*PAGES*20, "новостей")
###############

#Цикл по ключевым словам
for word in keywords:
    print("Начинаю поиск по слову:", word, "будет выданно", PAGES*20, "со словом", word)
    #new_link = f'https://ria.ru/search/?query={word}'
    new_link = f'https://ria.ru/services/search/getmore/?query={word}'
    #Цикл для поиска нескольких пачек новостей
    for page in range(PAGES):
        print('Вызов новых новостей. Итерация номер:', page+1)
        response = requests.get(new_link, headers=headers)
        #print(response.text)

        articles = re.findall(r"href=\"(https://ria.ru/\d{8}/[^\"]+\.html)", response.text)
        articles = list(dict.fromkeys(articles))
        print("Article", articles)
        #Цикл парсинга одной пачки новостей
        for i in range(len(articles)):
            res = requests.get(articles[i], headers=headers)
            # заголовок время
            title = re.search(r"<.*? class=\"article__title\">(.*?)<.*?>", res.text)
            time = re.search(r"<a href=\"/\d{8,10}/\">(\d{2}:\d{2}\s+\d{2}.\d{2}.\d{4})</a>", res.text)


            # кушаю текст
            blocks = re.findall(r"<div class=\"article__text\"[^>]*>(.*?)</div>", res.text, re.DOTALL)

            # убираю лишнее
            article_text = " ".join(re.sub(r'<[^>]+>', '', b) for b in blocks).strip()

            # удаляю шапку вида "БЕРЛИН, 14 ноя - РИА Новости." Если вдруг эта регулярка косячная то можно удалить строку ниже
            article_text = re.sub(r'^[А-ЯЁA-Z\s\-]+,\s*\d{1,2}\s+[а-яё]+\s*[—–-]\s*РИА\s+Новости\.\s*', '', article_text).lstrip()

            title_str = title.group(1).strip() if title else ""
            time_str = time.group(1).strip() if time else ""

            cursor.execute("INSERT OR IGNORE INTO News (time, clu_word, title, link, article) VALUES (?, ?, ?, ?, ?)", (time_str, word, title_str, articles[i], article_text))
            print(time_str, title_str, articles[i])

        con.commit()


        # Ищем либо data-url, либо data-next-url
        n = re.search(fr'data-(?:url|next-url)=\"(/services/search/getmore/\?[^"]+)\"', response.text)


        if n:
            new_link = 'https://ria.ru' + n.group(1).replace("&amp;", "&")
            print("Ссылка на новые 20 новостей", new_link)
        else:
            print("\nПоломка на цикле номер:", page+1, n)
            break

con.close()
