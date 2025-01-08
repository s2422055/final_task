import requests
import sqlite3
import os
import json
import time
from bs4 import BeautifulSoup
import pandas as pd
import flet as ft

# データベースファイルの名前
db_name = "final_task.db"

# データベースファイルを作成
if not os.path.exists(db_name):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    sql = 'CREATE TABLE IF NOT EXISTS treasure (prefectures INTEGER PRIMARY KEY, Number_of_pieces int)'
    sql2 = 'CREATE TABLE IF NOT EXISTS evaluation (prefectures INTEGER PRIMARY KEY, price int, evaluation int)'
    cur.execute(sql)
    cur.execute(sql2)
    con.close()

def main(page: ft.Page):
    page.title = "Prefecture Selection"
    page.scroll = ft.ScrollMode.AUTO

    # 選択された都道府県を表示するテキスト
    selected_text = ft.Text(value="", size=20, weight=ft.FontWeight.BOLD)

    # ボタンがクリックされたときの処理
    def on_button_click(e):
        selected_text.value = f"Selected prefecture: {e.control.text}"
        page.update()

    # 都道府県リスト
    prefectures = [
        "Hokkaido", "Aomori", "Iwate", "Miyagi", "Akita", "Yamagata", "Fukushima",
        "Ibaraki", "Tochigi", "Gunma", "Saitama", "Chiba", "Tokyo", "Kanagawa",
        "Niigata", "Toyama", "Ishikawa", "Fukui", "Yamanashi", "Nagano", "Gifu", "Shizuoka", "Aichi",
        "Mie", "Shiga", "Kyoto", "Osaka", "Hyogo", "Nara", "Wakayama",
        "Tottori", "Shimane", "Okayama", "Hiroshima", "Yamaguchi",
        "Tokushima", "Kagawa", "Ehime", "Kochi",
        "Fukuoka", "Saga", "Nagasaki", "Kumamoto", "Oita", "Miyazaki", "Kagoshima", "Okinawa"
    ]

    # 都道府県ボタンを行ごとに配置
    button_rows = []
    for i in range(0, len(prefectures), 6):  # 1行に8個のボタン
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
