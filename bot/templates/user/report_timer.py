def format_futures_update(old_list: list, new_list: list) -> str:
    """
    Формирует сообщение для админа о смене списка фьючерсов.
    
    :param old_list: старый список фьючерсов
    :param new_list: новый список фьючерсов
    :return: готовый текст сообщения
    """
    # Преобразуем в строки для вывода
    old_str = ', '.join(old_list) if old_list else '—'
    new_str = ', '.join(new_list) if new_list else '—'

    # Если новый список пуст
    if not new_list:
        return (
            f"⚠️ Новый список фьючерсов оказался пустым.\n"
            f"📌 Оставлен старый список ({len(old_list)}):\n"
            f"{old_str}"
        )
    
    # Если новый список непустой — стандартная замена
    return (
        f"⚠️ Обновлён список фьючерсов!\n\n"
        f"📉 Было ({len(old_list)}):\n"
        f"{old_str}\n\n"
        f"📈 Стало ({len(new_list)}):\n"
        f"{new_str}"
    )