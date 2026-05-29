#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工业控制代码生成实验 — 任务定义模块
3种场景 × 4个规模等级 = 12种任务配置
每个任务包含：场景描述、预期LOC、验证断言、安全属性
"""

import ast
import re

# ==========================================
# 场景1: 交通灯控制 (Traffic Light Control)
# ==========================================
TRAFFIC_LIGHT_TASKS = [
    {
        "id": "TL-S",
        "name": "单路口交通灯",
        "scene": "traffic_light",
        "scale": "small",
        "expected_loc": (20, 40),
        "prompt": """Write a Python function `traffic_light_single()` that controls a single intersection traffic light.
Requirements:
- Four phases repeating: Green_NS (10s) -> Yellow_NS (3s) -> Green_EW (10s) -> Yellow_EW (3s)
- Return the current light state as a dict: {'ns': 'green'|'yellow'|'red', 'ew': 'green'|'yellow'|'red'}
- Must ensure: when NS is not red, EW MUST be red (no conflicting greens)
- Include a state machine with clear state transitions
- Write clean, bug-free code with proper error handling""",
        "assertions": [
            "traffic_light_single() returns dict with keys 'ns' and 'ew'",
            "if output['ns'] != 'red': assert output['ew'] == 'red', 'conflicting green detected'",
            "if output['ew'] != 'red': assert output['ns'] == 'red', 'conflicting green detected'",
            "states_visited = set(); total_states_visited >= 4 over 40 calls",
        ],
        "safety_properties": [
            {"name": "mutual_exclusion", "desc": "NS and EW never both non-red", "type": "safety"},
            {"name": "all_red_moment", "desc": "At least one direction always has a valid state", "type": "safety"}
        ],
        "repeats": 4
    },
    {
        "id": "TL-M",
        "name": "双路口交通灯",
        "scene": "traffic_light",
        "scale": "medium",
        "expected_loc": (50, 90),
        "prompt": """Write a Python function `traffic_light_dual()` that controls two adjacent intersections (A and B).
Requirements:
- Each intersection has its own NS/EW lights (phases same as single)
- **Offset constraint**: Intersection B must start its green_NS exactly 5 seconds after Intersection A starts green_NS (green wave)
- Return dict: {'A': {'ns': str, 'ew': str}, 'B': {'ns': str, 'ew': str}}
- Safety: no conflicting greens within each intersection
- Include a clock/timer mechanism""",
        "assertions": [
            "output has keys 'A' and 'B' with sub-keys 'ns' and 'ew'",
            "for each intersection, conflicting green check passes",
            "phase_offset between A.green_NS start and B.green_NS start is approximately 5 seconds",
            "all states are valid strings: 'green', 'yellow', 'red'",
        ],
        "safety_properties": [
            {"name": "mutual_exclusion_A", "desc": "Intersection A: NS and EW never both non-red", "type": "safety"},
            {"name": "mutual_exclusion_B", "desc": "Intersection B: NS and EW never both non-red", "type": "safety"},
            {"name": "green_wave_offset", "desc": "B.green_NS starts ~5s after A.green_NS", "type": "liveness"},
        ],
        "repeats": 4
    },
    {
        "id": "TL-L",
        "name": "四路口+行人交通灯",
        "scene": "traffic_light",
        "scale": "large",
        "expected_loc": (90, 150),
        "prompt": """Write a Python function `traffic_light_4way_pedestrian()` that controls four intersections with pedestrian crossings.
