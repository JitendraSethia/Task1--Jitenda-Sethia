"""Seed sample HCPs (and a few sample interactions / follow-ups) so the app has
data to show on first run — the search/insights tools and the Recent Activity
panel are populated immediately on a fresh clone.

Seeding is idempotent: HCPs are only added when missing, and the sample
interactions/follow-ups are only inserted when the interactions table is empty
(delete the DB to reset).
"""
from . import crud
from .database import SessionLocal
from .models import HCP

SAMPLE_HCPS = [
    {"name": "Dr. Anjali Sharma", "specialty": "Oncology", "institution": "Apollo Hospital"},
    {"name": "Dr. Rajesh Menon", "specialty": "Cardiology", "institution": "Fortis Healthcare"},
    {"name": "Dr. Emily Smith", "specialty": "Endocrinology", "institution": "City General Hospital"},
    {"name": "Dr. Vikram Patel", "specialty": "Neurology", "institution": "Manipal Hospital"},
    {"name": "Dr. Sarah Johnson", "specialty": "Pulmonology", "institution": "Mayo Clinic"},
]

# Chronological order (oldest first) so the newest inserted row is the most recent.
SAMPLE_INTERACTIONS = [
    {
        "hcp_name": "Dr. Emily Smith",
        "interaction_type": "Meeting",
        "date": "2026-07-02",
        "time": "10:30",
        "attendees": ["Dr. Emily Smith"],
        "topics_discussed": "Discussed Product X efficacy data and its endocrinology indications.",
        "materials_shared": ["Product X efficacy brochure"],
        "samples_distributed": ["OncoBoost 10mg x2"],
        "sentiment": "Positive",
        "outcomes": "Dr. Smith was receptive and open to trialling Product X with select patients.",
        "follow_up_actions": "Share the Phase III safety summary.",
        "ai_summary": "Positive meeting with Dr. Emily Smith covering Product X efficacy; "
        "left a brochure and 2 OncoBoost samples. She is open to a trial.",
        "ai_suggested_followups": [
            "Send OncoBoost Phase III PDF",
            "Schedule a follow-up in 2 weeks",
        ],
    },
    {
        "hcp_name": "Dr. Anjali Sharma",
        "interaction_type": "Meeting",
        "date": "2026-07-05",
        "time": "15:00",
        "attendees": ["Dr. Anjali Sharma", "Nurse Practitioner"],
        "topics_discussed": "Reviewed OncoBoost Phase III outcomes and dosing for oncology patients.",
        "materials_shared": ["OncoBoost Phase III summary"],
        "samples_distributed": [],
        "sentiment": "Positive",
        "outcomes": "Strong interest; requested an invite to the upcoming advisory board.",
        "follow_up_actions": "Add Dr. Sharma to the advisory board invite list.",
        "ai_summary": "Productive meeting with Dr. Anjali Sharma on OncoBoost Phase III results; "
        "she requested an advisory board invitation.",
        "ai_suggested_followups": [
            "Add Dr. Sharma to advisory board invite list",
            "Send OncoBoost dosing guide",
        ],
    },
    {
        "hcp_name": "Dr. Emily Smith",
        "interaction_type": "Call",
        "date": "2026-07-08",
        "time": "09:15",
        "attendees": ["Dr. Emily Smith"],
        "topics_discussed": "Follow-up call on Product X titration and patient tolerability questions.",
        "materials_shared": [],
        "samples_distributed": [],
        "sentiment": "Neutral",
        "outcomes": "Wants more real-world tolerability data before expanding use.",
        "follow_up_actions": "Send real-world evidence pack.",
        "ai_summary": "Follow-up call with Dr. Emily Smith on Product X titration; neutral, "
        "awaiting real-world tolerability data before broader use.",
        "ai_suggested_followups": ["Send real-world evidence pack"],
    },
]


def seed_hcps() -> None:
    db = SessionLocal()
    try:
        # HCPs (only add the ones that don't already exist).
        for entry in SAMPLE_HCPS:
            if not crud.get_hcp_by_name(db, entry["name"]):
                db.add(HCP(**entry))
        db.commit()

        # Sample interactions + follow-ups — only when there are none yet.
        if not crud.list_interactions(db, limit=1):
            created = [crud.create_interaction(db, data) for data in SAMPLE_INTERACTIONS]
            by_hcp = {i.hcp_name: i for i in created}

            emily = by_hcp.get("Dr. Emily Smith")
            anjali = by_hcp.get("Dr. Anjali Sharma")
            crud.create_follow_up(
                db,
                {
                    "description": "Send OncoBoost Phase III PDF",
                    "hcp_name": "Dr. Emily Smith",
                    "due_date": "2026-07-15",
                    "interaction_id": emily.id if emily else None,
                },
            )
            crud.create_follow_up(
                db,
                {
                    "description": "Add Dr. Sharma to advisory board invite list",
                    "hcp_name": "Dr. Anjali Sharma",
                    "due_date": "2026-07-20",
                    "interaction_id": anjali.id if anjali else None,
                },
            )
    finally:
        db.close()
