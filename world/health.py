"""
Disease & Medicine System - Health Challenges Drive Innovation

Implements:
- Disease types (plague, flu, infections, injuries)
- Disease spread (proximity-based contagion)
- Symptoms and severity levels
- Medicine discovery (herbs, treatments, cures)
- Healer specialization (medical knowledge)
- Public health (quarantine, sanitation, hygiene)

Philosophy: Disease creates pressure for medical innovation.
Without health challenges, no healers, no medicine, no public health systems.
"""

import random
from engine.ids import new_uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum


class DiseaseType(Enum):
    """Types of diseases"""
    # Infectious diseases (spread between agents)
    PLAGUE = "plague"  # Deadly, fast-spreading
    FLU = "flu"  # Common, moderate severity
    INFECTION = "infection"  # From wounds/injuries

    # Environmental diseases
    FOOD_POISONING = "food_poisoning"  # From bad food
    HEAT_STROKE = "heat_stroke"  # From extreme heat
    HYPOTHERMIA = "hypothermia"  # From extreme cold

    # Chronic conditions
    MALNUTRITION = "malnutrition"  # From lack of food
    DEHYDRATION = "dehydration"  # From lack of water
    EXHAUSTION = "exhaustion"  # From overwork


class Severity(Enum):
    """Disease severity levels"""
    MILD = "mild"  # Minor discomfort, recovers naturally
    MODERATE = "moderate"  # Significant impact, needs rest
    SEVERE = "severe"  # Life-threatening, needs treatment
    CRITICAL = "critical"  # Imminent death without treatment


class MedicineType(Enum):
    """Types of medicine"""
    HERB = "herb"  # Plant-based remedies
    POULTICE = "poultice"  # Topical treatments
    TONIC = "tonic"  # Drinkable medicines
    SALVE = "salve"  # Ointments
    BANDAGE = "bandage"  # Wound care
    ANTIDOTE = "antidote"  # Poison/disease cure


@dataclass
class Disease:
    """An active disease affecting an agent"""
    id: str
    disease_type: DiseaseType
    infected_agent_id: str
    severity: Severity

    # Progression
    infection_tick: int  # When infected
    duration: int = 100  # How long it lasts (ticks)
    progress: float = 0.0  # 0-1, how far along

    # Effects
    health_damage_per_tick: float = 0.5
    energy_drain_per_tick: float = 1.0
    contagious: bool = True
    transmission_radius: float = 10.0  # Meters
    transmission_chance: float = 0.05  # Per tick when near infected

    # Treatment
    treated: bool = False
    treatment_effectiveness: float = 0.0  # 0-1

    # Symptoms (visible to others)
    symptoms: List[str] = field(default_factory=list)


@dataclass
class Medicine:
    """A discovered medicinal treatment"""
    id: str
    name: str
    medicine_type: MedicineType

    # Discovery
    discoverer_id: str
    discovered_at: int

    # Ingredients and recipe
    ingredients: Dict[str, int]  # material_name -> quantity
    preparation_method: str  # "grind", "boil", "ferment", etc.

    # Effectiveness
    cures_diseases: List[DiseaseType] = field(default_factory=list)
    effectiveness: float = 0.5  # 0-1, how well it works
    side_effects: List[str] = field(default_factory=list)

    # Knowledge spread
    known_by: Set[str] = field(default_factory=set)
    times_used: int = 0
    success_rate: float = 0.0  # Learned through use


@dataclass
class MedicalKnowledge:
    """Healer's accumulated medical knowledge"""
    agent_id: str
    healing_skill: float = 0.0  # 0-1, improves with practice

    # Known diseases and treatments
    diagnosed_diseases: Set[DiseaseType] = field(default_factory=set)
    known_medicines: Set[str] = field(default_factory=set)  # Medicine IDs

    # Experience
    patients_treated: int = 0
    successful_treatments: int = 0
    patients_lost: int = 0

    # Specialization
    is_healer: bool = False  # Recognized as medical specialist


