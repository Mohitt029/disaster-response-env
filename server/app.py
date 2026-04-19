"""
FastAPI server for Disaster Response Environment
"""

import sys
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from server.environment import DisasterResponseEnvironment
from models import DisasterAction, DisasterObservation, DisasterGraderResult

app = FastAPI(
    title="Disaster Response Environment",
    description="Multi-agent disaster response simulation for RL training",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
metrics = {
    "total_episodes": 0,
    "total_scores": {"easy": [], "medium": [], "hard": []},
    "total_lives_saved": {"easy": 0, "medium": 0, "hard": 0},
    "avg_response_times": {"easy": [], "medium": [], "hard": []}
}

def get_or_create_session(session_id: Optional[str] = None):
    if session_id and session_id in sessions:
        return sessions[session_id], session_id
    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = DisasterResponseEnvironment()
    metrics["total_episodes"] += 1
    return sessions[new_session_id], new_session_id

@app.post("/reset")
async def reset(session_id: Optional[str] = Query(None), difficulty: str = Query("easy")):
    env, sid = get_or_create_session(session_id)
    env.set_difficulty(difficulty)
    observation = env.reset(difficulty)
    
    if sid not in metrics:
        metrics[sid] = {}
    metrics[sid]["start_time"] = time.time()
    metrics[sid]["difficulty"] = difficulty
    
    return {
        "session_id": sid,
        "observation": observation.__dict__
    }

@app.post("/step")
async def step(
    action: DisasterAction,
    session_id: Optional[str] = Query(None)
):
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="No active session. Call reset first.")
    
    env = sessions[session_id]
    start_time = metrics.get(session_id, {}).get("start_time", time.time())
    time_taken = time.time() - start_time
    
    observation = env.step(action)
    
    difficulty = metrics.get(session_id, {}).get("difficulty", "easy")
    metrics["avg_response_times"][difficulty].append(time_taken)
    
    return {
        "session_id": session_id,
        "observation": observation.__dict__,
        "done": observation.done,
        "time_taken": time_taken
    }

@app.get("/state")
async def get_state(session_id: str = Query(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=400, detail="Session not found")
    env = sessions[session_id]
    return env.state.__dict__

@app.get("/tasks")
async def get_tasks() -> Dict[str, Any]:
    from server.tasks import get_all_tasks
    tasks = get_all_tasks()
    
    return {
        "tasks": [
            {
                "id": difficulty,
                "description": task.description,
                "difficulty": difficulty,
                "time_limit_hours": task.time_limit_hours,
                "expected_lives_saved": task.expected_lives_saved
            }
            for difficulty, task in tasks.items()
        ],
        "action_schema": {
            "allocations": {
                "type": "array",
                "items": {
                    "resource_id": {"type": "string"},
                    "victim_id": {"type": "string"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 10}
                }
            },
            "strategic": {
                "type": "object",
                "properties": {
                    "evacuation_order": {"type": "boolean"},
                    "resource_retasking": {"type": "string"},
                    "request_reinforcements": {"type": "boolean"},
                    "priority_zone": {"type": "string"}
                }
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        }
    }

@app.post("/grader")
async def get_grader(session_id: str = Query(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=400, detail="Session not found")
    
    env = sessions[session_id]
    if env.state.step_count == 0:
        raise HTTPException(status_code=400, detail="No episode completed yet")
    
    result = env.get_grader_result()
    
    difficulty = metrics.get(session_id, {}).get("difficulty", "easy")
    metrics["total_scores"][difficulty].append(result.score)
    metrics["total_lives_saved"][difficulty] += result.total_lives_saved
    
    return {
        "score": result.score,
        "feedback": result.feedback,
        "breakdown": result.breakdown,
        "lives_saved": result.total_lives_saved,
        "lives_lost": result.total_lives_lost,
        "steps_taken": env.state.step_count
    }

@app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    avg_scores = {}
    for diff in ["easy", "medium", "hard"]:
        scores = metrics["total_scores"][diff]
        avg_scores[diff] = sum(scores) / len(scores) if scores else 0.0
    
    return {
        "total_episodes": metrics["total_episodes"],
        "average_scores": avg_scores,
        "total_lives_saved": metrics["total_lives_saved"],
        "average_response_times": {
            diff: sum(times) / len(times) if times else 0.0
            for diff, times in metrics["avg_response_times"].items()
        }
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy", "environment": "disaster_response", "version": "1.0.0"}

@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "name": "Disaster Response Environment",
        "version": "1.0.0",
        "description": "Multi-agent disaster response simulation for training LLM agents",
        "endpoints": {
            "/reset": "POST - Start new episode",
            "/step": "POST - Take action",
            "/state": "GET - Get current state",
            "/tasks": "GET - List tasks",
            "/grader": "POST - Get episode score",
            "/metrics": "GET - Performance dashboard",
            "/health": "GET - Health check"
        }
    }

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()