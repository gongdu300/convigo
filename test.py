from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DATABASE_URL: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("\n✅ DB 연결 성공!")
        print(result.fetchone()[0])

except Exception as e:
    print(f"\n❌ DB 연결 실패: {e}")
    import traceback
    traceback.print_exc()