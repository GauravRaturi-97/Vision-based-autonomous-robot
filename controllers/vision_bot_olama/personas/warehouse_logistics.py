"""
personas/warehouse_logistics.py
Official Knowledge Base & Fleet Logistics Engine for AURA Logistics Warehouse.
Provides ground-truth inventory manifests, pallet load ratings, aisle clearance standards,
WMS tracking, and integrates TinyFish for live supply-chain and OSHA material handling lookups.
"""

PERSONA_CONFIG = {
    "key": "WAREHOUSE_LOGISTICS",
    "name": "Logistics-Bot (Fleet Runner)",
    "voice_rate": 188,
    "greeting": "Logistics-Bot active. Ready for multi-stop warehouse dispatch, manifest tracking, and pallet routing.",
    "customer_word": "operator",
    "arrival_person_msg": "Arrived at warehouse operator. Manifest ready for handoff and barcode validation!",
    "arrival_landmark_fmt": "Reached {target} station. Logging inventory checkpoint and aisle clearance.",
    "tinyfish_query_fmt": "warehouse supply chain material handling standard {target}",
    "hud_theme_bgr": (24, 18, 18),
    "accent_bgr": (255, 200, 90),
}

INVENTORY_MANIFEST = {
    "oil barrel": {
        "sku": "SKU-OIL-208L",
        "name": "Industrial Lubricant Drum (55 Gallon / 208L)",
        "unit_weight_kg": 215,
        "hazard_class": "Class 9 Environmentally Hazardous / Flammable III",
        "packaging": "UN 1A1 tight-head steel drum with tamper-evident bung seal",
        "storage_rule": "Secondary containment sump required; max 3 drums per pallet; 1.5m aisle clearance",
        "standard": "OSHA 1910.106 & NFPA 30 Flammable and Combustible Liquids Code",
    },
    "wooden box": {
        "sku": "SKU-CRATE-HD",
        "name": "Heavy-Duty Pine Shipping Crate",
        "unit_weight_kg": 180,
        "hazard_class": "Non-Hazardous Solid Freight",
        "packaging": "ISPM-15 heat-treated certified pine, steel banded",
        "storage_rule": "Stack limit max 3 tiers high; interlocking corner blocks",
        "standard": "ASTM D6251 Standard Specification for Wood-Cleated Shipping Boxes",
    },
    "wooden pallet": {
        "sku": "SKU-PALLET-EUR",
        "name": "EUR-1 / GMA Heavy Wooden Pallet Stack",
        "unit_weight_kg": 125,
        "hazard_class": "Logistics Platform",
        "packaging": "5-unit stacked nestable hardwood pallets (1200 x 800 mm)",
        "storage_rule": "Static load rating 4000 kg; dynamic load rating 1500 kg; inspect bottom deckboards",
        "standard": "ISO 6780 & ANSI MH1 Flat Pallets for Material Handling",
    },
    "cardboard box": {
        "sku": "SKU-CARTON-EXP",
        "name": "Double-Wall Corrugated Export Carton",
        "unit_weight_kg": 25,
        "hazard_class": "General Merchandise",
        "packaging": "200 PSI burst test, recyclable kraft fiberboard",
        "storage_rule": "Store on pallet platforms at least 10 cm above floor; humidity < 65%",
        "standard": "ASTM D5118 Standard Practice for Fabrication of Fiberboard Shipping Boxes",
    },
}

FLEET_ZONES = {
    "loading dock": {
        "name": "Bay A1 Outbound Logistics Dock",
        "equipment": "Hydraulic dock leveler, dock seal, wheel chocks, green/red LED signal",
        "procedure": "Verify trailer wheel chocks locked before forklift or robot enters container bed.",
    },
    "aisle 1": {
        "name": "North High-Density Racking Corridor",
        "spec": "Clearance width 1.35m; overhead sprinkler clearance minimum 45 cm",
        "speed": "Autonomous transit speed capped at 1.8 m/s with continuous LiDAR obstacle sweep",
    },
    "aisle 2": {
        "name": "Central Heavy Freight Highway",
        "spec": "Bidirectional heavy transit aisle, width 1.60m; yellow pedestrian boundary stripes",
        "speed": "Standard cruising speed 2.5 m/s; sound horn at intersection with Aisle 1",
    },
    "aisle 3": {
        "name": "Hazardous Material & Drum Storage Bay",
        "spec": "Epoxy-sealed containment floor with 110% capacity drainage sump",
        "speed": "Restricted crawl speed 1.2 m/s; proximity sensor threshold set to 0.65m",
    },
    "counter": {
        "name": "WMS Dispatch & Barcode Handoff Desk",
        "equipment": "Zebra industrial barcode printer, RFID portal antenna, packing slip terminal",
        "procedure": "Scan barcode manifest, verify piece count, and issue digital bill of lading.",
    },
    "stairs": {
        "name": "Mezzanine Access Stairway",
        "spec": "Anti-slip tread, safety kickplates, maximum distributed load 250 kg",
        "procedure": "Keep stairway entrance clear of pallets, boxes, and mobile AGVs at all times.",
    },
}


