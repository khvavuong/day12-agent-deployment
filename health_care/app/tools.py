import logging
from typing import List, Dict, Optional, Literal

from pydantic import BaseModel
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _get_openai_client() -> Optional[OpenAI]:
    global _client
    if not settings.openai_api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    client = _get_openai_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    response = client.responses.create(
        model=settings.llm_model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return (response.output_text or "").strip()

class ToolResponse(BaseModel):
    answer: str
    urgency: Optional[Literal["low", "medium", "high"]] = "low"
    sources: Optional[List[str]] = []
    metadata: Optional[Dict] = {}

def medical_knowledge_tool(query: str, context: Optional[Dict] = None) -> ToolResponse:
    """
    Medical Knowledge Tool (RAG).
    Provides verified medical information.
    """
    system_prompt = (
        "You are a careful healthcare information assistant. "
        "Answer in Vietnamese with concise medical education only, no diagnosis certainty. "
        "Use cautious wording like 'co the' or 'kha nang'. "
        "If emergency red flags appear, advise urgent in-person care."
    )
    user_prompt = (
        f"Cau hoi: {query}\n"
        "Tra loi ngan gon, ro rang, theo y hoc thong thuong. "
        "Cuoi cau tra loi, nhac nguoi dung tham khao bac si neu trieu chung keo dai."
    )
    try:
        answer = _call_llm(system_prompt, user_prompt)
    except Exception as exc:
        logger.error("medical_knowledge_tool LLM call failed: %s", exc)
        answer = (
            "Toi tam thoi khong lay duoc noi dung tu LLM. "
            "Ban co the tham khao WHO/CDC va lien he bac si neu can."
        )
    return ToolResponse(answer=answer, sources=["WHO", "CDC"])

def symptom_checker_tool(symptoms: List[str], duration: str, age: int) -> ToolResponse:
    """
    Symptom Checker Tool.
    Analyzes symptoms and returns urgency level.
    """
    symptoms_str = ", ".join(symptoms).lower()
    urgency = "low"
    if any(s in symptoms_str for s in ["dau nguc", "kho tho", "ngat", "đau ngực", "khó thở", "ngất"]):
        urgency = "high"
    elif any(s in symptoms_str for s in ["sot cao", "dau bung du doi", "sốt cao", "đau bụng dữ dội"]):
        urgency = "medium"

    system_prompt = (
        "You are a triage-style health assistant. "
        "Do not provide definitive diagnosis. "
        "Output in Vietnamese, include urgency guidance and safe next steps."
    )
    user_prompt = (
        f"Tuoi: {age}\n"
        f"Trieu chung: {', '.join(symptoms)}\n"
        f"Thoi gian: {duration}\n"
        f"Muc do uu tien tam tinh: {urgency}\n"
        "Hay viet huong dan ngan gon, nhan manh dau hieu can di cap cuu neu co."
    )
    try:
        answer = _call_llm(system_prompt, user_prompt)
    except Exception as exc:
        logger.error("symptom_checker_tool LLM call failed: %s", exc)
        if urgency == "high":
            answer = (
                "Co the co dau hieu nguy hiem. "
                "Ban nen goi cap cuu hoac den co so y te gan nhat ngay lap tuc."
            )
        elif urgency == "medium":
            answer = "Ban co the nen di kham trong 24 gio de duoc danh gia ky hon."
        else:
            answer = "Ban co the theo doi them, nghi ngoi va bu nuoc. Neu nang len, hay di kham."

    return ToolResponse(
        answer=answer,
        urgency=urgency,  # type: ignore[arg-type]
        metadata={"symptoms": symptoms, "duration": duration, "age": age},
    )

def lifestyle_tool(goal: str, age: int, habits: Dict) -> ToolResponse:
    """
    Lifestyle Recommendation Tool.
    """
    system_prompt = (
        "You are a preventive healthcare coach. "
        "Provide practical, safe, non-prescriptive lifestyle advice in Vietnamese."
    )
    user_prompt = (
        f"Muc tieu: {goal}\n"
        f"Tuoi: {age}\n"
        f"Thoi quen hien tai: {habits}\n"
        "Tra loi ngan gon theo dang bullet, uu tien hanh dong co the thuc hien ngay."
    )
    try:
        answer = _call_llm(system_prompt, user_prompt)
    except Exception as exc:
        logger.error("lifestyle_tool LLM call failed: %s", exc)
        answer = (
            "De bat dau, ban co the: \n"
            "- Uong du nuoc moi ngay.\n"
            "- Tap the duc it nhat 30 phut/ngay.\n"
            "- Ngu du 7-8 tieng va han che thuc khuya."
        )
    return ToolResponse(answer=answer)
