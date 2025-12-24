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
</style>
"""

if st.session_state.theme == 'dark':
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    st.markdown(light_css, unsafe_allow_html=True)

# --- КОНСТАНТИ ТА ПРАВА ДОСТУПУ ---
# Залишаємо списки для сумісності з іншими функціями, але обмежуємо вхід
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
    "1СОФА": ["Генсіцька Аліна Миколаївна", "Курільченко Кіра Дмитрівна", "Мецгер Катерина Валеріївна", "Чернецька Наталія Сергіївна", "Шведун Валерій Володимирович"]
}

# --- BACKEND ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_connection():
    return sqlite3.connect('university_admin_v1.db', check_same_thread=False)

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
    return conn

# --- СТОРІНКА ВХОДУ (ОБМЕЖЕНО) ---
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
                # ПЕРЕВІРКА: Лише admin та dean мають доступ
                if user[2] not in ['admin', 'dean']:
                    st.error("Доступ заблоковано. Ця панель лише для Адміністраторів та Деканів.")
                else:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user[0]
                    st.session_state['role'] = user[2]
                    st.session_state['full_name'] = user[3]
                    log_action(user[3], "Login", "Вхід в систему")
                    st.success(f"Вітаємо, {user[3]}!")
                    st.rerun()
            else:
                st.error("Невірний логін або пароль")

    elif action == "Реєстрація":
        st.info("Реєстрація доступна лише для Адміністраторів та Деканів.")
        new_user = st.text_input("Вигадайте логін")
        new_pass = st.text_input("Вигадайте пароль", type='password')
        
        # ВИДАЛЕНО ВСІ ІНШІ РОЛІ: залишено лише admin та dean
        role = st.selectbox("Оберіть посаду", ["admin", "dean"])
        
        full_name = st.text_input("Ваше ПІБ (повністю)")
        group_link = "Staff"

        if st.button("Зареєструватися"):
            if new_user and new_pass and full_name:
                try:
                    c.execute('INSERT INTO users VALUES (?,?,?,?,?)', (new_user, make_hashes(new_pass), role, full_name, group_link))
                    conn.commit()
                    log_action(full_name, "Registration", f"Новий аккаунт: {role}")
                    st.success("Успішно! Тепер перейдіть до входу.")
                except sqlite3.IntegrityError:
                    st.error("Цей логін вже зайнятий.")
            else:
                st.warning("Заповніть всі поля.")

# --- МОДУЛІ ПАНЕЛІ ---

def main_panel():
    st.title("🏠 Головна панель")
    conn = create_connection()
    kpi1, kpi2, kpi3 = st.columns(3)
    
    total_students = pd.read_sql_query("SELECT count(*) FROM students", conn).iloc[0,0]
    total_files = pd.read_sql_query("SELECT count(*) FROM file_storage", conn).iloc[0,0]
    avg_grade = pd.read_sql_query("SELECT avg(grade) FROM grades", conn).iloc[0,0]
    
    kpi1.metric("Всього студентів", total_students)
    kpi2.metric("Матеріалів", total_files)
    kpi3.metric("Середній бал", round(avg_grade, 1) if avg_grade else 0)

    st.subheader("📢 Останні оголошення")
    news_df = pd.read_sql_query("SELECT title, message, author, date FROM news ORDER BY id DESC LIMIT 5", conn)
    for _, row in news_df.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['title']}**")
            st.write(row['message'])
            st.caption(f"🗓️ {row['date']} | ✍️ {row['author']}")

def students_groups_view():
    st.title("👥 Студенти та Групи")
    conn = create_connection()
    all_groups = ["Всі"] + list(GROUPS_DATA.keys())
    selected_group = st.selectbox("Фільтр по групі:", all_groups)
    
    query = "SELECT id, full_name as 'ПІБ', group_name as 'Група' FROM students"
    if selected_group != "Всі": query += f" WHERE group_name='{selected_group}'"
    
    df = pd.read_sql_query(query, conn)
    st.dataframe(df, use_container_width=True)

    with st.expander("➕ Додати нового студента"):
        with st.form("add_std"):
            name = st.text_input("ПІБ")
            grp = st.selectbox("Група", list(GROUPS_DATA.keys()))
            if st.form_submit_button("Зберегти"):
                conn.execute("INSERT INTO students (full_name, group_name) VALUES (?,?)", (name, grp))
                conn.commit()
                st.rerun()

def schedule_view():
    st.title("📅 Розклад занять")
    conn = create_connection()
    grp = st.selectbox("Група", list(GROUPS_DATA.keys()))
    
    with st.form("sch_form"):
        col1, col2, col3 = st.columns(3)
        day = col1.selectbox("День", ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"])
        tm = col2.text_input("Час (напр. 08:30)")
        sbj = col3.text_input("Предмет")
        tch = st.text_input("Викладач")
        if st.form_submit_button("Додати пару"):
            conn.execute("INSERT INTO schedule (group_name, day, time, subject, teacher) VALUES (?,?,?,?,?)", (grp, day, tm, sbj, tch))
            conn.commit()
            st.rerun()
            
    df = pd.read_sql_query(f"SELECT day, time, subject, teacher FROM schedule WHERE group_name='{grp}'", conn)
    st.dataframe(df, use_container_width=True)

def gradebook_view():
    st.title("💯 Електронний журнал")
    conn = create_connection()
    c = conn.cursor()
    grp = st.selectbox("Група", list(GROUPS_DATA.keys()), key="gr_gb")
    sbj = st.selectbox("Предмет", SUBJECTS_LIST, key="sb_gb")

    if st.button("➕ Створити колонку (Сьогодні)"):
        stds = pd.read_sql(f"SELECT full_name FROM students WHERE group_name='{grp}'", conn)['full_name'].tolist()
        for s in stds:
            c.execute("INSERT INTO grades (student_name, group_name, subject, type_of_work, grade, date) VALUES (?,?,?,?,?,?)",
                      (s, grp, sbj, "Заняття", 0, str(datetime.now().date())))
        conn.commit()
        st.rerun()

    raw = pd.read_sql(f"SELECT student_name, type_of_work, grade FROM grades WHERE group_name='{grp}' AND subject='{sbj}'", conn)
    if not raw.empty:
        matrix = raw.pivot_table(index='student_name', columns='type_of_work', values='grade', aggfunc='first').fillna(0)
        edited = st.data_editor(matrix, use_container_width=True)
        if st.button("Зберегти оцінки"):
            for s_name, row in edited.iterrows():
                for w_name, val in row.items():
                    c.execute("UPDATE grades SET grade=? WHERE student_name=? AND subject=? AND type_of_work=?", (val, s_name, sbj, w_name))
            conn.commit()
            st.success("Дані оновлено")

def attendance_view():
    st.title("📝 Журнал відвідуваності")
    conn = create_connection()
    grp = st.selectbox("Група", list(GROUPS_DATA.keys()), key="gr_att")
    sbj = st.selectbox("Предмет", SUBJECTS_LIST, key="sb_att")
    
    if st.button("➕ Додати дату"):
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
        st.data_editor(matrix, use_container_width=True)

def reports_view():
    st.title("📊 Звіти та Пошук")
    conn = create_connection()
    t1, t2 = st.tabs(["Зведена відомість", "Електронна анкета"])
    
    with t1:
        grp = st.selectbox("Оберіть групу", list(GROUPS_DATA.keys()))
        data = pd.read_sql(f"SELECT student_name, subject, avg(grade) as score FROM grades WHERE group_name='{grp}' GROUP BY student_name, subject", conn)
        if not data.empty:
            pivot = data.pivot_table(index='student_name', columns='subject', values='score').fillna(0)
            st.dataframe(pivot)
    
    with t2:
        search = st.text_input("ПІБ Студента для пошуку")
        if search:
            res = pd.read_sql(f"SELECT * FROM students WHERE full_name LIKE '%{search}%'", conn)
            st.write(res)

def file_repository_view():
    st.title("🗄️ Файловий Репозиторій")
    conn = create_connection()
    
    with st.expander("📤 Завантажити новий матеріал"):
        f = st.file_uploader("Файл")
        sbj = st.selectbox("Предмет", SUBJECTS_LIST)
        desc = st.text_input("Опис")
        if st.button("Зберегти"):
            if f:
                conn.execute("INSERT INTO file_storage (filename, file_content, upload_date, uploader, subject, description) VALUES (?,?,?,?,?,?)",
                             (f.name, f.read(), str(datetime.now()), st.session_state['full_name'], sbj, desc))
                conn.commit()
                st.success("Файл завантажено")

    files = pd.read_sql("SELECT id, filename, subject, description, upload_date FROM file_storage", conn)
    st.dataframe(files, use_container_width=True)

def deanery_modules_view():
    st.title("🏛️ Модулі Деканату")
    tab1, tab2, tab3 = st.tabs(["Гуртожиток", "Стипендії", "Контракти"])
    conn = create_connection()
    
    with tab1:
        st.subheader("Облік поселення")
        df = pd.read_sql("SELECT * FROM dormitory", conn)
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("Стипендіальний фонд")
        df = pd.read_sql("SELECT * FROM scholarship", conn)
        st.dataframe(df, use_container_width=True)
        
    with tab3:
        st.subheader("Фінансовий моніторинг")
        df = pd.read_sql("SELECT * FROM student_contracts", conn)
        st.dataframe(df, use_container_width=True)

def session_module_view():
    st.title("🚀 Сесія та Рух контингенту")
    conn = create_connection()
    
    with st.container(border=True):
        st.subheader("Переведення групи")
        grp_old = st.selectbox("Поточна група", list(GROUPS_DATA.keys()))
        grp_new = st.text_input("Нова назва (напр. 2СОМ)")
        if st.button("Виконати переведення"):
            conn.execute("UPDATE students SET group_name=? WHERE group_name=?", (grp_new, grp_old))
            conn.commit()
            st.success("Групу переведено!")

def system_settings_view():
    st.title("⚙️ Системні налаштування")
    conn = create_connection()
    
    st.subheader("Користувачі системи")
    users = pd.read_sql("SELECT username, full_name, role FROM users", conn)
    st.dataframe(users, use_container_width=True)
    
    st.subheader("Журнал дій (Audit Log)")
    logs = pd.read_sql("SELECT * FROM system_logs ORDER BY id DESC LIMIT 50", conn)
    st.dataframe(logs, use_container_width=True)

# --- ГОЛОВНА ЛОГІКА ---
def main():
    init_db()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        login_register_page()
    else:
        st.sidebar.title(f"👤 {st.session_state['full_name']}")
        st.sidebar.caption(f"Роль: {st.session_state['role'].upper()}")
        
        if st.sidebar.button("Змінити тему 🌓"):
            toggle_theme()
            st.rerun()
            
        st.sidebar.divider()
        
        # ПОВНА НАВІГАЦІЯ
        menu_options = {
            "Головна панель": main_panel,
            "Студенти та Групи": students_groups_view,
            "Розклад занять": schedule_view,
            "Електронний журнал": gradebook_view,
            "Журнал відвідуваності": attendance_view,
            "Звіти та Пошук": reports_view,
            "Файловий репозиторій": file_repository_view,
            "Модулі Деканату": deanery_modules_view,
            "Сесія та Рух": session_module_view
        }
        
        if st.session_state['role'] == 'admin':
            menu_options["Системні налаштування"] = system_settings_view

        selection = st.sidebar.radio("Навігація", list(menu_options.keys()))
        menu_options[selection]()
        
        st.sidebar.divider()
        if st.sidebar.button("Вийти 🚪"):
            st.session_state['logged_in'] = False
            st.rerun()

if __name__ == '__main__':
    main()
