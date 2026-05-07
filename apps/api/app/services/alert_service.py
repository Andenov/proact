"""
Generates Alert records from the latest district risk scores.
Only creates alerts for Medium and High levels to avoid noise.
"""

import logging
from datetime import date
from typing import List

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.district import District
from app.models.risk_score import DistrictRiskScore

logger = logging.getLogger(__name__)

ALERT_TYPES = [
    ("flood", "flood_score", "flood_level"),
    ("landslide", "landslide_score", "landslide_level"),
    ("food_stress", "food_stress_score", "food_stress_level"),
]

ALERT_TITLES = {
    "flood": {
        "Medium": "Moderate Flood Risk",
        "High": "High Flood Risk — Immediate Attention Required",
    },
    "landslide": {
        "Medium": "Moderate Landslide Risk",
        "High": "High Landslide Risk — Urgent Action Needed",
    },
    "food_stress": {
        "Medium": "Moderate Food Stress Risk",
        "High": "High Food Stress Risk — Intervention Required",
    },
}


def generate_alerts_from_scores(db: Session, score_date: date = None) -> List[Alert]:
    """
    Read all district_risk_scores for score_date (defaults to today),
    create Alert records for any Medium or High risk level not already alerted today.
    Returns list of new Alert objects created.
    """
    if score_date is None:
        score_date = date.today()

    scores = (
        db.query(DistrictRiskScore)
        .filter(DistrictRiskScore.date == score_date)
        .all()
    )

    # Find existing alerts for today to avoid duplicates
    existing = (
        db.query(Alert)
        .filter(Alert.issued_at >= str(score_date))
        .all()
    )
    existing_keys = {(a.district_id, a.alert_type) for a in existing}

    new_alerts: List[Alert] = []

    for score in scores:
        district = db.query(District).filter(District.id == score.district_id).first()
        district_name = district.name if district else f"District {score.district_id}"

        for alert_type, score_field, level_field in ALERT_TYPES:
            level = getattr(score, level_field)
            if level not in ("Medium", "High"):
                continue
            if (score.district_id, alert_type) in existing_keys:
                continue

            recs = score.recommendations_json or {}
            recommended_action = "; ".join(recs.get(alert_type, []))

            title = ALERT_TITLES.get(alert_type, {}).get(level, f"{level} {alert_type} risk")
            message = (
                f"{level} {alert_type.replace('_', ' ')} risk detected in {district_name}. "
                f"Risk score: {getattr(score, score_field, 0):.0f}/100."
            )

            alert = Alert(
                district_id=score.district_id,
                alert_type=alert_type,
                severity=level,
                title=title,
                message=message,
                recommended_action=recommended_action,
                status="active",
            )
            db.add(alert)
            new_alerts.append(alert)
            logger.info(f"Alert created: {title} — {district_name}")

    db.commit()
    for a in new_alerts:
        db.refresh(a)

    return new_alerts
