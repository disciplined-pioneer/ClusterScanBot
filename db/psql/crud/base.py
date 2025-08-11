import logging
from core.psql import async_db_session, engine
from db.psql.models.models import Base


async def init_postgres() -> bool:
    """
    Создать все таблицы в ядре
    :return: True or False
    """
    async with async_db_session() as s:
        try:

            await s.run_sync(
                lambda s_value: Base.metadata.create_all(
                    bind=s_value.bind
                )
            )

            return True

        except Exception as e:
            logging.exception(e)
            return False