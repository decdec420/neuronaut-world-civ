"""
Knowledge Transmission System - Memory of Civilization

How knowledge spreads through society:
- Oral tradition (fast but lossy, mutations over time)
- Written records (slow but permanent, requires literacy)
- Libraries (centralize knowledge, become cultural hubs)
- Teaching/Apprenticeship (skill transfer between agents)
- Schools (emerge when teachers gather students)

This enables civilization to BUILD ON previous discoveries!

Without this: Each generation rediscovers fire
With this: Each generation invents something NEW
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from datetime import datetime, timedelta
import random
import uuid


# ==============================================================================
# KNOWLEDGE TYPES
# ==============================================================================

class KnowledgeType:
    """Types of knowledge that can be transmitted"""
    # Practical
    RECIPE = "recipe"
    TECHNIQUE = "technique"
    BUILDING_METHOD = "building_method"
    TOOL_USE = "tool_use"

    # Scientific
    MATERIAL_PROPERTY = "material_property"
    NATURAL_LAW = "natural_law"
    MATHEMATICS = "mathematics"

    # Social
    LAW = "law"
    CUSTOM = "custom"
    STORY = "story"
    SONG = "song"

    # Advanced
    THEORY = "theory"
    INNOVATION = "innovation"
    PHILOSOPHY = "philosophy"


# ==============================================================================
# KNOWLEDGE RECORDS
# ==============================================================================

@dataclass
class KnowledgeRecord:
    """
    A piece of knowledge that can be transmitted.

    Can exist as:
    - Oral tradition (in agent's memory)
    - Written document (in library)
    - Demonstrated skill (learned through observation)
    """
    id: str
    knowledge_type: str
    name: str
    content: Union[str, Dict, Any]  # The actual knowledge (text, recipe, data)

    # Origin
    original_author: str
    creation_date: datetime

    # Transmission
    transmission_method: str  # "oral", "written", "demonstration"
    accuracy: float = 1.0  # Degrades with oral transmission

    # Spread
    known_by: Set[str] = field(default_factory=set)
    times_taught: int = 0
    times_copied: int = 0

    # Mutations (oral tradition changes)
    original_content: Union[str, Dict, Any] = ""
    mutation_count: int = 0


@dataclass
class WrittenDocument:
    """
    A written record - PERMANENT knowledge storage.

    Requires:
    - Literacy skill
    - Writing materials
    - Time to write
    """
    id: str
    title: str
    content: str
    author_id: str
    written_date: datetime

    # Physical document
    material: str = "paper"  # Could be clay, papyrus, stone, etc.
    condition: float = 1.0  # Degrades over time

    # Knowledge contained
    knowledge_ids: List[str] = field(default_factory=list)

    # Library storage
    stored_in_library: Optional[str] = None
    times_read: int = 0


@dataclass
class Library:
    """
    A building that stores written knowledge.

    Becomes a hub of civilization!
    """
    id: str
    name: str
    location: Tuple[float, float]
    founded_by: str
    founded_date: datetime

    # Collection
    documents: Dict[str, WrittenDocument] = field(default_factory=dict)
    total_knowledge_pieces: int = 0

    # Access
    librarian_id: Optional[str] = None  # Emerges from behavior
    visitors: Set[str] = field(default_factory=set)
    times_visited: int = 0

    # Reputation
    is_famous: bool = False
    scholars: Set[str] = field(default_factory=set)  # Regular users


@dataclass
class TeachingSession:
    """
    A teaching event between agents.

    Knowledge transfer in real-time!
    """
    id: str
    teacher_id: str
    student_ids: Set[str]
    knowledge_taught: List[str]
    session_date: datetime

    # Effectiveness
    teacher_skill: float = 0.5
    student_comprehension: Dict[str, float] = field(default_factory=dict)

    # Method
    method: str = "demonstration"  # demonstration, lecture, apprenticeship


# ==============================================================================
# KNOWLEDGE SYSTEM
# ==============================================================================

class KnowledgeSystem:
    """
    Manages all knowledge transmission in the world.

    This is what separates primitive societies from advanced civilizations!
    """

    def __init__(self):
        self.knowledge_records: Dict[str, KnowledgeRecord] = {}
        self.documents: Dict[str, WrittenDocument] = {}
        self.libraries: Dict[str, Library] = {}
        self.teaching_sessions: List[TeachingSession] = []

    # ==========================================================================
    # KNOWLEDGE CREATION
    # ==========================================================================

    def create_knowledge(
        self,
        agent_id: str,
        knowledge_type: str,
        name: str,
        content: Union[str, Dict, Any]
    ) -> KnowledgeRecord:
        """Agent creates new knowledge"""

        record = KnowledgeRecord(
            id=str(uuid.uuid4()),
            knowledge_type=knowledge_type,
            name=name,
            content=content,
            original_author=agent_id,
            creation_date=datetime.now(),
            transmission_method="oral",  # Starts as oral
            known_by={agent_id},
            original_content=content
        )

        self.knowledge_records[record.id] = record
        return record

    # ==========================================================================
    # ORAL TRANSMISSION
    # ==========================================================================

    def oral_transmission(
        self,
        teacher_id: str,
        student_id: str,
        knowledge_id: str,
        teacher_skill: float = 0.5
    ) -> Dict:
        """
        Teach knowledge orally.

        Fast but lossy - accuracy degrades!
        Can introduce mutations (like telephone game).
        """

        knowledge = self.knowledge_records.get(knowledge_id)
        if not knowledge:
            return {"success": False, "reason": "Knowledge not found"}

        # Accuracy based on teacher skill
        base_accuracy = knowledge.accuracy
        transmission_accuracy = base_accuracy * (0.7 + teacher_skill * 0.3)

        # Mutation chance (5-20% depending on accuracy)
        mutation_chance = 0.05 + (1 - transmission_accuracy) * 0.15

        transmitted_content = knowledge.content

        if random.random() < mutation_chance:
            # MUTATION - content changes slightly
            transmitted_content = self._mutate_content(knowledge.content)
            knowledge.mutation_count += 1
            knowledge.content = transmitted_content
            knowledge.accuracy *= 0.95  # Accuracy degrades

        # Student learns
        knowledge.known_by.add(student_id)
        knowledge.times_taught += 1

        return {
            "success": True,
            "accuracy": transmission_accuracy,
            "mutated": transmitted_content != knowledge.original_content,
            "content_learned": transmitted_content
        }

    def _mutate_content(self, original: str) -> str:
        """Introduce small mutations to oral tradition"""

        mutations = [
            lambda s: s.replace("mix", "combine"),
            lambda s: s.replace("heat", "warm"),
            lambda s: s.replace("10", str(random.randint(8, 12))),
            lambda s: s + " (approximately)",
            lambda s: s.replace("always", "usually"),
        ]

        if random.random() < 0.5:
            mutation = random.choice(mutations)
            try:
                return mutation(original)
            except (AttributeError, IndexError, TypeError) as e:
                logger.debug(f"Knowledge mutation failed: {e}, keeping original")
                return original

        return original

    # ==========================================================================
    # WRITING & LITERACY
    # ==========================================================================

    def agent_writes_document(
        self,
        agent_id: str,
        title: str,
        knowledge_ids: List[str],
        material: str = "paper",
        literacy_skill: float = 0.5
    ) -> Optional[WrittenDocument]:
        """
        Agent writes down knowledge.

        Requires literacy skill!
        Creates PERMANENT record.
        """

        # Need literacy
        if literacy_skill < 0.1:
            return None

        # Gather knowledge content
        content_parts = []
        for kid in knowledge_ids:
            knowledge = self.knowledge_records.get(kid)
            if knowledge and agent_id in knowledge.known_by:
                content_parts.append(f"{knowledge.name}: {knowledge.content}")

        if not content_parts:
            return None

        # Create document
        document = WrittenDocument(
            id=str(uuid.uuid4()),
            title=title,
            content="\n\n".join(content_parts),
            author_id=agent_id,
            written_date=datetime.now(),
            material=material,
            knowledge_ids=knowledge_ids
        )

        self.documents[document.id] = document

        # Mark knowledge as written
        for kid in knowledge_ids:
            knowledge = self.knowledge_records[kid]
            knowledge.transmission_method = "written"
            knowledge.accuracy = min(1.0, knowledge.accuracy + 0.1)  # Writing preserves!
            knowledge.times_copied += 1

        return document

    def agent_reads_document(
        self,
        agent_id: str,
        document_id: str,
        literacy_skill: float = 0.5
    ) -> Dict:
        """
        Agent reads document and learns knowledge.

        High literacy = better comprehension
        """

        document = self.documents.get(document_id)
        if not document:
            return {"success": False, "reason": "Document not found"}

        # Need literacy
        if literacy_skill < 0.1:
            return {"success": False, "reason": "Cannot read - no literacy"}

        # Comprehension based on literacy
        comprehension = min(1.0, literacy_skill * 1.2)

        # Learn all knowledge in document
        learned = []
        for kid in document.knowledge_ids:
            knowledge = self.knowledge_records.get(kid)
            if knowledge:
                knowledge.known_by.add(agent_id)
                learned.append(knowledge.name)

        document.times_read += 1

        return {
            "success": True,
            "comprehension": comprehension,
            "knowledge_learned": learned
        }

    # ==========================================================================
    # LIBRARIES
    # ==========================================================================

    def create_library(
        self,
        founder_id: str,
        name: str,
        location: Tuple[float, float]
    ) -> Library:
        """
        Agent founds a library.

        Can become cultural hub!
        """

        library = Library(
            id=str(uuid.uuid4()),
            name=name,
            location=location,
            founded_by=founder_id,
            founded_date=datetime.now()
        )

        self.libraries[library.id] = library
        return library

    def add_document_to_library(
        self,
        library_id: str,
        document_id: str
    ) -> bool:
        """Add written document to library collection"""

        library = self.libraries.get(library_id)
        document = self.documents.get(document_id)

        if not library or not document:
            return False

        library.documents[document_id] = document
        library.total_knowledge_pieces += len(document.knowledge_ids)
        document.stored_in_library = library_id

        return True

    def visit_library(
        self,
        agent_id: str,
        library_id: str,
        duration_hours: int = 2
    ) -> Dict:
        """
        Agent visits library.

        Can read documents, discover new knowledge!
        """

        library = self.libraries.get(library_id)
        if not library:
            return {"success": False, "reason": "Library not found"}

        library.visitors.add(agent_id)
        library.times_visited += 1

        # Become scholar if frequent visitor
        if library.times_visited > 20:
            library.scholars.add(agent_id)

        # Can read multiple documents based on duration
        documents_read = min(duration_hours, len(library.documents))
        available_docs = list(library.documents.values())
        random.shuffle(available_docs)

        knowledge_discovered = []
        for doc in available_docs[:documents_read]:
            for kid in doc.knowledge_ids:
                knowledge = self.knowledge_records.get(kid)
                if knowledge and agent_id not in knowledge.known_by:
                    knowledge.known_by.add(agent_id)
                    knowledge_discovered.append(knowledge.name)

        return {
            "success": True,
            "documents_read": documents_read,
            "knowledge_discovered": knowledge_discovered
        }

    # ==========================================================================
    # TEACHING & APPRENTICESHIP
    # ==========================================================================

    def teaching_session(
        self,
        teacher_id: str,
        student_ids: Set[str],
        knowledge_ids: List[str],
        method: str = "demonstration",
        teacher_skill: float = 0.5
    ) -> TeachingSession:
        """
        Formal teaching session.

        More effective than casual oral transmission.
        """

        session = TeachingSession(
            id=str(uuid.uuid4()),
            teacher_id=teacher_id,
            student_ids=student_ids,
            knowledge_taught=knowledge_ids,
            session_date=datetime.now(),
            teacher_skill=teacher_skill,
            method=method
        )

        # Each student learns based on teacher skill + method
        method_bonus = {
            "demonstration": 0.3,
            "lecture": 0.2,
            "apprenticeship": 0.5  # Most effective!
        }

        bonus = method_bonus.get(method, 0.2)
        effectiveness = min(1.0, teacher_skill + bonus)

        for student_id in student_ids:
            comprehension = effectiveness * random.uniform(0.8, 1.0)
            session.student_comprehension[student_id] = comprehension

            # Students learn knowledge
            for kid in knowledge_ids:
                knowledge = self.knowledge_records.get(kid)
                if knowledge:
                    knowledge.known_by.add(student_id)
                    knowledge.times_taught += 1

        self.teaching_sessions.append(session)
        return session

    def apprenticeship(
        self,
        master_id: str,
        apprentice_id: str,
        skill_to_learn: str,
        duration_days: int = 30
    ) -> Dict:
        """
        Long-term apprenticeship.

        Deepest knowledge transfer - includes tacit knowledge!
        """

        # Find all knowledge master has about this skill
        master_knowledge = [
            kr for kr in self.knowledge_records.values()
            if master_id in kr.known_by and skill_to_learn in kr.name.lower()
        ]

        if not master_knowledge:
            return {"success": False, "reason": "Master has no knowledge to teach"}

        # Transfer ALL knowledge over duration
        knowledge_transferred = []
        for knowledge in master_knowledge:
            knowledge.known_by.add(apprentice_id)
            knowledge.times_taught += 1
            knowledge_transferred.append(knowledge.name)

        # Create teaching session
        session = self.teaching_session(
            master_id,
            {apprentice_id},
            [k.id for k in master_knowledge],
            method="apprenticeship",
            teacher_skill=0.9  # Apprenticeship is very effective
        )

        return {
            "success": True,
            "knowledge_transferred": knowledge_transferred,
            "session_id": session.id,
            "duration_days": duration_days
        }

    # ==========================================================================
    # KNOWLEDGE SPREAD ANALYSIS
    # ==========================================================================

    def get_knowledge_spread(self, knowledge_id: str) -> Dict:
        """Analyze how knowledge has spread"""

        knowledge = self.knowledge_records.get(knowledge_id)
        if not knowledge:
            return {}

        return {
            "name": knowledge.name,
            "original_author": knowledge.original_author,
            "created": knowledge.creation_date,
            "known_by_count": len(knowledge.known_by),
            "times_taught": knowledge.times_taught,
            "times_copied": knowledge.times_copied,
            "accuracy": knowledge.accuracy,
            "mutations": knowledge.mutation_count,
            "transmission_method": knowledge.transmission_method,
            "is_written": knowledge.transmission_method == "written"
        }

    def get_statistics(self) -> Dict:
        """Get knowledge system statistics"""

        oral_knowledge = sum(
            1 for kr in self.knowledge_records.values()
            if kr.transmission_method == "oral"
        )

        written_knowledge = sum(
            1 for kr in self.knowledge_records.values()
            if kr.transmission_method == "written"
        )

        return {
            "total_knowledge": len(self.knowledge_records),
            "oral_tradition": oral_knowledge,
            "written_records": written_knowledge,
            "total_documents": len(self.documents),
            "total_libraries": len(self.libraries),
            "teaching_sessions": len(self.teaching_sessions),
            "literacy_rate": (
                written_knowledge / len(self.knowledge_records)
                if len(self.knowledge_records) > 0
                else 0.0
            ),
            "most_spread_knowledge": self._find_most_spread(),
            "famous_libraries": [
                lib.name for lib in self.libraries.values()
                if len(lib.documents) > 10
            ]
        }

    def _find_most_spread(self) -> Optional[str]:
        """Find most widely known knowledge"""
        if not self.knowledge_records:
            return None

        most_known = max(
            self.knowledge_records.values(),
            key=lambda k: len(k.known_by)
        )

        return f"{most_known.name} (known by {len(most_known.known_by)} agents)"
