import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import io
import altair as alt
import re

# --- КОНФІГУРАЦІЯ СТОРІНКИ ---
st.set_page_config(page_title="LMS ФМФКН - Адміністрація", layout="wide", page_icon="🎓")

# --- ЛОГІКА ПЕРЕМИКАННЯ ТЕМИ ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# --- CSS СТИЛІ ---
dark_css = """
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #262730; }
    h1, h2, h3, h4, h5, h6, p, li, span, label, .stMarkdown { color: #FFFFFF !important; }
    .stTextInput > div > div, .stSelectbox > div > div, .stTextArea > div > div, .stDateInput > div > div, .stNumberInput > div > div {
        background-color: #41444C !important; color: #FFFFFF !important;
    }
    input, textarea { color: #FFFFFF !important; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { color: #FFFFFF !important; }
    .streamlit-expanderHeader { background-color: #262730 !important; color: #FFFFFF !important; }
    button { color: #FFFFFF !important; }
</style>
"""

light_css = """
<style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    [data-testid="stSidebar"] { background-color: #F0F2F6; }
    h1, h2, h3, h4, h5, h6, p, li, span, label, .stMarkdown { color: #000000 !important; }
    .stTextInput > div > div, .stSelectbox > div > div, .stTextArea > div > div, .stDateInput > div > div, .stNumberInput > div > div {
        background-color: #FFFFFF !important; color: #000000 !important; border: 1px solid #D3D3D3;
    }
    input, textarea { color: #000000 !important; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { color: #000000 !important; }
    .streamlit-expanderHeader { background-color: #F0F2F6 !important; color: #000000 !important; }
    button { color: #000000 !important; }
</style>
"""

if st.session_state.theme == 'dark':
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    st.markdown(light_css, unsafe_allow_html=True)

# --- КОНСТАНТИ ТА ПРАВА ДОСТУПУ ---
ROLES_LIST = ["student", "starosta", "teacher", "methodist", "dean", "admin"]
TEACHER_LEVEL = ['teacher', 'methodist', 'dean', 'admin']
DEAN_LEVEL = ['methodist', 'dean', 'admin']

SUBJECTS_LIST = [
    "Математичний аналіз", "Програмування", "Аналітична геометрія", "Дискретна математика", 
    "Фізика", "Англійська мова", "Філософія", "Числові системи", "Елементарна математика", 
    "Шкільний курс алгебри", "Шкільний курс геометрії", "Основи алгебри і дискретної математики", 
    "Лінійна алгебра і дискретна математика", "Вступ до спеціальності", "Основи статистики і аналізу даних", 
    "Експериментальна фізика", "Алгебра і теорія чисел", "Загальна психологія", "Інформатика", 
    "Основи структурного та об'єктно-орієнтованого програмування", "Загальна фізика", 
    "Методика виховної роботи", "Технології навчання фізики та інформатики", "Системи керування базами даних", 
    "Диференціальні рівняння", "Функціональний аналіз", "Бази даних та інформаційні системи", 
    "Методика навчання інформатики", "Методика навчання математики", "Алгоритми і структури даних", 
    "Основи педагогічної майстерності", "Теоретична фізика", "Інтегральні рівняння і варіаційне числення", 
    "Методика навчання фізики", "Методи обчислень", "Теорія і методика поглибленого навчання стереометрії", 
    "Фізика та методика її навчання у ліцеях", "Системи комп'ютерної математики", 
    "Теорія і практика математичних олімпіад", "Додаткові розділи геометрії", "Педагогіка і психологія вищої школи", 
    "Методологія та цифрові технології наукових досліджень у математиці", "Машинне навчання в освіті", 
    "Вибрані питання сучасної дидактики фізики", "Педагогіка і психологія профільної середньої освіти", 
    "Вибрані питання вищої математики", "Теорія і методика поглибленого навчання алгебри і початків аналізу", 
    "Астрофізика", "Цивільний захист", "Математичні моделі і моделі в освіті/педагогіці", 
    "Практикум з фізичного експерименту", "Статистичні методи обробки експериментальних даних", 
    "Основи теорії солітонів", "Ймовірнісно-статистичні методи досліджень", "Основи машинного навчання", 
    "Основи штучного інтелекту", "Загальна фізика. Оптика", "Практикум розв'язування задач з оптики", 
    "Практикум розв'язування олімпіадних задач з алгебри", "Основи теорії інтелектуальних систем"
]

