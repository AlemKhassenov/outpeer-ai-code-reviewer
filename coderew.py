import streamlit as st
import subprocess
import tempfile
import os
import openai
from openai import OpenAI
from io import StringIO
from pylint.reporters.text import TextReporter
import pylint.lint
import importlib.util
import json
import importlib.util
import nltk


# Инициализация OpenAI клиента
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "your-api-key-here")

st.set_page_config(page_title="🧪 CodeGrader AI (stdin+functions)", layout="centered")
st.title("📥 Goderew")

# Список задач с примерами тестов
tasks = {
    "Имя и возраст": {
        "text": "Напиши программу, которая спрашивает у пользователя его имя и возраст, а затем выводит сообщение в формате: 'Привет, [имя]! Тебе уже [возраст] лет!'.",
        "input": "Айдана\n14",
        "output": "Привет, Айдана! Тебе уже 14 лет!",
        "type": "stdin"
    },
    "Сумма двух чисел": {
        "text": "Напиши программу, которая считывает два целых числа и выводит их сумму.",
        "input": "3\n4",
        "output": "7",
        "type": "stdin"
    },
    "Чётное или нечётное": {
        "text": "Программа должна определить, чётное число или нечётное, и вывести соответствующее сообщение.",
        "input": "7",
        "output": "Нечётное",
        "type": "stdin"
    },
    "Гипотенуза": {
        "text": "Вычисли длину гипотенузы по заданным катетам a и b с использованием модуля math.",
        "input": "3\n4",
        "output": "5.0",
        "type": "stdin"
    },
    "Факториал числа": {
        "text": "Напиши программу, которая находит факториал введённого числа n (n!).",
        "input": "5",
        "output": "120",
        "type": "stdin"
    },
    "Частота слов (NLTK)": {
        "text": "Реализуй функцию count_word_frequencies(text), которая подсчитывает частоту каждого слова в строке с использованием Tokenization из библиотеки NLTK.",
        "input": "Привет мир. Привет снова!",
        "output": "{'привет': 2, 'мир': 1, 'снова': 1}",
        "type": "function",
        "function_name": "count_word_frequencies"
    },
    "Удаление стоп-слов (NLTK)": {
    "text": "Реализуй функцию remove_stopwords(text), которая удаляет стоп-слова из строки с использованием списка stopwords из библиотеки NLTK.",
    "input": "Это пример предложения с некоторыми стоп-словами.",
    "output": "пример предложения некоторыми стоп-словами.",
    "type": "function",
    "function_name": "remove_stopwords"
    },
    "Предобработка данных (Pandas)": {
    "text": """Реализуй функцию preprocess_data(data), которая выполняет предварительную обработку загруженных данных.
    - Нормализуй числовые признаки.
    - Удали пропущенные значения.
    - Верни результат в виде DataFrame.""",
    "input": "sample.csv",  # здесь можно указать путь к файлу, если нужно его создать заранее
    "output": "DataFrame",  # здесь будет просто маркер, сравнение нужно реализовать отдельно
    "type": "function",
    "function_name": "preprocess_data"
    }

   
}

# Выбор задачи
task_name = st.selectbox("Выберите задачу:", list(tasks.keys()))
task = tasks[task_name]
st.markdown(f"### 🧩 Условие задачи:\n{task['text']}")

# Ввод кода
code = st.text_area("✏️ Впишите свой код:", height=300)

def_input = task["input"]
def_output = task["output"]
test_input = st.text_area("📥 Тестовые данные:", value=def_input)
expected_output = st.text_input("📤 Ожидаемый вывод:", value=def_output)

# Кнопки разных уровней проверки
col1, col2, col3 = st.columns(3)
col4 = st.columns(1)[0]
show_sample = col4.button("📄 Показать образец решения")
run_basic = col1.button("▶️ Проверить выполнение")
run_with_style = col2.button("🧪 Проверить со стилем")
run_with_gpt = col3.button("🤖 Проверить с GPT-помощью")

if show_sample:
    sample = task.get("sample_code")
    if sample:
        st.markdown("### 🧪 Пример решения:")
        st.code(sample, language="python")
    else:
        st.info("Для этой задачи образец решения пока не задан.")

