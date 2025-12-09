import os
import pandas as pd
import seaborn as sns
import mplfinance as mpf
import matplotlib.pyplot as plt


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

        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)

        sns.set(style="darkgrid")
        fig, ax = plt.subplots(
            2, 1, gridspec_kw={"height_ratios": [3, 1]}, figsize=(15, 10), dpi=200
        )

        mpf.plot(
            data,
            type='ohlc',
            ax=ax[0],
            style='classic',
            volume=False
        )

        # === ДОБАВЛЕН ОБЪЁМ ПОД БАРЫ ===
        ax_vol = ax[0].twinx()
        ax_vol.bar(
            data.index,
            data["volume"],
            width=0.6,
            alpha=0.25,
            color="#000000"
        )
        ax_vol.set_yticks([])      # скрываем ось объёма
        ax_vol.set_ylim(0, data["volume"].max() * 3)  # чтобы столбики были «низом» графика

        # уровни
        for levels, color in vap_levels:
            for level in levels.values():
                ax[0].axhline(level, color=color, linestyle="-", linewidth=1)

        # аномалии
        ax[0].plot(
            anomaly.index, anomaly["close"],
            "bs", alpha=0.6, markersize=8, label="Аномалия - кластер"
        )

        ax[0].set_title(f"Ценовые данные с аномалиями. График: {futures_name}, ТФ: {time_frame}")
        ax[0].legend()

        # кумулятивная дельта
        ax[1].plot(data.index, cum_delta, color="#696969")

        plt.tight_layout()
        return self._save_plot(fig, futures_name, time_frame, number)

    def visualize_anomalies_senior(self, data, vap_levels: list, futures_name: str, time_frame: str, number: int=1):
        """График с аномалиями"""
        anomaly = data[data["is_anomaly"]]

        # гарантируем правильный индекс
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)

        sns.set(style="darkgrid")

        # ОДИН AX
        fig, ax = plt.subplots(figsize=(15, 8), dpi=200)

        # OHLC бары
        mpf.plot(
            data,
            type='ohlc',
            ax=ax,
            style='classic',
            volume=False
        )

        # Уровни
        for levels, color in vap_levels:
            for level in levels.values():
                ax.axhline(level, color=color, linestyle="-", linewidth=1)

        # Аномалии
        ax.plot(
            anomaly.index,
            anomaly["close"],
            "bs",
            alpha=0.6,
            markersize=8,
            label="Аномалия - кластер"
        )

        # Заголовок / Легенда
        ax.set_title(f"Ценовые данные с аномалиями. График: {futures_name}, ТФ: {time_frame}")
        ax.legend()

        plt.tight_layout()
        return self._save_plot(fig, futures_name, time_frame, number)

    def get_saved_files(self):
        """Возвращает список всех сохранённых файлов"""
        return self.saved_files
