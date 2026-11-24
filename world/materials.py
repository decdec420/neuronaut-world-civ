"""
Advanced Materials System - Material Science Evolution

Implements:
- Material progression (stone → bronze → iron → steel → composites → semiconductors)
- Material properties (strength, durability, conductivity)
- Alloy creation and metallurgy
- Ceramics and glass production
- Polymers and plastics
- Composites and advanced materials
- Semiconductors and electronics

Philosophy: Materials define civilization eras.
Stone Age → Bronze Age → Iron Age → Steel Age → Silicon Age
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class MaterialCategory(Enum):
    """Categories of materials"""
    # Natural
    STONE = "stone"
    WOOD = "wood"
    BONE = "bone"
    LEATHER = "leather"

    # Metals
    PURE_METAL = "pure_metal"
    ALLOY = "alloy"

    # Ceramics
    CERAMIC = "ceramic"
    GLASS = "glass"

    # Organic
    POLYMER = "polymer"
    RUBBER = "rubber"

    # Advanced
    COMPOSITE = "composite"
    SEMICONDUCTOR = "semiconductor"
    SUPERCONDUCTOR = "superconductor"


class MaterialEra(Enum):
    """Historical eras defined by materials"""
    STONE_AGE = "stone_age"
    BRONZE_AGE = "bronze_age"
    IRON_AGE = "iron_age"
    STEEL_AGE = "steel_age"
    PLASTIC_AGE = "plastic_age"
    SILICON_AGE = "silicon_age"


@dataclass
class Material:
    """A material with physical properties"""
    id: str
    name: str
    category: MaterialCategory

    # Physical properties (0-1 normalized)
    strength: float = 0.5  # Tensile/compressive strength
    hardness: float = 0.5  # Resistance to deformation
    durability: float = 0.5  # Resistance to wear
    flexibility: float = 0.5  # Ability to bend without breaking
    density: float = 0.5  # Mass per volume

    # Special properties
    electrical_conductivity: float = 0.0  # 0-1
    thermal_conductivity: float = 0.0  # 0-1
    transparency: float = 0.0  # 0-1
    magnetic: bool = False

    # Processing
    melting_point: int = 1000  # Celsius
    requires_smelting: bool = False
    requires_refining: bool = False

    # Recipe (what's needed to create it)
    recipe: Dict[str, int] = field(default_factory=dict)  # material_id -> quantity

    # Discovery
    discovered: bool = False
    discoverer_id: Optional[str] = None
    discovered_tick: int = 0

    # Era unlocked
    unlocks_era: Optional[MaterialEra] = None


@dataclass
class Alloy:
    """A metal alloy (combination of metals)"""
    id: str
    name: str
    formula: str  # e.g., "Cu3Sn" for bronze

    # Component metals (element_symbol -> ratio)
    components: Dict[str, float] = field(default_factory=dict)

    # Properties
    strength: float = 0.7
    hardness: float = 0.7
    melting_point: int = 1200

    # Discovery
    discovered: bool = False
    discoverer_id: Optional[str] = None
    discovered_tick: int = 0


@dataclass
class MaterialProcess:
    """A manufacturing/processing technique"""
    id: str
    name: str
    process_type: str  # smelting, forging, casting, molding, etc.

    # Input → Output
    input_materials: Dict[str, int] = field(default_factory=dict)
    output_material: str = ""
    output_quantity: int = 1

    # Requirements
    requires_heat: bool = False
    required_temperature: int = 25
    required_tools: List[str] = field(default_factory=list)

    # Discovery
    discovered: bool = False


class MaterialsManager:
    """
    Manages materials science and technological progression.

    Key mechanics:
    - Materials unlock through discovery and experimentation
    - Alloys created by combining metals
    - Material properties determine what can be built
    - Advanced materials enable new technologies
    """

    def __init__(self):
        self.materials: Dict[str, Material] = {}
        self.alloys: Dict[str, Alloy] = {}
        self.processes: Dict[str, MaterialProcess] = {}

        # Discovery tracking
        self.discovered_materials: Set[str] = set()
        self.discovered_alloys: Set[str] = set()
        self.current_era: MaterialEra = MaterialEra.STONE_AGE

        # Statistics
        self.total_materials_discovered: int = 0
        self.total_alloys_created: int = 0

        # Initialize material library
        self._init_materials()
        self._init_alloys()
        self._init_processes()

    # ===== MATERIAL INITIALIZATION =====

    def _init_materials(self):
        """Initialize material library"""

        materials_data = [
            # STONE AGE (always available)
            ("stone", "Stone", MaterialCategory.STONE, 0.6, 0.8, 0.9, 0.1, 0.8, 0.0, 0.0, 0.0, False, 2000, False, False, {}, True, MaterialEra.STONE_AGE),
            ("wood", "Wood", MaterialCategory.WOOD, 0.4, 0.3, 0.5, 0.7, 0.3, 0.0, 0.1, 0.0, False, 200, False, False, {}, True, None),
            ("bone", "Bone", MaterialCategory.BONE, 0.5, 0.6, 0.6, 0.3, 0.5, 0.0, 0.0, 0.0, False, 1200, False, False, {}, True, None),
            ("leather", "Leather", MaterialCategory.LEATHER, 0.3, 0.4, 0.7, 0.9, 0.2, 0.0, 0.0, 0.0, False, 100, False, False, {}, True, None),

            # METALS (discovered through mining/smelting)
            ("copper", "Copper", MaterialCategory.PURE_METAL, 0.4, 0.3, 0.6, 0.8, 0.9, 1.0, 0.9, 0.0, False, 1085, True, False, {"copper_ore": 1}, False, None),
            ("tin", "Tin", MaterialCategory.PURE_METAL, 0.3, 0.2, 0.5, 0.9, 0.7, 0.6, 0.7, 0.0, False, 232, True, False, {"tin_ore": 1}, False, None),
            ("bronze", "Bronze", MaterialCategory.ALLOY, 0.7, 0.6, 0.8, 0.4, 0.85, 0.3, 0.5, 0.0, False, 950, True, False, {"copper": 3, "tin": 1}, False, MaterialEra.BRONZE_AGE),

            ("iron", "Iron", MaterialCategory.PURE_METAL, 0.8, 0.7, 0.7, 0.3, 0.95, 0.2, 0.8, 0.0, True, 1538, True, False, {"iron_ore": 1}, False, MaterialEra.IRON_AGE),
            ("steel", "Steel", MaterialCategory.ALLOY, 0.95, 0.9, 0.9, 0.4, 0.98, 0.2, 0.5, 0.0, True, 1370, True, True, {"iron": 1, "carbon": 1}, False, MaterialEra.STEEL_AGE),

            ("gold", "Gold", MaterialCategory.PURE_METAL, 0.2, 0.3, 0.9, 0.9, 0.95, 1.0, 0.8, 0.0, False, 1064, True, False, {"gold_ore": 1}, False, None),
            ("silver", "Silver", MaterialCategory.PURE_METAL, 0.3, 0.4, 0.8, 0.8, 0.9, 1.0, 0.9, 0.0, False, 962, True, False, {"silver_ore": 1}, False, None),
            ("aluminum", "Aluminum", MaterialCategory.PURE_METAL, 0.6, 0.5, 0.8, 0.7, 0.3, 0.6, 0.9, 0.0, False, 660, True, True, {"bauxite": 1}, False, None),
            ("titanium", "Titanium", MaterialCategory.PURE_METAL, 0.9, 0.8, 0.95, 0.5, 0.6, 0.1, 0.4, 0.0, False, 1668, True, True, {"titanium_ore": 1}, False, None),

            # CERAMICS
            ("clay", "Clay", MaterialCategory.CERAMIC, 0.2, 0.2, 0.3, 0.8, 0.4, 0.0, 0.1, 0.0, False, 1000, True, False, {}, True, None),
            ("brick", "Brick", MaterialCategory.CERAMIC, 0.5, 0.6, 0.8, 0.1, 0.6, 0.0, 0.1, 0.0, False, 1500, True, False, {"clay": 1}, False, None),
            ("glass", "Glass", MaterialCategory.GLASS, 0.4, 0.7, 0.3, 0.1, 0.3, 0.0, 0.2, 1.0, False, 1400, True, False, {"sand": 1}, False, None),
            ("porcelain", "Porcelain", MaterialCategory.CERAMIC, 0.6, 0.8, 0.7, 0.1, 0.5, 0.0, 0.1, 0.8, False, 1280, True, True, {"clay": 2}, False, None),

            # POLYMERS (modern era)
            ("rubber", "Rubber", MaterialCategory.RUBBER, 0.3, 0.2, 0.7, 0.95, 0.3, 0.0, 0.1, 0.0, False, 150, False, True, {"latex": 1}, False, None),
            ("plastic", "Plastic", MaterialCategory.POLYMER, 0.4, 0.4, 0.6, 0.8, 0.3, 0.0, 0.1, 0.5, False, 120, False, True, {"oil": 1}, False, MaterialEra.PLASTIC_AGE),
            ("nylon", "Nylon", MaterialCategory.POLYMER, 0.5, 0.4, 0.8, 0.9, 0.2, 0.0, 0.1, 0.3, False, 220, False, True, {"oil": 2}, False, None),

            # ADVANCED MATERIALS
            ("fiberglass", "Fiberglass", MaterialCategory.COMPOSITE, 0.8, 0.6, 0.9, 0.7, 0.4, 0.0, 0.1, 0.5, False, 800, False, True, {"glass": 2, "resin": 1}, False, None),
            ("carbon_fiber", "Carbon Fiber", MaterialCategory.COMPOSITE, 0.95, 0.9, 0.95, 0.8, 0.2, 0.3, 0.5, 0.0, False, 3600, False, True, {"carbon": 3, "polymer": 1}, False, None),

            # SEMICONDUCTORS (silicon age)
            ("silicon", "Silicon", MaterialCategory.SEMICONDUCTOR, 0.5, 0.7, 0.9, 0.2, 0.3, 0.5, 0.3, 0.5, False, 1414, True, True, {"sand": 1}, False, MaterialEra.SILICON_AGE),
            ("silicon_chip", "Silicon Chip", MaterialCategory.SEMICONDUCTOR, 0.3, 0.6, 0.8, 0.1, 0.3, 0.9, 0.7, 0.2, False, 1414, False, True, {"silicon": 1, "gold": 1}, False, None),
        ]

        for (name_id, name, category, strength, hardness, durability, flexibility, density,
             elec_cond, therm_cond, transparency, magnetic, melt_point, requires_smelt,
             requires_refine, recipe, discovered, unlocks_era) in materials_data:

            material_id = str(new_uuid())
            material = Material(
                id=material_id,
                name=name,
                category=category,
                strength=strength,
                hardness=hardness,
                durability=durability,
                flexibility=flexibility,
                density=density,
                electrical_conductivity=elec_cond,
                thermal_conductivity=therm_cond,
                transparency=transparency,
                magnetic=magnetic,
                melting_point=melt_point,
                requires_smelting=requires_smelt,
                requires_refining=requires_refine,
                recipe=recipe,
                discovered=discovered,
                unlocks_era=unlocks_era
            )

            self.materials[name_id] = material

            if discovered:
                self.discovered_materials.add(name_id)

    def _init_alloys(self):
        """Initialize metal alloys"""

        alloys_data = [
            ("bronze", "Bronze", "Cu3Sn", {"Cu": 0.75, "Sn": 0.25}, 0.7, 0.6, 950),
            ("steel", "Steel", "FeC", {"Fe": 0.99, "C": 0.01}, 0.95, 0.9, 1370),
            ("brass", "Brass", "CuZn", {"Cu": 0.7, "Zn": 0.3}, 0.6, 0.5, 900),
            ("stainless_steel", "Stainless Steel", "FeCrNi", {"Fe": 0.7, "Cr": 0.2, "Ni": 0.1}, 0.9, 0.85, 1400),
        ]

        for alloy_id, name, formula, components, strength, hardness, melt_point in alloys_data:
            alloy = Alloy(
                id=str(new_uuid()),
                name=name,
                formula=formula,
                components=components,
                strength=strength,
                hardness=hardness,
                melting_point=melt_point
            )
            self.alloys[alloy_id] = alloy

    def _init_processes(self):
        """Initialize manufacturing processes"""
        # Processes can be added later as needed
        pass

    # ===== MATERIAL DISCOVERY =====

    def discover_material(
        self,
        material_id: str,
        discoverer_id: str,
        current_tick: int
    ) -> Optional[Material]:
        """Agent discovers a new material"""

        if material_id not in self.materials:
            return None

        material = self.materials[material_id]

        if material.discovered:
            return material  # Already discovered

        # Discovery successful!
        material.discovered = True
        material.discoverer_id = discoverer_id
        material.discovered_tick = current_tick

        self.discovered_materials.add(material_id)
        self.total_materials_discovered += 1

        # Check if this unlocks a new era
        if material.unlocks_era:
            self._advance_era(material.unlocks_era)

        return material

    def _advance_era(self, new_era: MaterialEra):
        """Advance to a new material era"""

        # Only advance if new era is later than current
        era_order = [
            MaterialEra.STONE_AGE,
            MaterialEra.BRONZE_AGE,
            MaterialEra.IRON_AGE,
            MaterialEra.STEEL_AGE,
            MaterialEra.PLASTIC_AGE,
            MaterialEra.SILICON_AGE
        ]

        current_idx = era_order.index(self.current_era)
        new_idx = era_order.index(new_era)

        if new_idx > current_idx:
            self.current_era = new_era

    # ===== ALLOY CREATION =====

    def create_alloy(
        self,
        alloy_id: str,
        creator_id: str,
        current_tick: int
    ) -> Optional[Alloy]:
        """Agent creates a metal alloy"""

        if alloy_id not in self.alloys:
            return None

        alloy = self.alloys[alloy_id]

        if alloy.discovered:
            return alloy  # Already created

        # Create successful!
        alloy.discovered = True
        alloy.discoverer_id = creator_id
        alloy.discovered_tick = current_tick

        self.discovered_alloys.add(alloy_id)
        self.total_alloys_created += 1

        return alloy

    # ===== MATERIAL PROCESSING =====

    def can_create_material(
        self,
        material_id: str,
        available_materials: Dict[str, int]
    ) -> bool:
        """Check if agent has materials to create this material"""

        if material_id not in self.materials:
            return False

        material = self.materials[material_id]

        # Check recipe requirements
        for required_mat, required_qty in material.recipe.items():
            if available_materials.get(required_mat, 0) < required_qty:
                return False

        return True

    def process_material(
        self,
        material_id: str,
        available_materials: Dict[str, int],
        has_heat: bool = False,
        temperature: int = 25
    ) -> Optional[Dict]:
        """Process raw materials into finished material"""

        if material_id not in self.materials:
            return None

        material = self.materials[material_id]

        # Check recipe
        if not self.can_create_material(material_id, available_materials):
            return {
                'success': False,
                'reason': 'Insufficient materials'
            }

        # Check temperature requirements
        if material.requires_smelting:
            if not has_heat or temperature < material.melting_point:
                return {
                    'success': False,
                    'reason': f'Requires {material.melting_point}°C heat'
                }

        # Success!
        return {
            'success': True,
            'material': material,
            'consumed': material.recipe
        }

    # ===== QUERIES =====

    def get_discovered_materials(self) -> List[Material]:
        """Get all discovered materials"""
        return [m for m in self.materials.values() if m.discovered]

    def get_materials_by_category(self, category: MaterialCategory) -> List[Material]:
        """Get materials in a category"""
        return [m for m in self.materials.values() if m.category == category and m.discovered]

    def get_current_era(self) -> MaterialEra:
        """Get current material era"""
        return self.current_era

    def get_statistics(self) -> Dict:
        """Get materials system statistics"""

        discovered_count = len(self.discovered_materials)
        total_count = len(self.materials)

        # Era progress
        era_materials = {
            MaterialEra.STONE_AGE: ["stone", "wood", "bone", "leather"],
            MaterialEra.BRONZE_AGE: ["copper", "tin", "bronze"],
            MaterialEra.IRON_AGE: ["iron"],
            MaterialEra.STEEL_AGE: ["steel"],
            MaterialEra.PLASTIC_AGE: ["plastic", "rubber", "nylon"],
            MaterialEra.SILICON_AGE: ["silicon", "silicon_chip"]
        }

        return {
            'current_era': self.current_era.value,
            'total_materials': total_count,
            'discovered_materials': discovered_count,
            'discovery_percentage': round((discovered_count / max(1, total_count)) * 100, 1),
            'total_alloys_created': self.total_alloys_created,
            'discovered_alloys': len(self.discovered_alloys)
        }
