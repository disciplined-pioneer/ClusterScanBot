def format_futures_update(old_list: list, new_list: list) -> str:
    """
    Формирует сообщение для админа о смене списка фьючерсов.
    
    :param old_list: старый список фьючерсов
    :param new_list: новый список фьючерсов
    :return: готовый текст сообщения
    """
    old_set = set(old_list)
    new_set = set(new_list)

    old_count = len(old_list)
    new_count = len(new_list)

    # Новые фьючерсы — которые появились в new_list, но отсутствовали в old_list
    added_futures = new_set - old_set
    added_count = len(added_futures)

    # Процент отобранных к исходным
    percent = new_count / 402 * 100

    # Формируем списки для вывода
    old_str = ', '.join(old_list) if old_list else '—'
    new_str = ', '.join(new_list) if new_list else '—'
    added_str = ', '.join(sorted(added_futures)) if added_futures else '—'

    if not new_list:
        return (
            f"⚠️ Новый список фьючерсов оказался пустым.\n"
            f"📌 Оставлен старый список ({old_count}):\n"
            f"{old_str}"
        )

    return (
        f"⚠️ Обновлён список фьючерсов!\n\n"
        f"📊 Исходное общее количество фьючерсов: {old_count}\n"
        f"📈 Отобрано по итогу: {new_count} ({percent:.1f}%)\n\n"
        f"✨ Новых добавлено: {added_count}\n"
        f"Новые фьючерсы: {added_str}\n\n"
        f"📉 Было ({old_count}):\n"
        f"{old_str}\n\n"
        f"📈 Стало ({new_count} - {percent:.1f}%)\n"
        f"{new_str}"
    )
