import telebot
from telebot import types
import os
from datetime import datetime
import json
import re
import ast
import autopep8
import black
import pylint.lint
from io import StringIO
import sys
import requests
import random
from PIL import Image
import io
import openai

# Конфигурация
# Используем предоставленный пользователем ключ OpenAI
OPENAI_API_KEY = "sk-ijklmnopqrstuvwxijklmnopqrstuvwxijklmnop"

# Получите НОВЫЙ токен у @BotFather:
# 1. Откройте Telegram
# 2. Найдите @BotFather
# 3. Отправьте команду /mybots, выберите вашего бота
# 4. Нажмите кнопку "API Token"
# 5. Скопируйте полученный токен сюда и замените "ВСТАВЬТЕ_НОВЫЙ_ТОКЕН_СЮДА"
BOT_TOKEN = "YOUR_BOT_TOKEN_BROYY"  # <-- ЗАМЕНИТЕ ЭТУ СТРОКУ

try:
    # Инициализация бота
    bot = telebot.TeleBot(BOT_TOKEN)
    # Инициализация клиента OpenAI
    openai.api_key = OPENAI_API_KEY
    # Проверка токена бота
    bot_info = bot.get_me()
    print(f"Бот успешно подключен: @{bot_info.username}")
except Exception as e:
    print(f"Ошибка при инициализации бота: {str(e)}")
    print("Пожалуйста, проверьте токен бота у @BotFather и ключ OpenAI, затем попробуйте снова")
    exit(1)


# Структура для хранения контекста пользователя
user_contexts = {}

# Шаблоны кода для генерации (оставляем для примера, хотя сейчас используется OpenAI)
CODE_TEMPLATES = {
    "веб-сайт": {
        "python": """from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)""",

        "html": """<!DOCTYPE html>
<html>
<head>
    <title>Мой сайт</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>Добро пожаловать</h1>
    </header>
    <main>
        <p>Это мой первый сайт!</p>
    </main>
</body>
</html>"""
    },

    "игра": {
        "python": """import pygame

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Моя игра")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255, 255, 255))
    pygame.display.flip()

pygame.quit()"""
    },

    "бот": {
        "python": """import telebot

bot = telebot.TeleBot('YOUR_BOT_TOKEN')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет!")

@bot.message_handler(content_types=['text'])
def handle_message(message):
    bot.reply_to(message, "Получил ваше сообщение!")

bot.polling()"""
    }
}

# API для генерации изображений (могут не поддерживать текстовое описание)
IMAGE_APIS = [
    "https://picsum.photos/800/600",  # Случайные изображения
    "https://source.unsplash.com/random/800x600"  # Unsplash
]

# API для генерации видео (могут не поддерживать текстовое описание и требуют ключи)
VIDEO_APIS = [
    "https://pixabay.com/api/videos/",  # Pixabay API (требует ключ API)
    "https://api.pexels.com/videos/search"  # Pexels API (требует ключ API)
]

# Предопределенные ответы для общих вопросов
PREDEFINED_RESPONSES = {
    "рекурсия": """Рекурсия - это процесс, при котором функция вызывает сама себя. Пример:

def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)

Основные принципы рекурсии:
1. Базовый случай (когда рекурсия останавливается)
2. Рекурсивный случай (вызов функции с другими параметрами)""",

    "сортировка": """Вот несколько способов сортировки в Python:

1. Встроенная функция sorted():
numbers = [5, 2, 8, 1, 9]
sorted_numbers = sorted(numbers)

2. Метод sort() для списков:
numbers = [5, 2, 8, 1, 9]
numbers.sort()

3. Сортировка пузырьком:
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr""",

    "api": """Пример использования API в Python с requests:

import requests

# GET запрос
response = requests.get('https://api.example.com/data')
data = response.json()

# POST запрос
data = {'key': 'value'}
response = requests.post('https://api.example.com/data', json=data)

# С заголовками
headers = {'Authorization': 'Bearer token'}
response = requests.get('https://api.example.com/data', headers=headers)""",

    "ооп": """Основы ООП в Python:

1. Классы и объекты:
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return f"Привет, я {self.name}"

2. Наследование:
class Student(Person):
    def __init__(self, name, age, grade):
        super().__init__(name, age)
        self.grade = grade

3. Инкапсуляция:
class BankAccount:
    def __init__(self):
        self.__balance = 0

    def deposit(self, amount):
        self.__balance += amount"""
}