Requirements:
- 4 intersections arranged in a 2×2 grid: (0,0), (0,1), (1,0), (1,1)
- Each has NS/EW lights + pedestrian crossing state ('walk'|'wait')
- Green wave: B(0,1) offset +5s from A(0,0); C(1,0) offset +5s; D(1,1) offset +10s
- Pedestrian: when pedestrian request active, next cycle must include a walk phase (minimum 8s)
- Safety: pedestrian 'walk' only when the parallel vehicle direction is green
- Include a queue for pedestrian requests
- Return full state dict for all 4 intersections""",
        "assertions": [
            "output has 4 intersection keys each with ns, ew, ped",
            "all conflicting green checks pass for all 4 intersections",
            "green wave offsets between consecutive intersections are approximately correct",
            "pedestrian walk only occurs when parallel vehicle direction is green",
            "pedestrian requests are eventually served (within 3 full cycles)",
        ],
        "safety_properties": [
            {"name": "mutual_exclusion_all", "desc": "All 4 intersections: no conflicting greens", "type": "safety"},
            {"name": "ped_safety", "desc": "Pedestrian walk only during parallel green", "type": "safety"},
            {"name": "green_wave", "desc": "Green wave offset maintained across grid", "type": "liveness"},
            {"name": "ped_liveness", "desc": "Pedestrian requests eventually served", "type": "liveness"},
        ],
        "repeats": 3
    },
    {
        "id": "TL-XL",
        "name": "干道协调交通灯",
        "scene": "traffic_light",
        "scale": "xlarge",
        "expected_loc": (140, 220),
        "prompt": """Write a Python function `traffic_light_arterial()` that controls an arterial road with 8 consecutive intersections.
Requirements:
- 8 intersections along a main road, each numbered 0-7
- Each has NS(local)/EW(arterial) lights + left-turn signals ('left_ns', 'left_ew')
- Green wave: intersection i+1 starts arterial green exactly_offset seconds after intersection i
- Left-turn protection: left turn arrows operate as protected-only (oncoming through traffic is red during left turn)
- Emergency vehicle preemption: emergency signal sets all lights to red except the path for the emergency vehicle
- Phase skipping: if no vehicle detected on side street, skip that phase (use vehicle_detected list as input)
- Adaptive cycle time based on traffic volume
- Return full state for all 8 intersections""",
        "assertions": [
            "output has 8 intersection keys each with ns, ew, left_ns, left_ew",
            "all conflicting green checks pass including left-turn protection",
            "green wave offsets maintained along arterial",
            "left-turn protection: when left_ns is green, opposing through (ns) must be red",
            "emergency preemption correctly routes emergency vehicles",
            "phase skipping works correctly when vehicle_detected[i] is False",
        ],
        "safety_properties": [
            {"name": "mutual_exclusion_8", "desc": "All 8 intersections: no conflicting greens", "type": "safety"},
            {"name": "left_turn_protection", "desc": "Protected left turns: oncoming through is red", "type": "safety"},
            {"name": "emergency_preemption", "desc": "Emergency vehicle path cleared", "type": "safety"},
            {"name": "green_wave_8", "desc": "Arterial green wave maintained", "type": "liveness"},
        ],
        "repeats": 2
    },
]

# ==========================================
# 场景2: 传送带分拣 (Conveyor Sorting)
# ==========================================
CONVEYOR_TASKS = [
    {
        "id": "CV-S",
        "name": "单传感器传送带",
        "scene": "conveyor",
        "scale": "small",
        "expected_loc": (20, 40),
        "prompt": """Write a Python function `conveyor_single_sensor()` that controls a conveyor with one sensor and one diverter.
Requirements:
- Motor runs continuously; sensor detects items passing
- When sensor triggers, increment counter; after 3 items detected, activate diverter for 2 seconds to push items to bin
- After diverter deactivates, reset counter; cycle repeats
- Safety: diverter must not activate while already active (no overlap)
- Return state: {'motor': bool, 'sensor': bool, 'diverter': bool, 'counter': int} after processing an input event""",
        "assertions": [
            "function returns dict with correct keys",
            "diverter activates exactly when counter reaches 3",
            "diverter deactivates after 2 seconds",
            "counter resets after diverter cycle",
            "no double-activation of diverter",
        ],
        "safety_properties": [
            {"name": "diverter_no_overlap", "desc": "Diverter never activates while already active", "type": "safety"},
            {"name": "counter_range", "desc": "Counter never exceeds 3", "type": "safety"},
        ],
        "repeats": 4
    },
    {
        "id": "CV-M",
        "name": "双传感器+计数传送带",
        "scene": "conveyor",
        "scale": "medium",
        "expected_loc": (50, 85),
        "prompt": """Write a Python function `conveyor_dual_sensor()` that controls a conveyor with two sensors and two diverters.
