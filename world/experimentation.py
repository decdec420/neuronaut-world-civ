"""
Open Experimentation Engine - TRUE Innovation System

Agents can experiment with ANY combination of materials, methods, and conditions.
NO predetermined outcomes - discoveries emerge from actual physics simulation.

This is the foundation for emergent technology progression:
- Stone Age: Fire, tools, pottery, textiles
- Bronze Age: Metalworking, writing, wheel
- Iron Age: Advanced metallurgy, engineering
- Industrial: Steam, electricity, machinery
- Modern: Electronics, computers, automation
- Space Age: Rocketry, satellites, space travel

Agents discover these organically through experimentation!
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
import random
import uuid


# ==============================================================================
# MATERIAL PROPERTIES - The Physics Engine
# ==============================================================================

class MaterialProperty(Enum):
    """Properties that materials can have"""
    # Physical
    HARD = "hard"
    SOFT = "soft"
    FLEXIBLE = "flexible"
    BRITTLE = "brittle"
    DENSE = "dense"
    LIGHT = "light"

    # Thermal
    FLAMMABLE = "flammable"
    HEAT_RESISTANT = "heat_resistant"
    CONDUCTIVE = "conductive"
    INSULATING = "insulating"

    # Chemical
    REACTIVE = "reactive"
    STABLE = "stable"
    CORROSIVE = "corrosive"
    SOLUBLE = "soluble"

    # Structural
    LOAD_BEARING = "load_bearing"
    WATERPROOF = "waterproof"
    TRANSPARENT = "transparent"
    MALLEABLE = "malleable"

    # Utility
    SHARP = "sharp"
    EDIBLE = "edible"
    TOXIC = "toxic"
    MEDICINAL = "medicinal"


@dataclass
class Material:
    """A material with emergent properties"""
    name: str
    base_properties: Set[MaterialProperty] = field(default_factory=set)
    discovered_properties: Set[MaterialProperty] = field(default_factory=set)
    melting_point: Optional[float] = None  # Celsius
    hardness: float = 0.5  # 0-1 scale
    discovered_by: Optional[str] = None
    discovery_date: Optional[datetime] = None

    def all_properties(self) -> Set[MaterialProperty]:
        """Get all known properties"""
        return self.base_properties | self.discovered_properties


class ExperimentCategory(Enum):
    """Categories of experimentation - what domain is this?"""
    COOKING = "cooking"  # Food preparation, heating organic materials
    CRAFTING = "crafting"  # Tool/item creation, shaping materials
    BUILDING = "building"  # Construction materials, structural
    MATERIAL_SCIENCE = "material_science"  # Discovering properties, combinations
    MEDICINE = "medicine"  # Healing, toxic/beneficial substances
    CHEMISTRY = "chemistry"  # Reactions, transformations
    METALLURGY = "metallurgy"  # Metal working, alloys
    TEXTILES = "textiles"  # Weaving, fabric creation


class ExperimentMethod(Enum):
    """Ways agents can experiment"""
    HEAT = "heat"  # Apply fire/heat
    COOL = "cool"  # Freeze/chill
    POUND = "pound"  # Physical force
    MIX = "mix"  # Combine liquids/powders
    LAYER = "layer"  # Stack materials
    WEAVE = "weave"  # Interlace fibers
    COMPRESS = "compress"  # Apply pressure
    DISSOLVE = "dissolve"  # Add liquid
    FERMENT = "ferment"  # Let sit with microbes
    REFINE = "refine"  # Remove impurities
    SHAPE = "shape"  # Mold/sculpt
    SHARPEN = "sharpen"  # Create edge
    OBSERVE = "observe"  # Study properties


# ==============================================================================
# BASE MATERIALS - What agents start with
# ==============================================================================

BASE_MATERIALS = {
    "wood": Material(
        name="wood",
        base_properties={
            MaterialProperty.FLAMMABLE,
            MaterialProperty.LIGHT,
            MaterialProperty.FLEXIBLE,
            MaterialProperty.LOAD_BEARING
        },
        hardness=0.3
    ),
    "stone": Material(
        name="stone",
        base_properties={
            MaterialProperty.HARD,
            MaterialProperty.BRITTLE,
            MaterialProperty.DENSE,
            MaterialProperty.LOAD_BEARING
        },
        hardness=0.7
    ),
    "clay": Material(
        name="clay",
        base_properties={
            MaterialProperty.SOFT,
            MaterialProperty.MALLEABLE,
            MaterialProperty.SOLUBLE
        },
        hardness=0.2
    ),
    "plant_fiber": Material(
        name="plant_fiber",
        base_properties={
            MaterialProperty.FLEXIBLE,
            MaterialProperty.FLAMMABLE,
            MaterialProperty.LIGHT
        },
        hardness=0.1
    ),
    "water": Material(
        name="water",
        base_properties={
            MaterialProperty.SOLUBLE,
            MaterialProperty.TRANSPARENT
        },
        hardness=0.0
    ),
    "sand": Material(
        name="sand",
        base_properties={
            MaterialProperty.GRANULAR,
            MaterialProperty.HEAT_RESISTANT
        } if hasattr(MaterialProperty, 'GRANULAR') else {MaterialProperty.HEAT_RESISTANT},
        hardness=0.2
    ),
    "metal_ore": Material(
        name="metal_ore",
        base_properties={
            MaterialProperty.DENSE,
            MaterialProperty.HARD,
            MaterialProperty.HEAT_RESISTANT
        },
        hardness=0.6,
        melting_point=1200.0
    ),
    "hide": Material(
        name="hide",
        base_properties={
            MaterialProperty.FLEXIBLE,
            MaterialProperty.WATERPROOF
        },
        hardness=0.3
    ),
}


# ==============================================================================
# DISCOVERY SYSTEM
# ==============================================================================

@dataclass
class ExperimentIntent:
    """
    The REASONING behind an experiment - WHY is the agent doing this?

    This is the chain-of-thought that drives purposeful experimentation.
    """
    # What problem are they trying to solve?
    problem: str  # "I'm hungry", "Need stronger shelter", "Want better tools"

    # What's their goal?
    goal: str  # "Make food more nutritious", "Create harder building material"

    # Why did they choose these materials/method?
    reasoning: str  # "Heat made food taste better before, maybe it works on plant_fiber too"

    # What do they expect to happen?
    hypothesis: str  # "This should create a stronger material"

    # What motivated this? (need-driven)
    motivation: str  # "hunger", "safety", "efficiency", "curiosity", "social_status"


@dataclass
class ExperimentResult:
    """Result of an experiment"""
    success: bool
    discovered_material: Optional[Material] = None
    discovered_properties: Set[MaterialProperty] = field(default_factory=set)
    failure_reason: Optional[str] = None

    # Consequences
    materials_consumed: Dict[str, int] = field(default_factory=dict)
    materials_produced: Dict[str, int] = field(default_factory=dict)
    explosion: bool = False
    fire: bool = False
    injury: bool = False

    # Learning
    lesson_learned: Optional[str] = None

    # Intent - WHY did they do this?
    intent: Optional[ExperimentIntent] = None


@dataclass
class Discovery:
    """A discovered material, tool, or technique"""
    id: str
    name: str  # Agent-named!
    discovered_by: str
    discovery_date: datetime

    # What it is
    material: Optional[Material] = None
    recipe: Optional[Dict] = None  # inputs + method
    category: ExperimentCategory = ExperimentCategory.MATERIAL_SCIENCE  # What domain

    # WHY was this discovered? (Chain of thought)
    intent: Optional[ExperimentIntent] = None

    # What it does
    properties: Set[MaterialProperty] = field(default_factory=set)
    effectiveness: float = 0.0  # Learned through use

    # Knowledge spread
    known_by: Set[str] = field(default_factory=set)
    times_used: int = 0
    success_rate: float = 0.5  # Improves with practice

    # Context
    description: str = ""
    discovery_context: Dict = field(default_factory=dict)


class ExperimentationEngine:
    """
    The core engine for TRUE innovation.

    Agents experiment with materials and discover emergent properties.
    NO predetermined outcomes - physics simulation determines results.
    """

    def __init__(self):
        self.materials: Dict[str, Material] = BASE_MATERIALS.copy()
        self.discoveries: Dict[str, Discovery] = {}
        self.failed_experiments: List[Dict] = []

    def _determine_experiment_category(
        self,
        materials: List[str],
        method: ExperimentMethod
    ) -> ExperimentCategory:
        """
        Intelligently determine what category this experiment belongs to
        based on materials and method used.
        """
        # Food-related materials
        food_materials = {'food', 'plant_fiber', 'water'}
        # Building materials
        building_materials = {'stone', 'wood', 'clay', 'sand'}
        # Metal materials
        metal_materials = {'metal_ore', 'iron', 'copper', 'bronze', 'steel'}
        # Textile materials
        textile_materials = {'plant_fiber', 'hide', 'fiber', 'cloth'}

        material_set = set(materials)

        # Cooking: heat + food materials
        if method in [ExperimentMethod.HEAT, ExperimentMethod.FERMENT] and material_set & food_materials:
            return ExperimentCategory.COOKING

        # Metallurgy: metal materials with heat/refine/pound
        if material_set & metal_materials and method in [ExperimentMethod.HEAT, ExperimentMethod.REFINE, ExperimentMethod.POUND]:
            return ExperimentCategory.METALLURGY

        # Textiles: weaving or using fibers
        if method == ExperimentMethod.WEAVE or material_set & textile_materials:
            return ExperimentCategory.TEXTILES

        # Building: construction materials with layer/compress/shape
        if material_set & building_materials and method in [ExperimentMethod.LAYER, ExperimentMethod.COMPRESS, ExperimentMethod.SHAPE]:
            return ExperimentCategory.BUILDING

        # Crafting: shaping/sharpening to make tools
        if method in [ExperimentMethod.SHAPE, ExperimentMethod.SHARPEN, ExperimentMethod.POUND]:
            return ExperimentCategory.CRAFTING

        # Chemistry: mixing, dissolving, reactions
        if method in [ExperimentMethod.MIX, ExperimentMethod.DISSOLVE, ExperimentMethod.FERMENT]:
            return ExperimentCategory.CHEMISTRY

        # Default to material science
        return ExperimentCategory.MATERIAL_SCIENCE

    def _generate_experiment_intent(
        self,
        materials: List[str],
        method: ExperimentMethod,
        category: ExperimentCategory,
        agent_context: Dict
    ) -> ExperimentIntent:
        """
        Generate realistic chain-of-thought reasoning for why the agent
        is doing this experiment.

        This makes agents feel intelligent and purposeful!
        """
        # Analyze agent's needs from context
        needs = agent_context.get('needs', {})
        hunger = needs.get('hunger', 0.5)
        energy = needs.get('energy', 0.5)

        # Determine primary motivation
        if hunger > 0.7:
            motivation = "hunger"
            problem = "I'm very hungry and need better food sources"
        elif energy < 0.3:
            motivation = "exhaustion"
            problem = "I'm exhausted and need to be more efficient"
        elif agent_context.get('curiosity', False):
            motivation = "curiosity"
            problem = "I wonder what happens if I try something new"
        else:
            motivation = "improvement"
            problem = "I want to improve our civilization's capabilities"

        # Generate goal based on category
        category_goals = {
            ExperimentCategory.COOKING: f"Create more nutritious food from {', '.join(materials)}",
            ExperimentCategory.BUILDING: f"Discover stronger building materials",
            ExperimentCategory.CRAFTING: f"Make better tools for gathering resources",
            ExperimentCategory.TEXTILES: f"Create fabric or rope from fibers",
            ExperimentCategory.METALLURGY: f"Work metal into useful forms",
            ExperimentCategory.CHEMISTRY: f"Understand how materials interact",
            ExperimentCategory.MEDICINE: f"Find healing properties in materials",
            ExperimentCategory.MATERIAL_SCIENCE: f"Learn what {', '.join(materials)} can do"
        }
        goal = category_goals.get(category, "Discover new materials")

        # Generate reasoning based on method and materials
        method_reasoning = {
            ExperimentMethod.HEAT: f"Heating {materials[0]} might change its properties - fire transforms things",
            ExperimentMethod.COMPRESS: f"Pressing {', '.join(materials)} together might make something stronger",
            ExperimentMethod.MIX: f"Combining {', '.join(materials)} could create something entirely new",
            ExperimentMethod.SHAPE: f"Molding {materials[0]} into a form could make it more useful",
            ExperimentMethod.REFINE: f"Purifying {materials[0]} might reveal hidden properties",
            ExperimentMethod.WEAVE: f"Interlacing {materials[0]} could create flexible material",
            ExperimentMethod.POUND: f"Crushing {', '.join(materials)} might break them down usefully"
        }
        reasoning = method_reasoning.get(
            method,
            f"Trying {method.value} on {', '.join(materials)} to see what happens"
        )

        # Generate hypothesis
        if category == ExperimentCategory.COOKING:
            hypothesis = f"This should make the food more edible and nutritious"
        elif category == ExperimentCategory.BUILDING:
            hypothesis = f"This could create a material strong enough for construction"
        elif category == ExperimentCategory.CRAFTING:
            hypothesis = f"This might produce a useful tool or component"
        else:
            hypothesis = f"This experiment should reveal new material properties"

        return ExperimentIntent(
            problem=problem,
            goal=goal,
            reasoning=reasoning,
            hypothesis=hypothesis,
            motivation=motivation
        )

    def attempt_experiment(
        self,
        agent_id: str,
        agent_name: str,
        inputs: Dict[str, int],  # material -> quantity
        method: ExperimentMethod,
        context: Dict = None
    ) -> ExperimentResult:
        """
        Agent attempts to experiment with materials.

        This is where TRUE innovation happens!

        40-50% of experiments FAIL - real risk, real reward.
        """
        context = context or {}

        # Get input materials
        input_materials = [
            self.materials[mat_name]
            for mat_name in inputs.keys()
            if mat_name in self.materials
        ]

        if not input_materials:
            return ExperimentResult(
                success=False,
                failure_reason="No valid materials",
                lesson_learned="Need actual materials to experiment"
            )

        # CHAIN-OF-THOUGHT: Generate reasoning BEFORE attempting
        # This is WHY the agent is doing this experiment
        category = self._determine_experiment_category(
            list(inputs.keys()),
            method if isinstance(method, ExperimentMethod) else ExperimentMethod(method)
        )

        intent = self._generate_experiment_intent(
            list(inputs.keys()),
            method if isinstance(method, ExperimentMethod) else ExperimentMethod(method),
            category,
            context
        )

        # Simulate the experiment
        result = self._simulate_experiment(
            input_materials,
            inputs,
            method,
            agent_id,
            context
        )

        # Attach intent to result
        result.intent = intent

        # Record if discovery made
        if result.success and result.discovered_material:
            discovery = Discovery(
                id=str(uuid.uuid4()),
                name=result.discovered_material.name,
                discovered_by=agent_id,
                discovery_date=datetime.now(),
                material=result.discovered_material,
                recipe={"inputs": inputs, "method": (method if isinstance(method, str) else method.value)},
                category=category,
                properties=result.discovered_properties,
                known_by={agent_id},
                description=f"{agent_name} discovered this!",
                discovery_context=context,
                intent=intent  # Store the chain-of-thought reasoning
            )

            self.discoveries[discovery.id] = discovery
            self.materials[result.discovered_material.name] = result.discovered_material

        # Record failures for learning - ENHANCED with full story AND chain-of-thought
        elif not result.success:
            self.failed_experiments.append({
                "agent_id": agent_id,
                "inputs": inputs,
                "method": (method if isinstance(method, str) else method.value),
                "category": category.value,
                "reason": result.failure_reason,
                "lesson_learned": result.lesson_learned,
                "consequences": {
                    "explosion": result.explosion,
                    "fire": result.fire,
                    "injury": result.injury,
                    "materials_lost": result.materials_consumed
                },
                "intent": {  # Store the chain-of-thought reasoning
                    "problem": intent.problem,
                    "goal": intent.goal,
                    "reasoning": intent.reasoning,
                    "hypothesis": intent.hypothesis,
                    "motivation": intent.motivation
                },
                "date": datetime.now()
            })

        return result

    def _simulate_experiment(
        self,
        materials: List[Material],
        quantities: Dict[str, int],
        method: ExperimentMethod,
        agent_id: str,
        context: Dict
    ) -> ExperimentResult:
        """
        Simulate the physics of combining materials.

        This is where emergent properties arise!
        """

        # Base success rate: 50%
        success_chance = 0.5

        # Agent skill affects success
        agent_skill = context.get('skill_level', 0.0)
        success_chance += agent_skill * 0.2

        # Some combinations are more likely to work
        compatibility = self._check_compatibility(materials, method)
        success_chance += compatibility * 0.3

        # Roll for success
        if random.random() > success_chance:
            # FAILURE
            return self._generate_failure(materials, method, quantities)

        # SUCCESS - generate new material
        return self._generate_discovery(materials, method, quantities, agent_id)

    def _check_compatibility(
        self,
        materials: List[Material],
        method: ExperimentMethod
    ) -> float:
        """Check if materials + method make sense"""

        all_props = set()
        for mat in materials:
            all_props.update(mat.all_properties())

        # Some method-property combos are logical
        compatibility = 0.0

        if method == ExperimentMethod.HEAT:
            # Heating clay makes it hard
            if MaterialProperty.MALLEABLE in all_props:
                compatibility += 0.4
            # Heating metal ore extracts metal
            if any("metal" in m.name for m in materials):
                compatibility += 0.5

        elif method == ExperimentMethod.WEAVE:
            # Weaving fibers makes fabric
            if MaterialProperty.FLEXIBLE in all_props:
                compatibility += 0.6

        elif method == ExperimentMethod.POUND:
            # Pounding stone makes sharp edges
            if MaterialProperty.BRITTLE in all_props:
                compatibility += 0.5

        elif method == ExperimentMethod.MIX:
            # Mixing soluble things works
            if MaterialProperty.SOLUBLE in all_props:
                compatibility += 0.3

        # More materials = harder to control
        if len(materials) > 3:
            compatibility -= 0.2

        return max(0.0, min(1.0, compatibility))

    def _generate_failure(
        self,
        materials: List[Material],
        method: ExperimentMethod,
        quantities: Dict[str, int]
    ) -> ExperimentResult:
        """Generate realistic failure"""

        # Determine what went wrong
        failures = [
            ("Materials didn't react", False, False, False),
            ("Materials crumbled apart", False, False, False),
            ("Process was too difficult", False, False, False),
            ("Materials were consumed without result", False, False, False),
        ]

        # Dangerous failures
        all_props = set()
        for mat in materials:
            all_props.update(mat.all_properties())

        if method == ExperimentMethod.HEAT:
            if MaterialProperty.FLAMMABLE in all_props:
                failures.append(("Materials caught fire!", True, False, False))
            if MaterialProperty.REACTIVE in all_props:
                failures.append(("Explosion!", False, True, True))

        reason, fire, explosion, injury = random.choice(failures)

        # Materials consumed
        consumed = quantities.copy()
        # Sometimes you lose only part
        if random.random() < 0.3:
            for mat in consumed:
                consumed[mat] = max(1, consumed[mat] // 2)

        return ExperimentResult(
            success=False,
            failure_reason=reason,
            materials_consumed=consumed,
            fire=fire,
            explosion=explosion,
            injury=injury,
            lesson_learned=f"Don't {method if isinstance(method, str) else (method if isinstance(method, str) else method.value)} {', '.join(quantities.keys())} that way"
        )

    def _generate_discovery(
        self,
        materials: List[Material],
        method: ExperimentMethod,
        quantities: Dict[str, int],
        agent_id: str
    ) -> ExperimentResult:
        """
        Generate a new discovered material with emergent properties!

        This is where innovation happens - agents discover:
        - Pottery (clay + heat)
        - Bronze (copper ore + tin ore + heat)
        - Fabric (plant fiber + weave)
        - Tools (stone + wood + pound)
        - And eventually... rockets!
        """

        # Generate name based on inputs + method
        material_names = list(quantities.keys())

        # ===== MILESTONE MATERIALS - Game-changing discoveries! =====

        # FIRE - The first milestone! (Stone Age → Bronze Age)
        if method == ExperimentMethod.HEAT and ("wood" in material_names or "plant_fiber" in material_names):
            # Agent discovered how to create fire!
            new_name = "fire"
            new_props = {MaterialProperty.FLAMMABLE, MaterialProperty.HEAT_RESISTANT}
            hardness = 0.1

        # POTTERY - Enables storage and cooking
        elif method == ExperimentMethod.HEAT and "clay" in material_names:
            new_name = "pottery"
            new_props = {MaterialProperty.HARD, MaterialProperty.BRITTLE, MaterialProperty.HEAT_RESISTANT}
            hardness = 0.6

        # BRONZE - The second milestone! (Bronze Age → Iron Age)
        elif method == ExperimentMethod.REFINE and "metal_ore" in material_names:
            new_name = "bronze"
            new_props = {MaterialProperty.HARD, MaterialProperty.MALLEABLE, MaterialProperty.CONDUCTIVE, MaterialProperty.LOAD_BEARING}
            hardness = 0.9

        # REFINED METAL - Alternative path to bronze
        elif method == ExperimentMethod.HEAT and "metal_ore" in material_names:
            new_name = "refined_metal"
            new_props = {MaterialProperty.HARD, MaterialProperty.MALLEABLE, MaterialProperty.CONDUCTIVE}
            hardness = 0.85

        # IRON / STEEL - The third milestone! (Iron Age → Medieval)
        elif (method == ExperimentMethod.REFINE or method == ExperimentMethod.HEAT) and "iron_ore" in material_names:
            if random.random() > 0.5:
                new_name = "iron"
            else:
                new_name = "steel"
            new_props = {MaterialProperty.HARD, MaterialProperty.LOAD_BEARING, MaterialProperty.SHARP}
            hardness = 0.95

        # FABRIC - Enables clothing and textiles
        elif method == ExperimentMethod.WEAVE and "plant_fiber" in material_names:
            new_name = "fabric"
            new_props = {MaterialProperty.FLEXIBLE, MaterialProperty.LIGHT}
            hardness = 0.2

        # SHARP STONE - Basic tools
        elif method == ExperimentMethod.POUND and "stone" in material_names:
            new_name = "sharp_stone"
            new_props = {MaterialProperty.HARD, MaterialProperty.SHARP}
            hardness = 0.7

        elif method == ExperimentMethod.MIX:
            new_name = f"mixture_of_{'_and_'.join(material_names[:2])}"
            # Inherit properties from both
            new_props = set()
            for mat in materials:
                new_props.update(list(mat.all_properties())[:2])
            hardness = sum(m.hardness for m in materials) / len(materials)

        else:
            # Generic combination
            new_name = f"{method if isinstance(method, str) else (method if isinstance(method, str) else method.value)}_{material_names[0]}"
            # Inherit some properties
            new_props = set(list(materials[0].all_properties())[:2])
            hardness = materials[0].hardness

        # Create the new material
        new_material = Material(
            name=new_name,
            base_properties=new_props,
            hardness=hardness,
            discovered_by=agent_id,
            discovery_date=datetime.now()
        )

        return ExperimentResult(
            success=True,
            discovered_material=new_material,
            discovered_properties=new_props,
            materials_consumed=quantities,
            materials_produced={new_name: 1},
            lesson_learned=f"Discovered that {(method if isinstance(method, str) else method.value)} + {material_names} = {new_name}!"
        )

    def get_statistics(self) -> Dict:
        """Get experimentation statistics"""
        return {
            "total_materials": len(self.materials),
            "base_materials": len(BASE_MATERIALS),
            "discovered_materials": len(self.materials) - len(BASE_MATERIALS),
            "total_discoveries": len(self.discoveries),
            "total_failed_experiments": len(self.failed_experiments),
            "success_rate": (
                len(self.discoveries) /
                (len(self.discoveries) + len(self.failed_experiments))
                if (len(self.discoveries) + len(self.failed_experiments)) > 0
                else 0.0
            ),
            "materials_by_discoverer": self._count_by_discoverer(),
        }

    def _count_by_discoverer(self) -> Dict[str, int]:
        """Count discoveries by agent"""
        counts = {}
        for discovery in self.discoveries.values():
            counts[discovery.discovered_by] = counts.get(discovery.discovered_by, 0) + 1
        return counts
