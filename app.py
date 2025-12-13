import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import io
import altair as alt

# --- КОНФІГУРАЦІЯ СТОРІНКИ ---
st.set_page_config(page_title="LMS ФМФКН", layout="wide", page_icon="🎓")

# --- КОНСТАНТИ ---
ADMIN_SECRET_KEY = ""

SUBJECTS_LIST = [
    "Математичний аналіз", 
    "Програмування", 
    "Аналітична геометрія", 
    "Дискретна математика", 
    "Фізика", 
    "Англійська мова", 
    "Філософія"
]

# --- ДАНІ (Студенти) ---
GROUPS_DATA = {
    "1СОМ": ["Алексєєнко Анна Олександрівна", "Гайдай Анатолій Олегович", "Журбелюк Павліна Павлівна", "Зарудняк Анастасія Сергіївна", "Книш Денис Олексійович", "Крапля Лілія Анатоліївна", "Логашкін Денис Владиславович", "Мазур Вероніка Сергіївна", "Мельник Богдан Олексійович", "Первий Андрій Миколайович", "Сулима Дарина Віталіївна", "Тимошенко Марія Миколаївна", "Шапельська Катерина Дмитрівна", "Шевчук Марія Олександрівна"],
    "1СОІ": ["Лисенко Тимофій Сергійович", "Лівий Павло Владиславович", "Муренко Степан Андрійович", "Поспелов Назар Андрійович", "Рибчук Андрій Олегович", "Томашевський Артем Васильович"],
    "1М": ["Басараба Олександр Ігорович", "Бондар Владислав Васильович", "Даньковський Нікіта Глібович", "Кокарєва Вікторія Олександрівна", "Сулима Маргаріта Андріївна", "Тишкіна Анастасія Павлівна"],
    "1СОФА": ["Генсіцька Аліна Миколаївна", "Курільченко Кіра Дмитрівна", "Мецгер Катерина Валеріївна", "Чернецька Наталія Сергіївна", "Шведун Валерій Володимирович"],
    "2СОМ": ["Адамлюк Владислав Романович", "Бичко Дар'я Юріївна", "Бугрова Юлія Вікторівна", "Бурейко Володимир Омелянович", "Гончарук Ангеліна Сергіївна", "Гріщенко Світлана Василівна", "Гунько Іван Романович", "Дорош Руслан Миколайович", "Журавель Альона Олександрович", "Зінченко Максим Олександрович", "Калінін Євген Олексійович", "Кисіль Яна Юріївна", "Киця Ярослав Володимирович", "Кравчук Юлія Юріївна", "Мартинюк Діана Сергіївна", "Назарук Діана Володимирівна", "Пасічник Софія Назарівна", "Пустовіт Анастасія Дмитрівна", "Пучкова Валерія Ігорівна", "Сичук Ангеліна Олександрівна", "Слободянюк Вікторія Вікторівна", "Стаськова Валентина Анатоліївна", "Харкевич Руслан Сергійович", "Черешня Станіслав Сергійович", "Чорна Єлизавета Миколаївна"],
    "2СОФА": ["Миколайчук Максим Олександрович", "Фурсік Марія Михайлівна"],
    "2СОІ": ["Адамов Владислав Віталійович", "Векшин Ігор Олександрович", "Діденко Артем Сергійович", "Кирилюк Ярослав Сергійович", "Кузовлєва Анастасія Сергіївна", "Новак Лілія Володимирівна", "Остапов Антон Юрійович", "Таранюк Степан Євгенійович", "Шило Гліб Олександрович", "Шпак Дар'я Володимирівна"],
    "2М": ["Блонський Владислав Ярославович", "Бондар Наталія Вікторівна", "Головата Валерія Олександрівна", "Граждан Тімур Костянтинович", "Гуцол Альона Василівна", "Левенець Владислава Дмитрівна", "Левченко Анна Миколаївна", "Миколаєнко Дмитро Олександрович", "Семенюк Ангеліна Дмитрівна", "Яцюк Вікторія Сергіївна"],
    "3СОМ": ["Винарчик Софія Степанівна", "Волинська Анна Сергіївна", "Кланцатий Костянтин Сергійович", "Крамар Анна Сергіївна", "Кузьменко Карина Леонідівна", "Лисаков Віталій Володимирович", "Лучко Анастасія Дмитрівна", "Мартиненко Владислав Ігорович", "Михайленко Вікторія Іванівна", "Нефедова Ксенія Євгеніїна", "Паплінська Ірина Петрівна", "Рудкевич Ольга Миколаївна", "Серветнік Лілія Ярославівна", "Усатюк Олександра Вадимівна", "Хованець Марʼяна Миколаївна", "Чернуха Софія Юріївна", "Шпортко Вікторія Михайлівна"],
    "3СОІ": ["Бабій Олександра Віталіївна", "Діхтяр Віталій Володимирович", "Довжок Віктор Петрович", "Казанок Єгор Михайлович", "Маковіцький Олексій Леонідович", "Письменний Сергій Васильович", "Репей Анна Сергіївна", "Станкевич Олександр Миколайович", "Стратійчук Іванна Олександрівна", "Шатковський Дмитро Петрович", "Шумило Дарина Василівна"],
    "3СОФА": ["Клапущак Богдан Віталійович", "Присяжнюк Іванна Олександрівна", "Стасюк Вадим Вольдемарович", "Теракт Дмитро Васильович", "Хіхло Ірина Валеріївна"],
    "3М": ["Бачок Микола Петрович", "Коберник Ірина Олександрівна", "Попіль Юліана Андріївна", "Семенець Вероніка Дмитрівна", "Цирульнікова Марина Віталіївна"],
    "4СОМ": ["Головата Марина Володимирівна", "Гріщенко Андрій Русланович", "Кліщ Юлія Сергіївна", "Мартинюк Анастасія Ігорівна", "Маховська Вікторія Юріївна", "Моцна Марія Анатоліївна", "Мруг Дарія Валентинівна", "Муляр Карина Сергіївна", "Неврюєва Дар'я Василівна", "Никитюк Юлія Ігорівна", "Павлова Вікторія Сергіївна", "Севастьянова Каріна Олегівна", "Струбчевська Дар'я Вячеславівна", "Тімощенко Ірина Романівна", "Фаштинська Марія Василівна", "Фурман Наталія Вікторівна", "Ходик Аліна Радіонівна", "Швець Наталія Юріївна"],
    "4СОІ": ["Барановський Нікіта Ярославович", "Вишковська Вероніка Олександрівна", "Вогник Владислав Олександрович", "Зозуля Юлія Миколаївна", "Красілич Назарій Євгенович", "Мальований Віталій Вадимович", "Пелешок Анастасія Юріївна", "Савіна Карина Дмитрівна", "Сорока Олександр Миколайович", "Табашнюк Каріна Олександрівна", "Шикір Тарас Романович"],
    "4М": ["Карнаущук Анастасія Олегівна", "Коцюбан Діана Вікторівна", "Коцюбинська Анна Олександрівна", "Саїнчук Анастасія Павлівна", "Шельман Лілія Віталіївна", "Якимчук Аліна Юріївна"],
    "4СОФА": ["Дельнецький Ігор Андрійович", "Довгаль Марина Геннадіївна", "Зозуля Софія Андріївна", "Коваленко Анна Олександрівна", "Чаленко Ольга Володимирівна"],
    "2МСОМ": ["Ворожко Вікторія Олексіївна", "Гончар Сергій Віталійович", "Дзюняк Олександр Олексійович", "Зіняк Іванна Іванівна", "Іванова Анастасія Сергіївна", "Кеба Анастасія Олександрівна", "Козярчук Катерина Миколаївна", "Лещенко Тетяна Тимурівна", "Михайлюта Олена Василівна", "Руткевич Тетяна Іванівна", "Рябуха Вероніка Олександрівна", "Сидоренко Анна Олександрівна", "Тищенко Яна Михайлівна", "Шуриняк Олександр Ігорович"],
    "2МСОФА": ["Бусел Софія Юріївна", "Гулич Наталія Русланівна", "Кульпекін Ігор Миколайович", "Миронюк Марина Анатоліївна"],
    "2МСОІ": ["Коптєв Іван Валерійович", "Косенюк Марк Володимирович", "Таскаєв Дмитро Леонідович", "Шевчук Павло Вікторович"],
    "2ММ": ["Гриценко Володимир Борисович", "Дідусенко Анастасія Вікторівна", "Кізім Степан Вадимович", "Піменов Андрій Сергійович", "Чернієнко Артем Вікторович"],
    "1МСОІ": ["Афанасьєв Дмитро Андрійович", "Брижак Владислав Анатолійович", "Вавшко Віталій Сергійович", "Кізім Степан Вадимович", "Коваленко Марічка Сергіївна", "Корольов Максим Сергійович", "Мулярчук Сергій Павлович", "Никитюк Діана Валентинівна", "Раплєв Андрій Євгенович", "Шевчук Євген Ігорович"],
    "1ММ": ["Гетманчук Анна Валентинівна", "Кухта Іванка Іванівна", "Стесюк Анастасія Ігорівна", "Воробець Анастасія Віталіївна", "Куліш Олександра Романівна", "Логвіненко Ганна Олександрівна", "Онищук Олексій Олександрович", "Юрчук Дарина Олександрівна"],
    "1МСОМ": ["Комарова Каріна Вадимівна", "Злотковська Алла Віленівна", "Таранюк Надія Василівна", "Казмірчук Валентина Вікторівна", "Остапчук Діана Олегівна", "Пашківський Богдан Олексійович", "Михайльо Лідія Олександрівна", "Торкотюк Юрій Сергійович", "Климчук Анна Олександрівна", "Дячук Єгор Сергійович", "Іськов Ігор Валерійович", "Брицова Ілона Богданівна", "Романько Олена Олександрівна", "Біла Карина Русланівна", "Антошко Марина Олександрівна", "Бондаренко Єлена Олександрівна", "Гурман Катерина Ігорівна", "Донська Анастасія Ігорівна", "Поштарук Сніжана Сергіївна", "Байда Каріна Ігорівна", "Мамчур Мирослава Дмитрівна", "Салкевич Дарина Романівна", "Семчук Олег Васильович"],
    "1МСОФА": ["Міщенко Владислав Сергійович", "Журжа Артем Арсенович", "Бережна Регіна Олександрівна", "Дмитренко Анастасія Олександрівна", "Дріма Віталій", "Олексійко Олександр Олександрович"]
}

