import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Bookmark, Settings, TrendingUp, TrendingDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ProductCard from '../components/ProductCard';
import { bookmarkAPI, authAPI } from '../services/api';

const MyPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('bookmarks');
  const [bookmarkedProducts, setBookmarkedProducts] = useState([]);
  const [bookmarkLoading, setBookmarkLoading] = useState(false);

  // --- 회원정보 수정 관련 상태 ---
  const [locked, setLocked] = useState(true);           // 비번 확인 전: 잠금
  const [verifyPw, setVerifyPw] = useState('');         // 확인용 현재 비번
  const [verifying, setVerifying] = useState(false);

  const [username, setUsername] = useState(user?.username || '');
  const [currPw, setCurrPw] = useState('');             // 변경용 현재 비번(선택)
  const [newPw, setNewPw] = useState('');               // 새 비번(선택)
  const [saving, setSaving] = useState(false);
  const [currPwError, setCurrPwError] = useState(""); // 현재 비밀번호 에러
  const [newPwError, setNewPwError] = useState("");   // 새 비밀번호 에러
  const [verifyError, setVerifyError] = useState("");  // 비밀번호 확인 에러 메시지

  const [deleting, setDeleting] = useState(false);      // 기존 탈퇴 버튼 계속 사용하려면

  const isPasswordInvalid = newPw && newPw.length < 8;
  
  useEffect(() => {
    if (activeTab === 'bookmarks') {
      fetchBookmarks();
    }
  }, [activeTab]);
  
  const fetchBookmarks = async () => {
    setBookmarkLoading(true);
    try {
      const data = await bookmarkAPI.getBookmarks();
      const products = data.bookmarks.map(bookmark => bookmark.product).filter(p => p);
      setBookmarkedProducts(products);
      console.log('✅ 북마크 목록 로드:', products.length, '개');
    } catch (error) {
      console.error('❌ 북마크 로딩 실패:', error);
    } finally {
      setBookmarkLoading(false);
    }
  };

  // 탭 전환: 회원정보 클릭 시 잠금 상태로 전환
  const goAccountTab = () => {
    setActiveTab('account');
    setLocked(true);
    setVerifyPw('');
    // 최신 사용자 정보 반영
    setUsername(user?.username || '');
    setCurrPw('');
    setNewPw('');
  };

  const handleVerifyPassword = async () => {
    if (!verifyPw) {
      setVerifyError("비밀번호를 입력하세요.");
      return;
    }
    setVerifying(true);
    setVerifyError("");            // 이전 에러 초기화
    try {
      const r = await authAPI.verifyPassword(verifyPw);
      if (!r?.success) {
        setVerifyError("비밀번호가 일치하지 않습니다.");
        return;
      }
      setLocked(false);            // 잠금 해제
      setCurrPw("");
      setNewPw("");
    } catch (e) {
      // alert 대신 인라인 에러
      setVerifyError(e?.response?.data?.detail || "비밀번호가 일치하지 않습니다.");
    } finally {
      setVerifying(false);
    }
  };

  const handleSave = async () => {
    // 에러 초기화
    setCurrPwError("");
    setNewPwError("");

    if (!username.trim()) {
      // 이름만 빈 경우엔 이름 입력 안내 (원하면 인라인로 바꿔도 됨)
      alert("이름을 입력하세요.");
      return;
    }

    // 새 비밀번호 유효성(있으면 8자 이상)
    if (newPw && newPw.length < 8) {
      setNewPwError("새 비밀번호는 최소 8자 이상이어야 합니다.");
      return;
    }

    setSaving(true);
    try {
      // 1) 이름 변경
      const updated = await authAPI.updateProfile(username.trim());
      const local = JSON.parse(localStorage.getItem("user") || "{}");
      localStorage.setItem(
        "user",
        JSON.stringify({
          ...local,
          username: updated.username || username.trim(),
        })
      );

      // 2) 비밀번호 변경(입력된 경우)
      if (newPw) {
        if (!currPw) {
          setCurrPwError("비밀번호 변경을 위해 현재 비밀번호를 입력하세요.");
          return;
        }
        try {
          await authAPI.changePassword(currPw, newPw);
          alert("정보가 변경되었습니다. 다시 로그인 해주세요.");
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          window.location.assign("/login");
          return;
        } catch (e) {
          // ✅ alert 대신 인라인 에러
          const msg = e?.response?.data?.detail || "현재 비밀번호가 올바르지 않습니다.";
          setCurrPwError(msg);
          return;
        }
      }

      // 비번 변경이 없고 이름만 변경된 경우
      alert("정보가 변경되었습니다.");
    } catch (e) {
      console.error(e);
      alert(e?.response?.data?.detail || "저장 실패");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("정말 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.")) return;
    setDeleting(true);
    try {
      await authAPI.deleteMe();
      alert("탈퇴가 완료되었습니다.");
      // 로그인 토큰/유저 캐시 정리 후 리다이렉트
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.replace("/");   // <-- 여기만 바꾸면 끝!
    } catch (e) {
      console.error(e);
      alert(e?.response?.data?.detail || "탈퇴 실패");
    } finally {
      setDeleting(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-red-500 transition-colors mb-4"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">홈으로</span>
          </button>
          
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-gray-900">마이페이지</h1>
            {user && (
              <p className="text-sm text-gray-600 mt-1">
                안녕하세요, <span className="font-semibold text-red-500">{user.username}</span>님!
              </p>
            )}
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('bookmarks')}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2
                ${activeTab === 'bookmarks' 
                  ? 'bg-red-500 text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              <Bookmark className="w-4 h-4" />
              북마크
            </button>
            <button
              onClick={goAccountTab}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2
                ${activeTab === 'account' 
                  ? 'bg-red-500 text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              <Settings className="w-4 h-4" />
              회원정보
            </button>
          </div>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto px-4 py-8">
        {activeTab === 'bookmarks' && (
          <div>
            {bookmarkLoading ? (
              <div className="text-center py-20">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
                <p className="mt-4 text-gray-600">북마크 불러오는 중...</p>
              </div>
            ) : bookmarkedProducts.length === 0 ? (
              <div className="text-center py-20 bg-white rounded-2xl shadow-sm">
                <Bookmark className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-xl text-gray-600 mb-2">북마크한 상품이 없습니다</p>
                <p className="text-sm text-gray-400 mb-6">
                  마음에 드는 상품을 북마크해보세요!
                </p>
                <button
                  onClick={() => navigate('/')}
                  className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                >
                  상품 둘러보기
                </button>
              </div>
            ) : (
              <div>
                <div className="mb-4 text-gray-600">
                  총 <span className="font-bold text-red-500">{bookmarkedProducts.length}</span>개 북마크
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                  {bookmarkedProducts.map(product => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'account' && (
          <div className="mx-auto max-w-3xl rounded-2xl bg-white p-8 shadow-sm space-y-8">

            {locked ? (
              // 1) 비밀번호 확인 단계
              <section className="mx-auto max-w-2xl">
                <h2 className="mb-4 text-center text-xl font-bold">비밀번호 확인</h2>
                <p className="mb-4 text-center text-sm text-gray-600">
                  회원정보 수정을 위해 현재 비밀번호를 입력하세요.
                </p>

                <div className="mx-auto grid max-w-md gap-2">
                  <input
                    type="password"
                    value={verifyPw}
                    onChange={(e) => {
                      setVerifyPw(e.target.value);
                      if (verifyError) setVerifyError("");
                    }}
                    className={`w-full rounded-lg border px-3 py-2 ${verifyError ? 'border-red-400' : ''}`}
                    placeholder="현재 비밀번호"
                  />
                  {/* 인라인 에러/안내 */}
                  <p className={`min-h-[1rem] text-xs ${verifyError ? 'text-red-500' : 'text-transparent'}`}>
                    {verifyError || 'placeholder'}
                  </p>

                  <div className="mt-1 flex justify-center">
                    <button
                      onClick={handleVerifyPassword}
                      disabled={verifying}
                      className="rounded-lg bg-red-500 px-5 py-2 text-white hover:bg-red-600 disabled:opacity-50"
                    >
                      {verifying ? "확인 중…" : "확인"}
                    </button>
                  </div>
                </div>
              </section>
            ) : (
              // 2) 수정 폼 단계
              <>
                <section>
                  <h2 className="mb-4 text-xl font-bold text-center">회원정보 수정</h2>
                  <div className="mx-auto grid max-w-md gap-3">
                    <label className="text-sm text-gray-600">이메일 (변경불가)</label>
                    <input value={user?.email || ''} disabled className="rounded-lg border bg-gray-100 px-3 py-2 text-gray-500" />

                    <label className="mt-3 text-sm text-gray-600">이름</label>
                    <input
                      value={username}
                      onChange={(e)=>setUsername(e.target.value)}
                      className="rounded-lg border px-3 py-2"
                      placeholder="이름"
                    />
                  </div>
                </section>

                <section className="border-t pt-6">
                  <h2 className="mb-4 text-xl font-bold text-center">비밀번호 변경 (선택)</h2>

                  <div className="mx-auto grid max-w-md gap-3">
                    {/* 현재 비밀번호 */}
                    <input
                      type="password"
                      value={currPw}
                      onChange={(e) => {
                        setCurrPw(e.target.value);
                        if (currPwError) setCurrPwError("");
                      }}
                      placeholder="현재 비밀번호"
                      className={`rounded-lg border px-3 py-2 ${currPwError ? "border-red-400" : ""}`}
                    />
                    <p className={`min-h-[1rem] text-xs ${currPwError ? "text-red-500" : "text-transparent"}`}>
                      {currPwError || "placeholder"}
                    </p>

                    {/* 새 비밀번호 */}
                    <input
                      type="password"
                      value={newPw}
                      onChange={(e) => {
                        setNewPw(e.target.value);
                        // 입력 중 실시간 유효성
                        if (e.target.value && e.target.value.length < 8) {
                          setNewPwError("새 비밀번호는 최소 8자 이상이어야 합니다.");
                        } else {
                          setNewPwError("");
                        }
                      }}
                      placeholder="새 비밀번호 (8자 이상)"
                      className={`rounded-lg border px-3 py-2 ${newPwError ? "border-red-400" : ""}`}
                    />
                    <p className={`min-h-[1rem] text-xs ${newPwError ? "text-red-500" : "text-gray-400"}`}>
                      {newPwError || "새 비밀번호는 최소 8자 이상이어야 합니다."}
                    </p>
                  </div>
                </section>

                <div className="flex flex-col items-center gap-3 border-t pt-6 sm:flex-row sm:justify-center">
                  <button
                    onClick={handleSave}
                    disabled={saving || isPasswordInvalid}
                    className="rounded-lg bg-red-500 px-4 py-2 text-white hover:bg-red-600 disabled:opacity-50"
                  >
                    {saving ? "저장 중…" : "변경사항 저장"}
                  </button>

                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="ml-auto rounded-lg border border-red-500 px-4 py-2 text-red-600 hover:bg-red-50 disabled:opacity-50"
                  >
                    {deleting ? "처리 중…" : "회원탈퇴"}
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default MyPage;