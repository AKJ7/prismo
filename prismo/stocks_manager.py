import logging
import asyncio
import enum
from dataclasses import dataclass
import random
import yfinance as yf
import pandas as pd
import numpy as np
import aiofiles
import aiohttp
from io import StringIO
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

logger = logging.getLogger(__name__)


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
   pass


class Tickers(enum.Enum):
    WORLD_INDEX = 'world-indices'
    TRENDING = 'trending-tickers'
    MOST_ACTIVE = 'most-active'
    GAINERS = 'gainers'
    LOSERS = 'losers'
    EFTS = 'efts'
    FUTURES = 'commodities'
    CURRENCIES = 'currencies'
    MUTUAL_FUNDS = 'mutualfunds'


@dataclass(frozen=True)
class StockInfo:
    name: str
    long_name: str
    last_price: float
    high_month_price: float
    low_month_price: float
    change: float
    currency: str


class StocksManager:

    STOCK_SRC = 'https://finance.yahoo.com/{index}'

    def __init__(self, queue: asyncio.Queue, event: asyncio.Event):
        self._data_queue = queue
        self._read_data_event = event
        logger.info('Initialized Stock mananger')

    @classmethod
    def get_url(cls, **args):
        return cls.STOCK_SRC.format(**args)

    async def fetch(self, ticker: Tickers = Tickers.TRENDING, period: str ='1d', start=None, end=None) -> List[StockInfo]:
        market_stock_index_url = self.get_url(index=ticker.value)
        logger.info(f'Fetching from url: {market_stock_index_url}')
        # df_list = await self.fetch_dataframe(market_stock_index_url)
        df_list = pd.read_html(market_stock_index_url)
        market_stock_index = df_list[0]
        # head = market_stock_index.head()
        # logger.info(head)
        await asyncio.sleep(0)
        stock_infos = []
        if start is None:
            start = datetime.today().replace(month=1)
        if end is None:
            end = datetime.today()
        logger.info(f'Gotten: {len(market_stock_index.Symbol)} Elements!')
        self._read_data_event.clear()
        for symb in market_stock_index.Symbol:
            current_symbol = symb
            ticker_data = yf.Ticker(symb)
            ticker_frame = ticker_data.history(period='1mo', interval='1mo')
            current_row = market_stock_index.loc[market_stock_index['Symbol'] == current_symbol]
            last_price = current_row['Last Price'].item()
            change = current_row['Change'].item()
            month_info = ticker_frame.iloc[0, :]
            high_month_price = month_info['High'].item()
            low_month_price = month_info['Low'].item()
            try:
                ticker_long_name = ticker_data.info['longName'] if 'longName' in ticker_data.info else ''
                currency = ticker_data.info.get('financialCurrency')
                stock_info = StockInfo(name=current_symbol, long_name=ticker_long_name, last_price=last_price, high_month_price=high_month_price, low_month_price=low_month_price, change=change, currency=currency)
            except Exception as e:
                logger.error(f'Error parsing: {current_symbol}, info: {str(ticker_data.info)}: {e}')
            # logger.info(f'Adding stock info: {ticker_data.info.keys()}')
            stock_infos.append(stock_info)
            await self._data_queue.put(stock_info) 
        easter_egg = await self.get_easter_egg()
        stock_infos.append(easter_egg)
        await self._data_queue.put(easter_egg)
        self._data_queue.task_done()
        return stock_infos

    @staticmethod
    async def get_full_soup(soup):
        return soup

    @classmethod
    async def fetch_dataframe(cls, url: str):
        dataframe = pd.DataFrame()
        task = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.text()
                task = asyncio.create_task(cls.get_full_soup(content))
                await asyncio.sleep(0)
        html_dicts = await asyncio.gather(task)
        df_list = pd.read_html(StringIO(html_dicts[0]))
        return df_list

    async def get_easter_egg(self) -> StockInfo:
        last_price = random.uniform(10, 20)
        high_month_price = last_price - random.uniform(3, 5)
        low_month_price = last_price - random.uniform(3, 5)
        change = random.uniform(100, 200)
        return StockInfo(name='COM', long_name='Compleo Charging Solutions AG', last_price=last_price, high_month_price=high_month_price, low_month_price=low_month_price, change=change, currency='EUR')
    
    async def run(self) -> None:
        counter = 0
        while True:
            logger.info(f"Running stock manager. Counter: {counter}")
            await self._read_data_event.wait()
            stock_infos = await self.fetch()
            counter += 1