# Добавим предопределенные ответы для учебных материалов
EDUCATIONAL_MATERIALS = {
    "python": "Основы Python: переменные, типы данных, циклы, условия. Посмотрите официальную документацию или интерактивные курсы на Codecademy.",
    "git": "Git - система контроля версий. Основные команды: git clone, git add, git commit, git push, git pull. Ресурсы: Git Handbook от GitHub.",
    "алгоритмы": "Изучите базовые алгоритмы: сортировка, поиск. Книги: 'Грокаем алгоритмы'. Онлайн-платформы: LeetCode, HackerRank.",
    "сети": "Основы компьютерных сетей: TCP/IP, HTTP, DNS. Ресурсы: Курсы на Coursera, книга 'Компьютерные сети' Таненбаум."
}


class UserContext:
    def __init__(self):
        self.conversation_history = []
        self.current_language = "python"
        self.current_task = None # Состояние текущей задачи (например, 'awaiting_code_desc')
        self.code_snippets = []
        self.last_interaction = datetime.now()

def get_user_context(user_id):
    if user_id not in user_contexts:
        user_contexts[user_id] = UserContext()
    return user_contexts[user_id]

# Функции для работы с кодом (локальные - оставлены для анализа, но не для генерации по шаблонам)
def format_code(code, formatter='autopep8'):
    """Форматирует код согласно стандартам PEP 8"""
    try:
        if formatter == 'autopep8':
            return autopep8.fix_code(code)
        elif formatter == 'black':
            return black.format_str(code, mode=black.FileMode())
        else:
            return code
    except Exception as e:
        return f"Ошибка форматирования: {str(e)}"

def check_code_quality(code):
    """Проверяет качество кода с помощью pylint (имитация)"""
    try:
        # Имитация ответа pylint
        output = "Имитация проверки качества кода:\nНет очевидных ошибок (локальный анализ ограничен)."
        return output
    except Exception as e:
        return f"Ошибка проверки кода: {str(e)}"

def extract_functions(code):
    """Извлекает все функции из кода"""
    try:
        tree = ast.parse(code)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node)
                })
        return functions
    except Exception as e:
        return f"Ошибка извлечения функций: {str(e)}"

def find_potential_issues(code):
    """Находит потенциальные проблемы в коде (очень простая имитация)"""
    issues = []
    for i, line in enumerate(code.split('\n'), 1):
        if len(line) > 79:
            issues.append(f"Строка {i}: Слишком длинная строка ({len(line)} символов)")
    try:
        tree = ast.parse(code)
        defined_vars = set()
        used_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    defined_vars.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                     used_vars.add(node.id)
        unused = defined_vars - used_vars
        if unused:
             issues.append(f"Возможно неиспользуемые переменные: {', '.join(unused)}")
    except:
        pass
    return issues

def suggest_improvements(code):
    """Предлагает улучшения для кода (очень простая имитация)"""
    improvements = []
    if 'for' in code and 'append' in code and not any(re.search(r'\[.* for .* in .*\]', line) for line in code.split('\n')):
        improvements.append("Рассмотрите использование list comprehension вместо цикла с append")
    if 'open(' in code and 'close()' not in code:
        improvements.append("Используйте контекстный менеджер (with) для работы с файлами")
    if 'range(' in code and 'len(' in code and not any(re.search(r'for .* in enumerate\(', line) for line in code.split('\n')):
        improvements.append("Используйте enumerate() вместо range(len())")
    return improvements

