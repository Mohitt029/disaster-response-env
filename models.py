"""
Advanced Type Models for Disaster Response Environment
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import math

# ============================================================================
# ENUMS - Strict Type Safety
# ============================================================================

class DisasterType(Enum):
    """Types of disasters with unique characteristics"""
    FLOOD = "flood"
    EARTHQUAKE = "earthquake"
    HURRICANE = "hurricane"
    WILDFIRE = "wildfire"
    TSUNAMI = "tsunami"

class ResourceType(Enum):
    """Resource types with distinct capabilities"""
    FIRE_TRUCK = "fire_truck"           # Fire suppression, rescue
    AMBULANCE = "ambulance"              # Medical evacuation
    RESCUE_TEAM = "rescue_team"          # Technical rescue
    HELICOPTER = "helicopter"            # Air evacuation
    SUPPLY_TRUCK = "supply_truck"        # Logistics support
    FIELD_HOSPITAL = "field_hospital"    # Medical treatment
    SEARCH_DOG = "search_dog"            # Victim detection

class VictimStatus(Enum):
    """Victim status progression"""
    UNDISCOVERED = "undiscovered"
    DISCOVERED = "discovered"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    RESCUED = "rescued"
    DECEASED = "deceased"

class TerrainType(Enum):
    """Terrain affects movement speed"""
    PLAINS = "plains"        # Speed multiplier: 1.0
    FOREST = "forest"        # Speed multiplier: 0.7
    MOUNTAIN = "mountain"    # Speed multiplier: 0.4
    URBAN = "urban"          # Speed multiplier: 0.8
    WATER = "water"          # Speed multiplier: 0.2
    RUBBLE = "rubble"        # Speed multiplier: 0.3

class WeatherCondition(Enum):
    """Weather affects all operations"""
    CLEAR = "clear"          # Multiplier: 1.0
    RAIN = "rain"            # Multiplier: 0.8
    STORM = "storm"          # Multiplier: 0.5
    FOG = "fog"              # Multiplier: 0.6
    EXTREME = "extreme"      # Multiplier: 0.3

# ============================================================================
# SPATIAL DATA STRUCTURES
# ============================================================================

@dataclass
class Position:
    """2D position with distance calculation"""
    x: float
    y: float
    
    def distance_to(self, other: 'Position') -> float:
        """Euclidean distance"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def manhattan_to(self, other: 'Position') -> float:
        """Manhattan distance for grid-based movement"""
        return abs(self.x - other.x) + abs(self.y - other.y)

@dataclass
class Zone:
    """Geographic zone with properties"""
    id: str
    name: str
    center: Position
    radius: float
    terrain: TerrainType
    population_density: float  # people per sq km
    infrastructure_damage: float  # 0.0 to 1.0
    accessible: bool = True

# ============================================================================
# VICTIM MODEL (Detailed)
# ============================================================================

@dataclass
class MedicalCondition:
    """Detailed medical condition"""
    type: str  # bleeding, fracture, burn, shock, respiratory, cardiac
    severity: int  # 1 (minor) to 5 (critical)
    requires: List[str]  # equipment or specialists needed
    
