from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from app.ai.orchestrator import Orchestrator
from app.dependency.deps import verify_token
from openai import APITimeoutError
import traceback


router = APIRouter()
orchestrator = Orchestrator()


class UserInfo(BaseModel):
    id: str
    name: str
    age: int
    gender: str


class QuestionnaireItem(BaseModel):
    question_id: str
    question: str
    answer: str


class DailyNutrition(BaseModel):
    carbs_g: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None


class DailyNutritionSummary(BaseModel):
    calories_kcal: Optional[float] = None
    nutrition: Optional[DailyNutrition] = None
    vitamins: Optional[List[str]] = None


class MetaInfo(BaseModel):
    timezone: Optional[str] = None
    data_completeness: Optional[float] = None


class UserInsightRequest(BaseModel):
    user: UserInfo
    daily_nutrition_summary: Optional[DailyNutritionSummary] = None
    meta: Optional[MetaInfo] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.model_dump()


class UserInsightResponse(BaseModel):
    health_score: int
    personal_ai_insight: str
    ai_important_notice: str
    confidence_level: int


@router.post("/user-insight", response_model=UserInsightResponse)
async def user_insight(request: UserInsightRequest, _: bool = Depends(verify_token)):
    try:
        payload = request.to_payload()
        response = await run_in_threadpool(orchestrator.handle_user_insight, payload)
        return UserInsightResponse(**response)

    except APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="LLM request timed out. Increase OPENAI_TIMEOUT_S (and optionally OPENAI_MAX_RETRIES).",
        )

    except Exception as e:
        print(f"ERROR in user_insight endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