GROUPS_DATA = {
    "1СОМ": ["Алексєєнко Анна Олександрівна", "Гайдай Анатолій Олегович", "Журбелюк Павліна Павлівна", "Зарудняк Анастасія Сергіївна", "Книш Денис Олексійович", "Крапля Лілія Анатоліївна", "Логашкін Денис Владиславович", "Мазур Вероніка Сергіївна", "Мельник Богдан Олексійович", "Первий Андрій Миколайович", "Сулима Дарина Віталіївна", "Тимошенко Марія Миколаївна", "Шапельська Катерина Дмитрівна", "Шевчук Марія Олександрівна"],
    "1СОІ": ["Лисенко Тимофій Сергійович", "Лівий Павло Владиславович", "Муренко Степан Андрійович", "Поспелов Назар Андрійович", "Рибчук Андрій Олегович", "Томашевський Артем Васильович"],
    "1М": ["Басараба Олександр Ігорович", "Бондар Владислав Васильович", "Даньковський Нікіта Глібович", "Кокарєва Вікторія Олександрівна", "Сулима Маргаріта Андріївна", "Тишкіна Анастасія Павлівна"],
    "2СОМ": ["Адамлюк Владислав Романович", "Бичко Дар'я Юріївна", "Бугрова Юлія Вікторівна", "Бурейко Володимир Омелянович", "Гончарук Ангеліна Сергіївна"],
    "2МСОМ": ["Ворожко Вікторія Олексіївна", "Гончар Сергій Віталійович", "Дзюняк Олександр Олексійович", "Зіняк Іванна Іванівна"]
}

TEACHERS_DATA = {
    "Кафедра алгебри і методики навчання математики": ["Коношевський Олег Леонідович", "Матяш Ольга Іванівна", "Михайленко Любов Федорівна", "Воєвода Аліна Леонідівна", "Панасенко Олексій Борисович"],
    "Кафедра математики та інформатики": ["Ковтонюк Мар'яна Михайлівна", "Бак Сергій Миколайович", "Клочко Оксана Віталіївна"],
    "Кафедра фізики і методики навчання": ["Сільвейстр Анатолій Миколайович", "Заболотний Володимир Федорович", "Білюк Анатолій Іванович"]
}

# --- BACKEND ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_connection():
    return sqlite3.connect('university_final_v1.db', check_same_thread=False)

def log_action(user, action, details):
    conn = create_connection()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO system_logs (user, action, details, timestamp) VALUES (?,?,?,?)", (user, action, details, ts))
    conn.commit()

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

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
    c.execute('''CREATE TABLE IF NOT EXISTS dormitory(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, room_number TEXT, payment_status TEXT, comments TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scholarship(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, type TEXT, amount INTEGER, status TEXT, date_assigned TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS system_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, details TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_education_info(student_name TEXT PRIMARY KEY, status TEXT, study_form TEXT, course INTEGER, is_contract TEXT, faculty TEXT, specialty TEXT, edu_program TEXT, enroll_order_num TEXT, enroll_date TEXT, student_id_card TEXT, last_modified TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_prev_education(student_name TEXT PRIMARY KEY, institution_name TEXT, institution_type TEXT, diploma_type TEXT, diploma_series TEXT, diploma_number TEXT, diploma_grades_summary TEXT, foreign_languages TEXT, last_modified TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS academic_certificates(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, cert_number TEXT, issue_date TEXT, source_institution TEXT, notes TEXT, added_by TEXT, added_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS individual_statements(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, subject TEXT, statement_type TEXT, reason TEXT, date_issued TEXT, status TEXT, created_by TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_contracts(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, contract_number TEXT, date_signed TEXT, end_date TEXT, total_amount REAL, paid_amount REAL, payment_status TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS exam_sheets(id INTEGER PRIMARY KEY AUTOINCREMENT, sheet_number TEXT, group_name TEXT, subject TEXT, control_type TEXT, exam_date TEXT, examiner TEXT, status TEXT)''')
    
    conn.commit()
    c.execute('SELECT count(*) FROM students')
    if c.fetchone()[0] == 0:
        c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)', ('admin', make_hashes('admin'), 'admin', 'Головний Адміністратор', ''))
        for group, names in GROUPS_DATA.items():
            for name in names:
                c.execute('INSERT INTO students (full_name, group_name) VALUES (?,?)', (name, group))
        conn.commit()
    return conn