@dataclass
class Victim:
    """Comprehensive victim model"""
    id: str
    position: Position
    zone_id: str
    discovered: bool
    discovered_at: Optional[datetime]
    status: VictimStatus
    assigned_resource_id: Optional[str]
    
    # Medical details
    conditions: List[MedicalCondition]
    triage_category: str  # Red (immediate), Yellow (delayed), Green (minor), Black (deceased)
    survival_probability: float  # 0.0 to 1.0 (degrades over time)
    
    # Priority scoring
    base_priority: int  # 1-10 based on triage
    time_multiplier: float  # increases with time waiting
    
    # Timestamps
    discovered_at: Optional[datetime]
    assigned_at: Optional[datetime]
    rescued_at: Optional[datetime]
    
    def current_priority(self, current_time: datetime) -> int:
        """Dynamic priority that increases with waiting time"""
        if self.rescued_at or self.status == VictimStatus.DECEASED:
            return 0
        
        wait_minutes = 0
        if self.discovered_at:
            wait_minutes = (current_time - self.discovered_at).total_seconds() / 60
        
        # Priority increases by 1 every 30 minutes waiting
        waiting_penalty = min(5, wait_minutes // 30)
        return min(10, self.base_priority + waiting_penalty)

# ============================================================================
# RESOURCE MODEL (Detailed)
# ============================================================================

@dataclass
class ResourceCapability:
    """What a resource can do"""
    can_extinguish_fire: bool = False
    can_medical_evac: bool = False
    can_technical_rescue: bool = False
    can_air_evac: bool = False
    can_supply_logistics: bool = False
    can_search: bool = False
    max_patients: int = 0
    max_supply_capacity: int = 0
    crew_size: int = 0

@dataclass
class Resource:
    """Comprehensive resource model"""
    id: str
    type: ResourceType
    position: Position
    zone_id: str
    
    # Capabilities
    capabilities: ResourceCapability
    
    # Operational parameters
    speed: float  # km/h
    fuel: float  # remaining hours of operation
    max_fuel: float
    crew_available: bool
    crew_fatigue: float  # 0.0 to 1.0
    
    # Current status
    available: bool
    current_task: Optional[str]
    assigned_victim_id: Optional[str]
    estimated_arrival_time: Optional[datetime]
    
    # History
    missions_completed: int = 0
    victims_rescued: int = 0
    
    def time_to_reach(self, target: Position, weather: WeatherCondition, terrain: TerrainType) -> float:
        """Calculate estimated time to reach target considering conditions"""
        distance = self.position.distance_to(target)
        terrain_multiplier = {
            TerrainType.PLAINS: 1.0,
            TerrainType.FOREST: 0.7,
            TerrainType.MOUNTAIN: 0.4,
            TerrainType.URBAN: 0.8,
            TerrainType.WATER: 0.2,
            TerrainType.RUBBLE: 0.3
        }.get(terrain, 0.5)
        
        weather_multiplier = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 0.8,
            WeatherCondition.STORM: 0.5,
            WeatherCondition.FOG: 0.6,
            WeatherCondition.EXTREME: 0.3
        }.get(weather, 0.5)
        
        effective_speed = self.speed * terrain_multiplier * weather_multiplier
        return distance / effective_speed if effective_speed > 0 else float('inf')

# ============================================================================
# ACTION MODELS (What Agent Sends)
# ============================================================================

@dataclass
class ResourceAllocation:
    """Agent decides which resource goes to which victim"""
    resource_id: str
    victim_id: str
    priority: int  # 1-10 urgency of this allocation
    reasoning: Optional[str] = None

@dataclass
class StrategicDecision:
    """Higher-level strategic decisions"""
    evacuation_order: bool = False
    resource_retasking: Optional[str] = None
    request_reinforcements: bool = False
    priority_zone: Optional[str] = None

@dataclass
class DisasterAction:
    """Combined action from agent"""
    allocations: List[ResourceAllocation]
    strategic: Optional[StrategicDecision] = None
    confidence: float = 0.85

# ============================================================================
# OBSERVATION MODELS (What Agent Sees)
# ============================================================================

@dataclass
class DisasterObservation:
    """Comprehensive observation for agent"""
    # Scenario context
    scenario_name: str
    difficulty: str
    disaster_type: DisasterType
    time_elapsed_hours: float
    time_remaining_hours: float
    weather: WeatherCondition
    
    # Victim status
    total_victims: int
    discovered_victims: int
    rescued_victims: int
    deceased_victims: int
    pending_victims: List[Dict[str, Any]]  # Simplified for agent
    
    # Resource status
    available_resources: List[Dict[str, Any]]
    deployed_resources: List[Dict[str, Any]]
    resource_health: Dict[str, float]  # fuel, fatigue
    
    # Environmental
    zones_status: List[Dict[str, Any]]
    active_hazards: List[Dict[str, Any]]
    infrastructure_status: Dict[str, float]
    
    # Metrics
    current_reward: float
    cumulative_reward: float
    done: bool = False

# ============================================================================
# STATE MODELS (Internal Tracking)
# ============================================================================

@dataclass
class DisasterState:
    """Internal state for debugging and metrics"""
    episode_id: str
    step_count: int
    simulation_time_hours: float
    
    # Performance metrics
    lives_saved: int
    lives_lost: int
    avg_response_time_minutes: float
    resource_utilization: float
    
    # Efficiency metrics
    fuel_consumed: float
    total_distance_traveled: float
    
    # Fairness metrics
    priority_adherence: float
    zone_distribution: Dict[str, float]

# ============================================================================
# GRADER RESULT (Final Evaluation)
# ============================================================================

@dataclass
class DisasterGraderResult:
    """Comprehensive final evaluation"""
    # Overall score (0.0-1.0)
    score: float
    
    # Component scores
    lives_saved_score: float
    response_time_score: float
    resource_efficiency_score: float
    fairness_score: float
    planning_depth_score: float
    
    # Detailed breakdown
    breakdown: Dict[str, float]
    
    # Human-readable feedback
    feedback: str
    
    # Statistics
    total_lives_saved: int
    total_lives_lost: int
    avg_rescue_time_minutes: float
    resources_deployed: int
    total_missions: int