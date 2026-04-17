from typing import List, Dict, Optional, Literal
from pydantic import BaseModel

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
    # Mock knowledge base
    knowledge_base = {
        "đau đầu": "Đau đầu có thể do nhiều nguyên nhân như căng thẳng, thiếu ngủ hoặc vấn đề về thị lực. Bạn nên nghỉ ngơi và uống đủ nước.",
        "sốt": "Sốt là phản ứng của cơ thể chống lại nhiễm trùng. Nếu sốt cao trên 38.5 độ C, bạn có thể sử dụng paracetamol theo hướng dẫn.",
        "covid": "COVID-19 là bệnh đường hô hấp do virus SARS-CoV-2 gây ra. Triệu chứng thường gặp là ho, sốt và mất vị giác.",
        "ngủ": "Giấc ngủ đủ (7-9 tiếng) rất quan trọng cho sức khỏe tim mạch và trí não."
    }
    
    answer = "Xin lỗi, tôi chưa có thông tin cụ thể về vấn đề này. Tuy nhiên, bạn nên tham khảo các nguồn uy tín như WHO hoặc CDC."
    sources = ["WHO", "CDC"]
    
    for key, value in knowledge_base.items():
        if key in query.lower():
            answer = value
            break
            
    return ToolResponse(answer=answer, sources=sources)

def symptom_checker_tool(symptoms: List[str], duration: str, age: int) -> ToolResponse:
    """
    Symptom Checker Tool.
    Analyzes symptoms and returns urgency level.
    """
    symptoms_str = ", ".join(symptoms).lower()
    urgency = "low"
    advice = "Theo dõi thêm tình trạng sức khỏe của bạn."
    
    if any(s in symptoms_str for s in ["đau ngực", "khó thở", "ngất"]):
        urgency = "high"
        advice = "TRIỆU CHỨNG NGUY HIỂM: Hãy gọi cấp cứu hoặc đến cơ sở y tế gần nhất ngay lập tức."
    elif any(s in symptoms_str for s in ["sốt cao", "đau bụng dữ dội"]):
        urgency = "medium"
        advice = "Bạn nên đi khám bác sĩ trong vòng 24 giờ tới."
        
    answer = f"Dựa trên các triệu chứng ({symptoms_str}) trong {duration}, mức độ ưu tiên của bạn là: {urgency}. {advice}"
    
    return ToolResponse(
        answer=answer, 
        urgency=urgency,
        metadata={"symptoms": symptoms, "duration": duration, "age": age}
    )

def lifestyle_tool(goal: str, age: int, habits: Dict) -> ToolResponse:
    """
    Lifestyle Recommendation Tool.
    """
    recommendations = [
        "Uống ít nhất 2 lít nước mỗi ngày.",
        "Tập thể dục ít nhất 30 phút mỗi ngày.",
        "Hạn chế thức khuya và sử dụng thiết bị điện tử trước khi ngủ."
    ]
    
    if "giảm cân" in goal.lower():
        recommendations.append("Tăng cường chất xơ và giảm lượng đường tinh luyện.")
    elif "cơ bắp" in goal.lower():
        recommendations.append("Bổ sung protein và tập các bài tập kháng lực.")
        
    answer = "Dưới đây là một số khuyến nghị lối sống dành cho bạn:\n- " + "\n- ".join(recommendations)
    return ToolResponse(answer=answer)
