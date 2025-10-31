import os
os.environ["OMP_NUM_THREADS"] = "1"

import warnings
warnings.filterwarnings("ignore", message="KMeans is known to have a memory leak")

import numpy as np
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

from scipy.stats import norm
from scipy.stats import gaussian_kde
from sklearn.mixture import GaussianMixture


class GaussianDistributionFinder:
    """
    Класс для поиска гауссовских распределений (кластеров) в данных
    и выделения их интервалов по временной оси.
    """

    def __init__(self, max_components=10, column=None):
        """
        Инициализация параметров модели.
        :param max_components: максимальное количество гауссовских компонент для подбора
        :param column: имя столбца в DataFrame, по которому строится распределение
        """
        self.max_components = max_components
        self.column = column

    def fit(self, df):
        """
        Подбор оптимальной модели GMM (Gaussian Mixture Model) по BIC-критерию.
        :param df: pandas.DataFrame с колонкой цен или данных
        :return: список интервалов индексов, соответствующих кластерам
        """
        # Извлечение данных
        data = df[self.column].values.reshape(-1, 1) if self.column else df.values.reshape(-1, 1)

        best_bic = np.inf
        best_model = None

        # Перебор количества компонент (кластеров) и выбор модели с минимальным BIC
        for k in range(1, self.max_components + 1):
            gmm = GaussianMixture(n_components=k, random_state=42, n_init=5)
            gmm.fit(data)
            bic = gmm.bic(data)
            if bic < best_bic:
                best_bic = bic
                best_model = gmm

        # Сохранение параметров модели
        self.model = best_model
        self.labels = self.model.predict(data)
        self.data = data.flatten()
        self.df = df
        self.intervals = self._extract_intervals_grouped()
        return self.intervals

    def _extract_intervals_grouped(self, central_fraction=0.8):
        """
        Выделяет интервалы индексов для центральной части каждого кластера.
        :param central_fraction: доля данных внутри каждого кластера, считаемая «основным объёмом»
        :return: список пар [start_idx, end_idx]
        """
        intervals = []
        labels = self.labels
        unique_labels = np.unique(labels)
    
        for lbl in unique_labels:
            idx = np.where(labels == lbl)[0]
            if len(idx) == 0:
                continue
    
            # Вычисляем границы центральной части кластера (по квантилям)
            q_low = (1 - central_fraction) / 2
            q_high = 1 - q_low
            start_idx = int(np.quantile(idx, q_low))
            end_idx = int(np.quantile(idx, q_high))
    
            if start_idx >= end_idx:
                continue
    
            intervals.append([start_idx, end_idx])
        
        # Сортировка по оси времени
        intervals = sorted(intervals, key=lambda x: x[0])
        return intervals
        
    def summary(self):
        """
        Возвращает краткую сводку по найденной модели:
        количество компонент, параметры каждой (вес, среднее, σ) и интервалы.
        """
        params = []
        for w, m, c in zip(self.model.weights_, self.model.means_, self.model.covariances_):
            params.append({
                "weight": float(w),
                "mean": float(m[0]),
                "sigma": float(np.sqrt(c[0][0]))
            })
        return {
            "n_components": self.model.n_components,
            "params": params,
            "intervals": self.intervals
        }

    def plot_gmm(self, bins=50):
        """
        Визуализирует общую смесь Гауссов (GMM) и каждую компоненту отдельно.
        Показывает плотность распределения данных и сглаженные кривые.
        """
        data = self.df[self.column].values

        sns.set(style='darkgrid')
        plt.figure(figsize=(12, 6))
        plt.hist(data, bins=bins, density=True, alpha=0.3, color="gray", label="Данные")

        # Общая плотность вероятности смеси
        x = np.linspace(data.min(), data.max(), 1000).reshape(-1, 1)
        logprob = self.model.score_samples(x)
        pdf = np.exp(logprob)
        plt.plot(x, pdf, '-k', lw=2, label='Общая смесь (GMM)')

        colors = plt.cm.tab10(np.linspace(0, 1, self.model.n_components))

        # Отдельные компоненты модели
        for i, (w, m, c) in enumerate(zip(self.model.weights_, self.model.means_, self.model.covariances_)):
            mean = m[0]
            sigma = np.sqrt(c[0][0])
            component_pdf = w * norm.pdf(x, mean, sigma)
            plt.plot(x, component_pdf, color=colors[i], lw=2.2, label=f'Распределение {i+1}')

        plt.title("Гауссовские распределения (KDE / VA визуализация)", fontsize=14)
        plt.xlabel(self.column)
        plt.ylabel("Плотность вероятности")
        plt.legend()
        plt.show()

    def plot_intervals(self):
        """
        Отображает временной ряд с найденными кластерами и уровнями VAH, VAL, POC
        для каждого интервала, определённого через ValueAreaProfile.
        """
        data = self.df[self.column].values
        x = np.arange(len(data))

        sns.set_style(style="darkgrid")
        plt.figure(figsize=(14, 6))
        plt.plot(x, data, color="black", lw=1.5, label="Данные")
    
        # Цветовая палитра для визуального разделения интервалов
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.intervals)))

        for i, (start, end) in enumerate(self.intervals):
            close_series = self.df[self.column].iloc[start:end]
            if len(close_series) > 1:   # проверка на минимальное количество данных
                vap = ValueAreaProfile(close_series)
                levels = vap.calculate()
    
                # Линии уровней VAH / VAL / POC на отрезке интервала
                end = self.df.iloc[-1].name
                plt.hlines(levels['VAH'], xmin=start, xmax=end, color=colors[i], linestyle='-', linewidth=1.5)
                plt.hlines(levels['VAL'], xmin=start, xmax=end, color=colors[i], linestyle='-', linewidth=1.5)
                plt.hlines(levels['POC'], xmin=start, xmax=end, color=colors[i], linestyle='-', linewidth=2)
    
                # Полупрозрачный фон для обозначения интервала
                plt.axvspan(start, end, color=colors[i], alpha=0.1)
    
        plt.title("Найденные Гауссовские распределения", fontsize=14)
        plt.xlabel("Индекс")
        plt.ylabel(self.column)
        plt.show()
    
    def plot_histogram(self, bins=50):
        """
        Горизонтальная гистограмма распределения данных с нанесёнными уровнями VAH, VAL, POC.
        Подходит для визуального анализа диапазонов объёмов.
        """
        sns.set_style(style="darkgrid")
        plt.figure(figsize=(14, 6))
        sns.histplot(y=self.df[self.column], bins=bins, alpha=0.3)
    
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.intervals)))
    
        # Для каждого интервала считаем уровни и рисуем горизонтальные линии
        for i, (start, end) in enumerate(self.intervals):
            close_series = self.df[self.column].iloc[start:end]
            if len(close_series) > 1:
                vap = ValueAreaProfile(close_series)
                levels = vap.calculate()
    
                plt.axhline(y=levels['VAH'], color=colors[i], linestyle='--', linewidth=2)
                plt.axhline(y=levels['VAL'], color=colors[i], linestyle='--', linewidth=2)
                plt.axhline(y=levels['POC'], color=colors[i], linestyle='--', linewidth=2)
    
        plt.title("Гистограмма с уровнями VAH/VAL/POC", fontsize=14)
        plt.xlabel("Количество")
        plt.ylabel(self.column)
        plt.show()


