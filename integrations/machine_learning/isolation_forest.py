import numpy as np
import pandas as pd
from typing import Union, List
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:

    def __init__(self, contamination: float = 0.15, random_state: int = 42, scale_by: str = 'row'):
        """
        :param contamination: доля аномалий в данных
        :param random_state: seed
        :param scale_by: 'row' - стандартизация по строкам (фьючерсам),
                         'column' - стандартизация по колонкам (барам)
        """
        self.columns = None
        self.fitted = False
        self.contamination = contamination
        self.random_state = random_state
        self.scale_by = scale_by
        self.model = None
        self.X_scaled = None
        self.data = None

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

        # Стандартизация
        if self.scale_by == 'row':
            # стандартизация по строкам (по каждому фьючерсу)
            X_scaled = self.data[self.columns].apply(lambda row: (row - row.mean()) / row.std(ddof=0), axis=1).values
        elif self.scale_by == 'column':
            # стандартная стандартизация по колонкам (по каждому бару)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            raise ValueError("scale_by должен быть 'row' или 'column'")

        self.X_scaled = X_scaled

        # Обучаем IsolationForest
        self.model = IsolationForest(contamination=self.contamination, random_state=self.random_state)
        self.model.fit(self.X_scaled)

        self.fitted = True

    def get_filtered_anomalies(self, reference_column: str = None, direction: str = "up") -> pd.DataFrame:
        """Возвращает DataFrame с колонкой is_anomaly, где True — выбросы по направлению"""
        if not self.fitted:
            raise ValueError("Сначала вызови .fit(df, columns)")

        preds = self.model.predict(self.X_scaled)
        scores = self.model.decision_function(self.X_scaled)

        self.data['score'] = scores
        self.data['pred'] = preds

        if reference_column is None:
            reference_column = self.columns[0]

        if reference_column not in self.data.columns:
            raise ValueError(f"column {reference_column} не найдена в данных.")

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
        """Объединённая точка входа: обучает и возвращает df с is_anomaly."""
        self.fit(df, columns)
        return self.get_filtered_anomalies(reference_column=reference_column, direction=direction)
