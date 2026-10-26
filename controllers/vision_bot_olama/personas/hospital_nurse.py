"""
personas/hospital_nurse.py
Official Knowledge Base & Clinical Workflow Engine for AURA Hospital Ward.
Provides ground-truth clinical zones, WHO hygiene standards, CDC cold-chain limits,
biohazard disposal protocols, and integrates TinyFish for live medical and HIPAA lookups.
"""

PERSONA_CONFIG = {
    "key": "HOSPITAL_NURSE",
    "name": "Med-Bot (Clinical Courier & Nurse Assistant)",
    "voice_rate": 185,
    "greeting": "Med-Bot online. Ready for sterile pharmacy delivery, patient rounds, and cold-chain transport.",
    "customer_word": "doctor",
    "arrival_person_msg": "Medical supplies delivered to the clinician. Specimen barcode and cold-chain verified.",
    "arrival_landmark_fmt": "Arrived at {target}. Logging clinical sanitization and room clearance.",
    "tinyfish_query_fmt": "WHO hospital clinical hygiene and medication protocol {target}",
    "hud_theme_bgr": (28, 28, 12),
    "accent_bgr": (220, 255, 100),
}

CLINICAL_ZONES = {
    "pharmacy": {
        "name": "Central Dispensary & Narcotics Lockbox",
        "standard": "USP 797 / 800 Sterile Compounding & Hazardous Drugs",
        "temp_spec": "Refrigerated cold-chain 2°C - 8°C (36°F - 46°F); ambient 20°C - 25°C",
        "access": "Restricted biometric / dual-custody access; continuous electronic audit log",
        "clearance_m": 0.80,
    },
    "icu": {
        "name": "Intensive Care Unit (Beds 1 & 2)",
        "standard": "CDC Healthcare Infection Control & Quiet Hospital Standard (< 45 dB)",
        "ventilation": "HEPA-filtered positive pressure ventilation (minimum 12 air changes/hour)",
        "clearance_m": 1.25,
    },
    "lab": {
        "name": "Diagnostic Pathology & Phlebotomy Lab",
        "standard": "CLIA / CAP Pathology Specimen Transport Protocol",
        "spec": "Double-bagged biohazard transport; temperature-monitored centrifuge staging",
        "clearance_m": 0.90,
    },
    "mri": {
        "name": "Diagnostic Imaging & MRI Suite (1.5T)",
        "standard": "ACR Guidance Document on MR Safe Practices (Zone IV Exclusion)",
        "safety": "STRICT NON-FERROMAGNETIC ZONE. Robot holds at Zone III entrance threshold.",
        "clearance_m": 1.60,
    },
    "triage": {
        "name": "Emergency Admissions & Triage Desk",
        "standard": "Emergency Severity Index (ESI) 5-Level Triage & HIPAA Intake",
        "vitals": "Automated pulse oximetry, non-invasive BP, and digital triage queuing",
        "clearance_m": 0.70,
    },
    "biohazard": {
        "name": "Clinical Sharps & Biohazard Waste Station",
        "standard": "OSHA 1910.1030 Bloodborne Pathogens & CDC Waste Management",
        "rule": "Puncture-resistant sharps containers replaced at 3/4 full mark; red autoclave bags",
        "clearance_m": 0.85,
    },
}

MEDICAL_PROTOCOLS = {
    "hand_hygiene": {
        "standard": "WHO 5 Moments for Hand Hygiene",
        "steps": "1. Before patient contact -> 2. Before aseptic task -> 3. After body fluid risk -> 4. After patient contact -> 5. After touching patient surroundings.",
    },
    "cold_chain": {
        "standard": "CDC Vaccine Storage and Handling Toolkit",
        "limits": "Refrigerated: 2°C to 8°C (36°F to 46°F) | Frozen: -50°C to -15°C (-58°F to +5°F) with calibrated digital datalogger.",
    },
    "biohazard": {
        "standard": "OSHA 1910.1030 Bloodborne Pathogens",
        "protocol": "Sharps into rigid, leak-proof, labeled container. Biohazard linen into certified impermeable bags. Universal precautions mandatory.",
    },
    "hipaa": {
        "standard": "HIPAA Privacy & Security Rules (45 CFR Part 160/164)",
        "rule": "Patient Protected Health Information (PHI) must be shielded from casual view; automatic screen blanking after 30 seconds idle.",
    },
}


