"""
Demo data seeder -- generates realistic synthetic data for the Rann of Kutch region.
!!️  All data is labelled DEMO and is synthetic for demonstration purposes only.
Run: python seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
import random
from database import Base, engine, SessionLocal
from models.models import (
    User, TouristProfile, Destination, TouristLoad, EcologicalMetric,
    CarryingCapacity, Artisan, CommunityExperience, Alert,
    UserRole, DestinationCategory, PressureLevel, DestinationStatus, AlertSeverity
)
from utils.auth import hash_password

random.seed(42)


# ─── Destination Master Data ─────────────────────────────────────────────────

DESTINATIONS = [
    {
        "name": "White Rann, Dhordo",
        "local_name": "ધોળો રણ, ધોરડો",
        "location": "Dhordo, Kutch, Gujarat",
        "latitude": 23.8880, "longitude": 69.8750,
        "category": DestinationCategory.desert,
        "description": "The iconic White Rann of Kutch -- a vast salt desert that glows white under moonlight. Primary venue for Rann Utsav.",
        "popularity_score": 9.8,
        "ecological_sensitivity": 8.5,
        "estimated_capacity": 3000,
        "current_load": 2650,
        "water_pressure": 0.82,
        "waste_pressure": 0.78,
        "infrastructure_capacity": 0.88,
        "recommended_duration_hours": 4.0,
        "best_visiting_months": [11, 12, 1, 2],
        "community_opportunities": True,
        "current_status": DestinationStatus.encourage_alternatives,
        "sustainable_practices": "Stick to designated viewing zones; no plastic; guided vehicles only.",
    },
    {
        "name": "Kalo Dungar (Black Hill)",
        "local_name": "કાળો ડુંગર",
        "location": "Khavda, Kutch, Gujarat",
        "latitude": 23.9957, "longitude": 69.6918,
        "category": DestinationCategory.nature,
        "description": "Highest point in Kutch at 458 m. Offers panoramic views of the Great Rann and Pakistan border. Sacred Dattatreya temple on top.",
        "popularity_score": 7.2,
        "ecological_sensitivity": 7.0,
        "estimated_capacity": 800,
        "current_load": 310,
        "water_pressure": 0.40,
        "waste_pressure": 0.35,
        "infrastructure_capacity": 0.45,
        "recommended_duration_hours": 3.0,
        "best_visiting_months": [10, 11, 12, 1, 2, 3],
        "community_opportunities": False,
        "current_status": DestinationStatus.open,
        "sustainable_practices": "Carry out all waste; respect temple sanctity; no camping outside designated zones.",
    },
    {
        "name": "Banni Grasslands",
        "local_name": "બન્ની ઘાસના મેદાન",
        "location": "Banni, Kutch, Gujarat",
        "latitude": 23.7490, "longitude": 69.5830,
        "category": DestinationCategory.wildlife,
        "description": "One of Asia's largest tropical grasslands. Home to wild asses, flamingos, and diverse birdlife. Seasonal wetlands attract migratory birds.",
        "popularity_score": 6.5,
        "ecological_sensitivity": 9.2,
        "estimated_capacity": 500,
        "current_load": 120,
        "water_pressure": 0.60,
        "waste_pressure": 0.30,
        "infrastructure_capacity": 0.35,
        "recommended_duration_hours": 5.0,
        "best_visiting_months": [11, 12, 1, 2],
        "community_opportunities": True,
        "current_status": DestinationStatus.open,
        "sustainable_practices": "Wildlife zone -- no noise, no littering, stay on tracks, guided tours only.",
    },
    {
        "name": "Indian Wild Ass Sanctuary",
        "local_name": "ઘુડખર અભ્યારણ્ય",
        "location": "Little Rann of Kutch, Surendranagar",
        "latitude": 23.5000, "longitude": 71.3330,
        "category": DestinationCategory.wildlife,
        "description": "World's last refuge for the Indian Wild Ass (Ghudkhar). Also home to wolves, nilgai, flamingos, and pelicans.",
        "popularity_score": 7.8,
        "ecological_sensitivity": 9.8,
        "estimated_capacity": 400,
        "current_load": 250,
        "water_pressure": 0.55,
        "waste_pressure": 0.40,
        "infrastructure_capacity": 0.50,
        "recommended_duration_hours": 6.0,
        "best_visiting_months": [10, 11, 12, 1, 2, 3],
        "community_opportunities": False,
        "current_status": DestinationStatus.permit_required,
        "sustainable_practices": "Official permit required. Strict vehicle limits. No off-road driving.",
    },
    {
        "name": "Bhuj Heritage City",
        "local_name": "ભુજ",
        "location": "Bhuj, Kutch, Gujarat",
        "latitude": 23.2419, "longitude": 69.6669,
        "category": DestinationCategory.heritage,
        "description": "Historic capital of Kutch. Home to Aina Mahal, Prag Mahal, Kutch Museum, and vibrant handicraft markets.",
        "popularity_score": 8.5,
        "ecological_sensitivity": 2.5,
        "estimated_capacity": 5000,
        "current_load": 1800,
        "water_pressure": 0.45,
        "waste_pressure": 0.55,
        "infrastructure_capacity": 0.60,
        "recommended_duration_hours": 5.0,
        "best_visiting_months": [10, 11, 12, 1, 2, 3],
        "community_opportunities": True,
        "current_status": DestinationStatus.normal,
        "sustainable_practices": "Support local artisans; use public transport within city; respect heritage structures.",
    },
    {
        "name": "Mandvi Beach & Vijay Vilas Palace",
        "local_name": "માંડવી",
        "location": "Mandvi, Kutch, Gujarat",
        "latitude": 22.8352, "longitude": 69.3499,
        "category": DestinationCategory.heritage,
        "description": "Pristine beach town with a 400-year-old shipbuilding tradition. Summer palace of Kutch royals on the beach.",
        "popularity_score": 7.5,
        "ecological_sensitivity": 5.5,
        "estimated_capacity": 2000,
        "current_load": 650,
        "water_pressure": 0.40,
        "waste_pressure": 0.50,
        "infrastructure_capacity": 0.55,
        "recommended_duration_hours": 4.0,
        "best_visiting_months": [10, 11, 12, 1, 2, 3],
        "community_opportunities": True,
        "current_status": DestinationStatus.open,
        "sustainable_practices": "No plastic on beach; support traditional shipbuilders; purchase authentic local crafts.",
    },
    {
        "name": "Hodka Village",
        "local_name": "હોડ્કા ગામ",
        "location": "Hodka, Kutch, Gujarat",
        "latitude": 23.7220, "longitude": 69.8080,
        "category": DestinationCategory.village,
        "description": "Award-winning community tourism village. Famous for Rabari embroidery, mud-mirror work, and traditional Bhunga architecture.",
        "popularity_score": 6.8,
        "ecological_sensitivity": 4.5,
        "estimated_capacity": 300,
        "current_load": 80,
        "water_pressure": 0.35,
        "waste_pressure": 0.28,
        "infrastructure_capacity": 0.40,
        "recommended_duration_hours": 4.0,
        "best_visiting_months": [10, 11, 12, 1, 2, 3],
        "community_opportunities": True,
        "current_status": DestinationStatus.open,
        "sustainable_practices": "Community-led homestays only; purchase directly from artisans; respect local customs.",
    },
    {
        "name": "Rann Utsav Tent City",
        "local_name": "રણ ઉત્સવ",
        "location": "Dhordo, Kutch, Gujarat",
        "latitude": 23.8830, "longitude": 69.8700,
        "category": DestinationCategory.culture,
        "description": "Seasonal festival village from Nov–Feb. Cultural shows, folk music, food, and craft exhibitions celebrating Kutch heritage.",
        "popularity_score": 9.5,
        "ecological_sensitivity": 6.0,
        "estimated_capacity": 2500,
        "current_load": 2450,
        "water_pressure": 0.88,
        "waste_pressure": 0.85,
        "infrastructure_capacity": 0.95,
        "recommended_duration_hours": 8.0,
        "best_visiting_months": [11, 12, 1, 2],
        "community_opportunities": True,
        "current_status": DestinationStatus.restricted,
        "sustainable_practices": "Pre-booking essential. Limited daily permits. Carry water bottles.",
    },
    {
        "name": "Narayan Sarovar",
        "local_name": "નારાયણ સરોવર",
        "location": "Lakhpat, Kutch, Gujarat",
        "latitude": 23.7200, "longitude": 68.8350,
        "category": DestinationCategory.culture,
        "description": "One of five sacred Hindu lakes. Located near Lakhpat Fort with views of the Rann and creek.",
        "popularity_score": 5.8,
        "ecological_sensitivity": 6.5,
        "estimated_capacity": 1000,
        "current_load": 220,
        "water_pressure": 0.30,
        "waste_pressure": 0.35,
        "infrastructure_capacity": 0.40,
        "recommended_duration_hours": 3.0,
        "best_visiting_months": [10, 11, 12, 1, 2, 3],
        "community_opportunities": False,
        "current_status": DestinationStatus.open,
        "sustainable_practices": "Sacred site -- no plastic; respect pilgrims; no loud music.",
    },
    {
        "name": "Lakhpat Fort",
        "local_name": "લખપત કિલ્લો",
        "location": "Lakhpat, Kutch, Gujarat",
        "latitude": 23.8180, "longitude": 68.7760,
        "category": DestinationCategory.heritage,
        "description": "Ghost town fort on the creek mouth. 7-km intact fortification wall, Sikh Gurudwara, and colonial cemetery. Low tourist pressure.",
        "popularity_score": 5.2,
        "ecological_sensitivity": 3.5,
        "estimated_capacity": 600,
        "current_load": 70,
        "water_pressure": 0.20,
        "waste_pressure": 0.22,
        "infrastructure_capacity": 0.30,
        "recommended_duration_hours": 3.0,
        "best_visiting_months": [10, 11, 12, 1, 2, 3],
        "community_opportunities": False,
        "current_status": DestinationStatus.open,
        "sustainable_practices": "No climbing on ruins; carry own water; excellent off-the-beaten-path alternative.",
    },
    {
        "name": "Kutch Desert Wildlife Sanctuary",
        "local_name": "કચ્છ રણ અભ્યારણ્ય",
        "location": "Northern Kutch, Gujarat",
        "latitude": 23.9800, "longitude": 70.1100,
        "category": DestinationCategory.wildlife,
        "description": "Protects the Great Rann ecosystem including flamingo breeding grounds. Restricted access zone.",
        "popularity_score": 6.0,
        "ecological_sensitivity": 9.5,
        "estimated_capacity": 200,
        "current_load": 50,
        "water_pressure": 0.50,
        "waste_pressure": 0.25,
        "infrastructure_capacity": 0.25,
        "recommended_duration_hours": 4.0,
        "best_visiting_months": [11, 12, 1, 2],
        "community_opportunities": False,
        "current_status": DestinationStatus.permit_required,
        "sustainable_practices": "Forest dept permit mandatory. Restricted to designated areas. No photography of nesting flamingos.",
    },
    {
        "name": "Bhujodi Craft Village",
        "local_name": "ભૂજોડી",
        "location": "Bhujodi, Kutch, Gujarat",
        "latitude": 23.2070, "longitude": 69.7200,
        "category": DestinationCategory.handicraft,
        "description": "Living craft village near Bhuj. 100+ artisan families practising Kutchi weaving, embroidery, and block printing.",
        "popularity_score": 7.0,
        "ecological_sensitivity": 2.0,
        "estimated_capacity": 1000,
        "current_load": 280,
        "water_pressure": 0.28,
        "waste_pressure": 0.32,
        "infrastructure_capacity": 0.45,
        "recommended_duration_hours": 3.0,
        "best_visiting_months": [9, 10, 11, 12, 1, 2, 3],
        "community_opportunities": True,
        "current_status": DestinationStatus.open,
        "sustainable_practices": "Purchase directly from weavers; no bargaining on handmade goods; respect workshop spaces.",
    },
]

# ─── Artisan Data ─────────────────────────────────────────────────────────────

ARTISANS = [
    {
        "name": "Hajibhai Siddik",
        "bio": "Third-generation Rabari embroidery master from Hodka village. Specialises in traditional mirror-work (Abhla bharat).",
        "location": "Hodka, Kutch",
        "latitude": 23.7220, "longitude": 69.8080,
        "category": "Embroidery",
        "speciality": "Rabari Embroidery, Mirror Work (Abhla Bharat)",
    },
    {
        "name": "Shantaben Vankar",
        "bio": "Award-winning Kutchi weaver from Bhujodi. Her shawls are exhibited internationally.",
        "location": "Bhujodi, Kutch",
        "latitude": 23.2070, "longitude": 69.7200,
        "category": "Weaving",
        "speciality": "Kutchi Shawl Weaving, Mashru Fabric",
    },
    {
        "name": "Mamu Khan",
        "bio": "Manganiyar folk musician from Kutch. Performs traditional Sindhi-Kutchi songs on traditional instruments.",
        "location": "Bhuj, Kutch",
        "latitude": 23.2419, "longitude": 69.6669,
        "category": "Performing Arts",
        "speciality": "Manganiyar Folk Music, Khamaycha",
    },
    {
        "name": "Ramiben Khatri",
        "bio": "Ajrakh block printer, 5th generation. UNESCO-recognized craft of resist-print textile dyeing.",
        "location": "Dhamadka, Kutch",
        "latitude": 23.4100, "longitude": 70.0800,
        "category": "Block Printing",
        "speciality": "Ajrakh Block Printing, Natural Dye",
    },
    {
        "name": "Gafurbhai Khatri",
        "bio": "Bandhani tie-dye master from Mandvi. Uses 500-year-old family technique passed down through generations.",
        "location": "Mandvi, Kutch",
        "latitude": 22.8352, "longitude": 69.3499,
        "category": "Textile",
        "speciality": "Bandhani Tie-Dye, Traditional Odhni",
    },
    {
        "name": "Fatimaben Jat",
        "bio": "Mud-mirror wall art artist. Creates stunning Lippan kaam (mud mirror work) decorating traditional Bhunga homes.",
        "location": "Hodka, Kutch",
        "latitude": 23.7220, "longitude": 69.8080,
        "category": "Mud Art",
        "speciality": "Lippan Kaam (Mud Mirror Work), Bhunga Architecture Decoration",
    },
    {
        "name": "Karimbhai Memon",
        "bio": "Traditional dhow (ship) builder from Mandvi shipyard. Builds wooden sailing vessels using 400-year-old techniques.",
        "location": "Mandvi Shipyard, Kutch",
        "latitude": 22.8400, "longitude": 69.3600,
        "category": "Craft / Heritage",
        "speciality": "Traditional Dhow Shipbuilding",
    },
    {
        "name": "Dilipbhai Rabari",
        "bio": "Nature guide and homestay host in Banni grasslands. Expert in local ecology, bird identification, and pastoral culture.",
        "location": "Banni, Kutch",
        "latitude": 23.7490, "longitude": 69.5830,
        "category": "Eco Guide",
        "speciality": "Birdwatching Tours, Grassland Ecology, Pastoral Culture",
    },
]

EXPERIENCES = [
    ("Hajibhai Siddik", "Rabari Embroidery Workshop", "embroidery", 800, 8, 3.0, ["English", "Gujarati", "Hindi"]),
    ("Shantaben Vankar", "Weaving Demonstration & Shawl Purchase", "weaving", 500, 12, 2.5, ["Gujarati", "Hindi"]),
    ("Mamu Khan", "Manganiyar Folk Music Evening", "music", 1200, 20, 2.0, ["Gujarati", "Hindi", "Sindhi"]),
    ("Ramiben Khatri", "Ajrakh Block Print Workshop", "printing", 1000, 10, 4.0, ["English", "Gujarati"]),
    ("Gafurbhai Khatri", "Bandhani Tie-Dye Experience", "textile", 600, 10, 2.0, ["Gujarati", "Hindi"]),
    ("Fatimaben Jat", "Lippan Kaam (Mud Mirror Art) Session", "mud_art", 700, 6, 3.0, ["Gujarati"]),
    ("Karimbhai Memon", "Shipyard Heritage Walk", "heritage", 400, 15, 1.5, ["Gujarati", "Hindi"]),
    ("Dilipbhai Rabari", "Banni Grassland Eco Walk", "eco_tour", 900, 8, 5.0, ["English", "Gujarati"]),
]


def seed_users(db):
    users_data = [
        {"name": "Admin User", "email": "admin@kutchtourism.in", "role": UserRole.admin},
        {"name": "Priya Sharma", "email": "tourist@example.com", "role": UserRole.tourist},
        {"name": "Tourism Authority", "email": "authority@kutchtourism.in", "role": UserRole.authority},
        {"name": "Rann Eco Tours", "email": "operator@example.com", "role": UserRole.operator},
    ]
    created = []
    for ud in users_data:
        existing = db.query(User).filter_by(email=ud["email"]).first()
        if not existing:
            u = User(name=ud["name"], email=ud["email"],
                     password_hash=hash_password("password123"), role=ud["role"])
            db.add(u)
            db.flush()
            if ud["role"] == UserRole.tourist:
                profile = TouristProfile(
                    user_id=u.id,
                    preferences={"language": "en"},
                    budget="moderate",
                    interests=["desert", "culture", "handicraft"],
                    group_size=4,
                )
                db.add(profile)
            created.append(u)
    db.commit()
    print(f"  OK Seeded {len(created)} users")


def seed_destinations(db):
    created = 0
    for dd in DESTINATIONS:
        existing = db.query(Destination).filter_by(name=dd["name"]).first()
        if not existing:
            d = Destination(**dd, data_label="DEMO")
            db.add(d)
            created += 1
    db.commit()
    print(f"  OK Seeded {created} destinations")


def seed_tourist_loads(db):
    destinations = db.query(Destination).all()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    created = 0
    for dest in destinations:
        for days_back in range(90, -1, -1):  # 90 days history + today
            date = today - timedelta(days=days_back)
            existing = db.query(TouristLoad).filter_by(
                destination_id=dest.id, date=date).first()
            if existing:
                continue

            dow = date.weekday()
            month = date.month
            is_peak = month in dest.best_visiting_months
            is_weekend = dow in [5, 6]
            is_event = month in [11, 12, 1, 2] and dest.name in ["White Rann, Dhordo", "Rann Utsav Tent City"]

            base = dest.estimated_capacity * 0.35
            if is_peak:
                base *= 1.6
            if is_weekend:
                base *= 1.3
            if is_event:
                base *= 1.8
            actual = int(min(base + random.gauss(0, base * 0.1), dest.estimated_capacity))
            actual = max(actual, 0)
            predicted = int(actual * random.uniform(0.92, 1.08))

            tl = TouristLoad(
                destination_id=dest.id,
                date=date,
                actual_visitors=actual,
                predicted_visitors=predicted,
                day_of_week=dow,
                is_holiday=(dow in [5, 6]),
                is_event_period=is_event,
                weather_condition=random.choice(["sunny", "sunny", "sunny", "hazy", "windy"]),
                confidence_score=round(random.uniform(0.78, 0.94), 2),
                data_label="DEMO"
            )
            db.add(tl)
            created += 1

    db.commit()
    print(f"  OK Seeded {created} tourist load records")


def seed_ecological_metrics(db):
    destinations = db.query(Destination).all()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    created = 0
    for dest in destinations:
        for days_back in range(30, -1, -1):
            date = today - timedelta(days=days_back)
            existing = db.query(EcologicalMetric).filter_by(
                destination_id=dest.id, date=date).first()
            if existing:
                continue
            em = EcologicalMetric(
                destination_id=dest.id,
                date=date,
                water_stress=round(dest.water_pressure + random.uniform(-0.05, 0.05), 2),
                waste_stress=round(dest.waste_pressure + random.uniform(-0.05, 0.05), 2),
                infrastructure_stress=round(dest.infrastructure_capacity + random.uniform(-0.05, 0.05), 2),
                ecological_risk=round(dest.ecological_sensitivity / 10 + random.uniform(-0.03, 0.03), 2),
                data_label="DEMO"
            )
            db.add(em)
            created += 1
    db.commit()
    print(f"  OK Seeded {created} ecological metric records")


def seed_artisans(db):
    created = 0
    for ad in ARTISANS:
        existing = db.query(Artisan).filter_by(name=ad["name"]).first()
        if existing:
            continue
        a = Artisan(**ad, rating=round(random.uniform(4.2, 5.0), 1), data_label="DEMO")
        db.add(a)
        db.flush()

        for exp_data in EXPERIENCES:
            if exp_data[0] == ad["name"]:
                exp = CommunityExperience(
                    artisan_id=a.id,
                    title=exp_data[1],
                    category=exp_data[2],
                    price_per_person=exp_data[3],
                    max_capacity=exp_data[4],
                    duration_hours=exp_data[5],
                    languages=exp_data[6],
                    data_label="DEMO"
                )
                db.add(exp)
        created += 1
    db.commit()
    print(f"  OK Seeded {created} artisans and their experiences")


def seed_alerts(db):
    destinations = db.query(Destination).all()
    dest_map = {d.name: d.id for d in destinations}

    alerts_data = [
        {
            "destination_id": dest_map.get("White Rann, Dhordo"),
            "alert_type": "overcrowding",
            "title": "High Tourism Pressure at White Rann",
            "message": "Tourist load at White Rann, Dhordo is approaching configured capacity threshold. "
                       "Consider redirecting visitors toward Kalo Dungar or Hodka Village for similar experiences with lower pressure.",
            "severity": AlertSeverity.warning,
        },
        {
            "destination_id": dest_map.get("Rann Utsav Tent City"),
            "alert_type": "overcrowding",
            "title": "Rann Utsav at Near-Capacity",
            "message": "Rann Utsav Tent City accommodation is near full capacity. New visitors are advised to plan an alternative itinerary.",
            "severity": AlertSeverity.critical,
        },
        {
            "destination_id": dest_map.get("Indian Wild Ass Sanctuary"),
            "alert_type": "ecological",
            "title": "Permit Required -- Wild Ass Sanctuary",
            "message": "Entry to the Indian Wild Ass Sanctuary requires a prior permit from the Forest Department. "
                       "Visitor numbers are strictly limited to protect habitat.",
            "severity": AlertSeverity.info,
        },
        {
            "destination_id": dest_map.get("Kutch Desert Wildlife Sanctuary"),
            "alert_type": "ecological",
            "title": "Flamingo Nesting Season",
            "message": "Flamingo breeding season is active. Photography near nesting areas is restricted. "
                       "Please follow guide instructions strictly.",
            "severity": AlertSeverity.warning,
        },
    ]

    created = 0
    for ad in alerts_data:
        if ad["destination_id"] is None:
            continue
        a = Alert(**ad)
        db.add(a)
        created += 1
    db.commit()
    print(f"  OK Seeded {created} alerts")


def main():
    print("Seeding Kutch Tourism Demo Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_destinations(db)
        seed_tourist_loads(db)
        seed_ecological_metrics(db)
        seed_artisans(db)
        seed_alerts(db)
        print("\nDatabase seeded successfully!")
        print("NOTE: All data is labelled DEMO -- synthetic for demonstration only.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
