import logging
from typing import Dict, List, Optional
from app.tools import medical_knowledge_tool, symptom_checker_tool, lifestyle_tool, ToolResponse

logger = logging.getLogger(__name__)

class HealthAgent:
    def __init__(self):
        self.disclaimer = " Lưu ý: Thông tin chỉ mang tính tham khảo, không thay thế chẩn đoán của bác sĩ."

    def route_request(self, message: str, context: Optional[Dict] = None) -> Dict:
        """
        MCP-like routing logic.
        Decides which tool to use based on message content and context.
        """
        msg_lower = message.lower()
        
        # 1. Symptom Checking
        if any(keyword in msg_lower for keyword in ["đau", "sốt", "mệt", "triệu chứng", "ho", "nhức"]):
            # Extract symptoms from message (simplified logic)
            symptoms = [s for s in ["đau đầu", "sốt", "ho", "đau ngực", "mệt mỏi"] if s in msg_lower]
            if not symptoms: symptoms = ["không rõ"]
            
            response = symptom_checker_tool(
                symptoms=symptoms,
                duration="vừa mới xuất hiện",
                age=context.get("age", 25) if context else 25
            )
            tool_used = "symptom_checker"
            
        # 2. Lifestyle Advice
        elif any(keyword in msg_lower for keyword in ["ăn", "uống", "tập thể dục", "giảm cân", "lối sống"]):
            response = lifestyle_tool(
                goal=message,
                age=context.get("age", 25) if context else 25,
                habits={}
            )
            tool_used = "lifestyle_tool"
            
        # 3. Default to Medical Knowledge (RAG)
        else:
            response = medical_knowledge_tool(query=message)
            tool_used = "medical_knowledge"

        # Apply Safety Layer & Formatting
        final_reply = self._format_response(response, tool_used)
        
        return {
            "reply": final_reply,
            "tool_used": tool_used,
            "urgency": getattr(response, "urgency", "low")
        }

    def _format_response(self, response: ToolResponse, tool_used: str) -> str:
        """
        Enforces safety rules and formats the final answer.
        """
        # Ensure 'có thể', 'khả năng' wording (Safety Layer requirement)
        answer = response.answer
        if tool_used == "symptom_checker":
            if "có thể" not in answer.lower() and "khả năng" not in answer.lower():
                answer = "Có khả năng bạn đang gặp vấn đề: " + answer
        
        # Add sources if available
        if response.sources:
            answer += f"\n\n(Nguồn: {', '.join(response.sources)})"
            
        # Add disclaimer
        answer += f"\n\n---\n{self.disclaimer}"
        
        return answer

agent = HealthAgent()