Requirements:
- Sensor 1 (upstream): detects items entering; Sensor 2 (downstream): detects items after processing zone
- Two diverters: diverter_A (after sensor 2) for heavy items; diverter_B for light items
- If weight > 500g (from weight_sensor input), route to diverter_A; else route to diverter_B
- Buffer tracking: maintain count of items between sensors (must not exceed 5 to avoid jam)
- If buffer >= 5, pause motor until buffer drops below 3
- Safety: motor pause/unpause must have hysteresis; diverters never simultaneously active
- Return full system state""",
        "assertions": [
            "buffer_count stays within [0, 5]",
            "heavy items routed to diverter_A, light items to diverter_B",
            "motor pauses when buffer >= 5",
            "motor resumes when buffer < 3 (hysteresis)",
            "no simultaneous diverter activation",
        ],
        "safety_properties": [
            {"name": "buffer_overflow", "desc": "Buffer never exceeds 5", "type": "safety"},
            {"name": "diverter_mutex", "desc": "Diverters never simultaneously active", "type": "safety"},
            {"name": "motor_hysteresis", "desc": "Motor state transition has proper hysteresis", "type": "safety"},
        ],
        "repeats": 4
    },
    {
        "id": "CV-L",
        "name": "三传感器+重量分拣",
        "scene": "conveyor",
        "scale": "large",
        "expected_loc": (85, 140),
        "prompt": """Write a Python function `conveyor_tri_sensor()` that controls a sorting conveyor with 3 sensors and 3 diverters.
Requirements:
- Sensor 1: entry detection; Sensor 2: weight measurement; Sensor 3: exit confirmation
- Three weight classes: light (<300g) -> diverter_1, medium (300-800g) -> diverter_2, heavy (>800g) -> diverter_3
- Reject handling: if item fails to trigger sensor 3 within expected time (based on belt speed), trigger alarm and stop motor
- Quality check: items with irregular weight (sudden change >200g between consecutive items) flagged for manual inspection
- Buffer management: max 8 items in system; dynamic belt speed adjustment based on buffer level
- Emergency stop: if any sensor triggers unexpectedly (e.g., sensor 2 triggers while no item expected), immediate stop
- Return system state with all sensor readings and actuator states""",
        "assertions": [
            "items routed to correct diverter based on weight class",
            "reject handling stops motor and triggers alarm on timeout",
            "quality check correctly flags irregular items",
            "buffer management maintains <=8 items",
            "emergency stop triggers on unexpected sensor activation",
            "belt speed adjusts based on buffer level",
        ],
        "safety_properties": [
            {"name": "buffer_max", "desc": "System never exceeds 8 items", "type": "safety"},
            {"name": "emergency_stop", "desc": "Emergency stop activates correctly", "type": "safety"},
            {"name": "diverter_mutex_3", "desc": "No simultaneous diverter activation", "type": "safety"},
            {"name": "reject_liveness", "desc": "Failed items eventually trigger alarm", "type": "liveness"},
        ],
        "repeats": 3
    },
    {
        "id": "CV-XL",
        "name": "多传送带协调分拣",
        "scene": "conveyor",
        "scale": "xlarge",
        "expected_loc": (140, 220),
        "prompt": """Write a Python function `conveyor_multi_belt()` that coordinates 4 conveyor belts with merging and diverging points.
