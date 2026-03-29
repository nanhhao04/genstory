from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.db import Base

class WorldBibleTable(Base):
    __tablename__ = "world_bibles"

    id = Column(String, primary_key=True)
    title = Column(String)
    genre = Column(String)
    art_style = Column(String)
    protagonist_name = Column(String)
    protagonist_description = Column(Text)
    lore = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    stories = relationship("StoryTable", back_populates="world_bible")

class StoryTable(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True)
    world_bible_id = Column(String, ForeignKey("world_bibles.id"))
    current_chapter_index = Column(Integer, default=1)
    target_chapters = Column(Integer, default=8)
    is_finished = Column(Integer, default=0) # 0: False, 1: True
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
    raw_response = Column(JSON)
    options = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("StoryTable", back_populates="chapters")
