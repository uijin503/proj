"""데이터베이스 테이블을 생성합니다. 사용법: python -m scripts.init_db"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from bot.db.base import make_engine
from bot.db.models import Base


async def main() -> None:
    load_dotenv()
    database_url = os.environ["DATABASE_URL"]
    engine = make_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database tables created.")


if __name__ == "__main__":
    asyncio.run(main())
