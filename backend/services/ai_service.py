from sqlalchemy.orm import Session
from fastapi import HTTPException
import json

from ai.client import generate_response
from ai.prompts import locality_prompt
from ai.prompts import chat_prompt
from ai.prompts import scam_check_prompt
from ai.prompts import budget_prompt
from ai.prompts import personalized_suggestions_prompt


from models.housing import Housing
from models.ai import AIChatMessage
from models.user import User

from schemas.ai import (
    AIChatRequest,
)


def generate_ai_response(question: str) -> str:
    """
    Generates a response using Gemini AI.
    """

    try:
        prompt= chat_prompt(question)
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

from schemas.ai import (
    LocalityRecommendationRequest,
    ScamCheckRequest,
    BudgetAdvisorRequest,
)


def get_locality_recommendation(
    request: LocalityRecommendationRequest,
    current_user: User,
    db: Session,
):
    houses = (
        db.query(Housing)
        .filter(Housing.city == request.city)
        .all()
    )

    housing_data = []

    for house in houses:
        housing_data.append(
            {
                "id": house.id,
                "title": house.title,
                "city": house.city,
                "locality": house.locality,
                "rent": house.rent,
                "house_type": house.house_type,
                "verified": house.verified,
                #Temporary values(not yet in DB)
                "rating": 4.5,
                "nearest_metro": "unknown",
                "distance_to_metro_km":1.5,
                "is_furnished": house.is_furnished,
            }
        )

    prompt = locality_prompt(
        request,
        housing_data,
    )

    ai_response = generate_response(prompt)

    try:
        return json.loads(ai_response)

    except json.JSONDecodeError:
        return {
            "summary": "Unable to generate recommendations.",
            "recommendations": [],
        }


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
    risk_score= min(risk_score,100)
    #Determining risk level
    if risk_score >= 70:
        level = "High"
    elif risk_score >= 40:
        level = "Medium"
    else:
        level = "Low"

    
    prompt = scam_check_prompt(request=request,risk_level=level,risk_score=risk_score, red_flags=red_flags,)
    ai_data={
        "summary":(
            f"The listing has been accessed as {level.lower()} risk"
            f"based on the available rental information."
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
        cleaned_response = ai_response.strip()
        if cleaned_response.startswith(""):
            cleaned_response = cleaned_response.replace(
                "```json", ""
            ).replace(
                "```",""
            ).strip()
        parsed_data = json.loads(cleaned_response)
        if isinstance(parsed_data, dict):
            ai_data.update(parsed_data)
    
    except Exception as e:
        print(f"Scam checker AI parsing error: {e}")
    return{
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
        "disclaimer":(
            "This is an AI-based risk assessment "
            "and not a legal guarantee."
        ),
    }  


def budget_advisor(
    request: BudgetAdvisorRequest,
    current_user: User,
    db: Session,
):
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
    summary= f"""
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
    try:
        ai_response = generate_response(prompt)
        ai_data = json.loads(ai_response)
    except Exception:
         ai_data = {
            "summary": ai_data["summary"],
            "recommendations":ai_data["recommendations"],
            "warnings":ai_data["warnings"],
         }    
    return {
        "status": status,
        "summary": "Budget analysis generated successfully.",
        "monthly_income": request.monthly_income,
        "recommended_housing_budget": (
            request.monthly_income * 0.30
        ),
        "current_housing_budget": request.housing_budget,
        "estimated_total_expenses": total_expenses,
        "estimated_savings": savings,
        "housing_percentage": round(
            housing_percentage,
            2,
        ),
        "expense_breakdown": [
            {
                "category": "Housing",
                "amount": request.housing_budget,
                "percentage": round(
                    housing_percentage,
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
        ],
        "recommendations": [
            "Keep housing below 30% of income.",
            "Maintain an emergency fund.",
        ],
        "warnings": (
            ["Housing budget is relatively high."]
            if housing_percentage > 35
            else []
        ),
    }


def get_suggestions(
    current_user: User,
    db: Session,
):
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

        ai_data = json.loads(ai_response)

        return ai_data

    except Exception:
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
                        "Matches your current preferences."
                    ),
                    "priority": "High",
                    "action_label": "Explore Housing",
                    "action_url": "/housing?city=Delhi",
                    "created_at": current_user.created_at,
                }
            ]
        }