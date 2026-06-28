"""LangGraph-based orchestration for story agents."""

from __future__ import annotations

from typing import Any, Callable, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents import ChapterWriterAgent, InteractionManagerAgent, StoryPlannerAgent
from src.schemas.story import Chapter, MemoryEntry, StorySession
from src.services.memory_service import select_relevant_memories
from src.services.image_service import generate_manga_page


class StoryGraphState(TypedDict, total=False):
    description: str
    genre: str
    art_style: str
    protagonist_name: str
    protagonist_description: str
    target_chapters: int
    chosen_option_text: str
    session: StorySession
    retrieved_memories: list[MemoryEntry]
    chapter: Chapter
    progress_callback: Optional[Callable[..., Any]]


class StoryLangGraphOrchestrator:
    """Coordinates story agents through LangGraph."""

    def __init__(
        self,
        story_planner: StoryPlannerAgent,
        chapter_writer: ChapterWriterAgent,
        interaction_manager: InteractionManagerAgent,
    ) -> None:
        self.story_planner = story_planner
        self.chapter_writer = chapter_writer
        self.interaction_manager = interaction_manager
        self._start_graph = self._build_start_graph()
        self._next_graph = self._build_next_graph()

    async def run_start_story(
        self,
        *,
        description: str,
        genre: str,
        art_style: str,
        protagonist_name: str,
        protagonist_description: str,
        target_chapters: int,
        progress_callback: Optional[Callable[..., Any]] = None,
    ) -> StoryGraphState:
        return await self._start_graph.ainvoke(
            {
                "description": description,
                "genre": genre,
                "art_style": art_style,
                "protagonist_name": protagonist_name,
                "protagonist_description": protagonist_description,
                "target_chapters": target_chapters,
                "progress_callback": progress_callback,
            }
        )

    async def run_next_chapter(
        self,
        *,
        session: StorySession,
        chosen_option_text: str,
        progress_callback: Optional[Callable[..., Any]] = None,
    ) -> StoryGraphState:
        return await self._next_graph.ainvoke(
            {
                "session": session,
                "chosen_option_text": chosen_option_text,
                "progress_callback": progress_callback,
            }
        )

    def _build_start_graph(self):
        graph = StateGraph(StoryGraphState)
        graph.add_node("plan_story", self._plan_story_node)
        graph.add_node("retrieve_memory", self._retrieve_memory_node)
        graph.add_node("write_chapter", self._write_chapter_node)
        graph.add_node("finalize_interaction", self._finalize_interaction_node)
        graph.add_node("generate_image", self._generate_image_node)
        graph.add_edge(START, "plan_story")
        graph.add_edge("plan_story", "retrieve_memory")
        graph.add_edge("retrieve_memory", "write_chapter")
        graph.add_edge("write_chapter", "finalize_interaction")
        graph.add_edge("finalize_interaction", "generate_image")
        graph.add_edge("generate_image", END)
        return graph.compile()

    def _build_next_graph(self):
        graph = StateGraph(StoryGraphState)
        graph.add_node("retrieve_memory", self._retrieve_memory_node)
        graph.add_node("write_chapter", self._write_chapter_node)
        graph.add_node("finalize_interaction", self._finalize_interaction_node)
        graph.add_node("generate_image", self._generate_image_node)
        graph.add_edge(START, "retrieve_memory")
        graph.add_edge("retrieve_memory", "write_chapter")
        graph.add_edge("write_chapter", "finalize_interaction")
        graph.add_edge("finalize_interaction", "generate_image")
        graph.add_edge("generate_image", END)
        return graph.compile()

    async def _plan_story_node(self, state: StoryGraphState) -> StoryGraphState:
        self._emit_progress(state, 0.1, "Dang lap ke hoach tong the cho cau chuyen...")
        session = await self.story_planner.plan_story(
            description=state["description"],
            genre=state["genre"],
            art_style=state["art_style"],
            protagonist_name=state["protagonist_name"],
            protagonist_description=state["protagonist_description"],
            target_chapters=state["target_chapters"],
        )
        return {"session": session}

    async def _write_chapter_node(self, state: StoryGraphState) -> StoryGraphState:
        session = state["session"]
        chosen_option_text = state.get("chosen_option_text", "")
        progress_message = (
            "Dang viet chuong dau tien theo outline..."
            if session.current_chapter_number == 0
            else "Dang viet tiep chuong moi..."
        )
        progress_value = 0.4 if session.current_chapter_number == 0 else 0.25
        self._emit_progress(state, progress_value, progress_message)
        chapter = await self.chapter_writer.write_chapter(
            session,
            chosen_option=chosen_option_text,
            retrieved_memories=state.get("retrieved_memories", []),
        )
        return {"chapter": chapter}

    async def _retrieve_memory_node(self, state: StoryGraphState) -> StoryGraphState:
        session = state["session"]
        next_num = session.current_chapter_number + 1
        beat = None
        if session.outline:
            for item in session.outline.beats:
                if item.chapter_number == next_num:
                    beat = item
                    break
        retrieved = select_relevant_memories(session, beat)
        return {"retrieved_memories": retrieved}

    async def _finalize_interaction_node(self, state: StoryGraphState) -> StoryGraphState:
        self._emit_progress(state, 0.7 if state["session"].current_chapter_number == 0 else 0.65, "Dang kiem tra logic, choices va memory...")
        chapter = await self.interaction_manager.finalize_chapter(state["session"], state["chapter"])
        return {"session": state["session"], "chapter": chapter}

    async def _generate_image_node(self, state: StoryGraphState) -> StoryGraphState:
        self._emit_progress(state, 0.85, "Dang ve manga page...")
        chapter = state["chapter"]
        chapter.image_path = await generate_manga_page(chapter, state["session"].world_bible)
        return {"chapter": chapter}

    def _emit_progress(self, state: StoryGraphState, value: float, desc: str) -> None:
        callback = state.get("progress_callback")
        if callback:
            callback(value, desc=desc)
