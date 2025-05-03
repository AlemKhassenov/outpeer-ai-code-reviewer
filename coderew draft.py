import streamlit as st
import subprocess
import tempfile
import os
import openai
from openai import OpenAI
from io import StringIO
from pylint.reporters.text import TextReporter
import pylint.lint

# Инициализация OpenAI клиента
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "your-api-key-here")

st.set_page_config(page_title="🧪 CodeGrader AI (stdin)", layout="centered")
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
        "output": "{'Привет': 2, 'мир': 1, 'снова': 1}",
        "type": "function",
        "function_name": "count_word_frequencies"
    }
}

# Выбор задачи
task_name = st.selectbox("Выберите задачу:", list(tasks.keys()))
task = tasks[task_name]
st.markdown(f"### 🧩 Условие задачи:\n{task['text']}")

# Ввод кода
code = st.text_area("✏️ Впишите свой код:", height=300)

# Тестовые данные по умолчанию из задачи
def_input = task["input"]
def_output = task["output"]
test_input = st.text_area("📥 Тестовые данные для input():", value=def_input)
expected_output = st.text_input("📤 Ожидаемый вывод:", value=def_output)

# Кнопки разных уровней проверки
col1, col2, col3 = st.columns(3)
run_basic = col1.button("▶️ Проверить выполнение")
run_with_style = col2.button("🧪 Проверить со стилем")
run_with_gpt = col3.button("🤖 Проверить с GPT-помощью")

# Основная функция выполнения кода
def execute_code(code_text, test_input_text):
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

# Выполнение базовой проверки
if run_basic:
    output, tmp_path = execute_code(code, test_input)
    if output is not None:
        if output == expected_output:
            st.success("✅ Всё верно! Вывод совпадает с ожидаемым.")
        else:
            st.error("❌ Неверный результат.")
            st.text(f"Ожидалось: {expected_output}\nПолучено: {output}")
    os.remove(tmp_path)

# Выполнение с проверкой стиля
if run_with_style:
    output, tmp_path = execute_code(code, test_input)
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

# Полный анализ с GPT
if run_with_gpt:
    output, tmp_path = execute_code(code, test_input)
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

    st.markdown("### 💬 Советы от GPT")
    try:
        prompt = f"""
        Студент решает задачу:
        {task['text']}

        Его код:
        {code}

        Подскажи, есть ли ошибки, как улучшить структуру и стиль.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        st.markdown(response.choices[0].message.content)
    except Exception as e:
        st.warning(f"GPT не ответил: {e}")
    os.remove(tmp_path)