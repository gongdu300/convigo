# backend/routers/ai_chat.py (에이전트 버전)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
from openai import OpenAI

from backend.database import get_db, Item

router = APIRouter(prefix="/ai", tags=["ai-chat"])
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    stream: bool = True

# ─────────────────────────────────────────────────────────────
# 🔧 DB 함수들 (기존 유지)
# ─────────────────────────────────────────────────────────────

def semantic_search_db(
    db: Session,
    keywords: List[str],
    store: Optional[str] = None,
    exclude_keywords: Optional[List[str]] = None,
    limit: int = 8
) -> List[Dict[str, Any]]:
    """키워드 기반 검색"""
    filters = []
    
    if keywords:
        keyword_conditions = []
        for kw in keywords:
            keyword_conditions.append(Item.name.ilike(f"%{kw}%"))
        filters.append(or_(*keyword_conditions))
    
    if exclude_keywords:
        for exclude_kw in exclude_keywords:
            filters.append(~Item.name.ilike(f"%{exclude_kw}%"))
    
    if store:
        store_upper = store.upper()
        if "7" in store_upper or "SEVEN" in store_upper:
            filters.append(Item.store == "SEVEN")
        elif "CU" in store_upper:
            filters.append(Item.store == "CU")
        elif "GS" in store_upper:
            filters.append(Item.store == "GS25")
    
    query = select(Item).where(and_(*filters)).order_by(Item.created_at.desc()).limit(limit)
    results = db.execute(query).scalars().all()
    
    return [
        {
            "id": item.id,
            "name": item.name,
            "price": item.price,
            "store": item.store,
            "promotion_type": item.promotion_type,
            "is_new": item.is_new,
            "image_url": item.image_url
        }
        for item in results
    ]


def search_products_db(
    db: Session,
    store: Optional[str] = None,
    promotion_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    is_new: Optional[bool] = None,
    limit: int = 8
) -> List[Dict[str, Any]]:
    """가격/필터 기반 검색"""
    filters = []
    
    if store:
        store_upper = store.upper()
        if "7" in store_upper or "SEVEN" in store_upper:
            filters.append(Item.store == "SEVEN")
        elif "CU" in store_upper:
            filters.append(Item.store == "CU")
        elif "GS" in store_upper:
            filters.append(Item.store == "GS25")
    
    if promotion_type:
        filters.append(Item.promotion_type == promotion_type)
    
    if min_price is not None:
        filters.append(Item.price >= min_price)
    
    if max_price is not None:
        filters.append(Item.price <= max_price)
    
    if is_new is not None:
        filters.append(Item.is_new == is_new)
    
    query = select(Item).where(and_(*filters)).order_by(Item.created_at.desc()).limit(limit)
    results = db.execute(query).scalars().all()
    
    return [
        {
            "id": item.id,
            "name": item.name,
            "price": item.price,
            "store": item.store,
            "promotion_type": item.promotion_type,
            "is_new": item.is_new,
            "image_url": item.image_url
        }
        for item in results
    ]


def compare_stores_db(
    db: Session,
    stores: List[str],
    promotion_type: Optional[str] = None
) -> Dict[str, Any]:
    """편의점 간 비교"""
    result = {}
    
    for store in stores:
        store_upper = store.upper()
        if "7" in store_upper or "SEVEN" in store_upper:
            store_name = "SEVEN"
        elif "CU" in store_upper:
            store_name = "CU"
        elif "GS" in store_upper:
            store_name = "GS25"
        else:
            continue
        
        filters = [Item.store == store_name]
        if promotion_type:
            filters.append(Item.promotion_type == promotion_type)
        
        avg_price = db.scalar(
            select(func.avg(Item.price)).where(and_(*filters))
        )
        count = db.scalar(
            select(func.count()).select_from(Item).where(and_(*filters))
        )
        cheapest = db.execute(
            select(Item).where(and_(*filters)).order_by(Item.price.asc()).limit(1)
        ).scalar_one_or_none()
        
        result[store_name] = {
            "average_price": round(avg_price, 2) if avg_price else 0,
            "product_count": count or 0,
            "cheapest_product": {
                "name": cheapest.name,
                "price": cheapest.price
            } if cheapest else None
        }
    
    return result