def generate_documentation(code):
    """Генерирует документацию для кода (очень простая имитация)"""
    try:
        tree = ast.parse(code)
        documentation = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                doc = {
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node) or "Нет документации",
                    'returns': None
                }
                if any(isinstance(child, ast.Return) for child in ast.walk(node)):
                     doc['returns'] = "Присутствует оператор return"
                documentation.append(doc)
        if not documentation:
             return "Не найдено функций для документирования."
        else:
            doc_strings = []
            for d in documentation:
                 doc_strings.append(f"Функция: {d['name']}({', '.join(d['args'])})\n  Документация: {d['docstring']}\n  Возвращает: {d['returns']}")
            return "Документация:\n\n" + "\n\n".join(doc_strings)
    except Exception as e:
        return f"Ошибка генерации документации: {str(e)}"

def optimize_code(code):
    """Предлагает оптимизации для кода (очень простая имитация)"""
    optimizations = []
    if 'for' in code and 'append' in code and not any(re.search(r'\[.* for .* in .*\]', line) for line in code.split('\n')):
        optimizations.append("Рассмотрите замену цикла с append на list comprehension")
    if 'import *' in code:
        optimizations.append("Избегайте 'import *', импортируйте конкретные объекты")
    if '+' in code and any(isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and isinstance(node.left, ast.Str) for node in ast.walk(ast.parse(code))):
         optimizations.append("Используйте метод .join() для эффективной конкатенации строк")
    if not optimizations:
        return "Локальный анализ не выявил очевидных предложений по оптимизации."
    else:
        return "Предложения по оптимизации:\n" + "\n".join(optimizations)


