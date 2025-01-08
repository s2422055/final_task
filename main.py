import requests
import sqlite3
import os
import json
import time
from bs4 import BeautifulSoup
import pandas as pd
import flet as ft

db_name = "final_task.db"

# final_task.dbという名前のデータベースファイルを作成する
if not os.path.exists(db_name):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    sql = 'CREATE TABLE IF NOT EXISTS treasure (prefectures INTEGER PRIMARY KEY, Number_of_pieces int)'
    sql2 = 'CREATE TABLE IF NOT EXISTS evaluation (prefectures INTEGER PRIMARY KEY, price int, evaluation int)'
    cur.execute(sql)
    cur.execute(sql2)
    con.close()


def main(page: ft.Page):
    page.add(ft.SafeArea(ft.Text("Hello, Flet!")))


ft.app(main)