"""
Resource Manager - Optimizes resource allocation decisions
"""

from typing import List, Dict, Any, Tuple
from models import ResourceAllocation, Victim, Resource, Position

class ResourceManager:
    """Helper class for resource allocation optimization"""
    
    @staticmethod
    def calculate_optimal_allocation(victims: List[Victim], resources: List[Resource]) -> List[ResourceAllocation]:
        """
        Calculate optimal allocation based on distance and priority
        This is a heuristic that can be used by the agent
        """
        allocations = []
        available_resources = [r for r in resources if r.available]
        pending_victims = [v for v in victims if v.status == "discovered"]
        
        # Sort victims by priority (highest first)
        pending_victims.sort(key=lambda v: v.base_priority, reverse=True)
        
        for victim in pending_victims[:len(available_resources)]:
            # Find closest available resource
            closest_resource = None
            min_distance = float('inf')
            
            for resource in available_resources:
                dist = resource.position.distance_to(victim.position)
                if dist < min_distance:
                    min_distance = dist
                    closest_resource = resource
            
            if closest_resource:
                allocations.append(ResourceAllocation(
                    resource_id=closest_resource.id,
                    victim_id=victim.id,
                    priority=victim.current_priority(datetime.now()),
                    reasoning=f"Optimal allocation: closest resource to high-priority victim"
                ))
                available_resources.remove(closest_resource)
        
        return allocations
    
    @staticmethod
    def calculate_resource_utilization(resources: List[Resource]) -> float:
        """Calculate overall resource utilization percentage"""
        if not resources:
            return 0.0
        deployed = sum(1 for r in resources if not r.available)
        return deployed / len(resources)
    
    @staticmethod
    def estimate_response_time(resource: Resource, victim: Victim, weather: str, terrain: str) -> float:
        """Estimate response time in minutes"""
        distance = resource.position.distance_to(victim.position)
        speed = resource.speed
        
        weather_multiplier = {
            "clear": 1.0,
            "rain": 0.8,
            "storm": 0.5,
            "fog": 0.6,
            "extreme": 0.3
        }.get(weather, 0.5)
        
        terrain_multiplier = {
            "plains": 1.0,
            "forest": 0.7,
            "mountain": 0.4,
            "urban": 0.8,
            "water": 0.2,
            "rubble": 0.3
        }.get(terrain, 0.5)
        
        effective_speed = speed * weather_multiplier * terrain_multiplier
        return (distance / effective_speed) * 60 if effective_speed > 0 else float('inf')