if show_sample:
    st.markdown("### 🧪 Пример решения от GPT")
    try:
        prompt = f"""
        Представь, что ты преподаватель. Студент должен решить следующую задачу:

        {task['text']}

        Напиши образец корректного и чистого кода Python, соответствующего этому заданию.
        """
        response = client.chat.completions.create(
            model="gpt-4o",  # или gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        sample_code = response.choices[0].message.content
        st.code(sample_code, language="python")
    except Exception as e:
        st.warning(f"Ошибка при получении образца кода: {e}")


# STDIN-режим
def execute_code_stdin(code_text, test_input_text):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(code_text)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["python", tmp_path],
            input=test_input_text,
            text=True,
            capture_output=True,
            timeout=5
        )
        actual_output = result.stdout.strip()
    except subprocess.TimeoutExpired:
        st.error("⚠️ Превышено время выполнения. Возможно, бесконечный цикл.")
        return None, tmp_path
    except Exception as e:
        st.error(f"Ошибка при выполнении кода: {e}")
        return None, tmp_path
    return actual_output, tmp_path

def execute_function_call(code_text, function_name, args):
    import tempfile
    import os
    import importlib.util
    import nltk

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
        # Если используется nltk, добавим загрузку punkt в начало
        if "nltk" in code_text:
            code_text = "import nltk_patch\n" + code_text

        tmp.write(code_text)
        tmp_path = tmp.name

    try:
        spec = importlib.util.spec_from_file_location("student_code", tmp_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, function_name):
            raise AttributeError(f"Функция '{function_name}' не найдена.")

        func = getattr(module, function_name)
        result = func(*args)
        return str(result), tmp_path

    except Exception as e:
        st.error(f"Ошибка при вызове функции:\n\n{e}")
        return None, tmp_path




# Универсальный запуск
# --- БАЗОВАЯ ПРОВЕРКА ---
if run_basic:
    output, tmp_path = execute_code_stdin(code, test_input) if task["type"] == "stdin" else execute_function_call(code, task["function_name"], [test_input])
    
    if output is not None:
        if output == expected_output:
            st.success("✅ Всё верно! Вывод совпадает с ожидаемым.")
        else:
            st.error("❌ Неверный результат.")
            st.text(f"Ожидалось: {expected_output}\nПолучено: {output}")
    
    os.remove(tmp_path)


# --- ПРОВЕРКА СО СТИЛЕМ ---
if run_with_style:
    output, tmp_path = execute_code_stdin(code, test_input) if task["type"] == "stdin" else execute_function_call(code, task["function_name"], [test_input])
    
    if output is not None:
        if output == expected_output:
            st.success("✅ Всё верно! Вывод совпадает с ожидаемым.")
        else:
            st.error("❌ Неверный результат.")
            st.text(f"Ожидалось: {expected_output}\nПолучено: {output}")
    
    st.markdown("### 📏 Проверка стиля (pylint)")
    pylint_output = StringIO()
    reporter = TextReporter(output=pylint_output)
    try:
        pylint.lint.Run([tmp_path], reporter=reporter, exit=False)
        st.text(pylint_output.getvalue())
    except Exception as e:
        st.warning(f"Ошибка pylint: {e}")

    os.remove(tmp_path)


# --- GPT-РАЗБОР ---
if run_with_gpt:
    output, tmp_path = execute_code_stdin(code, test_input) if task["type"] == "stdin" else execute_function_call(code, task["function_name"], [test_input])
    
    if output is not None:
        if output == expected_output:
            st.success("✅ Всё верно! Вывод совпадает с ожидаемым.")
        else:
            st.error("❌ Неверный результат.")
            st.text(f"Ожидалось: {expected_output}\nПолучено: {output}")
    
    st.markdown("### 💬 Советы от GPT")
    try:
        prompt = f"""
        Оцени структуру кода по 3 критериям:
        1. Наличие и понятность docstring.
        2. Разделение на функции и повторное использование кода.
        3. Читаемость и соблюдение PEP8.
        Студент решает задачу:
        {task['text']}

        Его код:
        {code}

        Подскажи, есть ли ошибки, как улучшить структуру и стиль.

        Выведи оценку по 10-балльной шкале и краткое обоснование.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        st.markdown("### 🧱 Оценка структуры кода")
        st.markdown(response.choices[0].message.content)
    except Exception as e:
        st.warning(f"GPT не ответил: {e}")

    os.remove(tmp_path)
