import requests
import sqlite3
import os
import csv
from bs4 import BeautifulSoup
import flet as ft
import matplotlib.pyplot as plt
import numpy as np
import io
from scipy.stats import pearsonr

# データベースファイルの名前
db_name = "final_task.db"

# データベースのセットアップ
if not os.path.exists(db_name):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
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
        "mie", "shiga", "kyoto", "oosaka", "hyogo", "nara", "wakayama",
        "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
        "tokushima", "kagawa", "ehime", "kochi",
        "fukuoka", "saga", "nagasaki", "kumamoto", "ooita", "miyazaki", "kagoshima", "okinawa"
    ]
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    for pref in prefectures:
        # 重複する場合は書き換える
        cur.execute('INSERT OR REPLACE INTO treasure (prefectures, national_treasure, important_cultural_property, important_cultural_landscape, important_traditional_buildings) VALUES (?, 0, 0, 0, 0)', (pref,))
        cur.execute('INSERT OR REPLACE INTO evaluation (prefectures, evaluation_score) VALUES (?, 0)', (pref,))
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
    try:
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

        japanese_hotel_urls = []
        for i in range(0, 3):
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

            content = [
                ft.Text(f"Found {len(hotel_urls)} hotel(s) in {prefecture}:"),
                *[ft.Text(url) for url in hotel_urls],
                ft.Text(f"Evaluation data has been stored in the database for {prefecture}.")
            ]
            page.add(ft.Column(content, spacing=10))
        except Exception as ex:
            page.add(ft.Text(f"Error fetching data for {prefecture}: {ex}", color="red"))
        page.update()

    def on_reset_click(e):
        # 出力結果を削除するためにページの内容をリセット
        selected_text.value = ""  # 選択した都道府県のテキストを消す
        page.controls.clear()  # 現在のページ上のすべてのコンテンツを削除
        main(page)  # ページに再度UI要素を追加
        page.update()  # ページを再描画してリセット後の状態を表示

    def on_view_data_click(e):
        # データベースからデータを取得して表示
        with sqlite3.connect(db_name) as con:
            cur = con.cursor()
            cur.execute("SELECT prefectures, evaluation_score FROM evaluation")
            rows = cur.fetchall()
            content = [ft.Text(f"Data from Database:")]
            for row in rows:
                content.append(ft.Text(f"{row[0]}: {row[1]}"))
            page.add(ft.Column(content, spacing=10))
        page.update()

    def on_compare_click(e):
        # evaluationテーブルのevaluation_scoreを数字の高い順で表示
        with sqlite3.connect(db_name) as con:
            cur = con.cursor()
            cur.execute("SELECT prefectures, evaluation_score FROM evaluation ORDER BY evaluation_score DESC")
            evaluation_rows = cur.fetchall()
            evaluation_content = [ft.Text(f"Evaluation Scores (High to Low):")]
            for row in evaluation_rows:
                evaluation_content.append(ft.Text(f"{row[0]}: {row[1]}"))
            page.add(ft.Column(evaluation_content, spacing=10))

            # treasureテーブルのimportant_cultural_propertyを数字の高い順で表示
            cur.execute("SELECT prefectures, important_cultural_property FROM treasure ORDER BY important_cultural_property DESC")
            treasure_rows = cur.fetchall()
            treasure_content = [ft.Text(f"Important Cultural Properties (High to Low):")]
            for row in treasure_rows:
                treasure_content.append(ft.Text(f"{row[0]}: {row[1]}"))
            page.add(ft.Column(treasure_content, spacing=10))

            # 重要文化財の数とホテル評価の相関計算
            prefectures = [row[0] for row in treasure_rows]  # 都道府県リスト
            cultural_properties = [row[1] for row in treasure_rows]  # 重要文化財の数
            evaluations = [row[1] for row in evaluation_rows]  # ホテルの評価スコア

            # 相関計算
            correlation, _ = pearsonr(cultural_properties, evaluations)
            page.add(ft.Text(f"ピアソンの相関係数: {correlation:.2f}"))

            # 散布図を描画
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(cultural_properties, evaluations, c='blue', alpha=0.6)
            ax.set_xlabel("Important Cultural Properties")
            ax.set_ylabel("Hotel Evaluation")
            ax.set_title("Scatter Plot: Important Cultural Properties vs Hotel Evaluation")

            # グラフを画像としてページに表示
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png')
            img_buf.seek(0)

            img = ft.Image(src=img_buf)
            page.add(img)

        page.update()

    # サイドバー作成
    sidebar = ft.Column([
        ft.ElevatedButton(text="Reset", on_click=on_reset_click),
        ft.ElevatedButton(text="View Past Data", on_click=on_view_data_click),
        ft.ElevatedButton(text="Compare", on_click=on_compare_click),
    ])

    # 都道府県ボタンを行ごとに配置
    prefectures = [
        "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima", "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa", "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu", "shizuoka", "aichi",
        "mie", "shiga", "kyoto", "oosaka", "hyogo", "nara", "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi", "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki", "kumamoto", "ooita", "miyazaki", "kagoshima", "okinawa"
    ]

    button_rows = []
    for i in range(0, len(prefectures), 5):  # 1行に5個のボタン
        row_buttons = [
            ft.ElevatedButton(text=pref, on_click=on_button_click)
            for pref in prefectures[i:i+5]
        ]
        button_rows.append(ft.Row(row_buttons, spacing=10))

    # UI要素をページに追加
    page.add(
        ft.Row([sidebar, ft.Column([
            ft.Text("Select a prefecture:", size=24, weight=ft.FontWeight.BOLD),
            *button_rows,
            selected_text
        ], spacing=20)])
    )

if __name__ == "__main__":
    # CSVファイルからデータを読み込む
    csv_file = 'final_task/final_data.csv'
    if os.path.exists(csv_file):
        load_data_from_csv(csv_file)
    else:
        print(f"CSV file '{csv_file}' not found.")
    ft.app(target=main)
