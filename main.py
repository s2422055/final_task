import requests
import sqlite3
import os
import time
from bs4 import BeautifulSoup
import flet as ft

# データベースファイルの名前
db_name = "final_task.db"

# データベースのセットアップ
if not os.path.exists(db_name):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    # prefectures カラムを TEXT 型に変更
    cur.execute('CREATE TABLE IF NOT EXISTS treasure (prefectures TEXT PRIMARY KEY, Number_of_pieces INT)')
    cur.execute('CREATE TABLE IF NOT EXISTS evaluation (prefectures TEXT PRIMARY KEY, price INT, evaluation INT)')
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
        "tokushima", "kagawa", "ehime", "kochi"
        "fukuoka", "saga", "nagasaki", "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
    ]
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    for pref in prefectures:
        cur.execute('INSERT OR IGNORE INTO treasure (prefectures, Number_of_pieces) VALUES (?, ?)', (pref, 0))
        cur.execute('INSERT OR IGNORE INTO evaluation (prefectures, price, evaluation) VALUES (?, ?, ?)', (pref, 0, 0))
    con.commit()
    con.close()

initialize_database()

# メイン関数
def main(page: ft.Page):
    page.title = "Prefecture Selection"
    page.scroll = ft.ScrollMode.AUTO

    # 選択された都道府県を表示するテキスト
    selected_text = ft.Text(value="", size=20, weight=ft.FontWeight.BOLD)

    # ボタンがクリックされたときの処理
    def on_button_click(e):
        selected_text.value = f"Selected prefecture: {e.control.text}"
        page.update()

        # 都道府県の名前を取得
        prefecture = e.control.text
        time.sleep(1)

        # スクレイピング処理
        try:
            page.add(ft.Text(f"Fetching hotel data for {prefecture}...", size=16))
            url = f'https://www.jalan.net/ikisaki/map/{prefecture}/'
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            hotel_urls = []
            for i in range(1, 4):
                element = soup.select_one(f'#faq-wrapper > div:nth-child(2) > div.faq-answer > ul > li:nth-child({i}) > a')
                if element:
                    href = element['href']
                    hotel_url = f'https://www.jalan.net{href}'
                    hotel_urls.append(hotel_url)
                else:
                    break



            Japanese_hotel_url = []  # リストとして初期化
            for i in range(0, 3):
                element = soup.select_one(f'#faq-wrapper > div:nth-child(3) > div.faq-answer > ul > li:nth-child({i+1}) > a')
                if element:
                    href = element['href']
                    hotel_url = f'https://www.jalan.net{href}'
                    Japanese_hotel_url.append(hotel_url)  # リストに追加
                else:
                    break

            # データベースに記録
            con = sqlite3.connect(db_name)
            cur = con.cursor()
            cur.execute('UPDATE treasure SET Number_of_pieces = ? WHERE prefectures = ?', (len(hotel_urls), prefecture))
            con.commit()
            con.close()

            # 結果を表示
            if hotel_urls:
                page.add(ft.Text(f"Found {len(hotel_urls)} hotel(s) in {prefecture}:", size=16))
                for url in hotel_urls:
                    page.add(ft.Text(url, size=14))
            else:
                page.add(ft.Text(f"No hotels found for {prefecture}.", size=16))

            if Japanese_hotel_url:
                page.add(ft.Text(f"Found {len(Japanese_hotel_url)} Japanese hotel(s) in {prefecture}:", size=16))
                for url in Japanese_hotel_url:
                    page.add(ft.Text(url, size=14))
            else:
                page.add(ft.Text(f"No Japanese hotels found for {prefecture}.", size=16))
        except Exception as ex:
            page.add(ft.Text(f"Error fetching data for {prefecture}: {ex}", color="red", size=16))

        page.update()

    # 都道府県リスト
    prefectures = [
        "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima",
        "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa",
        "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu", "shizuoka", "aichi",
        "mie", "shiga", "Kyoto", "osaka", "hyogo", "nara", "wakayama",
        "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
        "tokushima", "kagawa", "ehime", "kochi"
        "fukuoka", "saga", "nagasaki", "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
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
    ft.app(target=main)