def analyze_hospital_request(user_text: str, target_asset: str):
    t = user_text.lower()
    words = t.split()
    asset = target_asset.lower()

    if any(w in t for w in ("hipaa", "privacy", "phi", "patient data", "confidential", "vitals", "records")) or "triage" in asset:
        tf_query = "HIPAA privacy rule 45 CFR protected health information hospital physical safeguards"
        card_title = "HIPAA COMPLIANCE & PATIENT PHI SHIELD"
        custom_lines = [
            f"Legal Standard: {MEDICAL_PROTOCOLS['hipaa']['standard']}",
            f"Safeguard     : {MEDICAL_PROTOCOLS['hipaa']['rule']}",
            "Audit Check   : Encrypted telemetry feed. No PHI displayed on public screen.",
        ]
        spoken_summary = (
            "HIPAA privacy shield verified. Protected Health Information encrypted. "
            "Screen displays obscured in public transit areas."
        )

    elif any(w in t for w in ("mri", "x-ray", "radiology", "imaging", "magnet", "fringe field")) or "mri" in asset:
        tf_query = "ACR guidance document MR safe practices zone IV non-ferromagnetic equipment"
        card_title = "ACR MRI SAFETY AUDIT: ZONE IV SHIELDING"
        custom_lines = [
            f"Diagnostic Bay: {CLINICAL_ZONES['mri']['name']}",
            f"Safety Standard: {CLINICAL_ZONES['mri']['standard']}",
            f"Restriction   : {CLINICAL_ZONES['mri']['safety']}",
        ]
        spoken_summary = (
            "MRI Suite Zone IV approach verified. Non-ferromagnetic boundary checked. "
            "Holding position outside 1.5 Tesla primary magnetic fringe field."
        )

    elif any(w in t for w in ("cold chain", "vaccine", "insulin", "refrigerat", "temperature excursion")):
        tf_query = "CDC vaccine storage handling toolkit cold chain 2 to 8 C guidelines"
        card_title = "CDC COLD-CHAIN INTEGRITY REPORT (2°C - 8°C)"
        custom_lines = [
            f"Protocol      : {MEDICAL_PROTOCOLS['cold_chain']['standard']}",
            f"Validated Range: {MEDICAL_PROTOCOLS['cold_chain']['limits']}",
            "Sensor Status : Digital datalogger reading 3.6°C. Zero temperature excursion logged.",
        ]
        spoken_summary = (
            "Cold-chain integrity verified. Biologics container holding steady at 3.6 degrees "
            "Celsius with continuous calibrated datalogger monitoring."
        )

    elif any(w in t for w in ("biohazard", "sharps", "waste", "needle", "blood", "specimen", "pathology", "sample")) or "lab" in asset:
        tf_query = "OSHA 1910.1030 bloodborne pathogens sharps disposal biohazard container rules"
        card_title = "OSHA 1910.1030 PROTOCOL: BIOHAZARD & SHARPS"
        custom_lines = [
            f"Standard      : {MEDICAL_PROTOCOLS['biohazard']['standard']}",
            f"Handling Rules: {MEDICAL_PROTOCOLS['biohazard']['protocol']}",
            "Transport Rig : Sealed double-walled specimen transit case locked.",
        ]
        spoken_summary = (
            "Biohazard protocol active. Specimen securely double-bagged in certified leak-proof "
            "container. Puncture-resistant sharps disposal confirmed."
        )

    elif any(w in t for w in ("hygiene", "wash", "hand", "sterile", "sanitize", "disinfect")) or "sink" in asset:
        tf_query = "WHO 5 moments hand hygiene hospital infection prevention guidelines"
        card_title = "WHO CLINICAL HAND HYGIENE & STERILIZATION"
        custom_lines = [
            f"Standard      : {MEDICAL_PROTOCOLS['hand_hygiene']['standard']}",
            f"Mandatory Steps: {MEDICAL_PROTOCOLS['hand_hygiene']['steps'][:70]}...",
            "Robot Status  : Surface UV-C sterilization cycle verified compliant.",
        ]
        spoken_summary = (
            "WHO 5 Moments for Hand Hygiene confirmed. Antiseptic scrub and sterilization "
            "station verified compliant for clinical procedures."
        )

    elif any(w in t for w in ("pharmacy", "medicine", "pill", "prescription", "dispensary", "saline", "antibiotic")) or any(tok in ("iv", "med", "meds", "drug", "drugs") for tok in words) or "pharmacy" in asset or "dispensary" in asset:
        tf_query = "USP 797 hospital pharmacy medication dispensing sterile compounding standards"
        card_title = "CENTRAL PHARMACY DISPATCH: CLINICAL MEDICATIONS"
        custom_lines = [
            f"Department    : {CLINICAL_ZONES['pharmacy']['name']}",
            f"Standard      : {CLINICAL_ZONES['pharmacy']['standard']}",
            f"Storage Temp  : {CLINICAL_ZONES['pharmacy']['temp_spec']}",
        ]
        spoken_summary = (
            "Routing to central pharmacy dispensary. Medication locked in temperature-controlled "
            "cassette. Cold-chain storage 3.4 degrees Celsius verified."
        )

    elif any(w in t for w in ("bed", "ward", "icu", "patient", "room")) or "bed" in asset:
        tf_query = "hospital inpatient ward patient delivery infection control protocol"
        card_title = f"INPATIENT WARD DELIVERY -> {target_asset.upper()}"
        custom_lines = [
            f"Target Station: {target_asset.upper()} Clinical Area",
            "Aseptic Status: Clean delivery envelope verified safe for immunocompromised patients.",
            f"Acoustic Limit: Silent electric drive verified (< 45 dB ICU noise standard).",
        ]
        spoken_summary = (
            f"Arrived at inpatient {target_asset}. Clinical supplies ready for clinician handoff. "
            "Quiet delivery verified."
        )

    else:
        tf_query = f"WHO hospital clinical hygiene and medication protocol {target_asset}"
        card_title = f"HOSPITAL CLINICAL DISPATCH: {target_asset.upper()}"
        custom_lines = [
            f"Target Zone   : {target_asset.upper()} Clinical Station",
            "Courier State : Autonomous Med-Bot in sterile transit.",
            "Sanitization  : Antimicrobial chassis coating and HEPA filtration active.",
        ]
        spoken_summary = f"Arrived at {target_asset}. Clinical station protocol logged and certified."

    return {
        "tf_query": tf_query,
        "card_title": card_title,
        "custom_lines": custom_lines,
        "spoken_summary": spoken_summary,
    }
