import json
import aiohttp
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from core.logger import downloading_data_logger


def volumes_table(data: dict, tf: str, bars: int = 50) -> pd.DataFrame:
    """
    Преобразует словарь {(symbol, timeframe): DataFrame} в таблицу объёмов.
    
    :param data: результат download_price
    :param tf: нужный таймфрейм ("1h", "5m" и т.д.)
    :param bars: сколько последних баров брать
    :return: DataFrame, где индекс = символ, колонки = бары
    """
    volumes_dict = {}

    for (symbol, timeframe), df in data.items():
        if timeframe == tf:
            # Берём последние N значений столбца volume
            last_volumes = df["volume"].tail(bars).tolist()
            volumes_dict[symbol] = last_volumes

    # Создаём DataFrame и транспонируем оси
    df_volumes = pd.DataFrame.from_dict(volumes_dict, orient="index")
    return df_volumes


class AsyncCryptoDataFetcher:

    BASE_URL = "https://fapi.binance.com"

    def __init__(self, save_dir: str = "data/klines", concurrency: int = 20):
        """
        :param save_dir: директория для сохранения CSV
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(concurrency)

    @staticmethod
    def float_type(df: pd.DataFrame) -> pd.DataFrame:
        """Меняет все колонки DataFrame на float."""
        return df.astype(float)

    @staticmethod
    def last_bar_open(time_frame: str) -> int:
        """
        Рассчитывает таймстамп открытия последней закрытой свечи указанного таймфрейма.
        """
        current_time = datetime.now()
        base_time = datetime(current_time.year, current_time.month, current_time.day, 3, 0, 0)

        bar_durations = {
            "15m": 15, "30m": 30, "1h": 60, "2h": 120,
            "4h": 240, "6h": 360, "12h": 720, "1d": 1440
        }
        duration = bar_durations[time_frame]
        last_open = base_time + ((current_time - base_time) // timedelta(minutes=duration)) * timedelta(minutes=duration)
        return round(last_open.timestamp() * 1000)

    def load_futures_from_json(self, path: str, key: str = None) -> list[str]:
        """
        Загружает список фьючерсов из JSON-файла.

        :param path: путь к JSON-файлу
        :param key: если JSON — словарь, укажи ключ, под которым лежит список фьючерсов
        :return: список фьючерсов
        """
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                return data

            if isinstance(data, dict):
                if key and key in data and isinstance(data[key], list):
                    return data[key]
                raise ValueError(f"Ключ '{key}' не найден или не является списком")

            raise TypeError("JSON должен быть списком или словарём с ключом, содержащим список")

        except Exception as e:
            downloading_data_logger.error(f"Ошибка при загрузке фьючерсов из {path}: {e}")
            return []

    async def _get(self, session: aiohttp.ClientSession, endpoint: str, params: dict):
        url = f"{self.BASE_URL}{endpoint}"
        async with self.semaphore:
            await asyncio.sleep(0.1)
            try:
                async with session.get(url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                downloading_data_logger.error(f"Ошибка при запросе {url} с params={params}: {e}")
                return None

    def prepare_folders(self, timeframes: list[str]):
        """
        Создаёт папки для хранения файлов по таймфреймам и типам данных.
        Пример: data/klines/1d/price, data/klines/1d/delta, ...
        """
        data_types = ["price", "delta", "oi", "info"]

        for tf in timeframes:
            for dtype in data_types:
                path = Path(self.save_dir) / tf / dtype
                path.mkdir(parents=True, exist_ok=True)

    async def download_price(self, futures_list, time_frames, limit=1500, save=False):
        """
        Скачивает исторические цены (klines) по списку фьючерсов и таймфреймов.

        :param futures_list: список символов, например ["BTCUSDT", "ETHUSDT"]
        :param time_frames: список таймфреймов, например ["1h", "1d"]
        :param limit: количество свечей (макс 1500)
        :param save: сохранять ли CSV файлы с результатами
        :return: dict {(futures, timeframe): DataFrame}
        """
        results = {}
        endpoint = "/fapi/v1/klines"
        self.prepare_folders(time_frames)

        self.prepare_folders(time_frames)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for fut in futures_list:
                for tf in time_frames:
                    params = {"symbol": fut, "interval": tf, "limit": limit}
                    tasks.append(self._fetch_price(session, fut, tf, endpoint, params))
            fetch_results = await asyncio.gather(*tasks)

        for fut, tf, df in fetch_results:
            if df is not None:
                results[(fut, tf)] = df
                if save:
                    filename = self.save_dir / tf / 'price' / f"{fut}.csv"
                    df.to_csv(filename, index=False)
                    downloading_data_logger.info(f"Сохранён файл {filename}")

        return results

    async def _fetch_price(self, session, fut, tf, endpoint, params):
        data = await self._get(session, endpoint, params)
        if not data:
            downloading_data_logger.warning(f"[{fut} {tf}] Нет данных price")
            return fut, tf, None

        rename_col = ["open_time", "open", "high", "low", "close", "volume", "close_time",
                      "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]

        df = pd.DataFrame(data, columns=rename_col)
        df = df[["open", "high", "low", "close", "volume"]]
        df = self.float_type(df)
        downloading_data_logger.info(f"[{fut} {tf}] Загружено {len(df)} цен")
        return fut, tf, df

    async def download_delta(self, futures_list, time_frames, limit=500, save=False):
        """
        Скачивает дельту по списку фьючерсов и таймфреймов.

        :param save: сохранять ли CSV файлы с результатами
        :return: dict {(futures, timeframe): DataFrame}
        """
        results = {}
        endpoint = "/futures/data/takerlongshortRatio"
        self.prepare_folders(time_frames)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for fut in futures_list:
                for tf in time_frames:
                    params = {"symbol": fut, "period": tf, "limit": limit}
                    tasks.append(self._fetch_delta(session, fut, tf, endpoint, params))
            fetch_results = await asyncio.gather(*tasks)

        for fut, tf, df in fetch_results:
            if df is not None:
                results[(fut, tf)] = df
                if save:
                    filename = self.save_dir / tf / 'delta' / f"{fut}.csv"
                    df.to_csv(filename, index=False)
                    downloading_data_logger.info(f"Сохранён файл {filename}")

        return results

    async def _fetch_delta(self, session, fut, tf, endpoint, params):
        data = await self._get(session, endpoint, params)
        if not data:
            downloading_data_logger.warning(f"[{fut} {tf}] Нет данных delta")
            return fut, tf, None

        df = pd.DataFrame(data[1:])  # Пропускаем заголовок
        df = self.float_type(df)
        df['delta'] = df['buyVol'] - df['sellVol']
        df = df[['buyVol', 'sellVol', 'delta']]

        if tf in ['1h', '4h', '1d']:
            st_time = self.last_bar_open(tf)
            bar_params = {"symbol": fut, "period": "5m", "limit": 500, "startTime": st_time}
            bar_data = await self._get(session, endpoint, bar_params)
            if bar_data:
                bar_df = pd.DataFrame(bar_data[1:])
                bar_df = self.float_type(bar_df)
                delta_bar = bar_df['buyVol'].sum() - bar_df['sellVol'].sum()
                df.loc[len(df)] = [bar_df['buyVol'].sum(), bar_df['sellVol'].sum(), delta_bar]
        else:
            df = df.shift(-1)

        return fut, tf, df.iloc[1:].reset_index(drop=True)

    async def download_oi(self, futures_list, time_frames, limit=500, save=False):
        """
        Скачивает открытый интерес (open interest) по списку фьючерсов и таймфреймов.

        :param save: сохранять ли CSV файлы с результатами
        :return: dict {(futures, timeframe): DataFrame}
        """
        results = {}
        endpoint = "/futures/data/openInterestHist"
        self.prepare_folders(time_frames)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for fut in futures_list:
                for tf in time_frames:
                    params = {"symbol": fut, "period": tf, "limit": limit}
                    tasks.append(self._fetch_oi(session, fut, tf, endpoint, params))
            fetch_results = await asyncio.gather(*tasks)

        for fut, tf, df in fetch_results:
            if df is not None:
                results[(fut, tf)] = df
                if save:
                    filename = self.save_dir / tf / 'oi' / f"{fut}.csv"
                    df.to_csv(filename, index=False)
                    downloading_data_logger.info(f"Сохранён файл {filename}")

        return results

    async def _fetch_oi(self, session, fut, tf, endpoint, params):
        data = await self._get(session, endpoint, params)
        if not data:
            downloading_data_logger.warning(f"[{fut} {tf}] Нет данных open interest")
            return fut, tf, None

        df = pd.DataFrame(data).rename(columns={'sumOpenInterest': 'sumOI'})

        # Оставляем только числовую колонку sumOI и вычисляем open interest
        df = df[['sumOI']]
        df['Old'] = df['sumOI'].shift(1)
        df = self.float_type(df)
        df['open interest'] = df['sumOI'] - df['Old']
        df = df[['sumOI', 'open interest']].dropna()

        if tf in ['1h', '4h', '1d']:
            st_time = self.last_bar_open(tf)
            bar_params = {"symbol": fut, "period": "5m", "limit": 500, "startTime": st_time}
            bar_data = await self._get(session, endpoint, bar_params)
            if bar_data:
                bar_df = pd.DataFrame(bar_data).rename(columns={'sumOpenInterest': 'sumOI'})
                bar_df = bar_df[['sumOI']]
                bar_df['Old'] = bar_df['sumOI'].shift(1)
                bar_df = self.float_type(bar_df)
                bar_df['open interest'] = bar_df['sumOI'] - bar_df['Old']
                bar_df = bar_df[['sumOI', 'open interest']].dropna()
                df.loc[len(df)] = [bar_df.iloc[-1]['sumOI'], bar_df['open interest'].sum()]
        else:
            df = df.shift(-1)

        return fut, tf, df.iloc[1:].reset_index(drop=True)

    async def download_info(self, futures_list, time_frames, limit=500, save=False):
        """
        Скачивает и объединяет price + delta + open interest данные.
        Возвращает dict {(futures, timeframe): DataFrame}
        """
        result = {}
        self.prepare_folders(time_frames)

        price_dict = await self.download_price(futures_list, time_frames, limit, save=save)
        delta_dict = await self.download_delta(futures_list, time_frames, limit, save=save)
        oi_dict = await self.download_oi(futures_list, time_frames, limit, save=save)

        keys = price_dict.keys() & delta_dict.keys() & oi_dict.keys()

        for key in keys:
            price_df = price_dict[key]
            delta_df = delta_dict[key]
            oi_df = oi_dict[key]

            min_len = min(len(price_df), len(delta_df), len(oi_df))

            price_df = price_df.tail(min_len).reset_index(drop=True)
            delta_df = delta_df.tail(min_len).reset_index(drop=True)
            oi_df = oi_df.tail(min_len).reset_index(drop=True)

            combined = pd.concat([price_df, delta_df, oi_df], axis=1)
            combined = combined[["open", "high", "low", "close", "volume", "delta", "open interest"]]
            combined = combined.dropna()

            result[key] = combined

            if save:
                fut, tf = key
                filename = self.save_dir / tf / 'info' / f"{fut}.csv"
                combined.to_csv(filename, index=False)
                downloading_data_logger.info(f"Сохранён файл {filename}")

        return result
    
    async def get_futures_prices(self):
        """
        Возвращает цены всех фьючерсов
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/fapi/v1/ticker/price") as resp:
                data = await resp.json()
                return {item['symbol']: float(item['price']) for item in data}

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()