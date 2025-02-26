import psycopg2
import csv

# Подключение к базе данных
connection = psycopg2.connect(
    host="localhost",
    database="session1",
    user="postgres",
    password="postgres",
)
cursor = connection.cursor()

def insert_possts():
    try:
        with open("possts.csv", "r", encoding="utf_8") as file:
            reader = csv.reader(file)
            for row in reader:
                cursor.execute('INSERT INTO public."Posts"(post_name) VALUES (%s)', (row[1],))
            else:
                print("error")
            connection.commit()
            print("good")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        connection.close()

def insert_deports():
    try:
        with open("deports.csv", "r", encoding="utf_8")as file:
            reader = csv.reader(file)
            for row in reader:
                # if len(row) >=2:
                    cursor.execute('INSERT INTO public."Departs"(departs_name) VALUES (%s)', (row[1],))
            else:
                print("123")
        connection.commit()
        print("Good")
    except Exception as e:
        
        print(e)
    finally:
        cursor.close()
        connection.close()        

def insert_rooms():
    try:
        with open('rooms.csv', 'r', encoding="utf_8") as file:
            reader = csv.reader(file)
            
            # # Пропускаем заголовок (если он есть)
            # next(reader, None)
            
            # Вставляем каждую строку в таблицу
            for row in reader:
                # Проверяем, что строка содержит достаточно данных
                if len(row) >= 2:
                    cursor.execute(
                        'INSERT INTO public."Rooms"(room_name) VALUES (%s)',
                        (row[1],)
                    )
                else:
                    print(f"Пропущена строка: {row} (недостаточно данных)")
        
        # Фиксируем изменения в базе данных
        connection.commit()
        print("Данные успешно вставлены!")

    except Exception as e:
        # Откатываем транзакцию в случае ошибки
        if connection:
            connection.rollback()
        print(f"Произошла ошибка: {e}")

    finally:
        # Закрываем курсор и соединение
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
def insert_subpost():
    try:
        with open("subposts.csv", "r", encoding="utf_8") as file:
            reader = csv.reader(file)
            
            for row in reader:
                cursor.execute('INSERT INTO public."Subdeparts"(depart_id, subdepart_name) VALUES (%s, %s)', (row[1], row[2]))
            connection.commit()
            print("good")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        connection.close()
        
def insert_subsubdeparts():
    try:
        with open("subsubdepars.csv", "r", encoding="utf_8") as file:
            reader = csv.reader(file)
            
            for row in reader:
                cursor.execute('INSERT INTO public."Subsubdeparts"(subdepart_id, subsubdepart_name)VALUES (%s, %s)', (row[0], row[1]))
            connection.commit()
            print("good")
            
    except Exception as e:
        print(e)
        
    finally:
        cursor.close()
        connection.close()
        
def insert_stuffs():
    try:
        with open("stufs.csv", "r", encoding="utf_8") as file:
            reader = csv.reader(file)
            
            for row in reader:
                processed_row = [
                    None if value.strip() == "" else value
                    for value in row
                ]
                cursor.execute('INSERT INTO public."Stuffs"(name, phone, date, room_id, depart_id, subdepart_id, post_id) VALUES (%s, %s, %s, %s, %s, %s, %s)', (row[0], row[2], row[1], row[3],row[4], row[5], row[7]))
            connection.commit()
            print("good")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        connection.close()
        
# Запуск функции
# insert_rooms()
# insert_deports(#)
insert_subsubdeparts()
#insert_stuffs()