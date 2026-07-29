from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database.session import Base


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    world_bibles = relationship("WorldBibleTable", back_populates="user")


class WorldBibleTable(Base):
    __tablename__ = "world_bibles"

    id = Column(String, primary_key=True)
    user_id = Column(
        String, ForeignKey("users.id"), nullable=True
    )  # Temporarily nullable for migration
    title = Column(String)
    genre = Column(String)
    art_style = Column(String)
    protagonist_name = Column(String)
    protagonist_description = Column(Text)
    lore = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserTable", back_populates="world_bibles")
    stories = relationship("StoryTable", back_populates="world_bible")


class StoryTable(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True)
    world_bible_id = Column(String, ForeignKey("world_bibles.id"))
    current_chapter_index = Column(Integer, default=1)
    target_chapters = Column(Integer, default=8)
    is_finished = Column(Integer, default=0)  # 0: False, 1: True
    created_at = Column(DateTime, default=datetime.utcnow)

    world_bible = relationship("WorldBibleTable", back_populates="stories")
    chapters = relationship("ChapterTable", back_populates="story")


class ChapterTable(Base):
    __tablename__ = "chapters"

    id = Column(String, primary_key=True)
    story_id = Column(String, ForeignKey("stories.id"))
    chapter_number = Column(Integer)
    title = Column(String)
    narrative_text = Column(Text)
    image_path = Column(String)
    summary = Column(Text)
    choice_that_led_here = Column(String)
    chapter_ending = Column(Text)
    key_events = Column(JSON)
    state_changes = Column(JSON)
    manga_page_data = Column(JSON)
    raw_response = Column(JSON)
    options = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("StoryTable", back_populates="chapters")
