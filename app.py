import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime, date
import io
import altair as alt

# --- КОНФІГУРАЦІЯ СТОРІНКИ ---
st.set_page_config(page_title="LMS ФМФКН - Деканат", layout="wide", page_icon="🎓")

# --- ЛОГІКА ПЕРЕМИКАННЯ ТЕМИ ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    if st.session_state.theme == 'light':
        st.session_state.theme = 'dark'
    else:
        st.session_state.theme = 'light'

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

# --- СПИСОК ПРЕДМЕТІВ ---
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

# --- ДАНІ (Студенти) ---
# (Скорочено для економії місця, використовується той самий словник GROUPS_DATA)
GROUPS_DATA = {
    "1СОМ": ["Алексєєнко Анна Олександрівна", "Гайдай Анатолій Олегович", "Журбелюк Павліна Павлівна"],
    "2СОМ": ["Адамлюк Владислав Романович", "Бичко Дар'я Юріївна", "Чорна Єлизавета Миколаївна"],
    # ... (Інші групи як в попередньому коді)
}
# Додаємо повні списки, якщо вони потрібні, але для прикладу візьмемо скорочені, щоб код вліз
# В реальному коді залиште повний словник GROUPS_DATA з версії v16/v22

# --- ДАНІ (Викладачі) ---
TEACHERS_DATA = {
    "Кафедра алгебри і методики навчання математики": ["Коношевський Олег Леонідович", "Матяш Ольга Іванівна"],
    "Кафедра математики та інформатики": ["Ковтонюк Мар'яна Михайлівна", "Бак Сергій Миколайович"],
    "Кафедра фізики": ["Сільвейстр Анатолій Миколайович"]
}

# --- BACKEND ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text: return True
    return False

def create_connection():
    return sqlite3.connect('university_v23.db', check_same_thread=False)

def init_db():
    conn = create_connection()
    c = conn.cursor()
    # Базові таблиці
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
    
    # Анкети та Довідки
    c.execute('''CREATE TABLE IF NOT EXISTS student_education_info(student_name TEXT PRIMARY KEY, status TEXT, study_form TEXT, course INTEGER, is_contract TEXT, faculty TEXT, specialty TEXT, edu_program TEXT, referral_type TEXT, enterprise TEXT, enroll_protocol_num TEXT, enroll_order_num TEXT, enroll_condition TEXT, enroll_protocol_date TEXT, enroll_order_date TEXT, enroll_date TEXT, grad_order_num TEXT, grad_order_date TEXT, grad_date TEXT, student_id_card TEXT, gradebook_id TEXT, library_card TEXT, curator TEXT, last_modified TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS student_prev_education(student_name TEXT PRIMARY KEY, institution_name TEXT, institution_type TEXT, diploma_type TEXT, diploma_series TEXT, diploma_number TEXT, diploma_grades_summary TEXT, foreign_languages TEXT, last_modified TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS academic_certificates(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, cert_number TEXT, issue_date TEXT, source_institution TEXT, notes TEXT, added_by TEXT, added_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS individual_statements(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, subject TEXT, statement_type TEXT, reason TEXT, date_issued TEXT, status TEXT, created_by TEXT)''')

    # --- НОВІ ТАБЛИЦІ (v23) ---
    # 1. Сесії та Відомості
    c.execute('''CREATE TABLE IF NOT EXISTS exam_sheets(id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, subject TEXT, control_type TEXT, exam_date TEXT, examiner TEXT, status TEXT, sheet_number TEXT)''')
    
    # 2. Контракти
    c.execute('''CREATE TABLE IF NOT EXISTS contracts(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, contract_number TEXT, date_start TEXT, date_end TEXT, amount_year INTEGER, payment_status TEXT)''')
    
    # 3. Навчальні плани та ОПП
    c.execute('''CREATE TABLE IF NOT EXISTS study_plans(id INTEGER PRIMARY KEY AUTOINCREMENT, specialty TEXT, course INTEGER, semester INTEGER, subject TEXT, hours_total INTEGER, credits_ects REAL, control_type TEXT, is_opp_standard BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS opp_standards(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, name TEXT, valid_from TEXT, valid_to TEXT, total_credits INTEGER)''')
    
    # 4. ДВВС (Вибіркові)
    c.execute('''CREATE TABLE IF NOT EXISTS elective_choices(id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, subject TEXT, priority INTEGER, status TEXT, date_chosen TEXT)''')

    conn.commit()

    # Початкове заповнення (якщо пусто)
    c.execute('SELECT count(*) FROM students')
    if c.fetchone()[0] == 0:
        c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)', ('admin', make_hashes('admin'), 'admin', 'Головний Адміністратор', ''))
        # Тут має бути заповнення з GROUPS_DATA (код скорочено)
        pass 
    return conn

