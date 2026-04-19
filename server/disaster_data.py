"""
Advanced Synthetic Disaster Data Generator - Enhanced Version
Generates realistic disaster scenarios with balanced difficulty and proper resource allocation
"""

import random
import math
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any
from models import (
    Position, Zone, TerrainType, WeatherCondition, DisasterType,
    Victim, MedicalCondition, Resource, ResourceType, ResourceCapability,
    VictimStatus
)

class DisasterDataGenerator:
    """Generates realistic, varied disaster scenarios with balanced difficulty"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
    
    def generate_terrain_grid(self, size_km: float, zones: int) -> List[Zone]:
        """Generate realistic terrain with varied geography"""
        zones_list = []
        
        terrain_distribution = [
            (TerrainType.PLAINS, 0.35),
            (TerrainType.URBAN, 0.25),
            (TerrainType.FOREST, 0.20),
            (TerrainType.MOUNTAIN, 0.10),
            (TerrainType.WATER, 0.05),
            (TerrainType.RUBBLE, 0.05)
        ]
        
        for i in range(zones):
            terrain = random.choices(
                [t for t, _ in terrain_distribution],
                [w for _, w in terrain_distribution]
            )[0]
            
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, size_km / 2)
            center = Position(
                x=size_km / 2 + radius * math.cos(angle),
                y=size_km / 2 + radius * math.sin(angle)
            )
            
            zones_list.append(Zone(
                id=f"zone_{i}",
                name=f"Zone {chr(65 + i)}",
                center=center,
                radius=random.uniform(1, 4),
                terrain=terrain,
                population_density=random.uniform(100, 5000),
                infrastructure_damage=random.uniform(0, 0.3)
            ))
        
        return zones_list
    
    def generate_balanced_victims(self, count: int, zones: List[Zone], disaster_type: DisasterType, difficulty: str) -> List[Victim]:
        """Generate victims with balanced priority distribution"""
        victims = []
        
        # Priority distribution based on difficulty
        if difficulty == "easy":
            # Mostly low priority for easy
            priority_weights = [(1, 0.1), (2, 0.1), (3, 0.2), (4, 0.2), (5, 0.2), (6, 0.1), (7, 0.05), (8, 0.03), (9, 0.01), (10, 0.01)]
        elif difficulty == "medium":
            # Balanced distribution for medium
            priority_weights = [(1, 0.05), (2, 0.05), (3, 0.1), (4, 0.1), (5, 0.15), (6, 0.15), (7, 0.15), (8, 0.1), (9, 0.08), (10, 0.07)]
        else:  # hard
            # More high-priority victims for hard
            priority_weights = [(1, 0.02), (2, 0.03), (3, 0.05), (4, 0.08), (5, 0.1), (6, 0.12), (7, 0.15), (8, 0.15), (9, 0.15), (10, 0.15)]
        
        # Injury patterns by disaster type
        injury_profiles = {
            DisasterType.EARTHQUAKE: [
                ("fracture", 0.4), ("bleeding", 0.3), ("crush", 0.2), ("shock", 0.1)
            ],
            DisasterType.FLOOD: [
                ("drowning", 0.3), ("hypothermia", 0.3), ("bleeding", 0.2), ("shock", 0.2)
            ],
            DisasterType.HURRICANE: [
                ("bleeding", 0.35), ("fracture", 0.25), ("shock", 0.2), ("respiratory", 0.2)
            ],
            DisasterType.WILDFIRE: [
                ("burn", 0.5), ("respiratory", 0.3), ("shock", 0.2)
            ],
            DisasterType.TSUNAMI: [
                ("drowning", 0.4), ("fracture", 0.3), ("bleeding", 0.2), ("shock", 0.1)
            ]
        }
        
        profile = injury_profiles.get(disaster_type, injury_profiles[DisasterType.EARTHQUAKE])
        
        for i in range(count):
            zone = random.choice(zones)
            
            # Generate position within zone
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, zone.radius)
            position = Position(
                x=zone.center.x + distance * math.cos(angle),
                y=zone.center.y + distance * math.sin(angle)
            )
            
            # Select priority based on weights
            priorities = [p for p, _ in priority_weights]
            weights = [w for _, w in priority_weights]
            base_priority = random.choices(priorities, weights=weights)[0]
            
            # Determine triage category based on priority
            if base_priority >= 8:
                triage_category = "Red"  # Immediate
                survival_prob = random.uniform(0.4, 0.7)
            elif base_priority >= 5:
                triage_category = "Yellow"  # Delayed
                survival_prob = random.uniform(0.7, 0.85)
            else:
                triage_category = "Green"  # Minor
                survival_prob = random.uniform(0.85, 0.98)
            
            # Generate medical conditions
            conditions = []
            num_conditions = random.randint(1, 3)
            for _ in range(num_conditions):
                injury_type, _ = random.choice(profile)
                conditions.append(MedicalCondition(
                    type=injury_type,
                    severity=random.randint(1, 5),
                    requires=[]
                ))
            
            # All victims discovered at start for easier testing
            discovered_at = datetime.now() - timedelta(minutes=random.randint(0, 30))
            
            victims.append(Victim(
                id=f"victim_{i:04d}",
                position=position,
                zone_id=zone.id,
                discovered=True,
                discovered_at=discovered_at,
                status=VictimStatus.DISCOVERED,
                assigned_resource_id=None,
                conditions=conditions,
                triage_category=triage_category,
                survival_probability=survival_prob,
                base_priority=base_priority,
                time_multiplier=1.0,
                assigned_at=None,
                rescued_at=None
            ))
        
        return victims
    
    def generate_balanced_resources(self, count: int, zones: List[Zone], difficulty: str) -> List[Resource]:
        """Generate resources with appropriate count for difficulty"""
        resources = []
        
        # Resource type distribution
        if difficulty == "easy":
            resource_distribution = [
                (ResourceType.AMBULANCE, 0.5),
                (ResourceType.FIRE_TRUCK, 0.3),
                (ResourceType.RESCUE_TEAM, 0.2)
            ]
        elif difficulty == "medium":
            resource_distribution = [
                (ResourceType.AMBULANCE, 0.4),
                (ResourceType.FIRE_TRUCK, 0.25),
                (ResourceType.RESCUE_TEAM, 0.2),
                (ResourceType.HELICOPTER, 0.1),
                (ResourceType.SEARCH_DOG, 0.05)
            ]
        else:  # hard
            resource_distribution = [
                (ResourceType.AMBULANCE, 0.3),
                (ResourceType.FIRE_TRUCK, 0.2),
                (ResourceType.RESCUE_TEAM, 0.15),
                (ResourceType.HELICOPTER, 0.15),
                (ResourceType.SEARCH_DOG, 0.1),
                (ResourceType.SUPPLY_TRUCK, 0.05),
                (ResourceType.FIELD_HOSPITAL, 0.05)
            ]
        
        # Resource capabilities mapping
        resource_caps = {
            ResourceType.FIRE_TRUCK: ResourceCapability(
                can_extinguish_fire=True,
                can_technical_rescue=True,
                max_patients=2,
                crew_size=4
            ),
            ResourceType.AMBULANCE: ResourceCapability(
                can_medical_evac=True,
                max_patients=2,
                crew_size=2
            ),
            ResourceType.RESCUE_TEAM: ResourceCapability(
                can_technical_rescue=True,
                can_search=True,
                max_patients=4,
                crew_size=6
            ),
            ResourceType.HELICOPTER: ResourceCapability(
                can_medical_evac=True,
                can_air_evac=True,
                can_search=True,
                max_patients=4,
                crew_size=4
            ),
            ResourceType.SUPPLY_TRUCK: ResourceCapability(
                can_supply_logistics=True,
                max_supply_capacity=10000,
                crew_size=2
            ),
            ResourceType.FIELD_HOSPITAL: ResourceCapability(
                can_medical_evac=True,
                max_patients=50,
                crew_size=20
            ),
            ResourceType.SEARCH_DOG: ResourceCapability(
                can_search=True,
                crew_size=1
            )
        }
        
        # Speed mapping (km/h)
        resource_speeds = {
            ResourceType.FIRE_TRUCK: 60,
            ResourceType.AMBULANCE: 80,
            ResourceType.RESCUE_TEAM: 30,
            ResourceType.HELICOPTER: 200,
            ResourceType.SUPPLY_TRUCK: 50,
            ResourceType.FIELD_HOSPITAL: 0,
            ResourceType.SEARCH_DOG: 15
        }
        
        # Endurance (hours of operation)
        resource_endurance = {
            ResourceType.FIRE_TRUCK: 24,
            ResourceType.AMBULANCE: 12,
            ResourceType.RESCUE_TEAM: 48,
            ResourceType.HELICOPTER: 8,
            ResourceType.SUPPLY_TRUCK: 36,
            ResourceType.FIELD_HOSPITAL: 72,
            ResourceType.SEARCH_DOG: 12
        }
        
        resource_types = [rt for rt, _ in resource_distribution]
        resource_weights = [w for _, w in resource_distribution]
        
        for i in range(count):
            res_type = random.choices(resource_types, weights=resource_weights)[0]
            caps = resource_caps[res_type]
            speed = resource_speeds[res_type]
            endurance = resource_endurance[res_type]
            
            # Place resources strategically (not all in same zone)
            if i < len(zones):
                zone = zones[i % len(zones)]
            else:
                zone = random.choice(zones)
            
            # Place at edge of zone for realistic deployment
            angle = random.uniform(0, 2 * math.pi)
            position = Position(
                x=zone.center.x + zone.radius * 0.8 * math.cos(angle),
                y=zone.center.y + zone.radius * 0.8 * math.sin(angle)
            )
            
            resources.append(Resource(
                id=f"resource_{res_type.value}_{i}",
                type=res_type,
                position=position,
                zone_id=zone.id,
                capabilities=caps,
                speed=speed,
                fuel=endurance,
                max_fuel=endurance,
                crew_available=True,
                crew_fatigue=0.0,
                available=True,
                current_task=None,
                assigned_victim_id=None,
                estimated_arrival_time=None,
                missions_completed=0,
                victims_rescued=0
            ))
        
        return resources
    
    def generate_dynamic_events(self, difficulty: str) -> List[Dict]:
        """Generate events that change the scenario mid-simulation"""
        events = []
        
        if difficulty == "easy":
            return events
        
        if difficulty == "medium":
            events.append({
                "time_hours": 12,
                "type": "aftershock",
                "new_victims": random.randint(3, 5),
                "affected_zone": random.choice(["zone_0", "zone_1", "zone_2"]),
                "description": "Aftershock causes additional casualties"
            })
            events.append({
                "time_hours": 24,
                "type": "weather_change",
                "new_condition": WeatherCondition.RAIN.value,
                "description": "Weather deteriorating"
            })
            events.append({
                "time_hours": 36,
                "type": "resource_arrival",
                "new_resources": 2,
                "description": "Additional resources arrive"
            })
        
        if difficulty == "hard":
            events.extend([
                {
                    "time_hours": 6,
                    "type": "aftershock",
                    "new_victims": random.randint(5, 8),
                    "affected_zone": random.choice(["zone_0", "zone_1", "zone_2"]),
                    "description": "Strong aftershock causes building collapses"
                },
                {
                    "time_hours": 12,
                    "type": "weather_deterioration",
                    "new_condition": WeatherCondition.STORM.value,
                    "description": "Hurricane intensifies"
                },
                {
                    "time_hours": 18,
                    "type": "road_blockage",
                    "affected_zones": ["zone_1", "zone_2"],
                    "duration_hours": 6,
                    "description": "Major roads blocked by debris"
                },
                {
                    "time_hours": 24,
                    "type": "secondary_disaster",
                    "disaster_type": "fire",
                    "affected_zone": "zone_3",
                    "new_victims": random.randint(4, 7),
                    "description": "Fire breaks out in industrial zone"
                },
                {
                    "time_hours": 30,
                    "type": "resource_arrival",
                    "new_resources": 3,
                    "description": "National Guard resources arrive"
                },
                {
                    "time_hours": 42,
                    "type": "evacuation_order",
                    "affected_zones": ["zone_0", "zone_1"],
                    "description": "Mandatory evacuation ordered"
                },
                {
                    "time_hours": 54,
                    "type": "power_outage",
                    "affected_zones": ["zone_2", "zone_3", "zone_4"],
                    "duration_hours": 12,
                    "description": "Widespread power outage"
                }
            ])
        
        return events
    
    def generate_easy_scenario(self) -> Dict:
        """Generate easy scenario: Localized flood"""
        zones = self.generate_terrain_grid(20, 3)
        victims = self.generate_balanced_victims(15, zones, DisasterType.FLOOD, "easy")
        resources = self.generate_balanced_resources(4, zones, "easy")
        
        return {
            "id": "easy_001",
            "name": "River Flood - Small Town",
            "difficulty": "easy",
            "disaster_type": DisasterType.FLOOD,
            "duration_hours": 24,
            "zones": zones,
            "victims": victims,
            "resources": resources,
            "dynamic_events": self.generate_dynamic_events("easy"),
            "weather": WeatherCondition.RAIN,
            "total_victims": len(victims)
        }
    
    def generate_medium_scenario(self) -> Dict:
        """Generate medium scenario: Earthquake with aftershocks"""
        zones = self.generate_terrain_grid(40, 5)
        victims = self.generate_balanced_victims(35, zones, DisasterType.EARTHQUAKE, "medium")
        resources = self.generate_balanced_resources(10, zones, "medium")
        
        return {
            "id": "medium_001",
            "name": "Earthquake - Urban Center",
            "difficulty": "medium",
            "disaster_type": DisasterType.EARTHQUAKE,
            "duration_hours": 48,
            "zones": zones,
            "victims": victims,
            "resources": resources,
            "dynamic_events": self.generate_dynamic_events("medium"),
            "weather": WeatherCondition.CLEAR,
            "total_victims": len(victims)
        }
    
    def generate_hard_scenario(self) -> Dict:
        """Generate hard scenario: Hurricane with cascading failures"""
        zones = self.generate_terrain_grid(60, 8)
        victims = self.generate_balanced_victims(75, zones, DisasterType.HURRICANE, "hard")
        resources = self.generate_balanced_resources(18, zones, "hard")
        
        return {
            "id": "hard_001",
            "name": "Hurricane - Coastal Metropolis",
            "difficulty": "hard",
            "disaster_type": DisasterType.HURRICANE,
            "duration_hours": 72,
            "zones": zones,
            "victims": victims,
            "resources": resources,
            "dynamic_events": self.generate_dynamic_events("hard"),
            "weather": WeatherCondition.STORM,
            "total_victims": len(victims)
        }

# Singleton instance for import
generator = DisasterDataGenerator()