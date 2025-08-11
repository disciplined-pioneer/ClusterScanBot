from aiogram.types import BotCommand
from pydantic_settings import BaseSettings


class PostgresConfig(BaseSettings):
    NAME: str
    HOST: str
    PORT: int
    PASSWORD: str
    USER: str

    @property
    def URL(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    class Config:
        env_prefix = 'POSTGRES_'
        env_file = '.env'
        extra = 'ignore'


class BotConfig(BaseSettings):
    TOKEN: str
    ADMINS: list[int] | None = []
    COMMANDS: list[BotCommand] = [
        BotCommand(command='start', description='Запустить бота 🚀')
    ]

    class Config:
        env_prefix = 'BOT_'
        env_file = '.env'
        extra = 'ignore'


class Settings:
    postgres = PostgresConfig()
    bot = BotConfig()


settings = Settings()