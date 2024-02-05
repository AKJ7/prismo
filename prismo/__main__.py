import logging 
import asyncio
from prismo import LOG_FORMAT
from prismo.stocks_manager import StocksManager
from prismo.display_manager import DisplayManager


logger = logging.getLogger(__name__)


async def main():
    logger.info('Starting main')
    display = DisplayManager()
    stocks = StocksManager(display.queue, display.data_request_event)

    await asyncio.gather(*[asyncio.create_task(task.run()) for task in [display, stocks]])

    logger.info(stock_info)
    return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logger.info('Starting PRISMO')

    ret_val = asyncio.run(main())

    logger.info(f'Exiting PRISMO with "{ret_val}". Have a nice day!')
