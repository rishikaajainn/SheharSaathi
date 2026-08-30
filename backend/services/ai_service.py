from datetime import datetime
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ai.client import generate_response
from ai.prompts import (
    budget_prompt,
    chat_prompt,
    locality_prompt,
    personalized_suggestions_prompt,
    scam_check_prompt,
)

from models.ai import AIChatMessage
from models.housing import Housing
from models.user import User

from schemas.ai import (
    AIChatRequest,
    BudgetAdvisorRequest,
    LocalityRecommendationRequest,
    ScamCheckRequest,
)


# ============================================================
# Helper Functions
# ============================================================

def _clean_ai_response(response: str) -> str:
    """
    Clean common Markdown formatting that Gemini may add
    around an otherwise valid JSON response.
    """

    if not response:
        return ""

    cleaned = response.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()

    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```"):].strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    return cleaned


def _parse_ai_json(response: str) -> dict:
    """
    Safely parse Gemini's response as JSON.

    Raises ValueError if the response is not a JSON object.
    """

    cleaned = _clean_ai_response(response)

    if not cleaned:
        raise ValueError("AI returned an empty response.")

    parsed = json.loads(cleaned)

    if not isinstance(parsed, dict):
        raise ValueError("AI response must be a JSON object.")

    return parsed


# ============================================================
# AI CHAT
# ============================================================

def generate_ai_response(question: str) -> str:
    """
    Generates a response using Gemini AI.
    """

    try:
        prompt = chat_prompt(question)

        return generate_response(prompt)

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(e)}",
        )


def chat_with_ai(
    chat_data: AIChatRequest,
    current_user: User,
    db: Session,
):
    user_message = AIChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_data.question,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    answer = generate_ai_response(
        chat_data.question,
    )

    assistant_message = AIChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=answer,
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "answer": answer,
        "message": assistant_message,
    }


def get_chat_history(
    current_user: User,
    db: Session,
):
    messages = (
        db.query(AIChatMessage)
        .filter(
            AIChatMessage.user_id == current_user.id
        )
        .order_by(
            AIChatMessage.created_at.asc()
        )
        .all()
    )

    return {
        "items": messages,
    }


def clear_chat_history(
    current_user: User,
    db: Session,
):
    (
        db.query(AIChatMessage)
        .filter(
            AIChatMessage.user_id == current_user.id
        )
        .delete()
    )

    db.commit()

    return {
        "success": True,
        "message": "Chat history cleared successfully.",
    }


# ============================================================
# LOCALITY RECOMMENDATION
# ============================================================

def get_locality_recommendation(
    request: LocalityRecommendationRequest,
    current_user: User,
    db: Session,
):
    """
    Generate locality recommendations using available housing
    data and Gemini.

    The backend guarantees a valid response structure even if
    Gemini is temporarily unavailable or returns malformed JSON.
    """

    houses = (
        db.query(Housing)
        .filter(Housing.city == request.city)
        .all()
    )

    # --------------------------------------------------------
    # No housing data available
    # --------------------------------------------------------

    if not houses:
        return {
            "summary": (
                f"No housing listings are currently available "
                f"for {request.city}."
            ),
            "recommendations": [],
        }

    # --------------------------------------------------------
    # Prepare housing data
    # --------------------------------------------------------

    housing_data = []

    for house in houses:
        housing_data.append(
            {
                "id": str(house.id),
                "title": house.title,
                "city": house.city,
                "locality": house.locality,
                "rent": float(house.rent),
                "house_type": house.house_type,
                "verified": bool(house.verified),
                "rating": 4.5,
                "nearest_metro": "Unknown",
                "distance_to_metro_km": 1.5,
                "is_furnished": bool(house.is_furnished),
            }
        )

    # --------------------------------------------------------
    # Generate prompt
    # --------------------------------------------------------

    prompt = locality_prompt(
        request,
        housing_data,
    )

    # --------------------------------------------------------
    # Gemini request
    # --------------------------------------------------------

    try:
        ai_response = generate_response(prompt)

        ai_data = _parse_ai_json(ai_response)

    except Exception as e:
        print(
            f"Locality recommendation AI error: "
            f"{type(e).__name__}: {e}"
        )

        # ----------------------------------------------------
        # Deterministic fallback
        # ----------------------------------------------------

        recommendations = []

        sorted_houses = sorted(
            houses,
            key=lambda house: float(house.rent),
        )[:3]

        for house in sorted_houses:
            rent = float(house.rent)

            recommendations.append(
                {
                    "id": str(house.id),
                    "locality": house.locality,
                    "city": house.city,
                    "match_score": 70.0,
                    "average_rent": rent,
                    "safety_score": 70.0,
                    "transport_score": 70.0,
                    "affordability_score": (
                        90.0
                        if rent <= request.budget
                        else 50.0
                    ),
                    "commute_minutes": (
                        request.maximum_commute_minutes
                        or 45
                    ),
                    "nearest_metro": "Unknown",
                    "distance_to_metro_km": 1.5,
                    "reasons": [
                        (
                            "Selected from available housing "
                            "listings in the requested city."
                        ),
                    ],
                    "pros": [
                        "Available in the requested city.",
                        (
                            "Housing listing is within the "
                            "available database."
                        ),
                    ],
                    "cons": [
                        (
                            "Detailed AI locality analysis "
                            "was unavailable."
                        ),
                    ],
                }
            )

        return {
            "summary": (
                "Recommendations generated from available "
                "housing listings. Detailed AI analysis is "
                "temporarily unavailable."
            ),
            "recommendations": recommendations,
        }

    # --------------------------------------------------------
    # Validate AI response structure
    # --------------------------------------------------------

    raw_recommendations = ai_data.get(
        "recommendations",
        [],
    )

    if not isinstance(raw_recommendations, list):
        raw_recommendations = []

    valid_recommendations = []

    for item in raw_recommendations:
        if not isinstance(item, dict):
            continue

        try:
            recommendation = {
                "id": str(item.get("id", "")),
                "locality": str(
                    item.get("locality", "")
                ),
                "city": str(
                    item.get("city", request.city)
                ),
                "match_score": float(
                    item.get("match_score", 0)
                ),
                "average_rent": float(
                    item.get("average_rent", 0)
                ),
                "safety_score": float(
                    item.get("safety_score", 0)
                ),
                "transport_score": float(
                    item.get("transport_score", 0)
                ),
                "affordability_score": float(
                    item.get("affordability_score", 0)
                ),
                "commute_minutes": int(
                    item.get(
                        "commute_minutes",
                        request.maximum_commute_minutes or 45,
                    )
                ),
                "nearest_metro": str(
                    item.get(
                        "nearest_metro",
                        "Unknown",
                    )
                ),
                "distance_to_metro_km": float(
                    item.get(
                        "distance_to_metro_km",
                        0,
                    )
                ),
                "reasons": (
                    item.get("reasons", [])
                    if isinstance(
                        item.get("reasons", []),
                        list,
                    )
                    else []
                ),
                "pros": (
                    item.get("pros", [])
                    if isinstance(
                        item.get("pros", []),
                        list,
                    )
                    else []
                ),
                "cons": (
                    item.get("cons", [])
                    if isinstance(
                        item.get("cons", []),
                        list,
                    )
                    else []
                ),
            }

            if not recommendation["locality"]:
                continue

            valid_recommendations.append(
                recommendation
            )

        except (TypeError, ValueError):
            continue

    return {
        "summary": str(
            ai_data.get(
                "summary",
                "Locality recommendations generated successfully.",
            )
        ),
        "recommendations": valid_recommendations,
    }


# ============================================================
# RENTAL SCAM CHECKER
# ============================================================

def scam_check(
    request: ScamCheckRequest,
    current_user: User,
    db: Session,
):
    risk_score = 20

    red_flags = []

    if request.payment_requested_before_visit:
        risk_score += 35

        red_flags.append(
            "Payment requested before property visit."
        )

    if request.owner_refuses_property_visit:
        risk_score += 35

        red_flags.append(
            "Owner refuses property visit."
        )

    if request.deposit and request.rent:
        if request.deposit > request.rent * 3:
            risk_score += 20

            red_flags.append(
                "Deposit appears unusually high."
            )

    risk_score = min(
        risk_score,
        100,
    )

    if risk_score >= 70:
        level = "High"

    elif risk_score >= 40:
        level = "Medium"

    else:
        level = "Low"

    prompt = scam_check_prompt(
        request=request,
        risk_level=level,
        risk_score=risk_score,
        red_flags=red_flags,
    )

    ai_data = {
        "summary": (
            f"The listing has been assessed as "
            f"{level.lower()} risk based on the "
            f"available rental information."
        ),
        "positive_signals": [],
        "recommendations": [
            "Visit the property before making any payment.",
            "Verify owner's identity and ownership documents.",
            "Avoid making advance payments before verification.",
        ],
    }

    try:
        ai_response = generate_response(prompt)

        parsed_data = _parse_ai_json(
            ai_response
        )

        ai_data.update(parsed_data)

    except Exception as e:
        print(
            f"Scam checker AI error: "
            f"{type(e).__name__}: {e}"
        )

    return {
        "risk_level": level,
        "risk_score": risk_score,
        "summary": ai_data.get(
            "summary",
            "Rental scam assessment completed.",
        ),
        "red_flags": red_flags,
        "positive_signals": ai_data.get(
            "positive_signals",
            [],
        ),
        "recommendations": ai_data.get(
            "recommendations",
            [],
        ),
        "disclaimer": (
            "This is an AI-based risk assessment "
            "and not a legal guarantee."
        ),
    }


# ============================================================
# BUDGET ADVISOR
# ============================================================

def budget_advisor(
    request: BudgetAdvisorRequest,
    current_user: User,
    db: Session,
):
    """
    Analyse the user's relocation budget.

    Financial calculations are deterministic and performed
    by the backend. Gemini is used for explanation,
    recommendations and warnings.
    """

    total_expenses = (
        request.housing_budget
        + request.monthly_food
        + request.monthly_transport
        + request.monthly_utilities
        + request.monthly_other_expenses
    )

    savings = (
        request.monthly_income
        - total_expenses
    )

    housing_percentage = (
        request.housing_budget
        / request.monthly_income
        * 100
    )

    if housing_percentage <= 30:
        status = "Safe"

    elif housing_percentage <= 40:
        status = "Manageable"

    elif housing_percentage <= 50:
        status = "Tight"

    else:
        status = "Risky"

    summary = f"""
Status: {status}
Monthly Income: {request.monthly_income}
Housing Budget: {request.housing_budget}
Estimated Expenses: {total_expenses}
Estimated Savings: {savings}
Housing Percentage: {round(housing_percentage, 2)}%
"""

    prompt = budget_prompt(
        request=request,
        summary=summary,
    )

    # --------------------------------------------------------
    # Safe default AI data
    # --------------------------------------------------------

    ai_data = {
        "summary": (
            f"Your current budget is classified as "
            f"{status.lower()} based on the proportion "
            f"of income allocated to housing and your "
            f"estimated monthly expenses."
        ),
        "recommendations": [
            "Keep housing costs within a manageable share of income.",
            "Maintain an emergency fund for unexpected expenses.",
            "Review transport and discretionary expenses regularly.",
        ],
        "warnings": [],
    }

    if housing_percentage > 35:
        ai_data["warnings"].append(
            "Housing costs are taking a relatively high share of income."
        )

    if savings < 0:
        ai_data["warnings"].append(
            "Estimated monthly expenses exceed your income."
        )

    # --------------------------------------------------------
    # Gemini analysis
    # --------------------------------------------------------

    try:
        ai_response = generate_response(prompt)

        parsed_data = _parse_ai_json(
            ai_response
        )

        if isinstance(
            parsed_data.get("summary"),
            str,
        ):
            ai_data["summary"] = parsed_data[
                "summary"
            ]

        if isinstance(
            parsed_data.get("recommendations"),
            list,
        ):
            ai_data["recommendations"] = (
                parsed_data["recommendations"]
            )

        if isinstance(
            parsed_data.get("warnings"),
            list,
        ):
            ai_data["warnings"] = (
                parsed_data["warnings"]
            )

    except Exception as e:
        print(
            f"Budget advisor AI error: "
            f"{type(e).__name__}: {e}"
        )

    # --------------------------------------------------------
    # Expense breakdown
    # --------------------------------------------------------

    expense_breakdown = [
        {
            "category": "Housing",
            "amount": request.housing_budget,
            "percentage": round(
                request.housing_budget
                / request.monthly_income
                * 100,
                2,
            ),
        },
        {
            "category": "Food",
            "amount": request.monthly_food,
            "percentage": round(
                request.monthly_food
                / request.monthly_income
                * 100,
                2,
            ),
        },
        {
            "category": "Transport",
            "amount": request.monthly_transport,
            "percentage": round(
                request.monthly_transport
                / request.monthly_income
                * 100,
                2,
            ),
        },
        {
            "category": "Utilities",
            "amount": request.monthly_utilities,
            "percentage": round(
                request.monthly_utilities
                / request.monthly_income
                * 100,
                2,
            ),
        },
        {
            "category": "Other",
            "amount": request.monthly_other_expenses,
            "percentage": round(
                request.monthly_other_expenses
                / request.monthly_income
                * 100,
                2,
            ),
        },
    ]

    return {
        "status": status,
        "summary": ai_data["summary"],
        "monthly_income": request.monthly_income,
        "recommended_housing_budget": (
            request.monthly_income * 0.30
        ),
        "current_housing_budget": (
            request.housing_budget
        ),
        "estimated_total_expenses": total_expenses,
        "estimated_savings": savings,
        "housing_percentage": round(
            housing_percentage,
            2,
        ),
        "expense_breakdown": expense_breakdown,
        "recommendations": ai_data[
            "recommendations"
        ],
        "warnings": ai_data[
            "warnings"
        ],
    }


# ============================================================
# PERSONALIZED SUGGESTIONS
# ============================================================

def get_suggestions(
    current_user: User,
    db: Session,
):
    """
    Generate personalized relocation suggestions.

    Backend guarantees that every returned suggestion has
    the fields required by SuggestionsResponse.
    """

    context = f"""
User Name: {current_user.name}
Email: {current_user.email}
Account Created: {current_user.created_at}
"""

    prompt = personalized_suggestions_prompt(
        current_user,
        context,
    )

    try:
        ai_response = generate_response(prompt)

        ai_data = _parse_ai_json(
            ai_response
        )

        raw_items = ai_data.get(
            "items",
            [],
        )

        if not isinstance(
            raw_items,
            list,
        ):
            raw_items = []

        valid_items = []

        for index, item in enumerate(
            raw_items,
            start=1,
        ):
            if not isinstance(
                item,
                dict,
            ):
                continue

            suggestion_type = item.get(
                "type",
                "general",
            )

            allowed_types = {
                "housing",
                "roommate",
                "budget",
                "locality",
                "safety",
                "transport",
                "expense",
                "general",
            }

            if suggestion_type not in allowed_types:
                suggestion_type = "general"

            priority = item.get(
                "priority",
                "Medium",
            )

            allowed_priorities = {
                "Low",
                "Medium",
                "High",
            }

            if priority not in allowed_priorities:
                priority = "Medium"

            valid_items.append(
                {
                    "id": f"suggestion-{index}",
                    "type": suggestion_type,
                    "title": str(
                        item.get(
                            "title",
                            "Relocation suggestion",
                        )
                    ),
                    "description": str(
                        item.get(
                            "description",
                            "Consider this recommendation while planning your relocation.",
                        )
                    ),
                    "reason": str(
                        item.get(
                            "reason",
                            "Based on your available profile information.",
                        )
                    ),
                    "priority": priority,
                    "action_label": str(
                        item.get(
                            "action_label",
                            "Explore",
                        )
                    ),
                    "action_url": str(
                        item.get(
                            "action_url",
                            "/housing",
                        )
                    ),
                    "created_at": (
                        current_user.created_at
                        or datetime.utcnow()
                    ),
                }
            )

        if valid_items:
            return {
                "items": valid_items,
            }

    except Exception as e:
        print(
            f"Personalized suggestions AI error: "
            f"{type(e).__name__}: {e}"
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return {
        "items": [
            {
                "id": "suggestion-1",
                "type": "housing",
                "title": "Consider shared housing",
                "description": (
                    "Shared accommodation can reduce "
                    "your monthly rent."
                ),
                "reason": (
                    "Shared housing can be useful when "
                    "trying to control relocation costs."
                ),
                "priority": "High",
                "action_label": "Explore Housing",
                "action_url": "/housing?city=Delhi",
                "created_at": (
                    current_user.created_at
                    or datetime.utcnow()
                ),
            },
            {
                "id": "suggestion-2",
                "type": "budget",
                "title": "Review your monthly budget",
                "description": (
                    "Compare housing, transport and "
                    "daily expenses before finalising "
                    "your relocation."
                ),
                "reason": (
                    "Planning expenses early can help "
                    "avoid unexpected monthly costs."
                ),
                "priority": "Medium",
                "action_label": "Check Budget",
                "action_url": "/ai",
                "created_at": (
                    current_user.created_at
                    or datetime.utcnow()
                ),
            },
        ]
    }