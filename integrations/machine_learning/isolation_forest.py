

import numpy as np
import pandas as pd
from typing import Union, List
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    
    def __init__(self, contamination: float = 0.2, random_state: int = 42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.fitted = False

    def fit(self, df: pd.DataFrame, columns: Union[str, List[str]]):
        """Обучает модель на указанных колонках, либо на всех числовых, если columns == 'ALL'"""
        self.data = df.copy()

        if columns == "ALL":
            self.columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        elif isinstance(columns, str):
            self.columns = [columns]
        else:
            self.columns = columns

        if not self.columns:
            raise ValueError("Нет числовых колонок для обучения.")

        X = self.data[self.columns].values
        self.model.fit(X)
        self.fitted = True

    def get_filtered_anomalies(self, reference_column: str = None, direction: str = "up") -> pd.DataFrame:
        """
        Возвращает DataFrame с колонкой is_anomaly, где True — выбросы по направлению
        """
        if not self.fitted:
            raise ValueError("Сначала вызови .fit(df, columns)")

        X = self.data[self.columns].values
        scores = self.model.decision_function(X)
        preds = self.model.predict(X)

        self.data['score'] = scores
        self.data['pred'] = preds

        # СДЕЛАЙ ФИЛЬТРАЦИЮ ПО КОЛОКНКЕ И СТРОЧКЕ, ЕСЛИ СТРОЧКА, ТО ДОЛЖЕН БЫТЬ РАСЧЁТ

        # Выбор колонки для определения направления
        if reference_column is None:
            reference_column = self.columns[0]

        if reference_column not in self.data.columns:
            raise ValueError(f"Колонка {reference_column} не найдена в данных.")

        median_value = self.data[reference_column].median()

        if direction == "up":
            condition = (preds == -1) & (self.data[reference_column] > median_value)
        elif direction == "down":
            condition = (preds == -1) & (self.data[reference_column] < median_value)
        elif direction == "both":
            condition = preds == -1
        else:
            raise ValueError("direction должен быть 'up', 'down' или 'both'")

        self.data['is_anomaly'] = condition
        return self.data.copy()

    def run(self, df: pd.DataFrame, columns: Union[str, List[str]] = "ALL",
            reference_column: str = None, direction: str = "up") -> pd.DataFrame:
        """
        Объединённая точка входа: обучает и возвращает df с is_anomaly.
        :param df: исходный DataFrame
        :param columns: одна колонка, список или "ALL"
        :param reference_column: колонка, по которой определять направление выброса
        :param direction: 'up', 'down', 'both'
        """
        self.fit(df, columns)
        result_df = self.get_filtered_anomalies(reference_column=reference_column, direction=direction)
        return result_df