TEACHERS_DATA = {
    "Кафедра алгебри і методики навчання математики": [
        "Коношевський Олег Леонідович (Завідувач кафедри)", "Матяш Ольга Іванівна", "Михайленко Любов Федорівна", "Воєвода Аліна Леонідівна (Декан факультету)",
        "Вотякова Леся Андріївна", "Калашніков Ігор В’ячеславович", "Наконечна Людмила Йосипівна", "Панасенко Олексій Борисович (Заступник декана)",
        "Тютюнник Діана Олегівна", "Комарова Карина Вадимівна"
    ],
    "Кафедра математики та інформатики": [
        "Ковтонюк Мар'яна Михайлівна (Завідувач кафедри)", "Бак Сергій Миколайович (Заступник декана)", "Клочко Оксана Віталіївна",
        "Граняк Валерій Федорович", "Ковтонюк Галина Миколаївна", "Косовець Олена Павлівна", "Крупський Ярослав Володимирович",
        "Соя Олена Миколаївна", "Тютюн Любов Андріївна", "Леонова Іванна Миколаївна", "Поліщук Віталій Олегович", "Ярош Оксана Іванівна"
    ],
    "Кафедра фізики і методики навчання фізики, астрономії": [
        "Сільвейстр Анатолій Миколайович (Завідувач кафедри)", "Заболотний Володимир Федорович", "Білюк Анатолій Іванович",
        "Думенко Вікторія Петрівна", "Моклюк Микола Олексійович", "Ксендзова Оксана Сергіївна", "Мамічева Інна Олексіївна",
        "Мороз Ярослав Олексійович", "Сіваєва Наталія Віталіївна", "Журжа Артем Арсенович"
    ]
}

