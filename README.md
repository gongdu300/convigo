# 🏪 ConviGo - 편의점 행사상품 통합 검색

> CU, GS25, 세븐일레븐의 모든 행사상품을 한눈에!

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![React](https://img.shields.io/badge/React-18.3.1-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)

**ConviGo**는 국내 3대 편의점(CU, GS25, 세븐일레븐)의 행사상품 정보를 실시간으로 수집하여 한 곳에서 비교·검색할 수 있는 통합 플랫폼입니다.

---

## 📋 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [빠른 시작 (TL;DR)](#-빠른-시작-tldr)
- [상세 설치 가이드](#-상세-설치-가이드)
- [시스템 아키텍처](#-시스템-아키텍처)
- [프로젝트 구조](#-프로젝트-구조)
- [크롤링 가이드](#-크롤링-가이드)
- [API 문서](#-api-문서)

---

## 🎯 프로젝트 소개

### 해결하는 문제
- 여러 편의점 앱을 일일이 확인해야 하는 번거로움
- 최저가 행사상품을 찾기 위한 시간 낭비
- 놓치기 쉬운 1+1, 2+1 행사 정보

### 제공하는 가치
- **통합 검색**: 3개 편의점 행사상품을 한 번에 검색
- **실시간 업데이트**: 자동 크롤링을 통한 최신 정보 제공
- **스마트 필터**: 편의점별, 행사유형별, 가격대별 정밀 검색
- **AI 챗봇**: 자연어로 상품 추천 및 검색 지원
- **개인화**: 북마크 및 맞춤 상품 추천

---

## ✨ 주요 기능

### 1. 통합 검색 & 필터링
- 🔍 **키워드 검색**: 상품명으로 실시간 검색
- 🏪 **편의점별 필터**: CU, GS25, 세븐일레븐 선택
- 🎁 **행사유형 필터**: 1+1, 2+1, 증정, 할인
- 💰 **가격대 필터**: 최소/최대 가격 범위 설정
- 🆕 **신상품 필터**: 신제품만 따로 확인
- 📊 **정렬 기능**: 최신순, 가격순(오름/내림차순)

### 2. 스마트 추천
- 🤖 **AI 챗봇**: 자연어 기반 상품 추천 및 검색
- 🎯 **유사 상품**: Vector Embedding 기반 유사 상품 추천
- 💡 **개인화 추천**: 사용자 선호도 기반 맞춤 상품

### 3. 사용자 기능
- 👤 **회원가입/로그인**: JWT 기반 인증 시스템
- ⭐ **북마크**: 관심 상품 저장 및 관리
- 📱 **마이페이지**: 북마크 상품 및 선호도 관리

### 4. 자동 데이터 수집
- 🕷️ **Selenium 웹 크롤링**: 3개 편의점 자동 수집
- ⏰ **스케줄러**: 주기적 자동 업데이트
- 📊 **중복 제거**: DB 레벨 유니크 제약

---

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (Docker)
- **Search Engine**: Elasticsearch (옵션)
- **Crawling**: Selenium WebDriver
- **Authentication**: JWT (JSON Web Token)
- **Task Queue**: APScheduler
- **AI/ML**: 
  - Sentence Transformers (Embedding)
  - Vector Similarity Search

### Frontend
- **Framework**: React 18.3.1
- **Build Tool**: Vite 5.1.4
- **Styling**: Tailwind CSS 3.4.1
- **Routing**: React Router DOM 6.22.0
- **HTTP Client**: Axios 1.6.7
- **Icons**: Lucide React 0.344.0

### DevOps & Tools
- **Containerization**: Docker (PostgreSQL, Elasticsearch)
- **Version Control**: Git
- **Package Manager**: npm (Frontend), pip (Backend)

---

## 🚀 빠른 시작 (TL;DR)

> 집 ↔ 학원 어디서든 **동일한 환경**으로 즉시 실행

### 필수 요구사항
- **Python** 3.11.x
- **Node.js** 20.x LTS
- **Docker Desktop** (WSL2 권장, Windows)
- **Chrome/Chromium** (크롤러용)

### 뇌 빼고 따라하기 🧠

```bash
# 1) 레포 클론
git clone <YOUR_REPO_URL>
cd convigo

# 2) 백엔드 가상환경 & 라이브러리
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 라이브러리 설치
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3) 인프라(컨테이너) 기동
docker compose -f docker-compose.yml up -d          # PostgreSQL 필수
docker compose -f docker-compose.elasticsearch.yml up -d   # (옵션) Elasticsearch

# 4) 환경변수 파일 생성
# Windows
copy backend\app\.env.example backend\app\.env

# macOS/Linux
cp backend/app/.env.example backend/app/.env

# .env 파일 내용은 아래 섹션 참고하여 수정!

# 5) API 서버 실행
uvicorn backend.main:app --reload --port 8000

# 6) 프론트 실행 (새 터미널)
cd frontend
npm ci   # 없으면: npm install
npm run dev
```

### 접속 확인
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

---

## 📚 상세 설치 가이드

### 1. 저장소 클론
```bash
git clone <YOUR_REPO_URL>
cd convigo
```

### 2. Backend 설정

#### 2.1 Python 가상환경 생성
```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate

# pip 업그레이드
python -m pip install --upgrade pip
```

#### 2.2 의존성 설치
```bash
# requirements.txt 설치
pip install -r requirements.txt

# 주요 패키지
# - fastapi, uvicorn[standard]
# - sqlalchemy, psycopg2-binary
# - python-jose[cryptography], passlib[bcrypt]
# - selenium, beautifulsoup4
# - sentence-transformers
```

#### 2.3 Docker 컨테이너 실행

**PostgreSQL (필수)**
```bash
# docker-compose.yml 사용
docker compose -f docker-compose.yml up -d

# 또는 개별 실행
docker run -d \
  --name convigo-postgres \
  -e POSTGRES_USER=convigo \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=convigo_db \
  -p 5432:5432 \
  postgres:15
```

**Elasticsearch (옵션)**
```bash
# docker-compose.elasticsearch.yml 사용
docker compose -f docker-compose.elasticsearch.yml up -d
```

**컨테이너 상태 확인**
```bash
docker ps
# convigo-postgres, elasticsearch 확인
```

#### 2.4 환경변수 설정

**파일 생성**
```bash
# Windows
copy backend\app\.env.example backend\app\.env

# macOS/Linux
cp backend/app/.env.example backend/app/.env
```

**`.env` 파일 내용 예시**
```bash
# Database
DATABASE_URL=postgresql://convigo:yourpassword@localhost:5432/convigo_db

# JWT
SECRET_KEY=your-super-secret-key-here-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Elasticsearch (옵션)
ELASTICSEARCH_URL=http://localhost:9200

# CORS (프론트엔드 URL)
FRONTEND_URL=http://localhost:5173

# API
API_BASE_URL=http://localhost:8000
```

#### 2.5 데이터베이스 초기화
```bash
# schema.sql 실행 (PostgreSQL 컨테이너에)
docker exec -i convigo-postgres psql -U convigo -d convigo_db < db/schema.sql

# 또는 로컬 psql 사용
psql -h localhost -U convigo -d convigo_db -f db/schema.sql
```

#### 2.6 Backend 서버 실행
```bash
# 개발 모드 (자동 재시작)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Frontend 설정

#### 3.1 의존성 설치
```bash
cd frontend

# package-lock.json이 있으면
npm ci

# 없으면
npm install
```

#### 3.2 환경변수 설정 (옵션)
```bash
# frontend/.env 파일 생성 (필요시)
VITE_API_BASE_URL=http://localhost:8000
```

> **참고**: `src/services/api.js`에서 기본 URL이 설정되어 있으면 생략 가능

#### 3.3 개발 서버 실행
```bash
npm run dev

# 포트 변경하려면
npm run dev -- --port 3000
```

#### 3.4 빌드 (배포용)
```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

### 4. 크롤링 실행

#### 4.1 개별 편의점 크롤링
```bash
# 가상환경 활성화 상태에서
cd crawler

# CU: 1+1, 2+1 전체 수집
python cu_crawler.py --all

# CU: 특정 행사만 수집
python cu_crawler.py --type 1+1

# GS25: 2+1 행사, 최대 5페이지
python gs25_crawler.py --type 2+1 --pages 5

# 세븐일레븐: 할인 행사, 무제한 수집
python seven_crawler.py --type 할인 --pages 0
```

#### 4.2 크롤러 옵션 상세

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--type` | 특정 행사만 수집 | `--type 1+1` |
| `--all` | 모든 행사 유형 수집 | `--all` |
| `--pages N` | 최대 페이지/클릭 수 (0=무제한) | `--pages 10` |

**지원 행사 유형**
- **CU**: 1+1, 2+1, 전체
- **GS25**: 1+1, 2+1, 증정, 전체
- **세븐일레븐**: 1+1, 2+1, 할인, 전체

#### 4.3 크롤링 결과 확인
```bash
# docs/ 폴더에 JSON 파일로 저장됨
ls docs/
# cu_1+1.json, gs25_2+1.json, seven_할인.json 등
```

---

## 🏗 시스템 아키텍처

```
┌─────────────────┐
│   사용자(Web)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  React Frontend  │  ← Vite + Tailwind CSS
│  (localhost:5173)│
└────────┬────────┘
         │ REST API
         ▼
┌─────────────────┐
│  FastAPI        │  ← JWT Auth, API Routes
│  (localhost:8000)│
└─────┬───┬───┬───┘
      │   │   │
      │   │   └──────────┐
      │   │              │
      ▼   ▼              ▼
┌──────────┐ ┌──────────┐  ┌──────────┐
│PostgreSQL│ │Elasticsearch│ │Scheduler │
│  (Docker)│ │  (옵션)    │ │ (크롤러) │
│  :5432   │ │  :9200    │ └─────┬────┘
└──────────┘ └──────────┘        │
                                 ▼
                     ┌────────────────────┐
                     │ Selenium Crawlers  │
                     │ (CU/GS25/SEVEN)   │
                     └────────────────────┘
                                 │
                                 ▼
                     ┌────────────────────┐
                     │  편의점 웹사이트    │
                     │  (실시간 데이터)    │
                     └────────────────────┘
```

---

## 📂 프로젝트 구조

```
convigo/
├── backend/              # FastAPI 백엔드
│   ├── ai/              # AI/ML 관련 코드
│   │   └── emb.py       # Sentence Embedding
│   ├── app/
│   │   ├── api/         # API 라우트
│   │   │   └── v1/
│   │   │       ├── auth.py          # 인증 API
│   │   │       ├── bookmark.py      # 북마크 API
│   │   │       ├── crawl.py         # 크롤링 트리거 API
│   │   │       ├── preferences.py   # 사용자 선호도 API
│   │   │       └── products.py      # 상품 검색 API
│   │   ├── core/        # 핵심 설정
│   │   │   ├── config.py   # 환경설정
│   │   │   ├── jwt.py      # JWT 유틸
│   │   │   └── security.py # 보안 유틸
│   │   └── services/    # 비즈니스 로직
│   │       ├── crawler.py     # 크롤링 서비스
│   │       ├── scheduler.py   # 스케줄링
│   │       └── summarizer.py  # AI 요약
│   ├── routers/         # API 라우터
│   │   ├── ai.py        # AI 추천 라우터
│   │   └── ai_chat.py   # 챗봇 라우터
│   ├── database.py      # DB 연결 및 세션
│   ├── main.py          # FastAPI 앱 진입점
│   ├── models.py        # SQLAlchemy 모델
│   └── schemas.py       # Pydantic 스키마
│
├── crawler/             # 웹 크롤러
│   ├── cu_crawler.py    # CU 크롤러
│   ├── gs25_crawler.py  # GS25 크롤러
│   └── seven_crawler.py # 세븐일레븐 크롤러
│
├── frontend/            # React 프론트엔드
│   ├── src/
│   │   ├── components/  # 재사용 컴포넌트
│   │   │   ├── FilterBar.jsx      # 필터 UI
│   │   │   ├── ProductCard.jsx    # 상품 카드
│   │   │   ├── ProtectedRoute.jsx # 인증 라우트
│   │   │   └── SimilarDrawer.jsx  # 유사상품 서랍
│   │   ├── contexts/    # React Context
│   │   │   └── AuthContext.jsx    # 인증 컨텍스트
│   │   ├── pages/       # 페이지 컴포넌트
│   │   │   ├── Chatbot.jsx   # AI 챗봇
│   │   │   ├── Detail.jsx    # 상품 상세
│   │   │   ├── Home.jsx      # 메인 페이지
│   │   │   ├── Login.jsx     # 로그인
│   │   │   ├── MyPage.jsx    # 마이페이지
│   │   │   └── Register.jsx  # 회원가입
│   │   ├── services/    # API 서비스
│   │   │   └── api.js        # Axios 인스턴스
│   │   ├── App.jsx      # 앱 루트
│   │   └── main.jsx     # 진입점
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── db/                  # 데이터베이스
│   └── schema.sql       # DB 스키마
│
├── docs/                # 크롤링 결과 (JSON)
│   ├── cu_1+1.json
│   ├── cu_2+1.json
│   ├── gs25_1+1.json
│   ├── gs25_2+1.json
│   ├── gs25_증정.json
│   ├── seven_1+1.json
│   ├── seven_2+1.json
│   └── seven_할인.json
│
├── docker-compose.yml                    # PostgreSQL
├── docker-compose.elasticsearch.yml      # Elasticsearch (옵션)
├── requirements.txt                      # Python 의존성
└── README.md                             # 이 문서
```

---

## 🕷️ 크롤링 가이드

### 지원 편의점 & 행사 유형

| 편의점 | 1+1 | 2+1 | 증정 | 할인 | URL |
|--------|-----|-----|------|------|-----|
| **CU** | ✅ | ✅ | - | - | [링크](https://cu.bgfretail.com/event/plus.do) |
| **GS25** | ✅ | ✅ | ✅ | - | [링크](http://gs25.gsretail.com/gscvs/ko/products/event-goods) |
| **세븐일레븐** | ✅ | ✅ | - | ✅ | [링크](http://www.7-eleven.co.kr/) |

### 크롤링 전략

#### CU (`cu_crawler.py`)
- **접근 방식**: 직접 행사 페이지 접속
- **탭 전환**: 링크 텍스트 기반 클릭 (1+1, 2+1)
- **페이지네이션**: "더보기" 버튼 반복 클릭
- **파싱 대상**:
  - 상품명: `.name` 클래스
  - 가격: `.price` 클래스
  - 이미지: `img` 태그 `src` 속성
  - 행사 정보: `.badge` 클래스

#### GS25 (`gs25_crawler.py`)
- **접근 방식**: 메뉴 네비게이션 (홈 → 상품 → 행사상품)
- **탭 전환**: `id` 기반 필터 버튼 클릭
- **페이지네이션**: "다음" 버튼 + 페이지 번호 추출
- **파싱 대상**:
  - 상품명: `.tit` 클래스
  - 가격: `.price` 클래스
  - 이미지: `img` 태그 `src` 속성
  - 행사 정보: `.flg01` 클래스 배지

#### 세븐일레븐 (`seven_crawler.py`)
- **접근 방식**: GNB 메뉴 hover 후 하위 메뉴 클릭
- **탭 전환**: `.wrap_tab` 리스트 인덱스 기반
- **페이지네이션**: "더보기" 버튼 + 상품 수 증가 확인
- **파싱 대상**:
  - 상품명: `.name` 클래스
  - 가격: `.price` 클래스
  - 이미지: `img` 태그 `src` 속성
  - 행사 정보: `.tag_list_01` 내부 배지

### 공통 크롤링 기능
- ✅ **Headless 모드**: GUI 없이 백그라운드 실행
- ✅ **안정성**: Stale Element 예외 처리
- ✅ **중복 방지**: DB 레벨 유니크 제약 (`store`, `name`, `promotion_type`)
- ✅ **디버깅**: JSON 파일로 크롤링 결과 저장 (`docs/`)
- ✅ **오류 허용**: 연속 40회 파싱 실패 시 중단

### 사용 예시

```bash
# 모든 편의점 1+1 행사 수집
python crawler/cu_crawler.py --type 1+1
python crawler/gs25_crawler.py --type 1+1
python crawler/seven_crawler.py --type 1+1

# CU 전체 수집 (1+1 + 2+1)
python crawler/cu_crawler.py --all

# GS25 2+1만 빠르게 수집 (5페이지 제한)
python crawler/gs25_crawler.py --type 2+1 --pages 5

# 세븐일레븐 할인 행사 전체 수집
python crawler/seven_crawler.py --type 할인 --pages 0
```

---

## 📡 API 문서

### Base URL
```
http://localhost:8000
```

### 주요 엔드포인트

#### 인증 (Authentication)
```http
POST /api/v1/auth/register    # 회원가입
POST /api/v1/auth/login        # 로그인
GET  /api/v1/auth/me           # 내 정보 조회
```

**Request Body (회원가입)**
```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (로그인)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 상품 (Products)
```http
GET  /api/v1/products          # 상품 목록 조회
GET  /api/v1/products/search   # 상품 검색 (텍스트/벡터)
GET  /api/v1/products/{id}     # 상품 상세 조회
GET  /api/v1/products/{id}/similar  # 유사 상품 추천
```

**쿼리 파라미터 예시**
```
GET /api/v1/products?store=CU&promo=1+1&min_price=1000&max_price=5000&is_new=true&sort=price_asc&page=1&page_size=20
```

**파라미터 설명**

| 파라미터 | 타입 | 설명 | 예시 |
|----------|------|------|------|
| `store` | string | 편의점 필터 (CU, GS25, SEVEN) | `CU` |
| `promo` | string | 행사 유형 (1+1, 2+1, 증정, 할인) | `1+1` |
| `is_new` | boolean | 신상품만 조회 | `true` |
| `min_price` | integer | 최소 가격 | `1000` |
| `max_price` | integer | 최대 가격 | `5000` |
| `sort` | string | 정렬 (newest, price_asc, price_desc) | `price_asc` |
| `page` | integer | 페이지 번호 (1부터 시작) | `1` |
| `page_size` | integer | 페이지당 결과 수 | `20` |

**Response 예시**
```json
{
  "items": [
    {
      "id": 1,
      "name": "코카스프라이트 1.5L",
      "price": 3700,
      "store": "CU",
      "promotion_type": "1+1",
      "image_url": "https://...",
      "is_new": false
    }
  ],
  "total": 5531,
  "page": 1,
  "page_size": 20
}
```

#### 북마크 (Bookmarks)
```http
GET    /api/v1/bookmarks       # 내 북마크 목록
POST   /api/v1/bookmarks       # 북마크 추가
DELETE /api/v1/bookmarks/{id}  # 북마크 삭제
```

**Request Body (추가)**
```json
{
  "product_id": 123
}
```

#### 사용자 선호도 (Preferences)
```http
GET  /api/v1/preferences       # 선호도 조회
POST /api/v1/preferences       # 선호도 저장/업데이트
```

**Request Body**
```json
{
  "favorite_stores": ["CU", "GS25"],
  "favorite_categories": ["음료", "스낵"],
  "price_range": [1000, 5000]
}
```

#### AI 챗봇
```http
POST /api/ai/chat              # 챗봇 대화
POST /api/ai/recommend         # AI 추천
```

**Request Body (챗봇)**
```json
{
  "message": "1000원 이하 음료 추천해줘",
  "conversation_id": "uuid-here"
}
```

#### 크롤링 (관리자)
```http
POST /api/v1/crawl/trigger     # 크롤링 트리거
GET  /api/v1/crawl/status      # 크롤링 상태 확인
```

### Swagger UI
API 문서는 FastAPI의 자동 생성 문서에서 상세히 확인 가능:
```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```

---

## 🔧 문제 해결 (Troubleshooting)

### 1. Docker 컨테이너가 실행되지 않을 때
```bash
# 컨테이너 상태 확인
docker ps -a

# 로그 확인
docker logs convigo-postgres

# 컨테이너 재시작
docker compose down
docker compose up -d
```

### 2. 포트 충돌 (이미 사용 중)
```bash
# Windows에서 포트 사용 프로세스 확인
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# macOS/Linux
lsof -i :8000
lsof -i :5432

# 프로세스 종료 후 재실행
```

### 3. 크롤러 실행 오류
```bash
# Chrome/Chromium이 설치되어 있는지 확인
# ChromeDriver는 selenium-manager가 자동 관리

# Selenium 관련 패키지 재설치
pip install --upgrade selenium

# Headless 모드가 안 되면 일반 모드로 테스트
# crawler 파일에서 options.add_argument("--headless=new") 주석 처리
```

### 4. DB 연결 오류
```bash
# PostgreSQL 컨테이너 접속 테스트
docker exec -it convigo-postgres psql -U convigo -d convigo_db

# 연결 성공하면 \dt 명령으로 테이블 확인
\dt

# .env 파일의 DATABASE_URL 확인
cat backend/app/.env | grep DATABASE_URL
```

### 5. Frontend에서 API 호출 실패
```bash
# CORS 에러라면 backend/main.py에서 CORS 설정 확인
# origins에 http://localhost:5173 추가되어 있는지 확인

# Network 탭에서 실제 요청 URL 확인
# 개발자 도구 > Network > Fetch/XHR
```

### 6. 가상환경 활성화 문제 (Windows PowerShell)
```bash
# 실행 정책 오류가 나면
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 그래도 안 되면 CMD 사용
.venv\Scripts\activate.bat
```

---

## 🎨 개발 팁

### 1. 백엔드 개발 시 자동 재시작
```bash
# uvicorn의 --reload 옵션 사용
uvicorn backend.main:app --reload --port 8000

# 코드 변경 시 자동으로 서버 재시작됨
```

### 2. 프론트엔드 Hot Module Replacement
```bash
# Vite는 기본적으로 HMR 지원
npm run dev

# 저장하면 브라우저가 자동으로 새로고침
```

### 3. DB 데이터 초기화
```bash
# PostgreSQL 컨테이너 접속
docker exec -it convigo-postgres psql -U convigo -d convigo_db

# 테이블 전체 삭제 후 재생성
DROP TABLE IF EXISTS bookmarks, preferences, users, items;

# 그 후 schema.sql 재실행
\i /path/to/db/schema.sql
```

### 4. 크롤링 결과 빠른 확인
```bash
# JSON 파일 열기
cat docs/cu_1+1.json | jq '.[:5]'  # macOS/Linux (jq 필요)

# 또는 직접 에디터로 열기
code docs/cu_1+1.json
```

### 5. API 테스트 (curl)
```bash
# 회원가입
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"test1234"}'

# 로그인
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test1234"}'

# 상품 검색
curl "http://localhost:8000/api/v1/products?store=CU&promo=1+1&page=1&page_size=10"
```

---

## 📊 데이터베이스 스키마

### 주요 테이블

#### 1. `items` - 상품 정보
```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    store VARCHAR(50) NOT NULL,              -- CU, GS25, SEVEN
    name VARCHAR(255) NOT NULL,              -- 상품명
    price INTEGER,                           -- 가격
    image_url TEXT,                          -- 이미지 URL
    promotion_type VARCHAR(50),              -- 1+1, 2+1, 증정, 할인
    is_new BOOLEAN DEFAULT FALSE,            -- 신상품 여부
    is_promo BOOLEAN DEFAULT FALSE,          -- 행사 상품 여부
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(store, name, promotion_type)      -- 중복 방지
);
```

#### 2. `users` - 사용자
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. `bookmarks` - 북마크
```sql
CREATE TABLE bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, item_id)
);
```

#### 4. `preferences` - 사용자 선호도
```sql
CREATE TABLE preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    favorite_stores JSONB,                   -- ["CU", "GS25"]
    favorite_categories JSONB,               -- ["음료", "스낵"]
    price_range JSONB,                       -- [1000, 5000]
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 배포 가이드 (추후)

### 1. 환경변수 프로덕션 설정
```bash
# .env.production 파일 생성
DATABASE_URL=postgresql://user:pass@production-db:5432/convigo
SECRET_KEY=production-secret-key-very-long-and-secure
FRONTEND_URL=https://convigo.com
```

### 2. Docker Compose로 전체 스택 배포
```yaml
# docker-compose.prod.yml (예시)
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: convigo_db
      POSTGRES_USER: convigo
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://convigo:${DB_PASSWORD}@postgres:5432/convigo_db
    depends_on:
      - postgres
    
  frontend:
    build: ./frontend
    environment:
      VITE_API_BASE_URL: https://api.convigo.com

volumes:
  postgres_data:
```

### 3. 프론트엔드 빌드 & 배포
```bash
# Vite 빌드
cd frontend
npm run build

# dist/ 폴더를 정적 호스팅 (Vercel, Netlify 등)
# 또는 Nginx로 서빙
```

---

## 🤝 기여 가이드

### 브랜치 전략
- `main`: 프로덕션 안정 버전
- `develop`: 개발 브랜치
- `feature/기능명`: 새 기능 개발
- `fix/버그명`: 버그 수정

### 커밋 컨벤션
```bash
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅 (기능 변경 없음)
refactor: 코드 리팩토링
test: 테스트 코드 추가
chore: 빌드/설정 변경

# 예시
git commit -m "feat: CU 크롤러 2+1 행사 지원 추가"
git commit -m "fix: 상품 검색 시 가격 필터 오류 수정"
```

### Pull Request 가이드
1. `develop` 브랜치에서 새 브랜치 생성
2. 기능 개발 또는 버그 수정
3. 커밋 메시지 컨벤션 준수
4. `develop` 브랜치로 PR 생성
5. 코드 리뷰 후 머지

---

## 📈 성능 최적화 팁

### Backend
```python
# 1. DB 쿼리 최적화 (Lazy Loading 방지)
items = db.query(Item).options(joinedload(Item.bookmarks)).all()

# 2. 응답 캐싱 (Redis 도입 시)
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.get("/api/v1/products")
@cache(expire=300)  # 5분 캐싱
async def get_products():
    ...

# 3. 페이지네이션 필수
LIMIT = 20
OFFSET = (page - 1) * LIMIT
items = db.query(Item).limit(LIMIT).offset(OFFSET).all()
```

### Frontend
```javascript
// 1. 이미지 Lazy Loading
<img loading="lazy" src={imageUrl} alt={name} />

// 2. React.memo로 불필요한 리렌더링 방지
export default React.memo(ProductCard);

// 3. 디바운싱으로 검색 최적화
const debouncedSearch = useMemo(
  () => debounce((value) => fetchProducts(value), 300),
  []
);
```

### 크롤링
```python
# 1. 불필요한 리소스 차단
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2  # 이미지 로드 안 함
})

# 2. 멀티프로세싱 (여러 편의점 동시 크롤링)
from multiprocessing import Process

processes = [
    Process(target=crawl_cu),
    Process(target=crawl_gs25),
    Process(target=crawl_seven)
]
for p in processes:
    p.start()
```

---

## 📚 참고 자료

### 공식 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [React 공식 문서](https://react.dev/)
- [Vite 공식 문서](https://vitejs.dev/)
- [Selenium 문서](https://www.selenium.dev/documentation/)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
- [Tailwind CSS 문서](https://tailwindcss.com/docs)

### 유용한 라이브러리
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Pydantic 데이터 검증](https://docs.pydantic.dev/)
- [Python-Jose JWT](https://python-jose.readthedocs.io/)
- [Axios HTTP 클라이언트](https://axios-http.com/)
- [Lucide React 아이콘](https://lucide.dev/guide/packages/lucide-react)

### 튜토리얼
- [FastAPI + PostgreSQL 연동](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [React + Vite 시작하기](https://vitejs.dev/guide/)
- [Selenium WebDriver 가이드](https://selenium-python.readthedocs.io/)
- [JWT 인증 구현](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

---

## 🐛 알려진 이슈

### 1. 크롤링 속도 저하
- **원인**: 각 편의점 사이트의 동적 로딩
- **해결**: `--pages` 옵션으로 페이지 제한

### 2. Elasticsearch 메모리 부족
- **원인**: Docker Desktop 메모리 할당 부족
- **해결**: Docker Desktop 설정에서 메모리 4GB 이상 할당

### 3. Windows에서 ChromeDriver 오류
- **원인**: 경로 문제 또는 권한 문제
- **해결**: Chrome을 기본 경로에 설치, 관리자 권한으로 실행

---

## 📞 문의 및 지원

### 개발팀
- **이메일**: convigo-dev@example.com
- **GitHub Issues**: [프로젝트 이슈 페이지]
- **Discord**: [개발자 커뮤니티]

### FAQ

**Q: 크롤링 주기는 어떻게 되나요?**  
A: 기본적으로 매일 새벽 2시에 자동 실행됩니다. `backend/app/services/scheduler.py`에서 수정 가능합니다.

**Q: 특정 편의점만 사용하고 싶어요.**  
A: Frontend의 필터 기능을 사용하거나, API 호출 시 `store` 파라미터를 지정하세요.

**Q: 데이터는 얼마나 보관되나요?**  
A: 현재는 무제한 보관이며, 추후 오래된 행사 상품은 자동 삭제 예정입니다.

**Q: 개인정보는 안전한가요?**  
A: 비밀번호는 bcrypt로 해싱되어 저장되며, JWT 토큰으로 인증합니다.

---

## 🎯 로드맵

### v1.0 (현재)
- ✅ 3개 편의점 크롤링
- ✅ 상품 검색 및 필터링
- ✅ 회원가입/로그인
- ✅ 북마크 기능

### v1.1 (예정)
- [ ] 가격 알림 기능
- [ ] 행사 종료일 표시
- [ ] 모바일 앱 (React Native)
- [ ] 소셜 로그인 (Google, Kakao)

### v2.0 (계획)
- [ ] 장바구니 및 구매 기록
- [ ] 편의점별 리뷰 시스템
- [ ] 지역별 재고 확인
- [ ] 프리미엄 구독 서비스

---

## 📄 라이선스

이 프로젝트는 **MIT License**를 따릅니다.

```
MIT License

Copyright (c) 2024 ConviGo Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들의 도움을 받아 만들어졌습니다:

- [FastAPI](https://fastapi.tiangolo.com/) - 현대적인 Python 웹 프레임워크
- [React](https://react.dev/) - 사용자 인터페이스 구축 라이브러리
- [Vite](https://vitejs.dev/) - 초고속 프론트엔드 빌드 도구
- [PostgreSQL](https://www.postgresql.org/) - 강력한 오픈소스 데이터베이스
- [Selenium](https://www.selenium.dev/) - 브라우저 자동화 도구
- [Tailwind CSS](https://tailwindcss.com/) - 유틸리티 우선 CSS 프레임워크
- [Lucide](https://lucide.dev/) - 아름다운 오픈소스 아이콘

---

## 🌟 Star History

프로젝트가 마음에 드셨다면 ⭐️ Star를 눌러주세요!

---

<div align="center">

**ConviGo**로 편의점 쇼핑이 더 똑똑해집니다! 🚀

Made with ❤️ by ConviGo Team

[🌐 Website](https://convigo.example.com) • [📧 Contact](mailto:convigo-dev@example.com) • [📚 Docs](https://docs.convigo.example.com)

</div>"# convigo" 
"# convigo" 
"# convigo" 
