import requests
import sqlite3
import os
import csv
from bs4 import BeautifulSoup
import flet as ft

# データベースファイルの名前
db_name = "final_task.db"

# データベースのセットアップ
if not os.path.exists(db_name):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    # prefectures カラムを TEXT 型に変更
    sql = '''CREATE TABLE IF NOT EXISTS treasure (
        prefectures TEXT PRIMARY KEY, 
        national_treasure INT, 
        important_cultural_property INT, 
        important_cultural_landscape INT, 
        important_traditional_buildings INT)'''
    sql2 = '''CREATE TABLE IF NOT EXISTS evaluation (
        prefectures TEXT PRIMARY KEY, 
        evaluation_score INT)'''
    cur.execute(sql)
    cur.execute(sql2)
    con.commit()
    con.close()

# データベースに都道府県を初期登録
def initialize_database():
    prefectures = [
        "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima",
        "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa",
        "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu", "shizuoka", "aichi",
        "mie", "shiga", "Kyoto", "osaka", "hyogo", "nara", "wakayama",
        "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
        "tokushima", "kagawa", "ehime", "kochi",
        "fukuoka", "saga", "nagasaki", "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
    ]
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    for pref in prefectures:
        # INSERT文を修正して、カラム数と一致するようにする
        cur.execute('INSERT OR IGNORE INTO treasure (prefectures, national_treasure, important_cultural_property, important_cultural_landscape, important_traditional_buildings) VALUES (?, ?, ?, ?, ?)', 
                    (pref, 0, 0, 0, 0))
        cur.execute('INSERT OR IGNORE INTO evaluation (prefectures, evaluation_score) VALUES (?, ?)', (pref, 0))
    con.commit()
    con.close()

initialize_database()

# CSVファイルからデータを読み込み、treasureテーブルに保存
def load_data_from_csv(csv_file):
    with sqlite3.connect(db_name) as con:
        cur = con.cursor()
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute('''
                    INSERT OR REPLACE INTO treasure (prefectures, national_treasure, important_cultural_property, important_cultural_landscape, important_traditional_buildings)
                    VALUES (?, ?, ?, ?, ?)
                ''', (row['prefectures'], row['national_treasure'], row['important_cultural_property'], row['important_cultural_landscape'], row['important_traditional_buildings']))
        con.commit()

# ホテルURLデータ取得
def fetch_hotel_data(prefecture):
    """指定された都道府県のホテルURLを取得する。"""
    try:
        url = f'https://www.jalan.net/ikisaki/map/{prefecture}/'
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        hotel_urls = []
        for i in range(1, 4):  # 通常ホテル
            element = soup.select_one(f'#faq-wrapper > div:nth-child(2) > div.faq-answer > ul > li:nth-child({i}) > a')
            if element:
                href = element['href']
                hotel_url = f'https://www.jalan.net{href}'
                hotel_urls.append(hotel_url)
            else:
                break
        
        japanese_hotel_urls = []
        for i in range(0, 3):  # 日本のホテル
            element = soup.select_one(f'#faq-wrapper > div:nth-child(3) > div.faq-answer > ul > li:nth-child({i+1}) > a')
            if element:
                href = element['href']
                hotel_url = f'https://www.jalan.net{href}'
                japanese_hotel_urls.append(hotel_url)
            else:
                break
        return hotel_urls + japanese_hotel_urls
    except Exception as ex:
        print(f"Error fetching hotel data for {prefecture}: {ex}")
        return []

# 評価データの保存
def fetch_and_store_evaluation(prefecture, hotel_urls):
    """指定されたホテルのURLから評価を取得し、DBに保存する。"""
    evaluation_sum = 0
    count = 0
    for url in hotel_urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            element = soup.select_one('#jlnpc-main-contets-area > div.shisetsu-kuchikomi_sougou_body_wrap > div > dl > dd > span > span')
            if element:
                evaluation = float(element.text.strip())
                evaluation_sum += evaluation
                count += 1
        except Exception as ex:
            print(f"Error fetching evaluation for {url}: {ex}")
    
    average_evaluation = evaluation_sum / count if count > 0 else 0
    with sqlite3.connect(db_name) as con:
        cur = con.cursor()
        cur.execute('UPDATE evaluation SET evaluation_score = ? WHERE prefectures = ?', (average_evaluation, prefecture))

# データベース更新（ホテル数を保存）
def update_database(prefecture, hotel_count):
    """ホテル数をデータベースに保存する。"""
    with sqlite3.connect(db_name) as con:
        cur = con.cursor()
        cur.execute('UPDATE treasure SET national_treasure = ? WHERE prefectures = ?', (hotel_count, prefecture))
        con.commit()

# メイン関数
def main(page: ft.Page):
    page.title = "Prefecture Selection"
    page.scroll = ft.ScrollMode.AUTO
    selected_text = ft.Text(value="", size=20, weight=ft.FontWeight.BOLD)

    def on_button_click(e):
        selected_text.value = f"Selected prefecture: {e.control.text}"
        page.update()

        prefecture = e.control.text
        try:
            hotel_urls = fetch_hotel_data(prefecture)
            fetch_and_store_evaluation(prefecture, hotel_urls)
            update_database(prefecture, len(hotel_urls))

            content = [
                ft.Text(f"Found {len(hotel_urls)} hotel(s) in {prefecture}:"),
                *[ft.Text(url) for url in hotel_urls],
                ft.Text(f"Evaluation data has been stored in the database for {prefecture}.")
            ]
            page.add(ft.Column(content, spacing=10))
        except Exception as ex:
            page.add(ft.Text(f"Error fetching data for {prefecture}: {ex}", color="red"))
        page.update()

    prefectures = [
        "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima", "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa", "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu", "shizuoka", "aichi",
        "mie", "shiga", "Kyoto", "osaka", "hyogo", "nara", "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi", "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki", "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
    ]

    # 都道府県ボタンを行ごとに配置
    button_rows = []
    for i in range(0, len(prefectures), 6):  # 1行に6個のボタン
        row_buttons = [
            ft.ElevatedButton(text=pref, on_click=on_button_click)
            for pref in prefectures[i:i+6]
        ]
        button_rows.append(ft.Row(row_buttons, spacing=10))

    # UI要素をページに追加
    page.add(
        ft.Column([
            ft.Text("Select a prefecture:", size=24, weight=ft.FontWeight.BOLD),
            *button_rows,
            selected_text
        ], spacing=20)
    )

if __name__ == "__main__":
    # CSVファイルからデータを読み込む
    csv_file = 'final_task/final_data.csv'
    if os.path.exists(csv_file):
        load_data_from_csv(csv_file)
    else:
        print(f"CSV file '{csv_file}' not found.")
    ft.app(target=main)