def analyze_warehouse_request(user_text: str, target_asset: str):
    t = user_text.lower()
    asset = target_asset.lower()

    ordered_manifest = []
    for key, item in INVENTORY_MANIFEST.items():
        if key in t or key in asset:
            ordered_manifest.append(item)

    if any(w in t for w in ("oil", "barrel", "drum", "hazardous", "chemical", "lube")) or "barrel" in asset:
        item = INVENTORY_MANIFEST["oil barrel"]
        tf_query = "OSHA 1910.106 oil barrel drum secondary containment storage rules warehouse"
        card_title = "WMS LOGISTICS MANIFEST: OIL BARREL DRUMS (208L)"
        custom_lines = [
            f"Item / SKU   : {item['name']} ({item['sku']})",
            f"Hazard Spec  : {item['hazard_class']} | Net Weight: {item['unit_weight_kg']} kg",
            f"Containment  : {item['storage_rule']}",
        ]
        spoken_summary = (
            f"Dispatching to {target_asset}. 55-gallon oil drum manifest verified. "
            f"Weight is 215 kg with secondary spill containment compliance."
        )

    elif any(w in t for w in ("pallet", "skid", "stack", "weight limit", "capacity")) or "pallet" in asset or "load" in t.split():
        item = INVENTORY_MANIFEST["wooden pallet"]
        tf_query = "ANSI MH1 pallet load capacity warehouse rack storage weight limits"
        card_title = "SUPPLY CHAIN MANIFEST: PALLET STACK INVENTORY"
        custom_lines = [
            f"Platform Type: {item['name']} ({item['sku']})",
            f"Rating Specs : Static: 4000 kg | Dynamic: 1500 kg capacity",
            f"Standard     : {item['standard']}",
        ]
        spoken_summary = (
            "Auditing wooden pallet stack. EUR-1 hardwood platform verified. "
            "Dynamic load capacity is 1500 kilograms with safe floor stacking."
        )

    elif any(w in t for w in ("crate", "wooden box", "boxes", "box", "cargo", "pack")) or "box" in asset or "crate" in asset:
        item = INVENTORY_MANIFEST["wooden box"]
        tf_query = "ASTM D6251 wooden shipping box crate stacking weight limits warehouse"
        card_title = f"FREIGHT DISPATCH TICKET -> {target_asset.upper()}"
        custom_lines = [
            f"Cargo Class  : {item['name']} ({item['sku']})",
            f"Gross Weight : Approx {item['unit_weight_kg']} kg | Rating: {item['packaging']}",
            f"Stacking Rule: {item['storage_rule']}",
        ]
        spoken_summary = (
            f"Moving cargo crates to {target_asset}. Gross weight is 180 kilograms. "
            "Three-tier stacking limit verified safe."
        )

    elif any(w in t for w in ("dock", "loading", "truck", "trailer", "entrance", "shipment")) or "entrance" in asset or "dock" in asset:
        tf_query = "OSHA 1910.178 loading dock trailer wheel chocks dock leveler safety standard"
        card_title = "LOADING DOCK LOGISTICS: BAY A1 OUTBOUND"
        custom_lines = [
            f"Dock Station : {FLEET_ZONES['loading dock']['name']}",
            f"Safety Gear  : {FLEET_ZONES['loading dock']['equipment']}",
            f"SOP Checklist: {FLEET_ZONES['loading dock']['procedure']}",
        ]
        spoken_summary = (
            "Arriving at loading dock bay. Trailer wheel chocks and hydraulic dock leveler "
            "are engaged. Ready for cargo loading."
        )

    elif any(w in t for w in ("manifest", "inventory", "sku", "stock", "count", "wms", "scan")):
        tf_query = "warehouse inventory management system cycle counting barcode accuracy standard"
        card_title = "AURA WMS INVENTORY AUDIT & CYCLE COUNT"
        custom_lines = [
            "Stock Status : 12x Oil Drums (Bay 3) | 16x Heavy Crates | 24x EUR Pallets",
            "WMS Sync     : Inventory accuracy 99.8% | Real-time RFID tracking active",
            "Dispatch Hub : Main logistics counter (Zebra RF gateway connected)",
        ]
        spoken_summary = (
            "Inventory cycle count complete. All 12 oil barrels and 16 cargo crates "
            "are matched to the active WMS manifest with 99.8% accuracy."
        )

    elif any(w in t for w in ("forklift", "aisle", "traffic", "speed", "clearance")):
        tf_query = "ISO 3691 industrial truck automated guided vehicle aisle clearance standard"
        card_title = "AISLE NAVIGATION & FLEET CLEARANCE REPORT"
        custom_lines = [
            f"Aisle Specs  : {FLEET_ZONES['aisle 2']['spec']}",
            f"Traffic Rule : {FLEET_ZONES['aisle 2']['speed']}",
            "LiDAR Status : Dual Hokuyo lasers running real-time 240-degree safety envelope.",
        ]
        spoken_summary = (
            "Aisle clearance verified. Fleet runner maintaining safe pedestrian separation "
            "and 1.6-meter travel corridor."
        )

    elif ordered_manifest:
        item = ordered_manifest[0]
        tf_query = f"{item['standard']} {item['name']} logistics handling"
        card_title = f"INVENTORY DISPATCH -> {target_asset.upper()}"
        custom_lines = [
            f"Target Item  : {item['name']} ({item['sku']})",
            f"Specification: Weight {item['unit_weight_kg']} kg | {item['packaging']}",
            f"Safety Rule  : {item['storage_rule']}",
        ]
        spoken_summary = f"Routing {item['name']} to {target_asset}. Manifest logged and verified."

    else:
        tf_query = f"warehouse logistics material handling standard {target_asset}"
        card_title = f"WAREHOUSE FLEET DISPATCH: {target_asset.upper()}"
        custom_lines = [
            f"Target Zone  : {target_asset.upper()} Logistics Station",
            "Fleet Status : Autonomous Runner in transit with active LiDAR envelope.",
            f"Checkstation : Verified at {FLEET_ZONES.get('counter', {}).get('name', 'Dispatch Desk')}",
        ]
        spoken_summary = f"Arrived at {target_asset} logistics station. Station verified and logged into WMS."

    return {
        "tf_query": tf_query,
        "card_title": card_title,
        "custom_lines": custom_lines,
        "spoken_summary": spoken_summary,
    }
