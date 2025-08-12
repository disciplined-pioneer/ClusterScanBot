futures_selection_msg = 'Выберите один из фьючерсов'

enter_futures_msg = "Введите фьючерс, который хотите проанализировать"

start_data_collection_msg = '📊 Начинаем сбор данных...'

data_collection_finished_msg = '✅ Сбор данных окончен! Проводим анализ фьючерса...'

futures_analyzed_msg = '📈 Фьючерс был проанализирован!'

select_timeframe_msg = "⚠️ Пожалуйста, выберите хотя бы один ТФ для анализа!"

def format_timeframes_message(futures_name: str) -> str:
    return (
        f'Вы выбрали фьючерс <i><b>"{futures_name}"</b></i>\n\n'
        'Пожалуйста, выберите таймфреймы для анализа:'
    )