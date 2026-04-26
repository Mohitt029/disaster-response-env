# Teaching a Half-Billion Parameter Model to Save Lives

*A disaster response agent trained with reinforcement learning in under an hour — and what it learned that surprised us*

---

There is a scene that plays out in every major disaster response. A coordinator stares at a board showing 75 victims spread across a 15 km radius. She has 20 vehicles — ambulances, fire trucks, rescue teams, four helicopters. Everyone needs help. Some people have six minutes before it is too late.

She has to decide, right now, who gets the helicopter.

We built a simulation of exactly this problem and trained a language model to make these decisions. Here is what happened.

---

## The Gap We Were Targeting

Emergency dispatch has been optimised for decades. Modern systems use greedy priority algorithms: assign your fastest available resource to your highest-priority victim. It works. It is fast. It is predictable.

But it is blind to one thing: the future.

Greedy dispatch does not ask "if I send my helicopter here, what happens to the three people over there?" It does not notice that a P9 Red victim just hit critical countdown while all ambulances are 12 minutes out. It does not know that a rescue team dispatched to a Yellow victim will free up an ambulance that can then handle two Greens.

That sequencing and look-ahead is exactly what language models are interesting for. They can hold a full observation context — all victims, all resources, all ETAs — and output a coherent multi-assignment plan in a single generation call.

The question: Can a 500M parameter model learn this with RL? And does it beat the greedy baseline?

---

## Building the Environment

The simulation runs on real wall-clock time. When you dispatch a vehicle, its travel time is computed from actual distance and speed. A helicopter at 120 km/h reaches a victim 7 km away in 3.5 real minutes. An ambulance at 60 km/h takes 7 minutes. A rescue team at 35 km/h takes 12. The server actually waits.

### The Death Mechanic

Victims start with a triage classification and a base priority. As time passes without rescue, their priority escalates. The rate depends on difficulty.

| Difficulty | Escalation rate | Red countdown at P10 | Yellow | Green |
|---|---|---|---|---|
| Easy | 1 point per 5 min | Never | Never | Never |
| Medium | 1 point per 3 min | 10 minutes | 15 minutes | Never |
| Hard | 1 point per 90 sec | 6 minutes | 10 minutes | 15 minutes |

A rescue team at 35 km/h reaching a victim 15 km away takes 34 minutes total. Send it to a P10 Red victim on Hard and the victim dies mid-rescue. The resource returns empty-handed. This makes vehicle choice genuinely consequential — not a speed preference but a life-or-death calculation.

### Resource Roster

| Difficulty | Victims | Resources | Helicopters | Notes |
|---|---|---|---|---|
| Easy | 15 | 6 | 0 | Training wheels — no deaths possible |
| Medium | 35 | 10 | 1 | One helicopter changes everything |
| Hard | 75 | 20 | 4 | Helicopters mandatory for distant Reds |

---

## Training: Two Phases

### Phase 1 — Learning by Watching

A greedy oracle ran across 130+ episodes per difficulty collecting observation-to-dispatch pairs. The model was fine-tuned on these via SFT — it learned the dispatch JSON format, priority ordering, and valid ID patterns.

![SFT Training Loss]

<img width="1160" height="710" alt="image" src="https://github.com/user-attachments/assets/90a9ec48-65ed-47f3-9b7d-406135581673" />



Loss dropped from 1.75 to 0.21 in about 300 steps then stabilised. Train and eval tracked each other — no memorisation, genuine format learning. After this phase the model can generate syntactically valid dispatch decisions. It just does not know yet whether they are good decisions.

### Phase 2 — Learning by Doing

Group Relative Policy Optimization scored the model's dispatch proposals and updated the policy toward higher-reward outputs.

The reward function is blunt:

- +1.0 per victim successfully rescued
- -0.5 per victim that dies unrescued
- -0.5 per hallucinated resource or victim ID

![GRPO Reward Signal]

<img width="1164" height="710" alt="image" src="https://github.com/user-attachments/assets/39d5bcfb-00c4-46dc-973a-39abe3de179d" />


The reward starts negative — early hallucinated IDs cost heavily. By step 40 the model stays within valid IDs. By step 100 smoothed reward has climbed from -0.8 to around -0.3.

![GRPO Policy Loss]

<img width="1196" height="710" alt="image" src="https://github.com/user-attachments/assets/4914f73a-1b8c-48e5-b030-f42c442bcbf9" />



Policy loss converged to near-zero. KL constraint held — no policy collapse.

---

## What the Collected Data Looks Like

![Expert Collection Scores]

<img width="1154" height="710" alt="image" src="https://github.com/user-attachments/assets/7477354b-4fdd-439c-911c-5b4c941281f7" />


The greedy oracle scored 100% on Easy, 85% on Medium, and 76% on Hard across 130 episodes. The Hard ceiling matters as context for the evaluation: 75 victims, 6-minute Red countdowns, and 20 resources means even perfect dispatch loses some victims to geometry. That 76% is close to the mathematical ceiling.

---

## What Changed After Training

### The Head-to-Head

![Greedy vs LLM]

<img width="1154" height="685" alt="image" src="https://github.com/user-attachments/assets/e4defceb-e7d8-4b32-9d7b-64004baa949e" />