# --- СТОРІНКА ВХОДУ ТА РЕЄСТРАЦІЇ ---
def login_register_page():
    st.header("🔐 Вхід / Реєстрація (Адміністрація)")
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
                if user[2] in ['student', 'starosta']:
                    st.error("Доступ для студентів заблоковано.")
                else:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user[0]
                    st.session_state['role'] = user[2]
                    st.session_state['full_name'] = user[3]
                    st.session_state['group'] = user[4]
                    log_action(user[3], "Login", "Вхід адміністрації")
                    st.success(f"Вітаємо, {user[3]}!")
                    st.rerun()
            else:
                st.error("Невірний логін або пароль")

    elif action == "Реєстрація":
        st.info("Реєстрація доступна лише для керівного складу факультету.")
        new_user = st.text_input("Вигадайте логін")
        new_pass = st.text_input("Вигадайте пароль", type='password')
        
        # Тільки Адмін та Декан
        role = st.selectbox("Оберіть роль", ["admin", "dean"])
        
        full_name = st.text_input("ПІБ (повністю)")
        group_link = "Administration"

        if st.button("Зареєструватися"):
            if new_user and new_pass and full_name:
                try:
                    c.execute('INSERT INTO users VALUES (?,?,?,?,?)', 
                              (new_user, make_hashes(new_pass), role, full_name, group_link))
                    conn.commit()
                    log_action(full_name, "Registration", f"Новий запис: {role}")
                    st.success("Обліковий запис створено! Тепер увійдіть у вкладці 'Вхід'.")
                except sqlite3.IntegrityError:
                    st.error("Цей логін вже зайнятий.")
            else:
                st.warning("Будь ласка, заповніть усі поля.")

# --- ОСНОВНІ ПАНЕЛІ ---