class HealthManager:
    """
    Manages disease, medicine, and healing in the simulation.

    Key mechanics:
    - Diseases spread through proximity
    - Agents can discover medicinal plants/treatments
    - Healers emerge as specialists
    - Public health measures (quarantine) develop
    """

    def __init__(self):
        self.active_diseases: Dict[str, Disease] = {}
        self.medicines: Dict[str, Medicine] = {}
        self.medical_knowledge: Dict[str, MedicalKnowledge] = {}

        # Disease outbreaks
        self.outbreak_history: List[Dict] = []

        # Statistics
        self.total_infections: int = 0
        self.total_deaths_from_disease: int = 0
        self.total_cured: int = 0
        self.total_medicines_discovered: int = 0

        # Acquired immunity: (agent_id, disease type) -> tick it wears off.
        # Without it, recovered agents caught the same flu straight back from
        # their neighbours and epidemics never ended (63 flu infections among
        # 12 agents in 8 days).
        self.immune_until: Dict[tuple, int] = {}

    # How long recovering from a contagious disease protects against it (ticks;
    # a day is 144)
    IMMUNITY_TICKS = 1440

    # ===== DISEASE SYSTEM =====

    def infect_agent(
        self,
        agent_id: str,
        disease_type: DiseaseType,
        severity: Severity,
        current_tick: int,
        source: str = "natural"
    ) -> Optional[Disease]:
        """Infect an agent with a disease. Returns None if the agent is immune."""

        if current_tick < self.immune_until.get((agent_id, disease_type), -1):
            return None

        # Check if already infected with this disease
        for disease in self.active_diseases.values():
            if disease.infected_agent_id == agent_id and disease.disease_type == disease_type:
                return disease  # Already infected

        disease_id = str(new_uuid())

        # Disease properties based on type
        properties = self._get_disease_properties(disease_type, severity)

        disease = Disease(
            id=disease_id,
            disease_type=disease_type,
            infected_agent_id=agent_id,
            severity=severity,
            infection_tick=current_tick,
            duration=properties['duration'],
            health_damage_per_tick=properties['damage'],
            energy_drain_per_tick=properties['energy_drain'],
            contagious=properties['contagious'],
            transmission_radius=properties['radius'],
            transmission_chance=properties['transmission'],
            symptoms=properties['symptoms']
        )

        self.active_diseases[disease_id] = disease
        self.total_infections += 1

        return disease

    def _get_disease_properties(self, disease_type: DiseaseType, severity: Severity) -> Dict:
        """Get properties for different disease types"""

        # Severity multipliers
        severity_mods = {
            Severity.MILD: {'damage': 0.3, 'duration': 50},
            Severity.MODERATE: {'damage': 0.7, 'duration': 100},
            Severity.SEVERE: {'damage': 1.5, 'duration': 150},
            Severity.CRITICAL: {'damage': 3.0, 'duration': 80}
        }

        mod = severity_mods[severity]

        # Disease-specific properties
        disease_data = {
            DiseaseType.PLAGUE: {
                'damage': 2.0 * mod['damage'],
                'energy_drain': 2.0,
                'duration': mod['duration'],
                'contagious': True,
                'radius': 15.0,
                'transmission': 0.08,  # Very contagious
                'symptoms': ['fever', 'weakness', 'coughing', 'boils']
            },
            DiseaseType.FLU: {
                'damage': 0.5 * mod['damage'],
                'energy_drain': 1.5,
                'duration': mod['duration'],
                'contagious': True,
                'radius': 10.0,
                'transmission': 0.05,
                'symptoms': ['fever', 'fatigue', 'sneezing', 'aches']
            },
            DiseaseType.INFECTION: {
                'damage': 1.0 * mod['damage'],
                'energy_drain': 0.5,
                'duration': mod['duration'],
                'contagious': False,
                'radius': 0.0,
                'transmission': 0.0,
                'symptoms': ['inflammation', 'pain', 'fever', 'pus']
            },
            DiseaseType.FOOD_POISONING: {
                'damage': 1.5 * mod['damage'],
                'energy_drain': 2.0,
                'duration': 30,  # Short but intense
                'contagious': False,
                'radius': 0.0,
                'transmission': 0.0,
                'symptoms': ['nausea', 'vomiting', 'weakness', 'cramps']
            },
            DiseaseType.MALNUTRITION: {
                'damage': 0.2,
                'energy_drain': 1.0,
                'duration': 200,  # Long-term
                'contagious': False,
                'radius': 0.0,
                'transmission': 0.0,
                'symptoms': ['weakness', 'fatigue', 'weight_loss']
            },
            DiseaseType.DEHYDRATION: {
                'damage': 0.3,
                'energy_drain': 1.5,
                'duration': 100,
                'contagious': False,
                'radius': 0.0,
                'transmission': 0.0,
                'symptoms': ['dizziness', 'dry_mouth', 'weakness']
            },
        }

        return disease_data.get(disease_type, {
            'damage': mod['damage'],
            'energy_drain': 1.0,
            'duration': mod['duration'],
            'contagious': False,
            'radius': 0.0,
            'transmission': 0.0,
            'symptoms': ['sickness']
        })

    def update_diseases(self, current_tick: int, agents: List) -> List[str]:
        """Update all active diseases, return list of agents who died"""

        deaths = []
        recovered = []

        for disease_id, disease in list(self.active_diseases.items()):
            disease.progress = (current_tick - disease.infection_tick) / disease.duration

            # Disease runs its course
            if disease.progress >= 1.0:
                # Disease ends - either recovery or death
                if disease.severity == Severity.CRITICAL and not disease.treated:
                    # Critical untreated disease = death
                    deaths.append(disease.infected_agent_id)
                    self.total_deaths_from_disease += 1
                else:
                    # Recovery
                    recovered.append(disease_id)
                    if disease.treated:
                        self.total_cured += 1
                    if disease.contagious:
                        self.immune_until[(disease.infected_agent_id, disease.disease_type)] = \
                            current_tick + self.IMMUNITY_TICKS

                del self.active_diseases[disease_id]

        return deaths

    def spread_diseases(self, agents: List, current_tick: int):
        """Spread contagious diseases between nearby agents"""

        for disease in list(self.active_diseases.values()):
            if not disease.contagious:
                continue

            # Find infected agent
            infected_agent = next((a for a in agents if a.id == disease.infected_agent_id), None)
            if not infected_agent or not infected_agent.alive:
                continue

            # Check nearby agents
            for other_agent in agents:
                if not other_agent.alive or other_agent.id == infected_agent.id:
                    continue

                # Calculate distance
                dist = ((infected_agent.location.x - other_agent.location.x)**2 +
                       (infected_agent.location.y - other_agent.location.y)**2)**0.5

                if dist < disease.transmission_radius:
                    # Transmission chance
                    if random.random() < disease.transmission_chance:
                        # Check if already infected with this disease
                        already_infected = any(
                            d.infected_agent_id == other_agent.id and d.disease_type == disease.disease_type
                            for d in self.active_diseases.values()
                        )

                        if not already_infected:
                            # Transmit disease!
                            self.infect_agent(
                                other_agent.id,
                                disease.disease_type,
                                disease.severity,
                                current_tick,
                                source="transmission"
                            )

    # ===== MEDICINE SYSTEM =====

    def discover_medicine(
        self,
        discoverer_id: str,
        discoverer_name: str,
        ingredients: Dict[str, int],
        preparation_method: str,
        current_tick: int
    ) -> Optional[Medicine]:
        """Agent discovers a new medicine through experimentation"""

        medicine_id = str(new_uuid())

        # Determine what diseases this might cure based on ingredients
        # (Simplified - in reality would need actual material properties)
        cures = self._determine_medicine_effectiveness(ingredients)

        # Generate medicine name
        ingredient_names = list(ingredients.keys())
        name = f"{ingredient_names[0].title()} {preparation_method.title()}"

        # Determine medicine type
        med_type = MedicineType.HERB if 'plant' in ingredient_names[0] else MedicineType.TONIC

        medicine = Medicine(
            id=medicine_id,
            name=name,
            medicine_type=med_type,
            discoverer_id=discoverer_id,
            discovered_at=current_tick,
            ingredients=ingredients,
            preparation_method=preparation_method,
            cures_diseases=cures,
            effectiveness=random.uniform(0.4, 0.8),
            known_by={discoverer_id}
        )

        self.medicines[medicine_id] = medicine
        self.total_medicines_discovered += 1

        # Add to discoverer's medical knowledge
        if discoverer_id not in self.medical_knowledge:
            self.medical_knowledge[discoverer_id] = MedicalKnowledge(agent_id=discoverer_id)

        self.medical_knowledge[discoverer_id].known_medicines.add(medicine_id)

        return medicine

    def _determine_medicine_effectiveness(self, ingredients: Dict[str, int]) -> List[DiseaseType]:
        """Determine what diseases ingredients might cure"""
        cures = []

        ingredient_list = [name.lower() for name in ingredients.keys()]

        # Simple heuristics (could be enhanced with real material properties)
        if any('herb' in ing or 'plant' in ing for ing in ingredient_list):
            cures.append(DiseaseType.FLU)
            cures.append(DiseaseType.INFECTION)

        if any('water' in ing for ing in ingredient_list):
            cures.append(DiseaseType.DEHYDRATION)

        if any('food' in ing or 'fruit' in ing for ing in ingredient_list):
            cures.append(DiseaseType.MALNUTRITION)

        # Random chance to cure other diseases
        if random.random() < 0.3:
            cures.append(random.choice(list(DiseaseType)))

        return cures

    def apply_treatment(
        self,
        patient_id: str,
        healer_id: str,
        medicine_id: Optional[str] = None
    ) -> Dict:
        """Apply medical treatment to a patient"""

        # Find patient's diseases
        patient_diseases = [d for d in self.active_diseases.values()
                          if d.infected_agent_id == patient_id]

        if not patient_diseases:
            return {'success': False, 'reason': 'Patient not sick'}

        # Get healer's skill
        healer_skill = 0.5
        if healer_id in self.medical_knowledge:
            healer_skill = self.medical_knowledge[healer_id].healing_skill

        # Apply treatment to most severe disease
        disease = max(patient_diseases, key=lambda d: d.health_damage_per_tick)

        # Treatment effectiveness
        base_effectiveness = healer_skill * 0.5

        if medicine_id and medicine_id in self.medicines:
            medicine = self.medicines[medicine_id]

            # Check if medicine cures this disease
            if disease.disease_type in medicine.cures_diseases:
                base_effectiveness += medicine.effectiveness * 0.5
                medicine.times_used += 1

        # Apply treatment
        disease.treated = True
        disease.treatment_effectiveness = min(1.0, base_effectiveness)

        # Reduce disease severity based on treatment
        disease.health_damage_per_tick *= (1.0 - disease.treatment_effectiveness)
        disease.duration = int(disease.duration * (1.0 - disease.treatment_effectiveness * 0.5))

        # Update healer's knowledge
        if healer_id not in self.medical_knowledge:
            self.medical_knowledge[healer_id] = MedicalKnowledge(agent_id=healer_id)

        healer_knowledge = self.medical_knowledge[healer_id]
        healer_knowledge.patients_treated += 1
        healer_knowledge.diagnosed_diseases.add(disease.disease_type)
        healer_knowledge.healing_skill = min(1.0, healer_knowledge.healing_skill + 0.02)

        # Check if healer should be recognized as specialist
        if healer_knowledge.patients_treated >= 5 and healer_knowledge.healing_skill > 0.6:
            healer_knowledge.is_healer = True

        return {
            'success': True,
            'effectiveness': disease.treatment_effectiveness,
            'disease_type': disease.disease_type.value
        }

    # ===== DIAGNOSIS =====

    def diagnose(self, patient_id: str, healer_id: str) -> Optional[Dict]:
        """Healer diagnoses patient's disease"""

        patient_diseases = [d for d in self.active_diseases.values()
                          if d.infected_agent_id == patient_id]

        if not patient_diseases:
            return None

        # Get most severe disease
        disease = max(patient_diseases, key=lambda d: d.health_damage_per_tick)

        # Get healer's skill
        healer_skill = 0.3  # Base skill
        if healer_id in self.medical_knowledge:
            healer_skill = self.medical_knowledge[healer_id].healing_skill

        # Diagnosis accuracy based on skill
        accurate = random.random() < (0.5 + healer_skill * 0.5)

        if accurate:
            return {
                'disease_type': disease.disease_type.value,
                'severity': disease.severity.value,
                'symptoms': disease.symptoms,
                'contagious': disease.contagious,
                'progress': f"{disease.progress*100:.0f}%"
            }
        else:
            # Misdiagnosis
            return {
                'disease_type': 'unknown',
                'severity': disease.severity.value,
                'symptoms': disease.symptoms[:2],  # Partial symptoms
                'contagious': 'uncertain',
                'progress': 'uncertain'
            }

    # ===== QUERIES =====

    def get_agent_diseases(self, agent_id: str) -> List[Disease]:
        """Get all diseases affecting an agent"""
        return [d for d in self.active_diseases.values() if d.infected_agent_id == agent_id]

    def is_agent_sick(self, agent_id: str) -> bool:
        """Check if agent has any active diseases"""
        return any(d.infected_agent_id == agent_id for d in self.active_diseases.values())

    def get_healers(self) -> List[str]:
        """Get list of recognized healer agent IDs"""
        return [agent_id for agent_id, knowledge in self.medical_knowledge.items()
                if knowledge.is_healer]

    def get_statistics(self) -> Dict:
        """Get health system statistics"""

        active_infections = len(self.active_diseases)
        total_healers = len(self.get_healers())

        return {
            'active_infections': active_infections,
            'total_infections': self.total_infections,
            'deaths_from_disease': self.total_deaths_from_disease,
            'total_cured': self.total_cured,
            'medicines_discovered': self.total_medicines_discovered,
            'recognized_healers': total_healers,
            'survival_rate': (self.total_cured / max(1, self.total_infections)) * 100
        }
