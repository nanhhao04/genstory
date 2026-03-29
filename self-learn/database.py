
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, select

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(DATABASE_URL, echo=True)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id:       Mapped[int] = mapped_column(primary_key=True)
    name:     Mapped[str] = mapped_column(String(50))
    email:    Mapped[str] = mapped_column(unique=True)
    items:    Mapped[list["Item"]] = relationship(back_populates="owner")

class Item(Base):
    __tablename__ = "items"
    id:       Mapped[int] = mapped_column(primary_key=True)
    title:    Mapped[str]
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner:    Mapped["User"] = relationship(back_populates="items")

# --- Session dependency ---
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import async_sessionmaker

async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

# --- CRUD ---
@app.post("/users/", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=list[UserSchema])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 10,
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()