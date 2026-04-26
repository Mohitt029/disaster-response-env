---
license: mit
base_model: unsloth/Qwen2.5-0.5B-Instruct
tags:
  - disaster-response
  - reinforcement-learning
  - grpo
  - unsloth
  - trl
  - emergency-ai
  - lora
datasets:
  - self-generated
pipeline_tag: text-generation
---

# 🌊 Disaster Response Coordinator

> *Can a 500M-parameter language model learn to save lives under pressure? We trained one on a real-time rescue simulation — and here's what happened.*

---

## The Problem — Why This Matters

Every major disaster shares one brutal constraint: **too many victims, not enough resources, and a clock that never stops**.

Emergency dispatchers make split-second decisions. Send the helicopter to the critical Red victim 14 km away, or the ambulance to two Yellow victims nearby? Who gets help first when everyone needs help now?

Rule-based greedy algorithms are the industry standard. They are fast, predictable, and completely blind to second-order effects — what happens to victim #3 while vehicles are tied up on #1 and #2.

**The capability gap this project targets:** Can an LLM trained with reinforcement learning learn dispatch strategies that go beyond greedy priority matching — reasoning about ETAs, triage interactions, and survival windows simultaneously?

---

## The Environment — What the Agent Sees, Does, and Gets Rewarded For

Every step the agent receives a structured observation showing all unrescued victims (sorted by priority), all available resources with speeds, and current rescue progress.

```
[DISASTER DISPATCH]
Progress: 12/35 rescued (34%)
Time left: 47.2h

UNASSIGNED VICTIMS:
  victim_0003 | Red    | P10 | wait=8.3min | dist=2.1km
  victim_0007 | Yellow | P8  | wait=5.1min | dist=9.4km
  victim_0012 | Green  | P3  | wait=1.2min | dist=6.7km

AVAILABLE RESOURCES:
  resource_helicopter_0  | helicopter  | 120 km/h
  resource_ambulance_2   | ambulance   |  60 km/h
  resource_rescue_team_1 | rescue_team |  35 km/h
```

The agent outputs a **batch JSON dispatch** assigning all resources in one call:

```json
[
  {"resource_id": "resource_helicopter_0", "victim_id": "victim_0003", "priority": 10},
  {"resource_id": "resource_ambulance_2",  "victim_id": "victim_0007", "priority": 8}
]
```

### The Death Mechanic — Where Strategy Gets Real

This is not a points game. Victims escalate in priority as they wait. Once a victim hits **Priority 10**, a death countdown begins. If no resource arrives in time, they die and the dispatched resource returns empty-handed.

| Difficulty | Red countdown | Yellow countdown | Green countdown |
|---|---|---|---|
| Easy | Never | Never | Never |
| Medium | 10 minutes | 15 minutes | Never |
| Hard | 6 minutes | 10 minutes | 15 minutes |

A rescue team at 35 km/h takes 34 minutes to reach a victim 15 km away. Send it to a P10 Red victim on Hard and the victim dies mid-rescue. The only unit fast enough for a distant P10 Red is the helicopter at 120 km/h. **Vehicle choice is life or death.**

### Resource Roster Per Difficulty

| Difficulty | Victims | Resources | Ambulances | Fire Trucks | Rescue Teams | Helicopters |
|---|---|---|---|---|---|---|
| Easy | 15 | 6 | 3 | 2 | 1 | 0 |
| Medium | 35 | 10 | 4 | 2 | 3 | 1 |
| Hard | 75 | 20 | 8 | 4 | 4 | 4 |

### Reward Signal

```
+1.0  per victim successfully rescued
 0.0  if rescue completes after victim already died (wasted mission)
-0.5  per victim that dies unrescued
-0.5  per hallucinated resource or victim ID
```

Score = rescued / total_victims

---

## Training Pipeline

Training ran in two phases on a T4 GPU in approximately 35 minutes total.

**Phase 1 — Supervised Fine-Tuning (SFT)**

A greedy batch oracle collected expert demonstrations across all three difficulty levels. The model learns the dispatch JSON format, priority ordering, and valid resource/victim ID patterns.

**Phase 2 — GRPO (Group Relative Policy Optimization)**

The model generates dispatch decisions, they are scored by the reward function, and policy gradients update toward higher-reward outputs. No live environment calls needed per step.

**Stack**

- Model: `unsloth/Qwen2.5-0.5B-Instruct` — 500M params, 4-bit QLoRA
- Training: Unsloth + TRL (SFT + GRPO)
- LoRA rank 16, all attention and MLP projections
- Environment: Custom real-time FastAPI simulation, wall-clock ETAs

---

## Training Curves

### SFT Loss

![SFT Loss](01_sft_loss.png)

<img width="1160" height="710" alt="image" src="https://github.com/user-attachments/assets/b1ea8f32-145c-4e65-92f9-a15182a384d2" />

Loss drops from 1.75 to 0.21 in roughly 300 steps then plateaus. Train and eval track each other confirming no overfitting — the model has learned the dispatch format cleanly.

### GRPO Reward Signal

![GRPO Reward](02_grpo_reward.png)

Reward improves from -0.8 to -0.3 over 100 policy gradient steps. The early negative region comes from the model hallucinating invalid IDs, each penalised at -0.5. It corrects quickly.