# --- BACKEND ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text: return True
    return False

def create_connection():
    return sqlite3.connect('university_v11.db', check_same_thread=False)

def init_db():
    conn = create_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT, role TEXT, full_name TEXT, group_link TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, group_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedule(id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, day TEXT, time TEXT, subject TEXT, teacher TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, student_name TEXT, status TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS file_storage(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, file_content BLOB, upload_date TEXT, uploader TEXT, subject TEXT, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS grades(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, group_name TEXT, subject TEXT, type_of_work TEXT, grade INTEGER, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, group_name TEXT, subject TEXT, date_column TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS news(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, message TEXT, author TEXT, date TEXT)''')
    conn.commit()

    c.execute('SELECT count(*) FROM students')
    if c.fetchone()[0] == 0:
        c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)', ('admin', make_hashes('admin'), 'admin', 'Головний Адміністратор', ''))
        for group, names in GROUPS_DATA.items():
            for name in names:
                clean_name = name.lstrip("0123456789. ")
                c.execute('INSERT INTO students (full_name, group_name) VALUES (?,?)', (clean_name, group))
        conn.commit()
    return conn

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# --- СТОРІНКИ ---

def login_register_page():
    st.header("🔐 Вхід / Реєстрація")
    action = st.radio("Оберіть дію:", ["Вхід", "Реєстрація"], horizontal=True)
    conn = create_connection()
    c = conn.cursor()

    if action == "Вхід":
        username = st.text_input("Логін")
        password = st.text_input("Пароль", type='password')
        if st.button("Увійти"):
            c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, make_hashes(password)))
            user = c.fetchone()
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user[0]
                st.session_state['role'] = user[2]
                st.session_state['full_name'] = user[3]
                st.session_state['group'] = user[4]
                st.success(f"Вітаємо, {user[3]}!")
                st.rerun()
            else:
                st.error("Невірний логін або пароль")

    elif action == "Реєстрація":
        new_user = st.text_input("Вигадайте логін")
        new_pass = st.text_input("Вигадайте пароль", type='password')
        role = st.selectbox("Хто ви?", ["student", "teacher", "admin"])
        full_name = ""
        group_link = ""

        if role == "admin":
            full_name = st.text_input("ПІБ Адміністратора", value="Адміністратор")
            group_link = "Administration"
        elif role == "student":
            all_groups = list(GROUPS_DATA.keys())
            selected_group = st.selectbox("Ваша група", all_groups)
            students_in_group = pd.read_sql_query(f"SELECT full_name FROM students WHERE group_name='{selected_group}'", conn)['full_name'].tolist()
            if not students_in_group:
                 st.warning("У цій групі ще немає списків.")
                 return
            selected_name = st.selectbox("Оберіть своє ім'я", students_in_group)
            full_name = selected_name
            group_link = selected_group
        else:
            full_name = st.text_input("Ваше ПІБ (повністю)")
            group_link = "Staff"

        if st.button("Зареєструватися"):
            if new_user and new_pass and full_name:
                try:
                    c.execute('INSERT INTO users VALUES (?,?,?,?,?)', (new_user, make_hashes(new_pass), role, full_name, group_link))
                    conn.commit()
                    st.success("Успішно! Перейдіть на вкладку 'Вхід'.")
                except sqlite3.IntegrityError:
                    st.error("Цей логін вже зайнятий.")
            else:
                st.warning("Заповніть всі поля.")

def main_panel():
    st.title("🏠 Головна панель LMS")
    st.markdown(f"### Вітаємо, {st.session_state['full_name']}!")
    conn = create_connection()
    c = conn.cursor()

    st.divider()
    st.subheader("📊 Аналітика та Статистика")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    if st.session_state['role'] == 'student':
        my_group = st.session_state['group']
        group_count = pd.read_sql_query(f"SELECT count(*) FROM students WHERE group_name='{my_group}'", conn).iloc[0,0]
        kpi1.metric("Моя група", f"{group_count} студ.")
    else:
        total_students = pd.read_sql_query("SELECT count(*) FROM students", conn).iloc[0,0]
        kpi1.metric("Всього студентів", total_students)

    file_count = pd.read_sql_query("SELECT count(*) FROM file_storage", conn).iloc[0,0]
    kpi2.metric("Завантажено матеріалів", file_count)

    if st.session_state['role'] == 'student':
        avg_q = f"SELECT avg(grade) FROM grades WHERE student_name='{st.session_state['full_name']}'"
    else:
        avg_q = "SELECT avg(grade) FROM grades"
    avg_val = pd.read_sql_query(avg_q, conn).iloc[0,0]
    avg_val = round(avg_val, 1) if avg_val else 0
    kpi3.metric("Середній бал", avg_val)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("**📈 Успішність (Середній бал)**")
        if st.session_state['role'] == 'student':
            query_chart = f"SELECT subject, avg(grade) as avg_grade FROM grades WHERE student_name='{st.session_state['full_name']}' GROUP BY subject"
        else:
            query_chart = "SELECT subject, avg(grade) as avg_grade FROM grades GROUP BY subject"
        df_chart = pd.read_sql_query(query_chart, conn)
        if not df_chart.empty: st.bar_chart(df_chart.set_index('subject'))
        else: st.info("Недостатньо даних.")

    with col_chart2:
        st.markdown("**📉 Відвідуваність**")
        q_att = f"SELECT status FROM attendance WHERE student_name='{st.session_state['full_name']}'" if st.session_state['role'] == 'student' else "SELECT status FROM attendance"
        df_att = pd.read_sql_query(q_att, conn)
        if not df_att.empty:
            absent_count = df_att[df_att['status'] != ''].shape[0] 
            present_count = df_att[df_att['status'] == ''].shape[0] 
            att_data = pd.DataFrame({'Статус': ['Присутній', 'Відсутній/Інше'], 'Кількість': [present_count, absent_count]})
            base = alt.Chart(att_data).encode(theta=alt.Theta("Кількість", stack=True))
            pie = base.mark_arc(outerRadius=120).encode(color=alt.Color("Статус"), order=alt.Order("Кількість", sort="descending"), tooltip=["Статус", "Кількість"])
            st.altair_chart(pie, use_container_width=True)
        else: st.info("Дані відсутні.")

    st.divider()
    st.subheader("📢 Оголошення та Новини")
    if st.session_state['role'] in ['admin', 'teacher']:
        with st.expander("📝 Додати нове оголошення"):
            with st.form("news_form"):
                n_title = st.text_input("Заголовок новини")
                n_msg = st.text_area("Текст оголошення")
                if st.form_submit_button("Опублікувати"):
                    if n_title and n_msg:
                        date_pub = datetime.now().strftime("%Y-%m-%d %H:%M")
                        c.execute("INSERT INTO news (title, message, author, date) VALUES (?,?,?,?)", (n_title, n_msg, st.session_state['full_name'], date_pub))
                        conn.commit()
                        st.success("Новину опубліковано!")
                        st.rerun()
    news_df = pd.read_sql_query("SELECT title, message, author, date FROM news ORDER BY id DESC", conn)
    if not news_df.empty:
        for i, row in news_df.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['title']}")
                st.write(row['message'])
                st.caption(f"🗓️ {row['date']} | ✍️ {row['author']}")
    else: st.info("Наразі немає актуальних оголошень.")

def students_groups_view():
    st.title("👥 Студенти та Групи")
    conn = create_connection()
    all_groups = ["Всі"] + list(GROUPS_DATA.keys())
    selected_group = st.selectbox("Фільтр по групі:", all_groups)
    query = "SELECT id, full_name as 'ПІБ', group_name as 'Група' FROM students"
    if selected_group != "Всі": query += f" WHERE group_name='{selected_group}'"
    df = pd.read_sql_query(query, conn)
    csv = convert_df_to_csv(df)
    st.download_button("⬇️ Експортувати (CSV)", csv, "students.csv", "text/csv")
    st.dataframe(df, use_container_width=True)
    if st.session_state['role'] in ['admin', 'teacher']:
        st.divider()
        st.subheader("🛠️ Управління")
        t1, t2, t3 = st.tabs(["➕ Додати", "📥 Імпорт", "🗑️ Видалити"])
        with t1:
            with st.form("add_s"):
                nm = st.text_input("ПІБ")
                gr = st.selectbox("Група", list(GROUPS_DATA.keys()))
                if st.form_submit_button("Додати"):
                    c = conn.cursor()
                    c.execute('INSERT INTO students (full_name, group_name) VALUES (?,?)', (nm, gr))
                    conn.commit()
                    st.success("Додано!")
                    st.rerun()
        with t2:
            if st.session_state['role'] == 'admin':
                f = st.file_uploader("CSV (full_name, group_name)", type="csv")
                if f:
                    try:
                        df_new = pd.read_csv(f)
                        df_new[['full_name', 'group_name']].to_sql('students', conn, if_exists='append', index=False)
                        st.success("Імпортовано!")
                        st.rerun()
                    except Exception as e: st.error(f"Помилка: {e}")
        with t3:
            if st.session_state['role'] == 'admin':
                ids = pd.read_sql("SELECT id, full_name FROM students", conn)
                s_del = st.selectbox("Студент", ids.apply(lambda x: f"{x['id']}: {x['full_name']}", axis=1))
                if st.button("Видалити"):
                    sid = int(s_del.split(":")[0])
                    conn.execute("DELETE FROM students WHERE id=?", (sid,))
                    conn.commit()
                    st.success("Видалено")
                    st.rerun()

def teachers_view():
    st.title("👨‍🏫 Викладачі")
    for dept, teachers in TEACHERS_DATA.items():
        with st.expander(f"📚 {dept}"):
            for t in teachers: st.write(f"- {t}")

def schedule_view():
    st.title("📅 Розклад")
    conn = create_connection()
    grp = st.selectbox("Група", list(GROUPS_DATA.keys()))
    df = pd.read_sql_query(f"SELECT day, time, subject, teacher FROM schedule WHERE group_name='{grp}'", conn)
    if not df.empty: 
        st.download_button("⬇️ Завантажити", convert_df_to_csv(df), f"schedule_{grp}.csv", "text/csv")
        st.table(df)
    else: st.info("Пусто")
    if st.session_state['role'] in ['admin', 'teacher']:
        st.divider()
        with st.form("sch"):
            d = st.selectbox("День", ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"])
            t = st.selectbox("Час", ["08:30", "10:10", "11:50", "13:30"])
            s = st.text_input("Предмет")
            tch = st.text_input("Викладач", value=st.session_state['full_name'])
            if st.form_submit_button("Додати"):
                conn.execute("INSERT INTO schedule (group_name, day, time, subject, teacher) VALUES (?,?,?,?,?)", (grp, d, t, s, tch))
                conn.commit()
                st.rerun()

def documents_view():
    st.title("📂 Документи")
    menu = ["Мої заяви", "Створити"]
    c = st.selectbox("Меню", menu)
    conn = create_connection()
    if c == "Створити":
        t = st.selectbox("Тип", ["Довідка", "Заява"])
        if st.button("Надіслати"):
            conn.execute("INSERT INTO documents (title, student_name, status, date) VALUES (?,?,?,?)", (t, st.session_state['full_name'], "Очікує", str(datetime.now().date())))
            conn.commit()
            st.success("Надіслано")
    else:
        q = f"SELECT * FROM documents WHERE student_name='{st.session_state['full_name']}'" if st.session_state['role'] == 'student' else "SELECT * FROM documents"
        st.dataframe(pd.read_sql(q, conn), use_container_width=True)

def file_repository_view():
    st.title("🗄️ Файловий Репозиторій")
    conn = create_connection()
    c = conn.cursor()
    col_f1, col_f2 = st.columns([2,1])
    with col_f1: filter_subj = st.selectbox("📂 Фільтр по предмету", ["Всі"] + SUBJECTS_LIST)
    if st.session_state['role'] in ['admin', 'teacher']:
        with st.expander("📤 Завантажити"):
            with st.form("upload_form"):
                uploaded_file = st.file_uploader("Файл", accept_multiple_files=False)
                f_subject = st.selectbox("Предмет", SUBJECTS_LIST)
                f_desc = st.text_input("Опис")
                if st.form_submit_button("Зберегти"):
                    if uploaded_file and f_desc:
                        c.execute("INSERT INTO file_storage (filename, file_content, upload_date, uploader, subject, description) VALUES (?,?,?,?,?,?)",
                                  (uploaded_file.name, uploaded_file.read(), datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state['full_name'], f_subject, f_desc))
                        conn.commit()
                        st.success("Збережено!")
                        st.rerun()
    query = "SELECT id, filename, subject, description, upload_date, uploader FROM file_storage"
    if filter_subj != "Всі": query += f" WHERE subject='{filter_subj}'"
    df_files = pd.read_sql_query(query, conn)
    if not df_files.empty:
        for s in df_files['subject'].unique():
            st.subheader(f"📘 {s}")
            for i, row in df_files[df_files['subject'] == s].iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 4, 2, 1])
                    c1.write(f"📄 **{row['filename']}**")
                    c2.write(f"📝 {row['description']}")
                    c3.caption(f"{row['uploader']}")
                    data = c.execute("SELECT file_content FROM file_storage WHERE id=?", (row['id'],)).fetchone()[0]
                    c3.download_button("⬇️", data, row['filename'], key=f"d{row['id']}")
                    if st.session_state['role'] == 'admin':
                        if c4.button("🗑️", key=f"del_{row['id']}"):
                            c.execute("DELETE FROM file_storage WHERE id=?", (row['id'],))
                            conn.commit()
                            st.rerun()
    else: st.info("Пусто")

def gradebook_view():
    st.title("💯 Журнал Оцінок")
    conn = create_connection()
    c = conn.cursor()
    if st.session_state['role'] == 'student':
        df = pd.read_sql(f"SELECT subject, type_of_work, grade, date FROM grades WHERE student_name='{st.session_state['full_name']}'", conn)
        st.dataframe(df, use_container_width=True)
    else:
        t_journal, t_ops = st.tabs(["Журнал", "📥/📤 Операції"])
        c1, c2 = st.columns(2)
        grp = c1.selectbox("Група", list(GROUPS_DATA.keys()))
        subj = c2.selectbox("Предмет", SUBJECTS_LIST)
        with t_journal:
            with st.expander("➕ Додати колонку"):
                with st.form("new_col"):
                    nm = st.text_input("Назва")
                    dt = st.date_input("Дата")
                    if st.form_submit_button("Створити"):
                        stds = pd.read_sql(f"SELECT full_name FROM students WHERE group_name='{grp}'", conn)['full_name'].tolist()
                        for s in stds:
                            c.execute("INSERT INTO grades (student_name, group_name, subject, type_of_work, grade, date) VALUES (?,?,?,?,?,?)", (s, grp, subj, nm, 0, str(dt)))
                        conn.commit()
                        st.rerun()
            raw = pd.read_sql(f"SELECT student_name, type_of_work, grade FROM grades WHERE group_name='{grp}' AND subject='{subj}'", conn)
            if not raw.empty:
                matrix = raw.pivot_table(index='student_name', columns='type_of_work', values='grade', aggfunc='first').fillna(0)
                edited = st.data_editor(matrix, use_container_width=True)
                if st.button("Зберегти зміни"):
                    for s_name, row in edited.iterrows():
                        for w_name, val in row.items():
                            exists = c.execute("SELECT id FROM grades WHERE student_name=? AND subject=? AND type_of_work=?", (s_name, subj, w_name)).fetchone()
                            if exists: c.execute("UPDATE grades SET grade=? WHERE id=?", (val, exists[0]))
                    conn.commit()
                    st.success("Збережено!")
            else: st.info("Додайте колонку.")
        with t_ops:
            raw_export = pd.read_sql(f"SELECT * FROM grades WHERE group_name='{grp}' AND subject='{subj}'", conn)
            st.download_button("⬇️ Експорт (Raw)", convert_df_to_csv(raw_export), "grades_raw.csv", "text/csv")
            if not raw.empty: st.download_button("⬇️ Експорт (Matrix)", convert_df_to_csv(matrix), "grades_matrix.csv", "text/csv")
            
            up_grades = st.file_uploader("Імпорт оцінок (CSV)", type="csv")
            if up_grades and st.button("Імпортувати"):
                try:
                    df_new = pd.read_csv(up_grades)
                    df_new.to_sql('grades', conn, if_exists='append', index=False)
                    st.success("Імпортовано!")
                except Exception as e: st.error(f"Помилка: {e}")

def attendance_view():
    st.title("📝 Журнал Відвідуваності")
    conn = create_connection()
    if st.session_state['role'] == 'student':
        df_att = pd.read_sql(f"SELECT subject, date_column as 'Дата', status FROM attendance WHERE student_name='{st.session_state['full_name']}'", conn)
        st.dataframe(df_att, use_container_width=True)
    else:
        c1, c2 = st.columns(2)
        grp = c1.selectbox("Група", list(GROUPS_DATA.keys()), key="att_grp")
        subj = c2.selectbox("Предмет", SUBJECTS_LIST, key="att_sbj")
        with st.expander("➕ Додати дату"):
            with st.form("new_att_col"):
                col_name = st.text_input("Назва")
                if st.form_submit_button("Створити"):
                    stds = pd.read_sql(f"SELECT full_name FROM students WHERE group_name='{grp}'", conn)['full_name'].tolist()
                    for s in stds:
                        conn.execute("INSERT INTO attendance (student_name, group_name, subject, date_column, status) VALUES (?,?,?,?,?)", (s, grp, subj, col_name, "")) 
                    conn.commit()
                    st.rerun()
        raw = pd.read_sql(f"SELECT student_name, date_column, status FROM attendance WHERE group_name='{grp}' AND subject='{subj}'", conn)
        if not raw.empty:
            matrix = raw.pivot_table(index='student_name', columns='date_column', values='status', aggfunc='first').fillna("")
            st.write("Ставте 'н' для відсутніх:")
            edited = st.data_editor(matrix, use_container_width=True)
            if st.button("💾 Зберегти"):
                for s_name, row in edited.iterrows():
                    for d_col, val in row.items():
                        exists = conn.execute("SELECT id FROM attendance WHERE student_name=? AND subject=? AND date_column=?", (s_name, subj, d_col)).fetchone()
                        if exists: conn.execute("UPDATE attendance SET status=? WHERE id=?", (val, exists[0]))
                conn.commit()
                st.success("Збережено!")
        else: st.info("Пусто.")

# --- НОВА СТОРІНКА ЗВІТІВ ---
def reports_view():
    st.title("📊 Звіти та Пошук")
    conn = create_connection()
    t1, t2, t3 = st.tabs(["📋 Відомість (Група/Предмет)", "🎓 Картка Студента", "📈 Зведена відомість"])
    
    with t1:
        st.subheader("Формування відомості")
        c1, c2 = st.columns(2)
        grp = c1.selectbox("Група", list(GROUPS_DATA.keys()), key="rep_grp")
        subj = c2.selectbox("Предмет", SUBJECTS_LIST, key="rep_subj")
        
        raw = pd.read_sql(f"SELECT student_name, type_of_work, grade FROM grades WHERE group_name='{grp}' AND subject='{subj}'", conn)
        if not raw.empty:
            matrix = raw.pivot_table(index='student_name', columns='type_of_work', values='grade', aggfunc='first').fillna(0)
            st.dataframe(matrix, use_container_width=True)
            st.download_button("⬇️ Завантажити відомість", convert_df_to_csv(matrix), f"vidomist_{grp}_{subj}.csv", "text/csv")
        else: st.warning("Дані відсутні.")

    with t2:
        st.subheader("Пошук студента")
        all_students = pd.read_sql("SELECT full_name FROM students", conn)
        if not all_students.empty:
            selected_student = st.selectbox("Оберіть студента", all_students['full_name'].tolist())
            
            # Інформація
            info = pd.read_sql(f"SELECT * FROM students WHERE full_name='{selected_student}'", conn)
            st.write("**Інформація:**")
            st.dataframe(info, use_container_width=True)
            
            # Оцінки
            grades = pd.read_sql(f"SELECT subject, type_of_work, grade, date FROM grades WHERE student_name='{selected_student}'", conn)
            st.write("**Оцінки:**")
            if not grades.empty:
                st.dataframe(grades, use_container_width=True)
                st.metric("Середній бал", f"{grades['grade'].mean():.2f}")
                st.download_button("⬇️ Скачати виписку оцінок", convert_df_to_csv(grades), f"grades_{selected_student}.csv", "text/csv")
            else: st.info("Оцінок немає.")
        else: st.error("База студентів порожня.")

    with t3:
        st.subheader("Генератор Зведеної Відомості")
        grp_sum = st.selectbox("Оберіть групу", list(GROUPS_DATA.keys()), key="rep_sum_grp")
        
        # Визначаємо доступні предмети для цієї групи
        available_subjects_query = f"SELECT DISTINCT subject FROM grades WHERE group_name='{grp_sum}'"
        available_subjects = pd.read_sql(available_subjects_query, conn)['subject'].tolist()
        
        if not available_subjects:
            available_subjects = SUBJECTS_LIST
            
        selected_subjects = st.multiselect("Оберіть предмети для відомості", options=available_subjects, default=available_subjects)
        
        if st.button("🔄 Згенерувати таблицю"):
            if selected_subjects:
                subjects_placeholder = "'" + "','".join(selected_subjects) + "'"
                query = f"""
                    SELECT student_name, subject, AVG(grade) as final_grade 
                    FROM grades 
                    WHERE group_name='{grp_sum}' AND subject IN ({subjects_placeholder})
                    GROUP BY student_name, subject
                """
                data = pd.read_sql(query, conn)
                
                if not data.empty:
                    summary_matrix = data.pivot_table(index='student_name', columns='subject', values='final_grade').fillna(0).round(0).astype(int)
                    # Додаємо повний список студентів
                    all_students_df = pd.read_sql(f"SELECT full_name FROM students WHERE group_name='{grp_sum}'", conn)
                    summary_matrix = all_students_df.merge(summary_matrix, left_on='full_name', right_index=True, how='left').fillna(0)
                    summary_matrix.set_index('full_name', inplace=True)
                    
                    st.success(f"Згенеровано відомість для групи {grp_sum}")
                    st.dataframe(summary_matrix, use_container_width=True)
                    
                    st.download_button(
                        label="⬇️ Завантажити таблицю (CSV)",
                        data=convert_df_to_csv(summary_matrix),
                        file_name=f"zvedena_vidomist_{grp_sum}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Для обраних предметів оцінки відсутні.")
            else:
                st.error("Будь ласка, оберіть хоча б один предмет.")

def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['role'] = None
        st.session_state['full_name'] = ""

    if not st.session_state['logged_in']:
        login_register_page()
    else:
        st.sidebar.title(f"👤 {st.session_state['full_name']}")
        st.sidebar.caption(f"Роль: {st.session_state['role']}")
        st.sidebar.divider()
        menu_options = {
            "Головна панель": main_panel,
            "Студенти та Групи": students_groups_view,
            "Викладачі та Кафедри": teachers_view,
            "Розклад занять": schedule_view,
            "Електронний журнал": gradebook_view,
            "Журнал відвідуваності": attendance_view,
            "Звіти та Пошук": reports_view, # <-- Нова сторінка
            "Документообіг": documents_view,
            "Файловий репозиторій": file_repository_view
        }
        selection = st.sidebar.radio("Навігація", list(menu_options.keys()))
        menu_options[selection]()
        st.sidebar.divider()
        if st.sidebar.button("Вийти"):
            st.session_state['logged_in'] = False
            st.rerun()

if __name__ == '__main__':
    main()
