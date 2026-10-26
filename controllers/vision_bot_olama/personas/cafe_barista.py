"""
personas/cafe_barista.py
Official Knowledge Base & Hospitality Engine for AURA Smart Cafe.
Provides ground-truth Menu, Pricing (INR), Allergen, Wi-Fi, and Facility facts
and integrates TinyFish for live web nutrition/health searches.
"""

PERSONA_CONFIG = {
    "key": "CAFE_WAITER",
    "name": "Barista-Bot (Smart Cafe Waiter)",
    "voice_rate": 188,
    "greeting": "Welcome to AURA Cafe! I am Barista-Bot, your automated table runner. How can I serve you today?",
    "customer_word": "guest",
    "arrival_person_msg": "Here is your fresh order from the barista counter! Enjoy your time at AURA Cafe!",
    "arrival_landmark_fmt": "Arrived at {target}! Ready for staff service.",
    "hud_theme_bgr": (30, 22, 14),
    "accent_bgr": (80, 215, 255),
}

# --- Official AURA Cafe Menu, Prices (INR), Calories & Diet Tags ---
CAFE_MENU = {
    "espresso": {
        "name": "Double Espresso",
        "category": "Coffee",
        "price_inr": 140,
        "kcal": 10,
        "caffeine_mg": 150,
        "diet": "Vegan, Keto, Sugar-Free",
    },
    "cappuccino": {
        "name": "Artisan Cappuccino",
        "category": "Coffee",
        "price_inr": 180,
        "kcal": 120,
        "caffeine_mg": 75,
        "diet": "Vegetarian (Contains Dairy; Oat/Almond milk +Rs.30)",
    },
    "latte": {
        "name": "Hazelnut Cafe Latte",
        "category": "Coffee",
        "price_inr": 200,
        "kcal": 160,
        "caffeine_mg": 75,
        "diet": "Vegetarian (Contains Dairy & Hazelnut syrup)",
    },
    "matcha": {
        "name": "Iced Oat Matcha Latte",
        "category": "Tea / Specialty",
        "price_inr": 240,
        "kcal": 135,
        "caffeine_mg": 65,
        "diet": "100% Vegan, Dairy-Free, Gluten-Free",
    },
    "cold brew": {
        "name": "Nitro Cold Brew",
        "category": "Coffee",
        "price_inr": 210,
        "kcal": 15,
        "caffeine_mg": 170,
        "diet": "Vegan, Sugar-Free, Low-Calorie",
    },
    "chai": {
        "name": "Himalayan Masala Chai",
        "category": "Tea / Specialty",
        "price_inr": 120,
        "kcal": 110,
        "caffeine_mg": 45,
        "diet": "Vegetarian, Spiced",
    },
    "hot chocolate": {
        "name": "Belgian Hot Chocolate",
        "category": "Specialty",
        "price_inr": 190,
        "kcal": 240,
        "caffeine_mg": 10,
        "diet": "Vegetarian, Kids Favorite",
    },
    "croissant": {
        "name": "Butter Croissant",
        "category": "Bakery",
        "price_inr": 160,
        "kcal": 260,
        "caffeine_mg": 0,
        "diet": "Fresh Baked (Contains Dairy & Gluten)",
    },
    "muffin": {
        "name": "Blueberry Muffin",
        "category": "Bakery",
        "price_inr": 150,
        "kcal": 280,
        "caffeine_mg": 0,
        "diet": "Vegetarian",
    },
    "sandwich": {
        "name": "Grilled Pesto Club Sandwich",
        "category": "Food",
        "price_inr": 220,
        "kcal": 340,
        "caffeine_mg": 0,
        "diet": "High-Protein Vegetarian",
    },
}

CAFE_FACILITIES = {
    "wifi_ssid": "AURA_Cafe_Guest",
    "wifi_pass": "BrewAI2026",
    "website": "https://www.auracafe-hackinhills.in",
    "hours": "8:00 AM - 11:00 PM Daily",
    "restroom": "Located in the South-East corner (Teal Door past Table 3).",
    "reception": "Located at the Main North Entrance door.",
}


