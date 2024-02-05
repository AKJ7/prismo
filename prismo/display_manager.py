import logging
import asyncio
from rgbmatrix import graphics, RGBMatrix, RGBMatrixOptions
from prismo.stocks_manager import StockInfo

logger = logging.getLogger(__name__)


class DisplayManager:

    red = graphics.Color(255, 0, 0)
    green= graphics.Color(0, 255, 0)
    blue = graphics.Color(0, 0, 255)
    white = graphics.Color(255, 255, 255)

    def __init__(self):
        self._queue = asyncio.Queue()
        self._data_request_event = asyncio.Event()
        self._data_request_event.clear()
        self._canvas_options = RGBMatrixOptions()
        self._matrix = RGBMatrix(options = self.setup_display_options())
        self._font = graphics.Font()
        self._font.LoadFont("fonts/6x13B.bdf")
        self._long_name_font = graphics.Font()
        self._long_name_font.LoadFont('fonts/4x6.bdf')
        self._value_font = graphics.Font()
        self._value_font.LoadFont('fonts/6x13B.bdf')
        self._start = 0
        logger.info('Initialised display manager')

    async def show(self, info: StockInfo) -> None:
        logger.info(f'Showing {info}')

    @staticmethod
    def setup_display_options():
        options = RGBMatrixOptions()
        options.disable_hardware_pulsing = True
        options.rows = 64
        options.cols = 64
        options.chain_length = 1
        options.brightness = 70
        return options

    @property
    def queue(self):
        return self._queue

    @property
    def data_request_event(self):
        return self._data_request_event

    async def run(self):
        counter = 0
        canvas = self._matrix.CreateFrameCanvas()
        self._pos = canvas.width
        while True:
            logger.info(f'Display task. Counter: {counter}')
            if self.queue.empty():
                self.data_request_event.set()
            stock_info = await self._queue.get()
            self.data_request_event.clear()
            logger.info(f'Displaying: "{stock_info}"')
            await self.scroll_info(stock_info, canvas)
            counter += 1    
            await asyncio.sleep(0.5)

    async def scroll_info(self, stock_info, canvas):
            for x in range(self._pos, -200, -1):
                canvas.Clear()
                l1 = graphics.DrawText(canvas, self._font, x, 13, self.blue, f'{stock_info.name} ({stock_info.currency.upper()})')
                l2 = graphics.DrawText(canvas, self._long_name_font, x, 20, self.blue, stock_info.long_name)
                change = stock_info.change
                l3 = graphics.DrawText(canvas, self._long_name_font, x, 30, self.red if change < 0 else self.green, f'{stock_info.last_price: < 8.3f} {change:+.2f}%')
                canvas = self._matrix.SwapOnVSync(canvas)
                await asyncio.sleep(0.02)
                if (self._pos + max(l1, l2, l3) < 0):
                    break
                
