# 🏥 Health Advisor Agent – Requirements Document

## 1. Overview

### 1.1 Purpose

Xây dựng một AI Agent tư vấn sức khỏe cơ bản sử dụng kiến trúc **3 tools + MCP (Model Context Protocol)** nhằm:

* Cung cấp thông tin y tế phổ thông
* Phân tích triệu chứng mức cơ bản
* Đưa ra khuyến nghị lối sống lành mạnh

⚠️ Lưu ý: Hệ thống **không thay thế bác sĩ** và không đưa ra chẩn đoán y khoa chính thức.

---

### 1.2 Scope

**In-scope:**

* Hỏi đáp kiến thức sức khỏe
* Phân tích triệu chứng cơ bản
* Tư vấn lifestyle

**Out-of-scope:**

* Chẩn đoán bệnh
* Kê đơn thuốc
* Xử lý cấp cứu y tế

---

## 2. System Architecture

### 2.1 High-level Architecture

User → LLM Agent → MCP Controller → Tools → Response + Safety Layer

---

### 2.2 Components

#### 1. LLM Agent

* Xử lý ngôn ngữ tự nhiên
* Hiểu intent người dùng
* Quyết định gọi tool

#### 2. MCP Controller

* Quản lý context (memory)
* Routing tool
* Chuẩn hóa input/output
* Áp dụng safety rules

#### 3. Tools (3 chính)

* Medical Knowledge Tool (RAG)
* Symptom Checker Tool
* Lifestyle Recommendation Tool

#### 4. Safety Layer

* Filter nội dung nguy hiểm
* Thêm disclaimer
* Escalation khi cần

---

## 3. Functional Requirements

---

### 3.1 Medical Knowledge Tool

#### Description

Cung cấp thông tin y khoa đáng tin cậy từ nguồn verified.

#### Inputs

```json
{
  "query": "string",
  "context": {
    "age": "number",
    "symptoms": ["string"]
  }
}
```

#### Outputs

```json
{
  "answer": "string",
  "confidence": "number",
  "sources": ["string"]
}
```

#### Requirements

* Sử dụng RAG với vector database
* Nguồn dữ liệu đáng tin cậy (WHO, CDC,...)
* Không đưa ra kết luận chắc chắn

---

### 3.2 Symptom Checker Tool

#### Description

Phân tích triệu chứng và đưa ra khả năng (không phải chẩn đoán).

#### Inputs

```json
{
  "symptoms": ["string"],
  "duration": "string",
  "age": "number"
}
```

#### Outputs

```json
{
  "possible_conditions": ["string"],
  "urgency": "low | medium | high",
  "advice": "string"
}
```

#### Requirements

* Rule-based + ML (optional)
* Phân loại mức độ nguy hiểm
* Không khẳng định bệnh

---

### 3.3 Lifestyle Recommendation Tool

#### Description

Đưa ra khuyến nghị cải thiện sức khỏe.

#### Inputs

```json
{
  "goal": "string",
  "age": "number",
  "habits": {
    "sleep": "string",
    "exercise": "string"
  }
}
```

#### Outputs

```json
{
  "recommendations": ["string"]
}
```

#### Requirements

* Cá nhân hóa theo user profile
* Không đưa lời khuyên cực đoan

---

## 4. MCP Requirements

### 4.1 Context Management

* Lưu thông tin:

  * Age
  * Symptoms history
  * Previous queries

### 4.2 Routing Logic

| Condition      | Tool              |
| -------------- | ----------------- |
| Có triệu chứng | Symptom Checker   |
| Hỏi kiến thức  | Medical Knowledge |
| Lifestyle      | Lifestyle Tool    |

---

### 4.3 Memory Structure

```json
{
  "user_profile": {
    "age": 0,
    "chronic_conditions": []
  },
  "history": []
}
```

---

## 5. Safety & Compliance

### 5.1 Must NOT

* Chẩn đoán bệnh
* Kê đơn thuốc
* Đưa lời khuyên nguy hiểm

### 5.2 Must HAVE

* Disclaimer nhẹ:

  > "Thông tin chỉ mang tính tham khảo"
* Escalation:

  * Nếu urgency = high → khuyên đi khám

### 5.3 Language Constraints

* Dùng từ:

  * "có thể"
  * "khả năng"
* Tránh:

  * "bạn bị bệnh X"

---

## 6. Non-functional Requirements

### 6.1 Performance

* Response time < 3s

### 6.2 Scalability

* Hỗ trợ concurrent users

### 6.3 Reliability

* Fallback khi tool fail

### 6.4 Security

* Không lưu dữ liệu nhạy cảm
* Mask thông tin cá nhân

---

## 7. API Design (Example)

### Endpoint: /chat

Request:

```json
{
  "message": "Tôi bị đau đầu"
}
```

Response:

```json
{
  "reply": "...",
  "tool_used": "symptom_checker"
}
```

---

## 8. Tech Stack

* LLM: OpenAI / Claude
* Backend: FastAPI / Node.js
* Vector DB: Pinecone / Weaviate
* Orchestration: LangChain / LangGraph

---

## 9. Future Enhancements

* Lab test interpretation
* Drug interaction checker
* Wearable integration

---

## 10. Risks

| Risk              | Mitigation       |
| ----------------- | ---------------- |
| AI hallucination  | RAG + guardrails |
| User over-trust   | Disclaimer       |
| Medical liability | Limit scope      |

---

## 11. Acceptance Criteria

* Agent trả lời đúng intent ≥ 90%
* Không vi phạm safety rules
* Tool routing chính xác ≥ 85%

---

# ✅ End of Document
