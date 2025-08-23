import pandas as pd
from integrations.binance.downloading_data import AsyncCryptoDataFetcher
from integrations.machine_learning.isolation_forest import AnomalyDetector

import asyncio

async def main():

    fetcher = AsyncCryptoDataFetcher(save_dir="data/klines")
    futures = ['BTCUSDT']

    fetcher.prepare_folders(["4h"])
    combined_data = await fetcher.download_price(futures, ["1h"], limit=500, save=True)

    df = pd.read_csv(r'D:\Programs\my_trading_project\data\klines\1h\price\BTCUSDT.csv')

    detector = AnomalyDetector(contamination=0.1, scale_by='column')
    result = detector.run(df, columns="volume", direction='up')

    result.to_csv("BTCUSDT.csv")
    print("Готово!")

asyncio.run(main())