class ValueAreaProfile:
    """
    Вычисляет VAH, VAL и POC по Series цен закрытия.
    """
    def __init__(self, prices: pd.Series, bandwidth: float = 0.002):
        """
        :param prices: Series с ценами close
        :param bandwidth: сглаживание для KDE
        """
        self.prices = prices.dropna().values
        self.bandwidth = bandwidth
        self.price_grid = None
        self.pdf = None
        self.val = None
        self.vah = None
        self.poc = None

    def _build_density(self):
        """Строим ядровую плотность по ценам close"""
        if len(self.prices) < 2:
            raise ValueError("Недостаточно данных для KDE")
        self.kde = gaussian_kde(self.prices, bw_method=self.bandwidth)
        self.price_grid = np.linspace(self.prices.min(), self.prices.max(), 500)
        self.pdf = self.kde(self.price_grid)

    def _find_value_area(self, coverage: float = 0.7):
        """Находит VAH/VAL/POC по охвату 70% плотности"""
        poc_idx = np.argmax(self.pdf)
        self.poc = self.price_grid[poc_idx]

        pdf_norm = self.pdf / self.pdf.sum()
        cumsum = np.cumsum(pdf_norm)

        lower_idx = np.where(cumsum >= (1 - coverage) / 2)[0][0]
        upper_idx = np.where(cumsum >= 1 - (1 - coverage) / 2)[0][0]

        self.val = self.price_grid[lower_idx]
        self.vah = self.price_grid[upper_idx]

    def calculate(self, coverage: float = 0.7):
        """Главный метод: возвращает VAH, VAL, POC"""
        self._build_density()
        self._find_value_area(coverage)
        return {
            "VAH": float(self.vah),
            "VAL": float(self.val),
            "POC": float(self.poc)
        }


def get_vap_levels(df, column="close", max_components=2):
    """
    Возвращает уровни Value Area Profile (VAP) для распределений,
    найденных методом Gaussian Mixture.

    Для каждого найденного интервала рассчитываются уровни VAP
    (например, VAH, VAL, POC) и присваивается уникальный цвет.

    Parameters
    ----------
    df : DataFrame — исходные данные с ценами
    column : str — название ценового столбца (по умолчанию "close")
    max_components : int — максимальное число распределений

    Returns
    -------
    list[tuple[list, tuple]] — список (levels, color)
    """
    finder = GaussianDistributionFinder(max_components=max_components, column=column)
    intervals = finder.fit(df)
    colors = sns.color_palette("husl", len(intervals))  

    result = []
    for i, interval in enumerate(intervals):
        close_series = df[column].iloc[interval[0]:interval[1]]
        if len(close_series) > 1:
            vap = ValueAreaProfile(close_series)
            levels = vap.calculate()
            result.append((levels, colors[i]))

    # Вывод всех графиков
    #finder.plot_intervals()
    #finder.plot_histogram()
    #finder.plot_gmm()

    return result


# --- пример использования ---
# df['close'] = np.random.normal(100, 5, 500)
# vap = ValueAreaProfile(df['close'])
# levels = vap.calculate()
# print(levels)


# Поиск VA
#vap_levels = get_vap_levels(df, column="close", max_components=2)
#print(vap_levels)