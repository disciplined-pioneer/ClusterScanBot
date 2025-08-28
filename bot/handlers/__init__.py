from bot.handlers.user.commands import router as start
from bot.handlers.user.auxiliary import router as auxiliary
from bot.handlers.user.update_futures import router as update_futures
from bot.handlers.user.futures_selection import router as futures_selection

routers = [
    start,
    update_futures,
    futures_selection,
    auxiliary,
]
