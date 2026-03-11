// frontend/src/App.jsx
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Detail from "./pages/Detail";
import Login from "./pages/Login";
import Register from "./pages/Register";
import MyPage from "./pages/MyPage";
import { AuthProvider } from "./contexts/AuthContext";

// (선택) 전역 스크롤 상단 이동
function ScrollToTop() {
  return null;
}

export default function App() {
  return (
    <AuthProvider>
    <HashRouter>
      <ScrollToTop />
      <Routes>
        {/* 메인 리스트 */}
        <Route path="/" element={<Home />} />

        {/* ✅ 카드에서 navigate(`/product/${id}`)로 가는 라우트 */}
        <Route path="/product/:id" element={<Detail />} />

        {/* 필요시 /detail/:id 도 허용(이전 북마크/외부링크 호환) */}
        <Route path="/detail/:id" element={<Detail />} />

        {/* 계정 관련 */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/mypage" element={<MyPage />} />

        {/* 없는 경로 → 홈으로 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
    </AuthProvider>
  );
}