def analyze_cafe_request(user_text: str, target_asset: str):
    t = user_text.lower()

    ordered_items = []
    for key, item in CAFE_MENU.items():
        if key in t:
            ordered_items.append(item)

    if any(w in t for w in ("bathroom", "washroom", "restroom", "toilet", "loo")) or target_asset == "bathroom":
        tf_query = "restaurant customer restroom hygiene sanitation standards"
        card_title = "AURA CAFE CONCIERGE: RESTROOM & HYGIENE"
        custom_lines = [
            f"Restroom Location: {CAFE_FACILITIES['restroom']}",
            f"Guest Wi-Fi     : Network '{CAFE_FACILITIES['wifi_ssid']}' (Password: {CAFE_FACILITIES['wifi_pass']})",
            f"Operating Hours : {CAFE_FACILITIES['hours']}",
        ]
        spoken_summary = "The washroom is located in the south-east corner with the teal door. Follow me, I am taking you there!"

    elif any(w in t for w in ("wifi", "wi-fi", "internet", "password")):
        tf_query = "coffee shop guest wifi cybersecurity best practices"
        card_title = "AURA CAFE GUEST WI-FI ACCESS"
        custom_lines = [
            f"Network Name : {CAFE_FACILITIES['wifi_ssid']}",
            f"Wi-Fi Password: {CAFE_FACILITIES['wifi_pass']}",
            f"Website      : {CAFE_FACILITIES['website']}",
        ]
        spoken_summary = f"Our guest Wi-Fi is {CAFE_FACILITIES['wifi_ssid']} with password {CAFE_FACILITIES['wifi_pass']}."

    elif any(w in t for w in ("website", "online", "url", "portal")):
        tf_query = "smart cafe online ordering automated table delivery"
        card_title = "AURA CAFE OFFICIAL WEBSITE & RESERVATIONS"
        custom_lines = [
            f"Website URL : {CAFE_FACILITIES['website']}",
            f"Store Hours : {CAFE_FACILITIES['hours']}",
            "Online Perks: Mobile table reservations, digital loyalty stamp card.",
        ]
        spoken_summary = f"You can explore our full digital menu and reservations at {CAFE_FACILITIES['website']}."

    elif any(w in t for w in ("menu", "price", "prices", "cost", "how much", "rate", "recommend", "vegan", "calorie")):
        tf_query = "specialty cafe espresso cappuccino matcha croissant pricing nutrition"
        card_title = "AURA CAFE OFFICIAL MENU & PRICING (INR)"
        custom_lines = [
            "Hot Drinks : Espresso (Rs.140) | Cappuccino (Rs.180) | Hazelnut Latte (Rs.200) | Chai (Rs.120)",
            "Cold & Tea : Iced Oat Matcha (Rs.240, Vegan) | Nitro Cold Brew (Rs.210) | Hot Cocoa (Rs.190)",
            "Bakery/Food: Butter Croissant (Rs.160) | Blueberry Muffin (Rs.150) | Pesto Sandwich (Rs.220)",
        ]
        spoken_summary = (
            "Here are our top menu prices: Espresso is 140 rupees, Cappuccino is 180, "
            "Vegan Oat Matcha is 240, and fresh Butter Croissants are 160 rupees!"
        )

    elif ordered_items:
        names_str = " + ".join(i["name"] for i in ordered_items)
        total_bill = sum(i["price_inr"] for i in ordered_items)
        total_kcal = sum(i["kcal"] for i in ordered_items)
        total_caff = sum(i["caffeine_mg"] for i in ordered_items)

        tf_query = f"{ordered_items[0]['name']} nutrition facts calories caffeine health benefits"
        card_title = f"TABLE DELIVERY ORDER TICKET -> {target_asset.upper()}"
        custom_lines = [
            f"Items Ordered : {names_str}",
            f"Bill Amount   : Rs. {total_bill} (incl. taxes)  |  Destination: {target_asset.upper()}",
            f"Nutrition Data: {total_kcal} kcal  |  Caffeine: {total_caff}mg  |  Diet: {ordered_items[0]['diet']}",
        ]
        spoken_summary = (
            f"Delivering {names_str} to {target_asset}! Total bill is {total_bill} rupees, "
            f"with {total_kcal} calories."
        )

    else:
        tf_query = f"cafe table runner service hospitality standards {target_asset}"
        card_title = f"CAFE FLOOR DISPATCH: {target_asset.upper()}"
        custom_lines = [
            f"Target Station: {target_asset.upper()} Area",
            "Staff Action  : Automated Table Runner Checkpoint verified.",
            f"Amenities     : Wi-Fi '{CAFE_FACILITIES['wifi_ssid']}' | Restroom: South-East Door",
        ]
        spoken_summary = f"Arrived at {target_asset}! Station service verified."

    return {
        "tf_query": tf_query,
        "card_title": card_title,
        "custom_lines": custom_lines,
        "spoken_summary": spoken_summary,
    }