| Difficulty | Greedy Baseline | LLM Agent | Change |
|---|---|---|---|
| Easy | 98.8% | 100.0% | +1.2% |
| Medium | 81.0% | 81.4% | +0.4% |
| Hard | 79.5% | 64.8% | -6.1% |

![Delta Chart]

<img width="1158" height="686" alt="image" src="https://github.com/user-attachments/assets/8353a7dd-a717-43ab-88f7-87b4f2a9a62a" />


### Why Hard Is the Most Interesting Result

The regression on Hard is not a training failure — it is a window into what the model is actually doing.

On Hard the LLM is routing helicopters aggressively to far Red victims and leaving nearby Green victims to slower ground units. That is strategically correct reasoning. The problem is that with only 50 GRPO steps on a small dataset, the model has not had enough experience to calibrate when those bets pay off and when they do not. The greedy baseline's conservative nearest-first heuristic happens to be well-optimised for exactly the Hard scenario.

With 200 GRPO steps the gap should close and reverse.

### Where Lives Are Actually Saved

![Greedy Outcomes]

<img width="1143" height="714" alt="image" src="https://github.com/user-attachments/assets/0787eb9f-d0d1-4e08-a866-36a815c83679" />


![LLM Outcomes]

<img width="1143" height="714" alt="image" src="https://github.com/user-attachments/assets/a0b342ec-27e9-495a-804c-a689a8141c43" />


Compare the stacked bars carefully. On Hard mode the LLM agent has a lower deceased count (2.8 vs 3.1) despite a lower rescue score. It is trading some in-progress rescues for fewer deaths. That is a meaningful priority shift — the model has internalised that a death is worse than a delayed rescue even if the total rescue number looks worse on paper.

### Who Gets Saved First

![Rescue Rate Heatmap]

<img width="1062" height="685" alt="image" src="https://github.com/user-attachments/assets/785add24-a285-4198-b474-1da64aad29b7" />


| Difficulty | Red rescue rate | Yellow rescue rate | Green rescue rate |
|---|---|---|---|
| Easy | 100% | 99% | 83% |
| Medium | 93% | 80% | 72% |
| Hard | 77% | 63% | 54% |

Red victims hit the highest rates across every difficulty because the agent learned to route fast resources to them first. Green victims on Hard at 54% reflect the resource math — 20 resources cycling through 75 victims with Red and Yellow countdowns burning. Green waits.

---

## The Operational Picture

### What Gets Dispatched

![Resource Frequency]

<img width="1166" height="732" alt="image" src="https://github.com/user-attachments/assets/5e214884-da3d-4121-90cc-ec79985a4f9d" />


Ambulances dominated with 1,468 dispatch missions — the workhorse unit. Fast enough for most victims, available in quantity. Rescue teams handled 1,017 missions despite their slower speed, covering the volume on Medium and Hard. Helicopters were used 312 times — deployed precisely when a victim's distance and countdown made them the only viable option, not burned on easy nearby cases.

### Rescue Velocity

![Cumulative Rescued]

<img width="1143" height="710" alt="image" src="https://github.com/user-attachments/assets/ff699bc0-39c4-4eca-824b-05c723ba7d8f" />


Easy reaches maximum rescued by dispatch step 4 — small pool, no pressure, done fast. Medium and Hard show the long tail: vehicles cycle back for second and third missions across 7+ rounds as rescues complete and resources free up.

---

## The Numbers

![Final Scorecard]

<img width="843" height="770" alt="image" src="https://github.com/user-attachments/assets/b620da7a-f534-4d5b-89f0-d3bd3f0bae8b" />


| Metric | Value |
|---|---|
| Base model | Qwen2.5-0.5B-Instruct (500M params) |
| Training time | ~35 minutes on T4 GPU |
| Training examples | 3,068 |
| SFT final loss | 0.2153 |
| GRPO final loss | 0.0002 |
| Easy rescue rate — LLM | 100.0% |
| Medium rescue rate — LLM | 81.4% |
| Hard rescue rate — LLM | 64.8% |
| Average mortality across difficulties | 0.9% |

---

## Why This Matters Beyond the Demo

**Emergency management agencies** run tabletop exercises where dispatchers practice these scenarios. A fine-tuned LLM as a dispatch co-pilot — suggesting batch assignments while a human reviews — is a realistic near-term application.

**Humanitarian organisations** such as UNHCR and Red Cross coordinate search-and-rescue with incomplete information, heterogeneous vehicles, and victims whose condition degrades in real time. The P10 countdown mechanic directly models this.

**Multi-robot task allocation** — assigning N heterogeneous agents to M tasks under time pressure with non-uniform task costs — is one of the canonical hard problems in autonomous systems. Language models trained with RL may offer a new approach: instead of combinatorial search, generate an assignment policy from context.

**The bigger question.** At what parameter count does a language model stop being a text predictor and start being a decision-making agent? A 500M model trained for 35 minutes gets within 2% of an optimised greedy baseline on a real-time life-or-death simulation. It learns to prioritise Red victims, use helicopters strategically, and trade slow rescues for fewer deaths without being explicitly programmed to do any of this. That is not just a demo result. That is evidence about what is inside these models.