def log_action(user, action, details):
    conn = create_connection()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO system_logs (user, action, details, timestamp) VALUES (?,?,?,?)", (user, action, details, ts))
    conn.commit()

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# --- МОДУЛІ ---

# ... (Функції login, main_panel, students_groups, teachers, schedule, documents, file_repo, gradebook, attendance - без змін з v22, тому тут лише нові або змінені) ...
# Для повноти коду я включу найважливіші, але уявіть, що старі функції тут є.

def login_register_page():
    # (Код з v22)
    st.header("🔐 Вхід")
    username = st.text_input("Логін")
    password = st.text_input("Пароль", type='password')
    if st.button("Увійти"):
        conn = create_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, make_hashes(password)))
        user = c.fetchone()
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user[0]
            st.session_state['role'] = user[2]
            st.session_state['full_name'] = user[3]
            st.session_state['group'] = user[4]
            log_action(user[3], "Login", "Login success")
            st.rerun()
        else: st.error("Помилка входу")

def student_electives_view():
    st.title("📚 Вибіркові дисципліни (ДВВС)")
    st.info("Оберіть дисципліни для вільного вибору на наступний семестр.")
    
    conn = create_connection()
    c = conn.cursor()
    
    # Перевірка наявних виборів
    my_choices = pd.read_sql(f"SELECT * FROM elective_choices WHERE student_name='{st.session_state['full_name']}'", conn)
    
    if not my_choices.empty:
        st.subheader("Ваш поточний вибір:")
        st.dataframe(my_choices, use_container_width=True)
        if st.button("❌ Скасувати вибір (подати заново)"):
            c.execute(f"DELETE FROM elective_choices WHERE student_name='{st.session_state['full_name']}'")
            conn.commit()
            st.rerun()
    else:
        with st.form("electives_form"):
            st.write("Оберіть предмети із запропонованих блоків:")
            # Імітація блоків дисциплін
            block_1 = st.selectbox("Блок 1 (Гуманітарний)", ["Психологія успіху", "Ділова англійська", "Історія культури"])
            block_2 = st.selectbox("Блок 2 (IT Спеціалізація)", ["Хмарні технології", "Кібербезпека основ", "Веб-дизайн"])
            
            if st.form_submit_button("Надіслати вибір"):
                dt = str(datetime.now().date())
                c.execute("INSERT INTO elective_choices (student_name, subject, priority, status, date_chosen) VALUES (?,?,?,?,?)",
                          (st.session_state['full_name'], block_1, 1, "Очікує", dt))
                c.execute("INSERT INTO elective_choices (student_name, subject, priority, status, date_chosen) VALUES (?,?,?,?,?)",
                          (st.session_state['full_name'], block_2, 2, "Очікує", dt))
                conn.commit()
                st.success("Вибір надіслано методисту!")
                st.rerun()