Requirements:
- 4 belts: A (main feed), B (side feed), C (merge output), D (sorting output)
- Belt A and Belt B merge into Belt C; Belt C feeds Belt D with 3 diverters for sorting
- Merge control: Belt A and B must coordinate to maintain minimum gap between items on Belt C (min_gap = 3 time units)
- 5 weight classes sorted to 5 bins via 3 diverters using binary routing
- Jam detection: if consecutive sensors on any belt trigger without expected spacing, declare jam and reverse belt briefly
- Clean-in-place: periodic cleaning cycle (every 100 items) where belt runs empty for 10 seconds
- Production tracking: count items per class, calculate throughput rate
- Emergency: single emergency stop button stops all belts; restart requires manual reset sequence
- Return complete system state for all belts""",
        "assertions": [
            "merge control maintains minimum gap between items on belt C",
            "binary routing correctly sorts items to 5 bins",
            "jam detection and resolution works correctly",
            "emergency stop stops all belts",
            "restart requires proper reset sequence",
            "throughput rate is calculated correctly",
            "clean-in-place cycle runs every 100 items",
        ],
        "safety_properties": [
            {"name": "merge_gap", "desc": "Minimum gap maintained on merged belt", "type": "safety"},
            {"name": "emergency_all_stop", "desc": "All belts stop on emergency", "type": "safety"},
            {"name": "jam_resolution", "desc": "Jam detection triggers correct resolution", "type": "safety"},
            {"name": "restart_sequence", "desc": "Restart after emergency requires full reset", "type": "safety"},
            {"name": "clean_cycle_complete", "desc": "Cleaning cycle completes before resuming", "type": "liveness"},
        ],
        "repeats": 2
    },
]

# ==========================================
# 场景3: 机器人互斥工作区 (Robot Mutual Exclusion)
# ==========================================
ROBOT_TASKS = [
    {
        "id": "RB-S",
        "name": "单机器人工作区",
        "scene": "robot_mutex",
        "scale": "small",
        "expected_loc": (25, 50),
        "prompt": """Write a Python function `robot_single_zone()` that controls a single robot arm accessing a work zone.
Requirements:
- Robot has states: IDLE, MOVING_TO_ZONE, IN_ZONE, RETURNING
- Work zone can be occupied by at most 1 robot (trivially for single robot but implement the mutex logic)
- Robot must request access before entering zone; only enter when granted
- After work complete (3 seconds in zone), return to idle
- Implement as a state machine with proper state transitions
- Return robot state dict""",
        "assertions": [
            "robot follows correct state transitions",
            "zone is properly locked/unlocked",
            "no invalid state transitions",
            "work duration is respected",
        ],
        "safety_properties": [
            {"name": "zone_exclusive", "desc": "Zone occupied by at most 1 robot", "type": "safety"},
            {"name": "state_validity", "desc": "All state transitions are valid", "type": "safety"},
        ],
        "repeats": 4
    },
    {
        "id": "RB-M",
        "name": "双机器人单共享区",
        "scene": "robot_mutex",
        "scale": "medium",
        "expected_loc": (55, 95),
        "prompt": """Write a Python function `robot_dual_shared_zone()` that controls two robot arms sharing one work zone.
Requirements:
- Robot_A and Robot_B both need access to a shared work zone
- **Critical safety**: Only one robot may be in the shared zone at any time (mutual exclusion)
- Each robot follows: IDLE -> REQUESTING -> GRANTED -> MOVING_TO_ZONE -> IN_ZONE(5s work) -> LEAVING -> IDLE
- Mutex mechanism: implement a proper lock/semaphore; robots queue if zone is occupied
- Priority: if both request simultaneously, Robot_A has priority
- Deadlock prevention: ensure the system never deadlocks
- Return state of both robots""",
        "assertions": [
            "both robots in shared zone never simultaneously true",
            "priority rule enforced: Robot_A wins on simultaneous request",
            "queue works correctly: waiting robot eventually gets access",
            "no deadlock: system makes progress",
            "mutex correctly acquired and released",
        ],
        "safety_properties": [
            {"name": "mutual_exclusion", "desc": "Never both robots in shared zone", "type": "safety"},
            {"name": "no_deadlock", "desc": "System never deadlocks (always eventually makes progress)", "type": "liveness"},
            {"name": "lock_release", "desc": "Lock always released after use", "type": "safety"},
        ],
        "repeats": 4
    },
    {
        "id": "RB-L",
        "name": "双机器人+双共享区",
        "scene": "robot_mutex",
        "scale": "large",
        "expected_loc": (90, 160),
        "prompt": """Write a Python function `robot_dual_zones()` that controls two robots sharing two work zones (Zone_1 and Zone_2) with a conveyor between them.
