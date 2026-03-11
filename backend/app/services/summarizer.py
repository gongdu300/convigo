# summarizer.py
import os
from dotenv import load_dotenv
import openai
from typing import Dict, Optional

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_product(product: Dict) -> Dict:
    """
    product: dict (name, brand, maybe description or source_url)
    반환: product 업데이트용 dict (summary, pros, cons, taste_score, value_score, health_score)
    """
    name = product.get("name", "")
    brand = product.get("brand", "")
    prompt = f"""다음 편의점 상품 정보를 분석해서 한줄 요약, 장점 2개, 단점 2개, 그리고
    맛/가성비/건강 점수(0~10 소수 한 자리) 를 JSON으로 반환하세요.

    상품명: {name}
    브랜드: {brand}

    출력 예시(JSON, 아무 설명 없이 JSON만):
    {{
      "summary": "짧은 한줄 요약",
      "pros": ["장점1", "장점2"],
      "cons": ["단점1", "단점2"],
      "taste_score": 8.5,
      "value_score": 7.0,
      "health_score": 4.0
    }}
    """

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # 또는 gpt-4 style 모델로 변경 가능
            messages=[
                {"role": "system", "content": "당신은 간결하게 JSON만 출력하는 분석가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        text = resp.choices[0].message.content.strip()
        # 안전하게 JSON 파싱 시도
        import json, re
        # 간혹 JSON 외 텍스트가 섞이면 순수 JSON 부분만 추출
        m = re.search(r'\{.*\}', text, re.S)
        json_text = m.group(0) if m else text
        data = json.loads(json_text)
        # sanitize fields
        result = {
            "summary": data.get("summary"),
            "pros": ", ".join(data.get("pros", [])) if isinstance(data.get("pros"), list) else data.get("pros"),
            "cons": ", ".join(data.get("cons", [])) if isinstance(data.get("cons"), list) else data.get("cons"),
            "taste_score": float(data.get("taste_score", 0)),
            "value_score": float(data.get("value_score", 0)),
            "health_score": float(data.get("health_score", 0)),
        }
        return result
    except Exception as e:
        print("LLM summarizer error:", e)
        return {
            "summary": None,
            "pros": None,
            "cons": None,
            "taste_score": None,
            "value_score": None,
            "health_score": None
        }
