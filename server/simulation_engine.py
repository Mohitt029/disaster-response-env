"""
Advanced Simulation Engine - Physics-based disaster dynamics
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from models import (
    Position, Zone, TerrainType, WeatherCondition, DisasterType,
    Victim, VictimStatus, Resource, ResourceAllocation, MedicalCondition
)

class DisasterSimulationEngine:
    """Core simulation engine with realistic physics and dynamics"""
    
    def __init__(self, scenario_data: Dict):
        self.scenario = scenario_data
        self.current_time = datetime.now()
        self.time_scale = 1.0  # 1 real second = 1 simulation minute
        self.event_queue = []
        self.damage_propagation = {}
        
        # Initialize damage propagation
        for zone in scenario_data["zones"]:
            self.damage_propagation[zone.id] = zone.infrastructure_damage
    
    def update(self, delta_minutes: float) -> Dict:
        """Update simulation state"""
        self.current_time += timedelta(minutes=delta_minutes * self.time_scale)
        
        changes = {
            "new_victims": [],
            "victim_status_changes": [],
            "resource_updates": [],
            "zone_damage_updates": [],
            "events_triggered": []
        }
        
        # Update victim survival probabilities
        for victim in self.scenario["victims"]:
            if victim.status not in [VictimStatus.RESCUED, VictimStatus.DECEASED]:
                # Survival probability decays exponentially with time
                if victim.discovered_at:
                    wait_minutes = (self.current_time - victim.discovered_at).total_seconds() / 60
                    decay_rate = 0.001 * (1 - victim.survival_probability)
                    victim.survival_probability *= math.exp(-decay_rate * wait_minutes)
                    
                    if victim.survival_probability < 0.01:
                        victim.status = VictimStatus.DECEASED
                        victim.survival_probability = 0.0
                        changes["victim_status_changes"].append({
                            "victim_id": victim.id,
                            "old_status": "discovered",
                            "new_status": "deceased",
                            "reason": "survival_timeout"
                        })
        
        # Update resource positions and status
        for resource in self.scenario["resources"]:
            if resource.current_task and resource.assigned_victim_id:
                target_victim = next(
                    (v for v in self.scenario["victims"] if v.id == resource.assigned_victim_id),
                    None
                )
                if target_victim:
                    # Move towards victim
                    distance = resource.position.distance_to(target_victim.position)
                    move_distance = resource.speed * (delta_minutes / 60)  # km per minute
                    
                    if move_distance >= distance:
                        # Arrived at victim
                        resource.position = target_victim.position
                        self._process_rescue(resource, target_victim)
                        changes["resource_updates"].append({
                            "resource_id": resource.id,
                            "status": "arrived",
                            "victim_id": target_victim.id
                        })
                    else:
                        # Move towards victim
                        ratio = move_distance / distance
                        resource.position.x += (target_victim.position.x - resource.position.x) * ratio
                        resource.position.y += (target_victim.position.y - resource.position.y) * ratio
                        resource.fuel -= delta_minutes / 60  # fuel consumption per hour
                        
                        if resource.fuel <= 0:
                            resource.available = False
                            resource.current_task = None
                            changes["resource_updates"].append({
                                "resource_id": resource.id,
                                "status": "out_of_fuel",
                                "position": {"x": resource.position.x, "y": resource.position.y}
                            })
        
        # Check for dynamic events
        current_hours = (self.current_time - datetime.now()).total_seconds() / 3600
        for event in self.scenario.get("dynamic_events", []):
            if event["time_hours"] <= current_hours and not event.get("triggered", False):
                event["triggered"] = True
                changes["events_triggered"].append(self._process_event(event))
        
        # Update infrastructure damage (spread)
        self._update_damage_propagation(delta_minutes)
        
        return changes
    
    def _process_rescue(self, resource: Resource, victim: Victim):
        """Process successful rescue"""
        victim.status = VictimStatus.RESCUED
        victim.rescued_at = self.current_time
        victim.assigned_resource_id = resource.id
        
        resource.available = True
        resource.current_task = None
        resource.assigned_victim_id = None
        resource.missions_completed += 1
        resource.victims_rescued += 1
        resource.crew_fatigue += 0.05
    
    def _process_event(self, event: Dict) -> Dict:
        """Process dynamic events like aftershocks, weather changes"""
        result = {"type": event["type"], "time": self.current_time.isoformat()}
        
        if event["type"] == "aftershock":
            # Generate new victims
            new_count = event.get("new_victims", random.randint(3, 8))
            affected_zone = next(
                (z for z in self.scenario["zones"] if z.id == event["affected_zone"]),
                None
            )
            
            if affected_zone:
                # Create new victims
                for i in range(new_count):
                    from server.disaster_data import generator
                    new_victim = generator.generate_victims(1, [affected_zone], self.scenario["disaster_type"])[0]
                    self.scenario["victims"].append(new_victim)
                    result["new_victims"] = new_count
            
            # Increase infrastructure damage
            if affected_zone:
                self.damage_propagation[affected_zone.id] = min(
                    1.0,
                    self.damage_propagation.get(affected_zone.id, 0) + 0.1
                )
        
        elif event["type"] == "weather_change":
            self.scenario["weather"] = WeatherCondition(event["new_condition"])
            result["new_weather"] = event["new_condition"]
        
        elif event["type"] == "road_blockage":
            for zone_id in event.get("affected_zones", []):
                # Reduce accessibility of zone
                zone = next((z for z in self.scenario["zones"] if z.id == zone_id), None)
                if zone:
                    # Temporarily block access
                    result["blocked_zones"] = event["affected_zones"]
        
        elif event["type"] == "resource_depletion":
            # Temporarily remove resources of certain type
            for resource in self.scenario["resources"]:
                if resource.type.value == event["resource_type"]:
                    resource.available = False
            result["affected_resource_type"] = event["resource_type"]
            result["duration_hours"] = event.get("duration_hours", 4)
        
        return result
    
    def _update_damage_propagation(self, delta_minutes: float):
        """Update damage propagation between zones"""
        # Damage spreads to adjacent zones over time
        pass
    
    def execute_allocations(self, allocations: List[ResourceAllocation]) -> List[Dict]:
        """Execute resource allocations from agent"""
        results = []
        
        for alloc in allocations:
            resource = next(
                (r for r in self.scenario["resources"] if r.id == alloc.resource_id),
                None
            )
            victim = next(
                (v for v in self.scenario["victims"] if v.id == alloc.victim_id),
                None
            )
            
            if not resource or not victim:
                results.append({
                    "success": False,
                    "error": "Resource or victim not found",
                    "resource_id": alloc.resource_id,
                    "victim_id": alloc.victim_id
                })
                continue
            
            if not resource.available:
                results.append({
                    "success": False,
                    "error": "Resource not available",
                    "resource_id": resource.id
                })
                continue
            
            if victim.status != VictimStatus.DISCOVERED:
                results.append({
                    "success": False,
                    "error": f"Victim status is {victim.status}, cannot assign",
                    "victim_id": victim.id
                })
                continue
            
            # Assign resource to victim
            resource.available = False
            resource.current_task = f"rescue_{victim.id}"
            resource.assigned_victim_id = victim.id
            victim.status = VictimStatus.ASSIGNED
            victim.assigned_at = self.current_time
            victim.assigned_resource_id = resource.id
            
            results.append({
                "success": True,
                "resource_id": resource.id,
                "victim_id": victim.id,
                "estimated_arrival_minutes": resource.time_to_reach(
                    victim.position,
                    self.scenario["weather"],
                    self._get_zone_by_id(victim.zone_id).terrain
                ) * 60
            })
        
        return results
    
    def _get_zone_by_id(self, zone_id: str) -> Zone:
        return next((z for z in self.scenario["zones"] if z.id == zone_id), None)
    
    def get_observation(self) -> Dict:
        """Generate current observation for agent"""
        victims_summary = []
        for v in self.scenario["victims"]:
            if v.status in [VictimStatus.DISCOVERED, VictimStatus.ASSIGNED]:
                victims_summary.append({
                    "id": v.id,
                    "zone_id": v.zone_id,
                    "triage_category": v.triage_category,
                    "priority": v.current_priority(self.current_time),
                    "status": v.status.value,
                    "waiting_minutes": (self.current_time - v.discovered_at).total_seconds() / 60 if v.discovered_at else 0
                })
        
        resources_summary = []
        for r in self.scenario["resources"]:
            resources_summary.append({
                "id": r.id,
                "type": r.type.value,
                "available": r.available,
                "fuel_percent": r.fuel / r.max_fuel if r.max_fuel > 0 else 0,
                "fatigue": r.crew_fatigue,
                "position": {"x": r.position.x, "y": r.position.y}
            })
        
        return {
            "time_elapsed_hours": (self.current_time - datetime.now()).total_seconds() / 3600,
            "weather": self.scenario["weather"].value,
            "victims_remaining": len([v for v in self.scenario["victims"] if v.status not in [VictimStatus.RESCUED, VictimStatus.DECEASED]]),
            "victims_rescued": len([v for v in self.scenario["victims"] if v.status == VictimStatus.RESCUED]),
            "victims_deceased": len([v for v in self.scenario["victims"] if v.status == VictimStatus.DECEASED]),
            "pending_victims": victims_summary[:20],  # Limit for LLM context
            "available_resources": [r for r in resources_summary if r["available"]],
            "deployed_resources": [r for r in resources_summary if not r["available"]]
        }