def main_panel():
    st.title("🏠 Головна панель LMS")
    conn = create_connection()
    st.markdown(f"### Вітаємо, {st.session_state['full_name']}!")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    total_students = pd.read_sql_query("SELECT count(*) FROM students", conn).iloc[0,0]
    file_count = pd.read_sql_query("SELECT count(*) FROM file_storage", conn).iloc[0,0]
    avg_grade = pd.read_sql_query("SELECT avg(grade) FROM grades", conn).iloc[0,0]
    
    kpi1.metric("Студентів", total_students)
    kpi2.metric("Матеріалів", file_count)
    kpi3.metric("Середній бал", round(avg_grade, 2) if avg_grade else 0)

    st.divider()
    st.subheader("📢 Останні оголошення")
    if st.session_state['role'] in TEACHER_LEVEL:
        with st.expander("📝 Опублікувати новину"):
            with st.form("news_form"):
                nt = st.text_input("Заголовок")
                nm = st.text_area("Текст")
                if st.form_submit_button("Додати"):
                    conn.execute("INSERT INTO news (title, message, author, date) VALUES (?,?,?,?)", 
                                 (nt, nm, st.session_state['full_name'], datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    st.rerun()
    
    news_df = pd.read_sql("SELECT * FROM news ORDER BY id DESC LIMIT 5", conn)
    for _, row in news_df.iterrows():
        st.info(f"**{row['title']}** | {row['date']}\n\n{row['message']}")

def students_groups_view():
    st.title("👥 Студенти та Групи")
    conn = create_connection()
    all_grps = ["Всі"] + list(GROUPS_DATA.keys())
    sel_grp = st.selectbox("Фільтр по групі", all_grps)
    
    query = "SELECT id, full_name as 'ПІБ', group_name as 'Група' FROM students"
    if sel_grp != "Всі": query += f" WHERE group_name='{sel_grp}'"
    
    df = pd.read_sql(query, conn)
    st.dataframe(df, use_container_width=True)
    
    if st.session_state['role'] in DEAN_LEVEL:
        with st.expander("➕ Додати студента"):
            with st.form("add_std"):
                fn = st.text_input("ПІБ")
                gn = st.selectbox("Група", list(GROUPS_DATA.keys()))
                if st.form_submit_button("Зберегти"):
                    conn.execute("INSERT INTO students (full_name, group_name) VALUES (?,?)", (fn, gn))
                    conn.commit()
                    st.rerun()

def teachers_view():
    st.title("👨‍🏫 Викладацький склад")
    for dept, teachers in TEACHERS_DATA.items():
        with st.expander(f"📚 {dept}"):
            for t in teachers:
                st.write(f"- {t}")

def schedule_view():
    st.title("📅 Розклад занять")
    conn = create_connection()
    grp = st.selectbox("Група для перегляду", list(GROUPS_DATA.keys()))
    
    if st.session_state['role'] in DEAN_LEVEL:
        with st.expander("➕ Додати заняття"):
            with st.form("add_sch"):
                d = st.selectbox("День", ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"])
                t = st.text_input("Час (напр. 08:30)")
                s = st.selectbox("Предмет", SUBJECTS_LIST)
                tch = st.text_input("Викладач")
                if st.form_submit_button("Додати"):
                    conn.execute("INSERT INTO schedule (group_name, day, time, subject, teacher) VALUES (?,?,?,?,?)", (grp, d, t, s, tch))
                    conn.commit()
                    st.rerun()
    
    df = pd.read_sql(f"SELECT day as 'День', time as 'Час', subject as 'Предмет', teacher as 'Викладач' FROM schedule WHERE group_name='{grp}'", conn)
    st.table(df)

def gradebook_view():
    st.title("💯 Електронний журнал")
    conn = create_connection()
    c = conn.cursor()
    col1, col2 = st.columns(2)
    grp = col1.selectbox("Оберіть групу", list(GROUPS_DATA.keys()))
    sbj = col2.selectbox("Оберіть предмет", SUBJECTS_LIST)
    
    if st.session_state['role'] in TEACHER_LEVEL:
        with st.expander("➕ Додати колонку оцінок"):
            with st.form("new_grade_col"):
                work_type = st.text_input("Назва роботи (напр. КР №1)")
                if st.form_submit_button("Створити"):
                    stds = pd.read_sql(f"SELECT full_name FROM students WHERE group_name='{grp}'", conn)['full_name'].tolist()
                    for s in stds:
                        c.execute("INSERT INTO grades (student_name, group_name, subject, type_of_work, grade, date) VALUES (?,?,?,?,?,?)", 
                                  (s, grp, sbj, work_type, 0, str(datetime.now().date())))
                    conn.commit()
                    st.rerun()
    
    raw = pd.read_sql(f"SELECT student_name, type_of_work, grade FROM grades WHERE group_name='{grp}' AND subject='{sbj}'", conn)
    if not raw.empty:
        matrix = raw.pivot_table(index='student_name', columns='type_of_work', values='grade', aggfunc='first').fillna(0)
        st.write("Редагування оцінок:")
        edited = st.data_editor(matrix, use_container_width=True)
        if st.button("💾 Зберегти зміни в журнал"):
            for s_name, row in edited.iterrows():
                for w_type, val in row.items():
                    c.execute("UPDATE grades SET grade=? WHERE student_name=? AND subject=? AND type_of_work=?", (val, s_name, sbj, w_type))
            conn.commit()
            st.success("Журнал оновлено!")
    else:
        st.info("Колонки ще не створені.")

def attendance_view():
    st.title("📝 Журнал відвідуваності")
    conn = create_connection()
    grp = st.selectbox("Група", list(GROUPS_DATA.keys()), key="att_grp")
    sbj = st.selectbox("Предмет", SUBJECTS_LIST, key="att_sbj")
    
    if st.session_state['role'] in TEACHER_LEVEL:
        if st.button("➕ Додати сьогоднішню дату"):
            today = datetime.now().strftime("%d.%m")
            stds = pd.read_sql(f"SELECT full_name FROM students WHERE group_name='{grp}'", conn)['full_name'].tolist()
            for s in stds:
                conn.execute("INSERT INTO attendance (student_name, group_name, subject, date_column, status) VALUES (?,?,?,?,?)", (s, grp, sbj, today, ""))
            conn.commit()
            st.rerun()

    raw = pd.read_sql(f"SELECT student_name, date_column, status FROM attendance WHERE group_name='{grp}' AND subject='{sbj}'", conn)
    if not raw.empty:
        matrix = raw.pivot_table(index='student_name', columns='date_column', values='status', aggfunc='first').fillna("")
        st.write("Ставте 'н' для відсутніх:")
        edited = st.data_editor(matrix, use_container_width=True)
        if st.button("Зберегти відвідуваність"):
            for s_name, row in edited.iterrows():
                for d_col, val in row.items():
                    conn.execute("UPDATE attendance SET status=? WHERE student_name=? AND subject=? AND date_column=?", (val, s_name, sbj, d_col))
            conn.commit()
            st.success("Збережено!")

def reports_view():
    st.title("📊 Звіти та Документи")
    t1, t2 = st.tabs(["Екзаменаційна відомість", "Анкета студента"])
    conn = create_connection()
    
    with t1:
        c1, c2 = st.columns(2)
        grp = c1.selectbox("Група", list(GROUPS_DATA.keys()), key="r1")
        sbj = c2.selectbox("Предмет", SUBJECTS_LIST, key="r2")
        data = pd.read_sql(f"SELECT student_name as 'Студент', grade as 'Бали' FROM grades WHERE group_name='{grp}' AND subject='{sbj}'", conn)
        st.dataframe(data, use_container_width=True)
        st.download_button("⬇️ Завантажити CSV", convert_df_to_csv(data), "report.csv")
    
    with t2:
        search_name = st.text_input("Введіть ПІБ студента")
        if search_name:
            info = pd.read_sql(f"SELECT * FROM students WHERE full_name LIKE '%{search_name}%'", conn)
            st.write(info)

def file_repository_view():
    st.title("🗄️ Навчальні матеріали")
    conn = create_connection()
    if st.session_state['role'] in TEACHER_LEVEL:
        with st.expander("📤 Завантажити файл"):
            uploaded_file = st.file_uploader("Оберіть файл")
            descr = st.text_input("Опис")
            fsbj = st.selectbox("Предмет", SUBJECTS_LIST, key="f_sbj")
            if st.button("Зберегти у сховище"):
                if uploaded_file:
                    conn.execute("INSERT INTO file_storage (filename, file_content, upload_date, uploader, subject, description) VALUES (?,?,?,?,?,?)",
                                 (uploaded_file.name, uploaded_file.read(), str(datetime.now()), st.session_state['full_name'], fsbj, descr))
                    conn.commit()
                    st.success("Завантажено!")

    files = pd.read_sql("SELECT filename, subject, description, upload_date FROM file_storage", conn)
    st.dataframe(files, use_container_width=True)

def deanery_modules_view():
    st.title("🏛️ Модулі деканату")
    tab1, tab2, tab3 = st.tabs(["Гуртожиток", "Стипендії", "Контракти"])
    conn = create_connection()
    
    with tab1:
        st.subheader("Облік мешканців")
        df = pd.read_sql("SELECT * FROM dormitory", conn)
        st.dataframe(df, use_container_width=True)
        with st.form("dorm_f"):
            st_name = st.text_input("Студент")
            st_room = st.text_input("Кімната")
            if st.form_submit_button("Поселити"):
                conn.execute("INSERT INTO dormitory (student_name, room_number, payment_status) VALUES (?,?,?)", (st_name, st_room, "Оплачено"))
                conn.commit()
                st.rerun()

    with tab2:
        st.subheader("Стипендіальний фонд")
        st.button("Розрахувати рейтинг успішності")
        df = pd.read_sql("SELECT * FROM scholarship", conn)
        st.dataframe(df)

    with tab3:
        st.subheader("Фінансовий моніторинг")
        df = pd.read_sql("SELECT * FROM student_contracts", conn)
        st.dataframe(df)

def session_module_view():
    st.title("🚀 Рух контингенту")
    conn = create_connection()
    with st.container(border=True):
        st.subheader("Переведення групи на наступний курс")
        grp_from = st.selectbox("Поточна назва групи", list(GROUPS_DATA.keys()))
        grp_to = st.text_input("Нова назва (напр. 2СОМ)")
        if st.button("Виконати наказ про переведення"):
            conn.execute("UPDATE students SET group_name=? WHERE group_name=?", (grp_to, grp_from))
            conn.commit()
            st.success("Дані оновлено в базі")

def system_settings_view():
    st.title("⚙️ Системні налаштування")
    conn = create_connection()
    st.subheader("Користувачі системи")
    users = pd.read_sql("SELECT username, full_name, role FROM users", conn)
    st.dataframe(users, use_container_width=True)
    
    st.subheader("Журнал аудиту (Audit Log)")
    logs = pd.read_sql("SELECT * FROM system_logs ORDER BY id DESC LIMIT 50", conn)
    st.dataframe(logs)

# --- ГОЛОВНА ЛОГІКА ---
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
        st.sidebar.caption(f"Посада: {st.session_state['role'].upper()}")
        
        if st.sidebar.button("Змінити тему 🌓"):
            toggle_theme()
            st.rerun()
            
        st.sidebar.divider()
        
        # Динамічне меню
        menu = {
            "Головна": main_panel,
            "Студенти": students_groups_view,
            "Викладачі": teachers_view,
            "Розклад": schedule_view,
            "Ел. Журнал": gradebook_view,
            "Відвідуваність": attendance_view,
            "Звіти": reports_view,
            "Репозиторій": file_repository_view
        }
        
        if st.session_state['role'] in DEAN_LEVEL:
            menu["Деканат"] = deanery_modules_view
            menu["Сесія/Рух"] = session_module_view 
        
        if st.session_state['role'] == 'admin':
            menu["Налаштування"] = system_settings_view

        selection = st.sidebar.radio("Навігація", list(menu.keys()))
        menu[selection]()
        
        st.sidebar.divider()
        if st.sidebar.button("Вийти 🚪"):
            st.session_state['logged_in'] = False
            st.rerun()

if __name__ == '__main__':
    main()