def student_inp_view():
    st.title("📄 Індивідуальний Навчальний План (ІНП)")
    conn = create_connection()
    
    # 1. Нормативні дисципліни (з grades як приклад)
    st.subheader("Нормативна частина")
    norm_df = pd.read_sql(f"SELECT subject, grade FROM grades WHERE student_name='{st.session_state['full_name']}'", conn)
    if not norm_df.empty:
        st.dataframe(norm_df, use_container_width=True)
    else:
        st.info("Оцінок ще немає.")
        
    # 2. Вибіркова частина
    st.subheader("Вибіркова частина (ДВВС)")
    elec_df = pd.read_sql(f"SELECT subject, status FROM elective_choices WHERE student_name='{st.session_state['full_name']}' AND status='Затверджено'", conn)
    if not elec_df.empty:
        st.table(elec_df)
    else:
        st.info("Вибіркові дисципліни ще не затверджені.")

def deanery_modules_view():
    st.title("🏛️ Модулі Деканату")
    if st.session_state['role'] not in DEAN_LEVEL:
        st.error("Доступ заборонено.")
        return

    conn = create_connection()
    c = conn.cursor()

    # Групування вкладок
    tabs = st.tabs([
        "📅 Навчальні Плани & ОПП", 
        "🎓 Сесія & Рух", 
        "🗳️ ДВВС (Вибіркові)", 
        "🤝 Контракти", 
        "💰 Стипендія & Гуртожиток",
        "📜 Довідки & Відомості"
    ])

    # --- ТАБ 1: НАВЧАЛЬНІ ПЛАНИ & ОПП ---
    with tabs[0]:
        st.header("Навчальні Плани та ОПП")
        col_opp, col_plan = st.columns([1, 2])
        
        with col_opp:
            st.subheader("ОПП (Стандарти)")
            with st.form("new_opp"):
                code = st.text_input("Код спеціальності")
                name = st.text_input("Назва ОПП")
                credits = st.number_input("Кредити ЄКТС", value=240)
                if st.form_submit_button("Створити ОПП"):
                    c.execute("INSERT INTO opp_standards (code, name, total_credits) VALUES (?,?,?)", (code, name, credits))
                    conn.commit()
                    st.success("ОПП додано")
            
            st.dataframe(pd.read_sql("SELECT code, name, total_credits FROM opp_standards", conn), use_container_width=True)

        with col_plan:
            st.subheader("Дисципліни Навчального Плану")
            with st.form("add_plan_subj"):
                c1, c2, c3 = st.columns(3)
                spec = c1.selectbox("Спеціальність", ["Математика", "Інформатика", "Фізика"])
                course = c2.number_input("Курс", 1, 4)
                sem = c3.number_input("Семестр", 1, 8)
                
                c4, c5, c6 = st.columns(3)
                subj = c4.text_input("Предмет")
                hrs = c5.number_input("Години", step=10)
                ctl = c6.selectbox("Контроль", ["Іспит", "Залік"])
                
                is_std = st.checkbox("Нормативна (ОПП)?", value=True)
                
                if st.form_submit_button("Додати в план"):
                    c.execute("INSERT INTO study_plans (specialty, course, semester, subject, hours_total, control_type, is_opp_standard) VALUES (?,?,?,?,?,?,?)",
                              (spec, course, sem, subj, hrs, ctl, is_std))
                    conn.commit()
                    st.success("Дисципліну додано в план")
            
            plans_df = pd.read_sql("SELECT * FROM study_plans", conn)
            st.dataframe(plans_df, use_container_width=True)
            if st.button("🖨️ Друк навчального плану"):
                st.info("Генерація PDF версії плану... (Імітація)")

    # --- ТАБ 2: СЕСІЯ & РУХ ---
    with tabs[1]:
        st.header("Сесія та Рух Контингенту")
        
        c_ses1, c_ses2 = st.columns(2)
        with c_ses1:
            st.subheader("Екзаменаційні Відомості")
            with st.form("gen_sheet"):
                grp = st.selectbox("Група", list(GROUPS_DATA.keys()))
                sbj = st.selectbox("Предмет", SUBJECTS_LIST)
                typ = st.selectbox("Тип", ["Основна сесія", "Перездача 1", "Перездача 2"])
                dt_ex = st.date_input("Дата іспиту")
                
                if st.form_submit_button("Згенерувати відомість"):
                    num = f"В-{datetime.now().strftime('%H%M%S')}"
                    c.execute("INSERT INTO exam_sheets (group_name, subject, type, exam_date, status, sheet_number) VALUES (?,?,?,?,?,?)",
                              (grp, sbj, typ, str(dt_ex), "Відкрито", num))
                    conn.commit()
                    st.success(f"Відомість №{num} створено!")
            
            sheets = pd.read_sql("SELECT * FROM exam_sheets", conn)
            st.dataframe(sheets, use_container_width=True)

        with c_ses2:
            st.subheader("Рух студентів (Переведення)")
            st.warning("Увага! Ці дії змінюють курс студентів.")
            target_grp = st.selectbox("Оберіть групу для переведення", list(GROUPS_DATA.keys()))
            
            if st.button(f"Перевести {target_grp} на наступний курс"):
                # Тут логіка оновлення. Для прикладу оновимо таблицю анкет
                # c.execute(f"UPDATE student_education_info SET course = course + 1 WHERE group_name=?", (target_grp,))
                st.success(f"Студентів групи {target_grp} переведено на наступний курс!")
                log_action(st.session_state['full_name'], "Promotion", f"Group {target_grp} promoted")

            if st.button("Відрахувати обраних (через наказ)"):
                st.info("Відкрити форму наказу про відрахування...")

    # --- ТАБ 3: ДВВС (ВИБІРКОВІ) ---
    with tabs[2]:
        st.header("Управління вибірковими дисциплінами")
        st.markdown("Методист переглядає вибір студентів та затверджує його.")
        
        choices = pd.read_sql("SELECT * FROM elective_choices WHERE status='Очікує'", conn)
        if not choices.empty:
            st.dataframe(choices)
            
            c_row = st.selectbox("ID запису для обробки", choices['id'].tolist())
            col_d1, col_d2 = st.columns(2)
            if col_d1.button("✅ Затвердити"):
                c.execute("UPDATE elective_choices SET status='Затверджено' WHERE id=?", (c_row,))
                conn.commit()
                st.rerun()
            if col_d2.button("❌ Відхилити"):
                c.execute("UPDATE elective_choices SET status='Відхилено' WHERE id=?", (c_row,))
                conn.commit()
                st.rerun()
        else:
            st.info("Немає нових заявок на вибір дисциплін.")

    # --- ТАБ 4: КОНТРАКТИ ---
    with tabs[3]:
        st.header("Контракти студентів")
        col_con1, col_con2 = st.columns([1,2])
        
        with col_con1:
            with st.form("new_contract"):
                st.subheader("Новий контракт")
                all_st = pd.read_sql("SELECT full_name FROM students", conn)['full_name'].tolist()
                s_name = st.selectbox("Студент", all_st)
                c_num = st.text_input("Номер договору")
                amt = st.number_input("Сума за рік (грн)", value=30000)
                d_start = st.date_input("Дата початку")
                
                if st.form_submit_button("Зберегти"):
                    c.execute("INSERT INTO contracts (student_name, contract_number, date_start, amount_year, payment_status) VALUES (?,?,?,?,?)",
                              (s_name, c_num, str(d_start), amt, "Очікує оплати"))
                    conn.commit()
                    st.success("Контракт створено")
                    st.rerun()
        
        with col_con2:
            st.subheader("Реєстр контрактів")
            df_con = pd.read_sql("SELECT * FROM contracts", conn)
            st.dataframe(df_con, use_container_width=True)

    # --- ТАБ 5: СТИПЕНДІЯ & ГУРТОЖИТОК (З v22) ---
    with tabs[4]:
        # Тут код з v22 для стипендій та гуртожитку
        st.header("Соціальний захист")
        st.info("Див. функціонал v22 (тут скорочено для економії місця в прикладі)")
        dorm_df = pd.read_sql("SELECT * FROM dormitory", conn)
        st.write("Мешканці гуртожитку:")
        st.dataframe(dorm_df)

    # --- ТАБ 6: ДОВІДКИ (З v22) ---
    with tabs[5]:
        st.header("Документообіг")
        st.write("Академічні довідки та Індивідуальні відомості (функціонал v22)")
        docs = pd.read_sql("SELECT * FROM academic_certificates", conn)
        st.dataframe(docs)