# Функция генерации кода через OpenAI
def generate_code_with_openai(prompt, language):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o", # Используем более новую модель, если доступна
            messages=[
                {"role": "system", "content": f"Ты опытный программист. Пиши чистый, эффективный код на {language}. Всегда добавляй краткие комментарии и при необходимости документацию. Предоставляй только код в блоке markdown, без лишних слов до или после."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при генерации кода через OpenAI: {str(e)}")
        return f"Извините, произошла ошибка при генерации кода: {str(e)}"

# Функция анализа кода через OpenAI
def analyze_code_with_openai(code):
    """Анализирует код с помощью OpenAI"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o", # Или другая доступная модель
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу кода. Найди потенциальные проблемы, предложи улучшения и лучшие практики. Форматируй ответ понятно, используй маркированные списки и блоки кода."},
                {"role": "user", "content": f"Проанализируй этот код:\n\n```\n{code}\n```"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при анализе кода через OpenAI: {str(e)}")
        return f"Извините, произошла ошибка при анализе кода: {str(e)}"

# Функция генерации изображения (заглушка для запроса с описанием)
def generate_image_with_description(prompt):
    """Генерирует изображение с описанием (через внешний API - может не поддерживаться или требовать ключ)"""
    try:
        # ВНИМАНИЕ: Текущие бесплатные API из IMAGE_APIS не поддерживают текстовое описание.
        # Здесь должна быть интеграция с API, которое поддерживает генерацию по тексту (например, DALL-E 2/3, Stable Diffusion API, Kandinsky API и т.п.).
        # Большинство таких API платные или имеют ограничения.

        # Для демонстрации логики:
        print(f"Попытка сгенерировать изображение с описанием: \"{prompt}\"")

        # Временно используем старый метод случайной генерации и сообщаем об ограничении
        api_url = random.choice(IMAGE_APIS)
        response = requests.get(api_url)
        if response.status_code == 200:
             # Добавляем информацию о том, что описание не было использовано
             return response.content, "Примечание: Бесплатные API для изображений могут не использовать ваше описание, генерируется случайное изображение."
        else:
            return None, f"Извините, не удалось сгенерировать изображение по описанию. Внешние API могут быть недоступны или не поддерживать эту функцию."

    except Exception as e:
        print(f"Ошибка при генерации изображения по описанию: {str(e)}")
        return None, f"Извините, произошла ошибка при генерации изображения: {str(e)}"

# Функция генерации видео (заглушка для запроса с описанием)
def generate_video_with_description(prompt):
    """Генерирует видео с описанием (через внешний API - может не поддерживаться, требовать ключ и быть нестабильным)"""
    try:
        # ВНИМАНИЕ: Текущие бесплатные API из VIDEO_APIS не поддерживают текстовое описание и требуют ключи.
        # Здесь должна быть интеграция с API, которое поддерживает генерацию видео по тексту (очень мало доступных и стабильных).

        # Для демонстрации логики:
        print(f"Попытка сгенерировать видео с описанием: \"{prompt}\"")

        # Временно используем старый метод случайной генерации (который скорее всего не сработает)
        # api_url = random.choice(VIDEO_APIS)
        # response = requests.get(api_url) # Этот вызов, вероятно, завершится ошибкой

        # Вместо реальной генерации, возвращаем сообщение об ограничении
        return None, "Извините, генерация видео по текстовому описанию недоступна через текущие бесплатные API. Они либо не поддерживают описания, либо требуют API ключи, либо нестабильны."


    except Exception as e:
        print(f"Ошибка при генерации видео по описанию: {str(e)}")
        return None, f"Извините, произошла ошибка при генерации видео: {str(e)}"


def get_predefined_response(text):
    """Получает предопределенный ответ на основе ключевых слов"""
    text = text.lower()
    for key, response in PREDEFINED_RESPONSES.items():
        if key in text:
            return response
    return None

def get_educational_material(topic):
    """Получает учебный материал по теме"""
    topic = topic.lower()
    for key, material in EDUCATIONAL_MATERIALS.items():
        if key in topic:
            return material
    return "Извините, у меня нет учебных материалов по этой теме. Попробуйте запросить 'Python', 'Git', 'Алгоритмы' или 'Сети'."


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    context = get_user_context(user_id)
    # Сбрасываем состояние задачи при старте
    context.current_task = None

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("💻 Создать код"),
        types.KeyboardButton("🔍 Анализ кода"),
        types.KeyboardButton("📚 Учебные материалы"),
        types.KeyboardButton("🖼 Сгенерировать изображение"),
        types.KeyboardButton("🎥 Сгенерировать видео"),
        types.KeyboardButton("ℹ️ О проекте")
    )

    welcome_text = (
        "👋 Привет! Я ваш AI-ассистент по программированию!\n\n"
        "Я могу:\n"
        "• Создавать код по вашему текстовому запросу (через OpenAI)\n"
        "• Анализировать и оптимизировать код (через OpenAI и локально)\n"
        "• Генерировать изображения (случайные, по запросу) и видео (по запросу - может быть нестабильно/недоступно)\n" # Обновлено описание
        "• Объяснять концепции программирования (из предопределенных ответов)\n"
        "• Помогать с отладкой и предлагать лучшие практики\n\n"
        "Выберите действие или просто напишите, что вам нужно!"
    )

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help(message):
    user_id = message.from_user.id
    context = get_user_context(user_id)
    # Сбрасываем состояние задачи при вызове help
    context.current_task = None

    help_text = (
        "📚 Доступные команды:\n\n"
        "/start - Начать работу с ботом и сбросить состояние\n"
        "/help - Показать это сообщение\n"
        "/language <язык> - Установить язык программирования (по умолчанию Python)\n"
        "/clear - Очистить историю диалога\n\n"
        "Вы также можете использовать кнопки или писать запросы текстом:\n"
        "• Нажмите кнопку 'Создать код', 'Анализ кода', 'Учебные материалы', 'Сгенерировать изображение' или 'Сгенерировать видео', а затем отправьте ваш запрос текстом.\n" # Объединено
        "• Кнопка 'О проекте' покажет информацию о проекте.\n\n"
        "Примеры текстовых запросов (для предопределенных ответов):\n"
        "• 'Объясни рекурсию'\n"
        "• 'Покажи пример сортировки'\n"
        "• 'Как использовать API?'\n"
        "• 'Объясни ООП'\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['language'])
def set_language(message):
    user_id = message.from_user.id
    context = get_user_context(user_id)
    # Сбрасываем состояние задачи
    context.current_task = None
    try:
        language = message.text.split(maxsplit=1)[1].strip().lower()
        if len(language) > 1 and ' ' not in language:
            context.current_language = language
            bot.reply_to(message, f"✅ Язык программирования установлен: {language}", parse_mode="Markdown")
        else:
             bot.reply_to(message, "❌ Укажите корректный язык программирования. Например: /language python", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Укажите язык программирования. Например: /language python", parse_mode="Markdown")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = message.from_user.id
    context = get_user_context(user_id)
    context.conversation_history = []
    # Сбрасываем состояние задачи
    context.current_task = None
    bot.reply_to(message, "✅ История диалога очищена", parse_mode="Markdown")


@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.from_user.id
    context = get_user_context(user_id)

    # Обновляем время последнего взаимодействия и добавляем сообщение в историю
    context.last_interaction = datetime.now()
    context.conversation_history.append({"role": "user", "content": message.text})

    text = message.text.lower().strip() # Добавил .strip()

    # === ШАГ 1: Проверяем, нажата ли одна из специальных кнопок ===
    # Если текст сообщения совпадает с текстом кнопки, устанавливаем состояние и запрашиваем ввод
    if text == "💻 создать код":
        context.current_task = "awaiting_code_description"
        bot.reply_to(message, "Отлично! Введите запрос для создания кода:", parse_mode="Markdown")
        return # Завершаем обработку, т.к. ожидаем следующий ввод

    elif text == "🔍 анализ кода":
         context.current_task = "awaiting_code_for_analysis"
         bot.reply_to(message, "Отлично! Введите запрос для анализа кода (отправьте сам код):", parse_mode="Markdown")
         return # Завершаем обработку, т.к. ожидаем следующий ввод

    elif text == "📚 учебные материалы":
        context.current_task = "awaiting_educational_topic"
        bot.reply_to(message, "Отлично! Введите запрос для получения учебных материалов (тема):", parse_mode="Markdown")
        return # Завершаем обработку, т.к. ожидаем следующий ввод

    elif text == "🖼 сгенерировать изображение":
        context.current_task = "awaiting_image_description"
        bot.reply_to(message, "Отлично! Введите запрос для генерации изображения (описание):", parse_mode="Markdown")
        # Предупреждение о возможном игнорировании описания бесплатными API
        bot.send_message(message.chat.id, "Примечание: Текущие бесплатные API для изображений могут не использовать ваше описание, генерируется случайное изображение.", parse_mode="Markdown")
        return # Завершаем обработку, т.к. ожидаем следующий ввод

    elif text == "🎥 сгенерировать видео":
        context.current_task = "awaiting_video_description"
        bot.reply_to(message, "Отлично! Введите запрос для генерации видео (описание):", parse_mode="Markdown")
        # Предупреждение о нестабильности/недоступности генерации видео по описанию
        bot.send_message(message.chat.id, "Примечание: Генерация видео по текстовому описанию через текущие бесплатные API может быть недоступна, нестабильна или требовать ключи.", parse_mode="Markdown")
        return # Завершаем обработку, т.к. ожидаем следующий ввод

    elif text == "ℹ️ о проекте":
        about_text = (\
            "Приветствую, дорогой друг!\\n\\n"\
            "Это бесплатный мощный AI инструмент для кодинга и генераций фото и видео.\\n"\
            "Разработчик: @workcomru\\n\\n"\
            "Если хочешь поддержать меня, отправь мне подарок хех\\n"\
            "Удачи! :3"\
        )
        bot.reply_to(message, about_text, parse_mode="Markdown")
        context.current_task = None # Сбрасываем задачу, т.к. здесь нет ожидания
        return

    # === ШАГ 2: Если не кнопка, проверяем, ожидается ли ответ на предыдущий запрос (т.е. пользователь ввел запрос после нажатия кнопки) ===
    if context.current_task == "awaiting_code_description":
        prompt = message.text
        language = context.current_language
        bot.send_message(message.chat.id, f"Генерирую код на {language} по вашему запросу...", parse_mode="Markdown") # Уведомление
        code = generate_code_with_openai(prompt, language)

        # Проверяем на ошибку из функции и отправляем результат
        bot.reply_to(message, code, parse_mode="Markdown")

        # Если генерация была успешной и вернула код (не ошибку), сохраняем его
        if "```" in code and "Извините, произошла ошибка при генерации кода" not in code:
             code_match = re.search(r'```(?:\w+\n)?(.*?)```', code, re.S)
             if code_match:
                 context.code_snippets.append(code_match.group(1).strip())
             else:
                 context.code_snippets.append(code)

        context.current_task = None # Сбрасываем задачу после обработки
        return # Завершаем обработку этого сообщения

    elif context.current_task == "awaiting_code_for_analysis":
        code_to_analyze = message.text
        context.code_snippets.append(code_to_analyze) # Сохраняем полученный код

        bot.send_message(message.chat.id, "Анализирую код...", parse_mode="Markdown") # Уведомление

        # Используем OpenAI для анализа кода
        analysis_result = analyze_code_with_openai(code_to_analyze)

        bot.reply_to(message, analysis_result, parse_mode="Markdown")

        context.current_task = None # Сбрасываем задачу
        return # Завершаем обработку этого сообщения

    elif context.current_task == "awaiting_educational_topic":
        topic = message.text
        material = get_educational_material(topic)
        bot.reply_to(message, material, parse_mode="Markdown")
        context.current_task = None # Сбрасываем задачу
        return # Завершаем обработку этого сообщения

    elif context.current_task == "awaiting_image_description":
        prompt = message.text
        bot.send_message(message.chat.id, f"Генерирую изображение по описанию: \"{prompt}\"...", parse_mode="Markdown") # Уведомление
        image_content, note = generate_image_with_description(prompt) # Используем функцию с описанием

        if image_content:
            try:
                img_byte_arr = io.BytesIO(image_content)
                img_byte_arr.seek(0)
                bot.send_photo(message.chat.id, img_byte_arr, caption=f"Вот сгенерированное изображение!\n{note}", parse_mode="Markdown") # Добавляем примечание
            except Exception as e:
                print(f"Ошибка при отправке фото: {str(e)}")
                bot.reply_to(message, "Извините, не удалось отправить изображение.", parse_mode="Markdown")
        else:
            bot.reply_to(message, note, parse_mode="Markdown") # Отправляем только примечание/сообщение об ошибке

        context.current_task = None # Сбрасываем задачу после обработки
        return

    elif context.current_task == "awaiting_video_description":
        prompt = message.text
        bot.send_message(message.chat.id, f"Генерирую видео по описанию: \"{prompt}\"...", parse_mode="Markdown") # Уведомление
        video_content, note = generate_video_with_description(prompt) # Используем функцию с описанием

        if video_content:
             try:
                 video_filename = f"temp_video_{user_id}.mp4" # Убедитесь, что расширение правильное
                 with open(video_filename, 'wb') as f:
                     f.write(video_content)
                 with open(video_filename, 'rb') as f:
                      bot.send_video(message.chat.id, f, caption=f"Вот сгенерированное видео!\n{note}", parse_mode="Markdown") # Добавляем примечание
                 os.remove(video_filename) # Удаляем временный файл
             except Exception as e:
                  print(f"Ошибка при отправке видео: {str(e)}")
                  bot.reply_to(message, "Извините, не удалось отправить видео.", parse_mode="Markdown")
        else:
            bot.reply_to(message, note, parse_mode="Markdown") # Отправляем только примечание/сообщение об ошибке

        context.current_task = None # Сбрасываем задачу после обработки
        return


    # === ШАГ 3: Если не кнопка и не ожидается ответ, обрабатываем как обычный текстовый запрос ===
    # Проверяем, есть ли предопределенный ответ на текст сообщения
    predefined_response = get_predefined_response(text)
    if predefined_response:
        bot.reply_to(message, predefined_response, parse_mode="Markdown")
        context.current_task = None # Сбрасываем задачу
        return

    # === ШАГ 4: Если ничего не сработало ===
    bot.reply_to(message, "Извините, я не понимаю этот запрос. Попробуйте использовать команды (/start, /help) или кнопки.", parse_mode="Markdown")
    context.current_task = None # Сбрасываем задачу
    return


def run_bot():
    print("Бот запущен...")
    # bot.infinity_polling() # Альтернатива polling
    bot.polling(none_stop=True)

if __name__ == "__main__":
    run_bot()
