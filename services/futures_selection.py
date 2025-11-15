import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc


class FuturesVisualizer:

    def __init__(self, save_dir: str = r"data\chats"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.saved_files = []

    def _save_plot(self, fig, futures: str, time_frame: str, number: int):
        """Сохраняет график и запоминает путь"""
        file_name = f"{number}_{futures}_{time_frame}.png"
        file_path = os.path.join(self.save_dir, file_name)

        plt.savefig(file_path)
        plt.close(fig)

        self.saved_files.append(file_path)
        return file_path

    def visualize_anomalies_junior(self, data, vap_levels: list, futures_name: str, time_frame: str, number: int=1):
        """График с аномалиями и кумулятивной дельтой"""
        cum_delta = data["delta"].cumsum()
        anomaly = data[data["is_anomaly"]]

        sns.set(style="darkgrid")
        fig, ax = plt.subplots(
            2, 1, gridspec_kw={"height_ratios": [3, 1]}, figsize=(15, 10), dpi=200
        )

        candlestick_ohlc(
            ax[0],
            zip(np.arange(len(data)), data['open'], data['high'], data['low'], data['close']),
            width=0.6, colorup='g', colordown='r', alpha=0.5
        )

        # Рисуем уровни
        for levels, color in vap_levels:
            for level in levels.values():
                ax[0].axhline(level, color=color, linestyle="-", linewidth=1)

        ax[0].plot(anomaly.index, anomaly["close"], "bs", alpha=0.6,
                   markersize=8, label="Аномалия - кластер")
        ax[0].set_title(f"Ценовые данные с аномалиями. График: {futures_name}, ТФ: {time_frame}")
        ax[0].legend()

        ax[1].plot(data.index, cum_delta, color="#696969")

        plt.tight_layout()
        return self._save_plot(fig, futures_name, time_frame, number)

    def visualize_anomalies_senior(self, data, vap_levels: list, futures_name: str, time_frame: str, number: int=1):
        """График с аномалиями + вертикальный объём"""
        anomaly = data[data["is_anomaly"]]

        sns.set(style="darkgrid")
        fig, ax = plt.subplots(
            2, 1, gridspec_kw={"height_ratios": [3, 1]}, figsize=(15, 10), dpi=200
        )

        # Основной график — свечи
        candlestick_ohlc(
            ax[0],
            zip(np.arange(len(data)), data['open'], data['high'], data['low'], data['close']),
            width=0.6, colorup='g', colordown='r', alpha=0.5
        )

        # Уровни
        for levels, color in vap_levels:
            for level in levels.values():
                ax[0].axhline(level, color=color, linestyle="-", linewidth=1)

        # Аномалии
        ax[0].plot(
            anomaly.index,
            anomaly["close"],
            "bs",
            alpha=0.6,
            markersize=8,
            label="Аномалия - кластер"
        )

        # === ВЕРТИКАЛЬНЫЙ ОБЪЁМ ===
        ax[1].bar(
            data.index,
            data["volume"],
            color="#000000", 
            alpha=0.35,
            width=0.8,
            align='center'
        )

        # Титл и легенда
        ax[0].set_title(f"Ценовые данные с аномалиями. График: {futures_name}, ТФ: {time_frame}")
        ax[0].legend()

        plt.tight_layout()
        return self._save_plot(fig, futures_name, time_frame, number)

    def get_saved_files(self):
        """Возвращает список всех сохранённых файлов"""
        return self.saved_files
