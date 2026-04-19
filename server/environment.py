"""
Core Disaster Response Environment - Working Rescue Simulation
"""

import uuid
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random

from models import (
    DisasterAction, DisasterObservation, DisasterState, DisasterGraderResult,
    ResourceAllocation, StrategicDecision, VictimStatus, ResourceType, Position
)
from server.disaster_data import generator
from server.simulation_engine import DisasterSimulationEngine

class DisasterResponseEnvironment:
    def __init__(self):
        self.current_scenario = None
        self.simulation = None
        self.current_difficulty = None
        self.episode_id = None
        self.step_count = 0
        self.total_reward = 0.0
        self.decisions = []
        self.done = False
        self.episode_start_time = None
        self.max_steps = 30
        self.rescued_victims_list = []
        self.active_rescues = {}  # victim_id -> completion_step
        
    def reset(self, difficulty: str = "easy") -> DisasterObservation:
        self.current_difficulty = difficulty
        
        if difficulty == "easy":
            scenario_data = generator.generate_easy_scenario()
            self.max_steps = 30
        elif difficulty == "medium":
            scenario_data = generator.generate_medium_scenario()
            self.max_steps = 40
        else:
            scenario_data = generator.generate_hard_scenario()
            self.max_steps = 60
        
        self.current_scenario = scenario_data
        self.simulation = DisasterSimulationEngine(scenario_data)
        self.episode_id = str(uuid.uuid4())
        self.step_count = 0
        self.total_reward = 0.0
        self.decisions = []
        self.done = False
        self.episode_start_time = time.time()
        self.rescued_victims_list = []
        self.active_rescues = {}
        
        # Set all victims to DISCOVERED initially
        for victim in self.current_scenario["victims"]:
            victim.status = VictimStatus.DISCOVERED
            victim.discovered_at = datetime.now()
        
        return self._get_observation()
    
    def step(self, action: DisasterAction) -> DisasterObservation:
        if self.done:
            raise RuntimeError("Episode already done. Call reset() first.")
        
        # FIRST: Process completed rescues
        rescues_completed_this_step = self._process_completed_rescues()
        
        # THEN: Execute new allocations (only if resources available)
        successful_allocations = 0
        for alloc in action.allocations:
            if self._execute_allocation(alloc):
                successful_allocations += 1
        
        # Calculate step reward based on completed rescues
        step_reward = len(rescues_completed_this_step) * 1.0
        self.total_reward += step_reward
        
        self.step_count += 1
        self.decisions.append({
            "step": self.step_count,
            "allocations": len(action.allocations),
            "successful": successful_allocations,
            "rescues_completed": len(rescues_completed_this_step),
            "reward": step_reward
        })
        
        # Check if episode should end
        obs = self._get_observation()
        all_rescued = obs.rescued_victims >= obs.total_victims
        max_steps_reached = self.step_count >= self.max_steps
        
        if all_rescued or max_steps_reached:
            self.done = True
        
        return obs
    
    def _process_completed_rescues(self) -> List[str]:
        """Process rescues that completed in this step"""
        completed = []
        
        for victim_id, completion_step in list(self.active_rescues.items()):
            if self.step_count >= completion_step:
                # Rescue completed!
                victim = next((v for v in self.current_scenario["victims"] if v.id == victim_id), None)
                if victim and victim.status != VictimStatus.RESCUED:
                    victim.status = VictimStatus.RESCUED
                    victim.rescued_at = datetime.now()
                    self.rescued_victims_list.append(victim_id)
                    completed.append(victim_id)
                    del self.active_rescues[victim_id]
                    
                    # Free up the resource
                    resource = next((r for r in self.current_scenario["resources"] 
                                    if r.assigned_victim_id == victim_id), None)
                    if resource:
                        resource.available = True
                        resource.current_task = None
                        resource.assigned_victim_id = None
        
        return completed
    
    def _execute_allocation(self, alloc: ResourceAllocation) -> bool:
        """Execute a resource allocation"""
        # Find an available resource
        available_resources = [r for r in self.current_scenario["resources"] if r.available]
        if not available_resources:
            return False
        
        resource = available_resources[0]  # Use first available resource
        
        # Find an unrescued victim (not already rescued or in progress)
        unrescued_victims = [v for v in self.current_scenario["victims"] 
                            if v.status not in [VictimStatus.RESCUED, VictimStatus.DECEASED]
                            and v.id not in self.active_rescues]
        
        if not unrescued_victims:
            return False
        
        # Use the requested victim or pick one
        victim = next((v for v in unrescued_victims if v.id == alloc.victim_id), unrescued_victims[0])
        
        # Calculate rescue time (2-5 steps based on distance)
        distance = resource.position.distance_to(victim.position)
        steps_needed = max(2, min(5, int(distance / 5) + 2))
        completion_step = self.step_count + steps_needed
        
        # Assign resource
        resource.available = False
        resource.current_task = f"rescuing_{victim.id}"
        resource.assigned_victim_id = victim.id
        victim.status = VictimStatus.ASSIGNED
        victim.assigned_at = datetime.now()
        
        # Track active rescue
        self.active_rescues[victim.id] = completion_step
        
        return True
    
    def _get_observation(self) -> DisasterObservation:
        """Generate current observation"""
        rescued_count = len([v for v in self.current_scenario["victims"] if v.status == VictimStatus.RESCUED])
        deceased_count = len([v for v in self.current_scenario["victims"] if v.status == VictimStatus.DECEASED])
        assigned_count = len([v for v in self.current_scenario["victims"] if v.status == VictimStatus.ASSIGNED])
        
        # Build victim list for agent
        pending_victims = []
        for v in self.current_scenario["victims"]:
            if v.status not in [VictimStatus.RESCUED, VictimStatus.DECEASED]:
                pending_victims.append({
                    "id": v.id,
                    "priority": v.base_priority,
                    "triage": v.triage_category,
                    "in_progress": v.id in self.active_rescues,
                    "completion_step": self.active_rescues.get(v.id, None)
                })
        
        # Build resource list
        available_resources = []
        for r in self.current_scenario["resources"]:
            if r.available:
                available_resources.append({
                    "id": r.id,
                    "type": r.type.value if hasattr(r.type, 'value') else str(r.type)
                })
        
        time_elapsed = (time.time() - self.episode_start_time) / 3600
        
        return DisasterObservation(
            scenario_name=self.current_scenario["name"],
            difficulty=self.current_difficulty,
            disaster_type=self.current_scenario["disaster_type"],
            time_elapsed_hours=time_elapsed,
            time_remaining_hours=self.current_scenario["duration_hours"] - time_elapsed,
            weather=self.current_scenario["weather"],
            total_victims=self.current_scenario["total_victims"],
            discovered_victims=len([v for v in self.current_scenario["victims"] if v.status != VictimStatus.UNDISCOVERED]),
            rescued_victims=rescued_count,
            deceased_victims=deceased_count,
            pending_victims=pending_victims,
            available_resources=available_resources,
            deployed_resources=[],
            resource_health={},
            zones_status=[],
            active_hazards=[],
            infrastructure_status={},
            current_reward=self.total_reward if self.decisions else 0.0,
            cumulative_reward=self.total_reward,
            done=self.done
        )
    
    def get_grader_result(self) -> DisasterGraderResult:
        """Calculate final score"""
        lives_saved = len([v for v in self.current_scenario["victims"] if v.status == VictimStatus.RESCUED])
        total_victims = self.current_scenario["total_victims"]
        
        lives_score = lives_saved / total_victims if total_victims > 0 else 0
        efficiency_score = min(1.0, lives_saved / max(1, self.step_count)) if lives_saved > 0 else 0
        time_taken = (time.time() - self.episode_start_time) / 3600
        time_score = max(0, 1.0 - (time_taken / self.current_scenario["duration_hours"]))
        
        total_score = (lives_score * 0.6 + efficiency_score * 0.2 + time_score * 0.2)
        
        if lives_saved == total_victims:
            feedback = f"🎉 PERFECT! All {total_victims} victims rescued in {self.step_count} steps!"
        elif lives_saved >= total_victims * 0.8:
            feedback = f"✅ EXCELLENT! Rescued {lives_saved}/{total_victims} victims."
        elif lives_saved >= total_victims * 0.5:
            feedback = f"👍 GOOD! Rescued {lives_saved}/{total_victims} victims."
        elif lives_saved > 0:
            feedback = f"⚠️ FAIR! Rescued {lives_saved}/{total_victims} victims."
        else:
            feedback = f"❌ POOR! No victims rescued. Need better strategy."
        
        return DisasterGraderResult(
            score=total_score,
            lives_saved_score=lives_score,
            response_time_score=time_score,
            resource_efficiency_score=efficiency_score,
            fairness_score=0.5,
            planning_depth_score=min(1.0, self.step_count / 10),
            breakdown={"lives_saved": lives_score, "efficiency": efficiency_score, "time": time_score},
            feedback=feedback,
            total_lives_saved=lives_saved,
            total_lives_lost=total_victims - lives_saved,
            avg_rescue_time_minutes=0,
            resources_deployed=0,
            total_missions=self.step_count
        )
    
    def set_difficulty(self, difficulty: str):
        if difficulty in ["easy", "medium", "hard"]:
            self.current_difficulty = difficulty
    
    @property
    def state(self) -> DisasterState:
        return DisasterState(
            episode_id=self.episode_id or "not_started",
            step_count=self.step_count,
            simulation_time_hours=(time.time() - self.episode_start_time) / 3600 if self.episode_start_time else 0,
            lives_saved=len([v for v in self.current_scenario["victims"] if v.status == VictimStatus.RESCUED]) if self.current_scenario else 0,
            lives_lost=len([v for v in self.current_scenario["victims"] if v.status == VictimStatus.DECEASED]) if self.current_scenario else 0,
            avg_response_time_minutes=0,
            resource_utilization=0,
            fuel_consumed=0,
            total_distance_traveled=0,
            priority_adherence=0.5,
            zone_distribution={}
        )