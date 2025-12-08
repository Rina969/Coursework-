from telebot import types
import sqlite3 as sq

bot= telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

#-----------------admin--------------------------
#------------------------------------------------
def add_studio:
    with sq.connect("student_studios_bot (1).db") as con:
        cur=con.cursor()

#Добавляем пока первичную информацию о студии
        cur.execute("""INSERT into studios name promo_photo_id promo_video_id description contacts """)

        con.commit()
        con.close()

