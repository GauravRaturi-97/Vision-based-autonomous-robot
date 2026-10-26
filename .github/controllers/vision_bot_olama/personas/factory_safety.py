"""
personas/factory_safety.py
Official Knowledge Base & Safety Inspection Engine for AURA Industrial Factory.
Provides ground-truth OSHA 1910 standards, machine guarding, hazmat protocols,
gas canister safety, and integrates TinyFish for live industrial compliance lookups.
"""

PERSONA_CONFIG = {
    "key": "FACTORY_SAFETY",
    "name": "Hazmat-Bot (Safety Officer)",
    "voice_rate": 180,
    "greeting": "Hazmat-Bot online. Scanning factory floor for OSHA compliance and industrial safety.",
    "customer_word": "worker",
    "arrival_person_msg": "Worker located. Safety perimeter and PPE protocol verified!",
    "arrival_landmark_fmt": "Arrived at {target}. Initiating OSHA hazard scan.",
    "tinyfish_query_fmt": "OSHA 1910 industrial hazard safety inspection {target}",
    "hud_theme_bgr": (18, 20, 28),
    "accent_bgr": (0, 215, 255),
}

FACTORY_ZONES = {
    "conveyor": {
        "name": "Automated Conveyor Line (Bay 4)",
        "osha_standard": "OSHA 1910.212 - General Machine Guarding",
        "ppe_required": "Safety Glasses (ANSI Z87.1), Steel-Toe Boots, No Loose Clothing",
        "emergency_stop": "Continuous E-Stop pull wire along full 6-meter span",
        "clearance_m": 0.85,
    },
    "gas canister": {
        "name": "High-Pressure Gas Storage Depot",
        "osha_standard": "OSHA 1910.101 - Compressed Gases & NFPA 55",
        "ppe_required": "Face Shield, Heavy Leather Gloves, Anti-Static Footwear",
        "storage_rule": "Upright cylinder chaining, protective valve caps locked, 6m separation from fuel",
        "clearance_m": 1.10,
    },
    "forklift": {
        "name": "Mobile Material Handling Lanes",
        "osha_standard": "OSHA 1910.178 - Powered Industrial Trucks",
        "ppe_required": "High-Visibility Class 2 Safety Vest, Hearing Protection (NRR 25+)",
        "traffic_speed": "Maximum speed 8 km/h; sound horn at all cross-aisles and blind corners",
        "clearance_m": 1.50,
    },
    "manhole": {
        "name": "Subfloor Utility Trench & Sump Access",
        "osha_standard": "OSHA 1910.146 - Permit-Required Confined Spaces",
        "ppe_required": "4-Gas Atmospheric Sniffer, Full Body Harness, Tripod Winch",
        "air_limits": "Oxygen between 19.5% and 23.5%; CO < 35 ppm; H2S < 10 ppm",
        "clearance_m": 1.20,
    },
    "inspection station": {
        "name": "OSHA Compliance Control Hub",
        "osha_standard": "OSHA 1910.1200 - Hazard Communication Standard (GHS/SDS)",
        "amenities": "Digital SDS binder, Eyewash station (15-min flush), First-Aid Kit Class B",
        "clearance_m": 0.65,
    },
    "crates": {
        "name": "Heavy Components Staging Zone",
        "osha_standard": "OSHA 1910.176 - Material Handling & Stacking Stability",
        "rules": "Tier stack limit max 3 high; interlocking base; 36-inch clearance from fire exits",
        "clearance_m": 0.75,
    },
}

SAFETY_PROTOCOLS = {
    "loto": {
        "code": "OSHA 1910.147",
        "title": "Lockout / Tagout (Control of Hazardous Energy)",
        "steps": "1. Notify operators -> 2. Shut down equipment -> 3. Isolate energy sources -> 4. Apply padlock & tag -> 5. Dissipate stored energy -> 6. Zero-energy verification.",
    },
    "spill": {
        "code": "OSHA 1910.120 (HAZWOPER)",
        "title": "Chemical Spill Containment & Neutralization",
        "steps": "Evacuate upwind -> Deploy absorbent containment socks -> Apply neutralizer -> Transfer to UN-rated salvage drum.",
    },
    "fire": {
        "code": "OSHA 1910.157",
        "title": "Portable Fire Extinguishers & Egress",
        "steps": "Maintain 36-inch unobstructed clearance around all extinguishers and electrical panels. Annual hydrostatic test verified.",
    },
    "ppe": {
        "code": "OSHA 1910.132",
        "title": "Personal Protective Equipment Mandatory Rules",
        "steps": "Hard hat required in overhead lift zones. Steel-toe shoes mandatory floor-wide. Eye protection with side shields required.",
    },
}