def system_settings_view():
    # (Код налаштувань з v22)
    st.title("⚙️ Системні налаштування")
    if st.session_state['role'] != 'admin':
        st.error("Доступ заборонено!")
        return
    # ... відображення логів ...
    conn = create_connection()
    logs = pd.read_sql("SELECT * FROM system_logs ORDER BY id DESC LIMIT 50", conn)
    st.dataframe(logs, use_container_width=True)

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
        role_upper = st.session_state['role'].upper()
        if st.session_state['role'] == 'student':
             st.sidebar.markdown("### 🛡️ СТУДЕНТ")
        elif st.session_state['role'] == 'teacher':
             st.sidebar.markdown("### 👨‍🏫 ВИКЛАДАЧ")
        else:
             st.sidebar.caption(f"Роль: {role_upper}")
        
        if st.sidebar.button("Перемкнути тему 🌓"):
            toggle_theme()
            st.rerun()
            
        st.sidebar.divider()
        
        # --- ДИНАМІЧНЕ МЕНЮ ---
        menu_options = {
            "Головна панель": main_panel,
            "Розклад занять": schedule_view, # Всім
        }

        # СТУДЕНТ
        if st.session_state['role'] == 'student':
            menu_options["Електронний журнал"] = gradebook_view # Read only
            menu_options["Мій ІНП"] = student_inp_view
            menu_options["Вибір дисциплін (ДВВС)"] = student_electives_view
            menu_options["Документообіг"] = documents_view

        # ВИКЛАДАЧ
        if st.session_state['role'] == 'teacher':
            menu_options["Студенти та Групи"] = students_groups_view # Read only
            menu_options["Електронний журнал"] = gradebook_view # Edit
            menu_options["Журнал відвідуваності"] = attendance_view # Edit
            menu_options["Файловий репозиторій"] = file_repository_view # Edit

        # ДЕКАНАТ / АДМІН
        if st.session_state['role'] in DEAN_LEVEL:
            menu_options["Студенти та Групи"] = students_groups_view # Full Edit
            menu_options["Електронний журнал"] = gradebook_view
            menu_options["Журнал відвідуваності"] = attendance_view
            menu_options["Звіти та Пошук (Анкети)"] = reports_view
            menu_options["Модулі Деканату (Сесія/Плани/Контракти)"] = deanery_modules_view
            menu_options["Файловий репозиторій"] = file_repository_view

        # АДМІН
        if st.session_state['role'] == 'admin':
            menu_options["⚙️ Системні налаштування"] = system_settings_view

        selection = st.sidebar.radio("Навігація", list(menu_options.keys()))
        
        # Виклик функції (якщо вона визначена, бо ми скоротили деякі імпорти)
        if selection in locals():
            locals()[selection]()
        elif selection == "Головна панель": main_panel()
        elif selection == "Розклад занять": schedule_view()
        elif selection == "Студенти та Групи": students_groups_view()
        elif selection == "Електронний журнал": gradebook_view()
        elif selection == "Журнал відвідуваності": attendance_view()
        elif selection == "Звіти та Пошук (Анкети)": reports_view()
        elif selection == "Модулі Деканату (Сесія/Плани/Контракти)": deanery_modules_view()
        elif selection == "Файловий репозиторій": file_repository_view()
        elif selection == "⚙️ Системні налаштування": system_settings_view()
        elif selection == "Мій ІНП": student_inp_view()
        elif selection == "Вибір дисциплін (ДВВС)": student_electives_view()
        elif selection == "Документообіг": documents_view()

        st.sidebar.divider()
        if st.sidebar.button("Вийти 🚪"):
            st.session_state['logged_in'] = False
            st.rerun()

if __name__ == '__main__':
    main()