def get_budget_recommendations_db(
    db: Session,
    max_budget: int,
    store: Optional[str] = None,
    limit: int = 8
) -> List[Dict[str, Any]]:
    """예산 내 추천"""
    filters = [Item.price <= max_budget]
    
    if store:
        store_upper = store.upper()
        if "7" in store_upper or "SEVEN" in store_upper:
            filters.append(Item.store == "SEVEN")
        elif "CU" in store_upper:
            filters.append(Item.store == "CU")
        elif "GS" in store_upper:
            filters.append(Item.store == "GS25")
    
    filters.append(Item.is_promo == True)
    
    query = select(Item).where(and_(*filters)).order_by(Item.price.asc()).limit(limit)
    results = db.execute(query).scalars().all()
    
    return [
        {
            "id": item.id,
            "name": item.name,
            "price": item.price,
            "store": item.store,
            "promotion_type": item.promotion_type,
            "image_url": item.image_url,
            "value_score": round((max_budget - item.price) / max_budget * 100, 1)
        }
        for item in results
    ]


# ─────────────────────────────────────────────────────────────
# 🤖 에이전트용 Function Tools
# ─────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": """상품을 검색합니다. 가격, 편의점, 행사 등 구조적 필터 사용.

⚠️ 중요: 사용자가 가격을 언급하면 반드시 min_price/max_price를 설정하세요!

사용 예시:
- "만원~2만원 먹을거" → min_price=10000, max_price=20000
- "5천원 이하" → max_price=5000
- "CU 1+1" → store="CU", promotion_type="1+1" """,
            "parameters": {
                "type": "object",
                "properties": {
                    "store": {"type": "string", "enum": ["GS25", "CU", "SEVEN"]},
                    "promotion_type": {"type": "string", "enum": ["1+1", "2+1", "증정", "할인"]},
                    "min_price": {"type": "integer"},
                    "max_price": {"type": "integer"},
                    "is_new": {"type": "boolean"},
                    "limit": {"type": "integer", "default": 8}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": """키워드 기반 자연어 검색. 가격 필터는 없음!

⚠️ 가격 조건이 있으면 이 함수 대신 search_products를 사용하세요!

사용 예시:
- "혈당 관리" → keywords: ["제로", "무설탕"]
- "숙취 해소" → keywords: ["숙취", "해장", "이온"]
- "단백질" → keywords: ["단백질", "프로틴", "닭가슴살"]""",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "exclude_keywords": {"type": "array", "items": {"type": "string"}},
                    "store": {"type": "string", "enum": ["GS25", "CU", "SEVEN"]},
                    "limit": {"type": "integer", "default": 8}
                },
                "required": ["keywords"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_stores",
            "description": "편의점 간 가격/상품 수 비교",
            "parameters": {
                "type": "object",
                "properties": {
                    "stores": {"type": "array", "items": {"type": "string"}},
                    "promotion_type": {"type": "string", "enum": ["1+1", "2+1", "증정", "할인"]}
                },
                "required": ["stores"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget_recommendations",
            "description": "예산 내 가성비 상품 추천",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_budget": {"type": "integer"},
                    "store": {"type": "string", "enum": ["GS25", "CU", "SEVEN"]},
                    "limit": {"type": "integer", "default": 8}
                },
                "required": ["max_budget"]
            }
        }
    }
]


def execute_function(function_name: str, arguments: Dict[str, Any], db: Session) -> str:
    """함수 실행"""
    try:
        if function_name == "semantic_search":
            results = semantic_search_db(db, **arguments)
            return json.dumps({"products": results, "count": len(results)}, ensure_ascii=False)
        
        elif function_name == "search_products":
            results = search_products_db(db, **arguments)
            return json.dumps({"products": results, "count": len(results)}, ensure_ascii=False)
        
        elif function_name == "compare_stores":
            results = compare_stores_db(db, **arguments)
            return json.dumps(results, ensure_ascii=False)
        
        elif function_name == "get_budget_recommendations":
            results = get_budget_recommendations_db(db, **arguments)
            return json.dumps({"recommendations": results, "count": len(results)}, ensure_ascii=False)
        
        else:
            return json.dumps({"error": f"Unknown function: {function_name}"})
    
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─────────────────────────────────────────────────────────────
# 🧠 ReAct 에이전트 (핵심!)
# ─────────────────────────────────────────────────────────────

async def stream_chat_response(message: str, db: Session):
    """ReAct 에이전트 패턴 적용"""
    
    # 🔴 [수정됨] 시스템 프롬프트를 수정하여 일반 대화와 도구 사용을 모두 처리하도록 지시
    messages = [
        {
            "role": "system",
            "content": """당신은 친절하고 유능한 '편의점 AI 도우미'입니다.