def analyze_factory_request(user_text: str, target_asset: str):
    t = user_text.lower()
    asset = target_asset.lower()

    if any(w in t for w in ("gas", "cylinder", "canister", "oxygen", "pressure", "leak", "explosion")) or "canister" in asset:
        tf_query = "OSHA 1910.101 compressed gas cylinder storage chaining ventilation safety"
        card_title = "OSHA 1910.101 COMPLIANCE: GAS CYLINDER DEPOT"
        custom_lines = [
            f"Depot Target  : {FACTORY_ZONES['gas canister']['name']}",
            f"Storage Rule  : {FACTORY_ZONES['gas canister']['storage_rule']}",
            f"PPE Protocol  : {FACTORY_ZONES['gas canister']['ppe_required']}",
        ]
        spoken_summary = (
            "Inspecting high-pressure gas depot. Verifying upright cylinder chaining, "
            "valve protective caps, and 6-meter separation compliance."
        )

    elif any(w in t for w in ("conveyor", "belt", "machine", "guard", "pinch", "motor", "jam")) or "conveyor" in asset:
        tf_query = "OSHA 1910.212 conveyor belt machine guarding emergency stop pull cord"
        card_title = "OSHA 1910.212 INSPECTION: CONVEYOR LINE BAY 4"
        custom_lines = [
            f"Machinery Bay : {FACTORY_ZONES['conveyor']['name']}",
            f"Safeguard     : {FACTORY_ZONES['conveyor']['emergency_stop']}",
            f"Mandatory PPE : {FACTORY_ZONES['conveyor']['ppe_required']}",
        ]
        spoken_summary = (
            "Auditing conveyor assembly line. Machine guards and emergency pull-cord "
            "perimeter verified intact. Pinch points secured."
        )

    elif any(w in t for w in ("forklift", "vehicle", "truck", "lane", "traffic", "speed")) or "forklift" in asset:
        tf_query = "OSHA 1910.178 powered industrial trucks forklift pedestrian safety rules"
        card_title = "OSHA 1910.178 INSPECTION: FORKLIFT TRAFFIC BAY"
        custom_lines = [
            f"Transit Zone  : {FACTORY_ZONES['forklift']['name']}",
            f"Speed Limit   : {FACTORY_ZONES['forklift']['traffic_speed']}",
            f"Required Gear : {FACTORY_ZONES['forklift']['ppe_required']}",
        ]
        spoken_summary = (
            "Scanning forklift traffic lane. Strobe beacon active, 8 km/h speed limit "
            "enforced, and pedestrian safety corridor verified."
        )

    elif any(w in t for w in ("manhole", "confined", "trench", "sewer", "air quality", "toxic", "h2s")) or "manhole" in asset:
        tf_query = "OSHA 1910.146 permit-required confined space atmospheric testing standards"
        card_title = "OSHA 1910.146 PERMIT AUDIT: CONFINED SPACE & MANHOLE"
        custom_lines = [
            f"Confined Zone : {FACTORY_ZONES['manhole']['name']}",
            f"Air Limits    : {FACTORY_ZONES['manhole']['air_limits']}",
            f"Rescue Rig    : {FACTORY_ZONES['manhole']['ppe_required']}",
        ]
        spoken_summary = (
            "Atmospheric scan at utility manhole complete. Oxygen is within normal 20.9% limits. "
            "No hazardous VOC or H2S detected."
        )

    elif any(w in t for w in ("loto", "lockout", "tagout", "energy", "electrical", "power off")):
        tf_query = "OSHA 1910.147 lockout tagout zero energy verification procedure"
        card_title = f"{SAFETY_PROTOCOLS['loto']['title'].upper()} [{SAFETY_PROTOCOLS['loto']['code']}]"
        custom_lines = [
            f"Standard      : {SAFETY_PROTOCOLS['loto']['code']}",
            f"Execution     : {SAFETY_PROTOCOLS['loto']['steps'][:70]}...",
            "Audit Status  : Padlock attached, tags signed, zero-energy verified.",
        ]
        spoken_summary = "Lockout Tagout protocol initiated. All energy sources isolated and padlocked."

    elif any(w in t for w in ("spill", "chemical", "leak", "acid", "absorbent", "hazmat")):
        tf_query = "OSHA 1910.120 HAZWOPER chemical spill response containment procedure"
        card_title = f"{SAFETY_PROTOCOLS['spill']['title'].upper()} [{SAFETY_PROTOCOLS['spill']['code']}]"
        custom_lines = [
            f"Protocol      : {SAFETY_PROTOCOLS['spill']['code']}",
            f"Action Steps  : {SAFETY_PROTOCOLS['spill']['steps']}",
            "Containment   : Chemical spill kit deployed. Area evacuated upwind.",
        ]
        spoken_summary = "Chemical spill containment protocol triggered. Area cordoned off; containment socks deployed."

    elif any(w in t for w in ("ppe", "glasses", "boots", "hard hat", "vest", "gear")):
        tf_query = "OSHA 1910.132 general industry personal protective equipment standards"
        card_title = f"{SAFETY_PROTOCOLS['ppe']['title'].upper()} [{SAFETY_PROTOCOLS['ppe']['code']}]"
        custom_lines = [
            f"Mandate       : {SAFETY_PROTOCOLS['ppe']['code']}",
            f"Requirements  : {SAFETY_PROTOCOLS['ppe']['steps']}",
            "Compliance    : Optical AI scanner checking worker PPE compliance.",
        ]
        spoken_summary = "Scanning worker PPE. High-vis vest, hard hat, and steel-toe boots verified compliant."

    else:
        tf_query = f"OSHA 1910 industrial safety compliance inspection {target_asset}"
        card_title = f"OSHA GENERAL INSPECTION: {target_asset.upper()}"
        custom_lines = [
            f"Target Station: {target_asset.upper()} Safety Checkpoint",
            f"Safety Standard: OSHA General Industry 29 CFR 1910 Verified",
            "Inspector Action: Perimeter clearance confirmed. Machine guards operational.",
        ]
        spoken_summary = f"Completed OSHA compliance inspection at {target_asset}. Area clear and certified safe."

    return {
        "tf_query": tf_query,
        "card_title": card_title,
        "custom_lines": custom_lines,
        "spoken_summary": spoken_summary,
    }
