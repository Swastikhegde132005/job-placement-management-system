import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            print(f"DATABASE SUCCESS! Connected and retrieved: {val}")
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
