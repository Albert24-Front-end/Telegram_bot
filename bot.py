import os
from dotenv import load_dotenv
import telebot
import speech_recognition
from pydub import AudioSegment

load_dotenv()

token = os.getenv('BOT_TOKEN')
# Создаем бота, передаем ему токен из BotFather
bot = telebot.TeleBot(token)

TEMP_DIR = 'temp_audio'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Конвертация формата файлов oga в wav
def convert_voice_format(filename):
    new_filename = filename.replace('.oga', '.wav')
    audio = AudioSegment.from_file(filename)
    audio.export(new_filename, format='wav')
    return new_filename

# Конвертация формата аудио в текст
def convert_voice_to_text(oga_filename):
    wav_filename = convert_voice_format(oga_filename)
    recognizer = speech_recognition.Recognizer()

    try:
        with speech_recognition.AudioFile(wav_filename) as source:
            # Настройка для улучшения распознавания
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language='ru-RU')

    except speech_recognition.UnknownValueError:
        text = "Не удалось распознать речь. Попробуйте говорить четче."
    except speech_recognition.RequestError as e:
        text = f"Ошибка сервиса распознавания: {e}"
    except Exception as e:
        text = f"Неизвестная ошибка: {e}"
    finally:
        # Удаляем файлы в любом случае
        try:
            if os.path.exists(oga_filename):
                os.remove(oga_filename)
            if os.path.exists(wav_filename):
                os.remove(wav_filename)
        except Exception as e:
            print(f"Ошибка удаления файлов: {e}")

    return text

# Скачивание файла, который прислал пользователь
def download_file(bot, file_id):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = os.path.join(TEMP_DIR, file_id + file_info.file_path.replace('/', '_'))

    with open(filename, 'wb') as f:
        f.write(downloaded_file)

    return filename

#@ - инструкция, для чего применяется последующая функция - здесь ф-ия say_hello применяется для обработчика сообщений бота в случае запуска команды старт
@bot.message_handler(commands=['start', 'salom', 'привет'])
def say_hello(message):
    bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name)

# @bot.message_handler(content_types=['sticker'])
# def get_sticker_id(message):
#     sticker_id = message.sticker.file_id
#     bot.send_message(message.chat.id, f"ID стикера: {sticker_id}")
#     print(f"Sticker ID: {sticker_id}")

@bot.message_handler(commands=['sticker'])
def send_sticker(message):
    sticker_id = 'CAACAgIAAxkBAAMTaQABcorHcO-j4ygkmOJe47yJnKw8AAJfGwACnUAISYL_u2xgtamZNgQ'
    bot.send_sticker(message.chat.id, sticker_id)

    # Вариант 2: Из файла
    # sticker_path = os.path.join('stickers', 'my_sticker.webm')
    # try:
    #     with open(sticker_path, 'rb') as sticker:
    #         bot.send_sticker(message.chat.id, sticker)
    # except FileNotFoundError:
    #     bot.send_message(message.chat.id, "❌ Стикер не найден!")
    #     print(f"Файл не найден: {sticker_path}")

# инструкция для обработчика в случае, если тип файла - аудио. Функция отправки текста
@bot.message_handler(content_types=['voice'])
def send_transcript(message):
    try:
        bot.send_message(message.chat.id, "⏳ Обрабатываю голосовое сообщение...")
        filename = download_file(bot, message.voice.file_id)
        text = convert_voice_to_text(filename)
        bot.send_message(message.chat.id, f"📝 Распознано:\n{text}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")
        print(f"Ошибка в send_transcript: {e}")

print("Бот запущен...")
bot.polling()