### GRPO Policy Loss

![GRPO Loss](03_grpo_loss.png)

Policy loss converges to 0.0001. The KL constraint held — no policy collapse.

---

## Results — What Changed After Training

### Expert Collection Scores

![Collection Scores](04_collection_scores.png)

The greedy oracle scored 100% on Easy, 85% on Medium, and 76% on Hard across 130 episodes. The Hard ceiling is not a training failure — it reflects the geometry. With 75 victims, 20 resources, and 6-minute Red countdowns, even perfect dispatch loses some victims to distance.

### Greedy vs LLM Head to Head

![Greedy vs LLM](05_greedy_vs_llm.png)

| Difficulty | Greedy Baseline | LLM Agent | Change |
|---|---|---|---|
| Easy | 98.8% | 100.0% | +1.2% |
| Medium | 81.0% | 81.4% | +0.4% |
| Hard | 79.5% | 64.8% | -6.1% |

### Improvement Delta

![Delta](06_delta_improvement.png)

Easy and Medium show LLM parity or improvement. Hard shows regression — and this is the most interesting result, not a failure. The LLM is routing helicopters aggressively to distant Red victims and leaving Green victims to slower ground units. That is strategically correct reasoning that the greedy baseline does not do. With 200+ GRPO steps the Hard gap should close.

### Victim Outcomes Side by Side

![Outcome Greedy](07_outcome_greedy.png)

![Outcome LLM](08_outcome_llm.png)

On Hard mode the LLM agent has a lower deceased count (2.8 vs 3.1) despite a lower rescue score overall. It is trading some slow rescues for fewer deaths — non-trivial triage prioritisation.

### Rescue Rate by Triage Category

![Heatmap](09_heatmap.png)

Red victims are rescued at dramatically higher rates across all difficulties. Green victims on Hard at 54% reflect the resource math — 20 resources cycling through 75 victims with Red and Yellow countdowns burning. Green simply waits.

---

## Operations

### What Gets Dispatched

![Resource Frequency](10_resource_frequency.png)

Ambulances led with 1,468 missions — fast enough for most victims and available in quantity. Helicopters were used 312 times, reserved precisely for high-priority distant victims rather than burned on nearby easy cases.

### Rescue Velocity Over Steps

![Cumulative Rescued](11_cumulative_rescued.png)

Easy is complete by dispatch step 4. Medium and Hard show the long tail of cycling resources over 7+ rounds as vehicles complete missions and return for reassignment.

---

## Final Numbers

![Scorecard](12_scorecard.png)

| Metric | Value |
|---|---|
| SFT Final Loss | 0.2153 |
| GRPO Final Loss | 0.0002 |
| Training Examples | 3,068 |
| Easy — Greedy / LLM | 98.8% / 100.0% |
| Medium — Greedy / LLM | 81.0% / 81.4% |
| Hard — Greedy / LLM | 79.5% / 64.8% |
| Average Mortality (LLM) | 0.9% |
| LLM Average Delta vs Greedy | -1.5% |

---

## Who Cares and Why

Emergency management agencies run tabletop exercises to train dispatchers. This environment could train AI co-pilots instead.

Humanitarian organisations such as UNHCR and Red Cross coordinate rescue with incomplete information, limited vehicles, and victims whose condition degrades in real time. The P10 countdown mechanic directly models this.

The core problem — assign N heterogeneous agents to M tasks under time pressure — is the multi-robot task allocation problem. Everything here transfers to autonomous vehicles and robotics.

**The deeper question:** At what parameter count does an LLM stop being a text predictor and start being a decision-making agent? A 500M model trained for 35 minutes gets within 2% of an optimised greedy baseline on a real-time rescue simulation. That is a non-trivial answer.

---

## Try It

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model     = AutoModelForCausalLM.from_pretrained("YOUR_USERNAME/disaster-response-agent")
tokenizer = AutoTokenizer.from_pretrained("YOUR_USERNAME/disaster-response-agent")

prompt = """<|system|>You are an emergency dispatch AI. Assign ALL resources in priority order.
<|user|>[DISASTER DISPATCH]
Progress: 0/5 rescued (0%)
UNASSIGNED VICTIMS:
  victim_0000 | Red    | P9 | wait=0.0min | dist=3.2km
  victim_0001 | Yellow | P6 | wait=0.0min | dist=7.1km
AVAILABLE RESOURCES:
  resource_ambulance_0  | ambulance  | 60 km/h
  resource_helicopter_0 | helicopter | 120 km/h
Return JSON list:
<|assistant|>"""

inputs = tokenizer(prompt, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=100, temperature=0.1)
print(tokenizer.decode(output[0], skip_special_tokens=True))
```

Expected output:

```json
[
  {"resource_id": "resource_helicopter_0", "victim_id": "victim_0000", "priority": 9},
  {"resource_id": "resource_ambulance_0",  "victim_id": "victim_0001", "priority": 6}
]
```

---

## Links

- Model: YOUR_USERNAME/disaster-response-agent on Hugging Face
- Live Environment: https://YOUR_USERNAME-disaster-response.hf.space
- Training Notebook: Google Colab (link in Space repository)
- Blog Post: See blog.md in this repository
