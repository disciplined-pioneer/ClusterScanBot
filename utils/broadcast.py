import re
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы MarkdownV2"""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


# Поиска всех ссылок в тексте
def extract_urls(text: str) -> list: 
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    return urls


# Удаляем все http/https ссылки
def remove_urls(text: str) -> str:
    
    url_pattern = r'https?://[^\s,]+'
    cleaned_text = re.sub(url_pattern, '', text)
    
    # Удаляем лишние пробелы и запятые, если они остались после удаления
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)  # двойные пробелы
    cleaned_text = re.sub(r'\s+,', ',', cleaned_text)    # пробел перед запятой
    cleaned_text = re.sub(r',\s+', ', ', cleaned_text)   # нормализация запятых
    return cleaned_text.strip()


# Получение кнопок для обработки ссылок
def create_url_keyboard(text: str, keyboard: list[list[InlineKeyboardButton]] = None):
    if keyboard:
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    urls = extract_urls(text)
    if not urls:
        return None

    buttons = []
    if len(urls) == 1:
        buttons.append([InlineKeyboardButton(text="Ссылка", url=urls[0])])
    else:
        for i, url in enumerate(urls, 1):
            buttons.append([InlineKeyboardButton(text=f"Ссылка {i}", url=url)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Отправка рассылки
async def send_preview(message: Message, content: dict, parse_mode):
    markup = create_url_keyboard(content["caption"], content.get("keyboard", []))
    try:
        if content["msg_type"] == "text":
            await message.answer(remove_urls(content["caption"]), parse_mode=parse_mode, reply_markup=markup)
        elif content["msg_type"] == "photo":
            await message.answer_photo(content["file_id"], caption=remove_urls(content["caption"]), parse_mode=parse_mode, reply_markup=markup)
        elif content["msg_type"] == "video":
            await message.answer_video(content["file_id"], caption=remove_urls(content["caption"]), parse_mode=parse_mode, reply_markup=markup)
        elif content["msg_type"] == "audio":
            await message.answer_audio(content["file_id"], caption=remove_urls(content["caption"]), parse_mode=parse_mode, reply_markup=markup)
        elif content["msg_type"] == "document":
            await message.answer_document(content["file_id"], caption=remove_urls(content["caption"]), parse_mode=parse_mode, reply_markup=markup)
    except Exception as e:
        await message.answer(f"Ошибка при создании превью: {e}")