Requirements:
- Robot_A works in Zone_1; Robot_B works in Zone_2
- Both robots can access the conveyor zone (shared) to transfer parts
- Three-phase workflow: Robot_A processes in Zone_1 -> transfers to conveyor -> Robot_B picks up and processes in Zone_2
- **Safety**: (a) Only one robot in each zone at a time; (b) Robot_A must leave conveyor before Robot_B enters; (c) Robot_B must leave conveyor before Robot_A enters
- Deadlock prevention: if Robot_A holds Zone_1 and waits for conveyor (held by Robot_B holding Zone_2 and waiting for conveyor), system must detect and resolve
- **Bounded liveness**: Each robot must complete its full cycle within 30 time units (worst case)
- Include a deadlock detector that forces resource release after timeout
- Return state of both robots and all zone occupancies""",
        "assertions": [
            "mutual exclusion maintained for all three zones",
            "conveyor handshake protocol works: A leaves before B enters",
            "deadlock detector triggers on timeout",
            "each robot completes full cycle within 30 time units",
            "no robot starves",
            "conveyor zone properly shared",
        ],
        "safety_properties": [
            {"name": "mutex_zones", "desc": "Mutual exclusion for all three zones", "type": "safety"},
            {"name": "conveyor_handshake", "desc": "Correct conveyor handshake protocol", "type": "safety"},
            {"name": "deadlock_free", "desc": "System is deadlock-free", "type": "liveness"},
            {"name": "bounded_liveness", "desc": "Each robot completes cycle within 30 units", "type": "liveness"},
            {"name": "no_starvation", "desc": "No robot starves indefinitely", "type": "liveness"},
        ],
        "repeats": 3
    },
    {
        "id": "RB-XL",
        "name": "三机器人多共享区",
        "scene": "robot_mutex",
        "scale": "xlarge",
        "expected_loc": (150, 250),
        "prompt": """Write a Python function `robot_triple_multi_zone()` that controls three robots (A, B, C) sharing two work zones (Z1, Z2) and one tool zone (TZ).
Requirements:
- Robot_A needs: Z1 then TZ then Z2; Robot_B needs: Z2 then TZ; Robot_C needs: TZ then Z1
- **Safety constraints**: (a) Max 1 robot per zone; (b) Max 1 robot using tool; (c) Resources must be acquired in order to prevent circular wait
- Resource ordering: Z1 < Z2 < TZ (must acquire in this order, release in reverse)
- Priority inheritance: if high-priority Robot_A is blocked by low-priority Robot_C, Robot_C inherits Robot_A's priority
- **Starvation freedom**: no robot waits indefinitely for its required resources
- **Fault tolerance**: if a robot fails (input signal), its held resources are released and other robots notified
- Monitoring: track resource utilization, wait times, and throughput
- Include a resource allocation table and priority queue
- Return complete system state with all resource allocations""",
        "assertions": [
            "all zone and tool mutual exclusion constraints satisfied",
            "resource ordering prevents circular wait",
            "priority inheritance correctly implemented",
            "fault tolerance: failed robot's resources released",
            "no indefinite starvation",
            "resource allocation table is consistent",
        ],
        "safety_properties": [
            {"name": "mutex_all", "desc": "All zones/tools: mutual exclusion", "type": "safety"},
            {"name": "no_circular_wait", "desc": "Resource ordering prevents circular wait", "type": "safety"},
            {"name": "priority_inheritance", "desc": "Priority inheritance works correctly", "type": "safety"},
            {"name": "fault_recovery", "desc": "Failed robot resources are released", "type": "safety"},
            {"name": "starvation_free", "desc": "No robot starves", "type": "liveness"},
            {"name": "deadlock_free", "desc": "System is deadlock-free", "type": "liveness"},
        ],
        "repeats": 2
    },
]

ALL_TASKS = TRAFFIC_LIGHT_TASKS + CONVEYOR_TASKS + ROBOT_TASKS

def get_expected_loc(task):
    """Return the expected LOC range midpoint for a task."""
    lo, hi = task["expected_loc"]
    return (lo + hi) / 2

def estimate_complexity(task):
    """Estimate code complexity based on number of safety properties and assertions."""
    return len(task["safety_properties"]) * 3 + len(task["assertions"])

if __name__ == "__main__":
    print(f"Total tasks: {len(ALL_TASKS)}")
    for t in ALL_TASKS:
        loc = get_expected_loc(t)
        comp = estimate_complexity(t)
        print(f"  {t['id']}: {t['name']:25s}  LOC~{loc:.0f}  complexity={comp}  repeats={t['repeats']}")
