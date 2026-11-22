"""
Action Handlers Package

Contains modular action handler implementations organized by system.
All handlers follow the ActionHandler pattern for testable, maintainable code.
"""

from engine.handlers.movement import MovementActionHandler
from engine.handlers.survival import SurvivalActionHandler
from engine.handlers.social import SocialInteractionHandler
from engine.handlers.resource_gathering import ResourceGatheringHandler
from engine.handlers.knowledge import KnowledgeActionHandler
from engine.handlers.agriculture import AgricultureHandler
from engine.handlers.construction import ConstructionHandler
from engine.handlers.entertainment import EntertainmentHandler
from engine.handlers.governance import GovernanceHandler
from engine.handlers.combat import CombatActionHandler
from engine.handlers.health import HealthHandler
from engine.handlers.religion import ReligionHandler
from engine.handlers.territory import TerritoryHandler
from engine.handlers.chemistry import ChemistryHandler
from engine.handlers.energy import EnergyHandler
from engine.handlers.materials import MaterialsHandler
from engine.handlers.economy import AdvancedEconomyHandler
from engine.handlers.family import FamilyHandler

__all__ = [
    'MovementActionHandler',
    'SurvivalActionHandler',
    'SocialInteractionHandler',
    'ResourceGatheringHandler',
    'KnowledgeActionHandler',
    'AgricultureHandler',
    'ConstructionHandler',
    'EntertainmentHandler',
    'GovernanceHandler',
    'CombatActionHandler',
    'HealthHandler',
    'ReligionHandler',
    'TerritoryHandler',
    'ChemistryHandler',
    'EnergyHandler',
    'MaterialsHandler',
    'AdvancedEconomyHandler',
    'FamilyHandler',
]
