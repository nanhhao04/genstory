import asyncio
import os
import sys

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to python path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database.models import ChapterTable, StoryTable, UserTable, WorldBibleTable
from src.database.session import Base

# SQLite connection URL (source)
SQLITE_URL = "sqlite+aiosqlite:///./genstory.db"


async def migrate():
    # 1. Read Supabase URL from environment or prompt user
    supabase_url = os.getenv("DATABASE_URL")
    if not supabase_url or "sqlite" in supabase_url:
        print("Error: DATABASE_URL in .env is still pointing to SQLite.")
        print("Please set your DATABASE_URL in .env to your Supabase PostgreSQL connection string.")
        print(
            "Example: postgresql+asyncpg://postgres:[password]@db.[project-id].supabase.co:5432/postgres"
        )
        return

    print("--- Starting Migration to Supabase ---")
    print(f"Source (SQLite): {SQLITE_URL}")
    print(f"Target (Supabase): {supabase_url}")
    print("\nConnecting to databases...")

    # Create engines
    sqlite_engine = create_async_engine(SQLITE_URL, echo=False)
    supabase_engine = create_async_engine(supabase_url, echo=False)

    # Create sessions
    SqliteSession = sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    SupabaseSession = sessionmaker(supabase_engine, class_=AsyncSession, expire_on_commit=False)

    # 2. Create tables on Supabase if they don't exist
    print("Creating tables on Supabase (if they do not exist)...")
    async with supabase_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

    # 3. Read data from SQLite and insert into Supabase
    models = [
        ("Users", UserTable),
        ("World Bibles", WorldBibleTable),
        ("Stories", StoryTable),
        ("Chapters", ChapterTable),
    ]

    async with SqliteSession() as src_session, SupabaseSession() as dest_session:
        for name, model in models:
            print(f"\nMigrating table: {name}...")

            # Inspect existing columns in SQLite database table
            async with sqlite_engine.connect() as conn:
                columns = await conn.run_sync(
                    lambda sync_conn, m=model: inspect(sync_conn).get_columns(m.__tablename__)
                )
                existing_cols = {col["name"] for col in columns}

            # Filter model columns to only those that exist in SQLite
            query_cols = [
                getattr(model, col_name) for col_name in existing_cols if hasattr(model, col_name)
            ]

            if not query_cols:
                print(f"No columns found/matched for {name} in SQLite. Skipping.")
                continue

            # Query all records from SQLite with only existing columns
            result = await src_session.execute(select(*query_cols))
            records = result.mappings().all()

            if not records:
                print(f"No records found for {name} in SQLite. Skipping.")
                continue

            print(f"Found {len(records)} records in SQLite. Inserting into Supabase...")

            # Merge records into target (using merge to avoid duplicate conflicts)
            for record_mapping in records:
                # Create a dictionary of existing data to insert
                data = dict(record_mapping)
                new_record = model(**data)
                await dest_session.merge(new_record)

            await dest_session.commit()
            print(f"Successfully migrated {name}!")

    print("\n--- Migration Completed Successfully ---")


if __name__ == "__main__":
    # Ensure correct event loop policy on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(migrate())
