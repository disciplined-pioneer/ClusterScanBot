from bot.handlers.user.commands import router as start
from bot.handlers.user.auxiliary import router as auxiliary
from bot.handlers.user.futures_selection import router as futures_selection

routers = [
    start,
    auxiliary,
    futures_selection
]