[당신의 역할]
1.  **일반 대화:** 사용자의 일상적인 질문이나 대화(예: "안녕?", "너는 누구야?", "오늘 날씨 어때?")에는 친절하게 대답합니다. 이 경우 도구를 사용하지 않습니다.
2.  **상품 검색/추천:** 사용자가 상품 관련 질문(예: "CU 1+1 상품", "만원 이하 간식")을 하면, 제공된 도구(함수)를 적극적으로 사용하여 DB에서 정보를 찾습니다.

[도구 사용 규칙]
-   사용자 질문을 분석하여 `search_products`, `semantic_search`, `compare_stores`, `get_budget_recommendations` 중 가장 적절한 도구를 선택합니다.
-   **가격 조건** (예: "만원~2만원", "5천원 이하")이 명시되면 반드시 `search_products`나 `get_budget_recommendations`를 사용해야 합니다.
-   **키워드 검색** (예: "숙취 해소", "단백질")은 `semantic_search`를 사용합니다.
-   함수 호출로 상품을 찾으면, 찾은 상품 데이터를 기반으로 사용자에게 친절하게 설명합니다.
-   상품 정보(이름, 가격 등)를 텍스트로 직접 나열하기보다는, "상품 5개를 찾았어요. 바로 보여드릴게요! 🍱"처럼 요약 멘트를 하는 것을 선호합니다. (상품 카드는 프론트엔드에서 보여줄 것입니다.)

[편의점 정보]
-   편의점: GS25, CU, SEVEN
-   행사: 1+1, 2+1, 증정, 할인
"""
        },
        {"role": "user", "content": message}
    ]
    
    try:
        # ═══════════════════════════════════════
        # 🔥 에이전트 루프 (최대 3번 반복)
        # ═══════════════════════════════════════
        max_iterations = 3
        all_products = []
        
        for iteration in range(max_iterations):
            # 1) GPT 호출
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message
            
            # 2) Tool Call 없으면 종료 (일반 대화)
            if not assistant_message.tool_calls:
                # 🔴 [추가됨] Tool Call이 없는 경우 (일반 대화) assistant_message.content를 messages에 추가
                if assistant_message.content:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content
                    })
                break
            
            # 3) Tool Call 실행
            messages.append({
                "role": "assistant",
                "content": assistant_message.content, # Tool call과 함께 나오는 텍스트도 추가
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # 함수 실행
                function_response = execute_function(function_name, function_args, db)
                tool_data = json.loads(function_response)
                
                # 상품 누적
                if "products" in tool_data:
                    all_products.extend(tool_data["products"])
                elif "recommendations" in tool_data:
                    all_products.extend(tool_data["recommendations"])
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response
                })
            
            # 4) 충분한 결과면 종료
            if len(all_products) >= 8:
                break
        
        # ═══════════════════════════════════════
        # 🔥 최종 답변 생성 (스트리밍)
        # ═══════════════════════════════════════
        
        # 중복 제거
        seen_ids = set()
        unique_products = []
        for p in all_products:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                unique_products.append(p)
        
        # 상품 데이터 먼저 전송
        if unique_products:
            yield f"data: {json.dumps({'type': 'products', 'products': unique_products[:8]}, ensure_ascii=False)}\n\n"
        
        # 텍스트 응답 생성
        # 🔴 [수정됨] 만약 에이전트 루프에서 tool call이 없었다면 (일반 대화),
        # 여기서 stream을 다시 호출하여 일반 답변을 생성
        # 만약 tool call이 있었다면, 기존 messages 기반으로 최종 요약 답변 생성
        
        # 1. 루프가 tool call 없이 (일반 대화로) 종료된 경우
        #    - response.choices[0].message.content 에 이미 답변이 있음
        final_text_response_message = messages[-1]
        
        if final_text_response_message.get("role") == "assistant" and \
           not final_text_response_message.get("tool_calls") and \
           final_text_response_message.get("content"):
            
            # 이미 생성된 일반 답변을 스트리밍처럼 전송
            content = final_text_response_message.get("content")
            yield f"data: {json.dumps({'type': 'text', 'content': content}, ensure_ascii=False)}\n\n"
        
        # 2. Tool call을 사용한 후 최종 답변을 생성하는 경우
        else:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'text', 'content': content}, ensure_ascii=False)}\n\n"
        
        yield "data: [DONE]\n\n"
    
    except Exception as e:
        error_msg = f"오류가 발생했어요: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"


# ─────────────────────────────────────────────────────────────
# 🚀 API 엔드포인트
# ─────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat_with_gpt(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """에이전트 기반 GPT 챗봇"""
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="메시지를 입력해주세요")
    
    if request.stream:
        return StreamingResponse(
            stream_chat_response(request.message, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        raise HTTPException(status_code=501, detail="비스트리밍 모드는 지원하지 않습니다")