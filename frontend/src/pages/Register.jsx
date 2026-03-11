import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserPlus, Mail, Lock, User as UserIcon, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';

const Register = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [passwordStrength, setPasswordStrength] = useState({
    strength: 0,
    message: ''
  });

  // 비밀번호 강도 체크
  const checkPasswordStrength = (password) => {
    if (!password) {
      return { strength: 0, message: '' };
    }
    
    let strength = 0;
    const checks = {
      length: password.length >= 8,
      number: /\d/.test(password),
      lowercase: /[a-z]/.test(password),
      uppercase: /[A-Z]/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    if (checks.length) strength += 20;
    if (checks.number) strength += 20;
    if (checks.lowercase) strength += 20;
    if (checks.uppercase) strength += 20;
    if (checks.special) strength += 20;
    
    let message = '';
    if (strength < 40) message = '약함';
    else if (strength < 60) message = '보통';
    else if (strength < 80) message = '강함';
    else message = '매우 강함';
    
    return { strength, message };
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    setError('');
    
    // 비밀번호 입력 시 강도 체크
    if (name === 'password') {
      setPasswordStrength(checkPasswordStrength(value));
    }
  };

  // 유효성 검증
  const validateForm = () => {
    if (!formData.email || !formData.username || !formData.password || !formData.confirmPassword) {
      setError('모든 필드를 입력해주세요.');
      return false;
    }
    
    // 이메일 형식 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('올바른 이메일 형식이 아닙니다.');
      return false;
    }
    // 사용자 이름 길이 검증
    if (formData.username.length < 2) {
      setError('사용자 이름은 2자 이상이어야 합니다.');
      return false;
    }
    // 비밀번호 길이 검증
    if (formData.password.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다.');
      return false;
    }
    // 아래 길이 제한 로직을 추가하세요.
    if (formData.password.length > 71) {
      setError('비밀번호는 72자 이하이어야 합니다.');
      return false;
    }
    
    // 비밀번호 확인
    if (formData.password !== formData.confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      console.log('🚀 회원가입 시도:', {
        email: formData.email,
        username: formData.username,
        password: '***'
      });
      
      // API 호출
      const response = await authAPI.register(
        formData.email,
        formData.password,
        formData.username
      );
      
      console.log('✅ 회원가입 성공:', response);
      
      // 회원가입 성공 - 자동 로그인
      login(response.user, response.token);
      
      // 홈으로 이동
      navigate('/', { replace: true });
      
    } catch (err) {
      console.error('❌ 회원가입 실패 전체 에러:', err);
      console.error('❌ 에러 응답:', err.response);
      console.error('❌ 에러 데이터:', err.response?.data);
      console.error('❌ 에러 상태:', err.response?.status);
      
      // 에러 메시지 처리
      const errorMessage = err.response?.data?.detail;
      if (errorMessage?.includes('이미 존재')) {
        setError('이미 존재하는 이메일입니다.');
      } else if (err.message?.includes('Network Error')) {
        setError('서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.');
      } else {
        setError(errorMessage || `회원가입에 실패했습니다: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* 로고/타이틀 */}
        <div className="text-center mb-8">
          <div className="inline-block p-4 bg-red-500 rounded-2xl mb-4">
            <UserPlus className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            회원가입
          </h1>
          <p className="text-gray-600">
            편의점 행사상품을 놓치지 마세요!
          </p>
        </div>

        {/* 회원가입 폼 */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 에러 메시지 */}
            {error && (
              <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* 이메일 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이메일 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="your@email.com"
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* 사용자 이름 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                사용자 이름 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="닉네임을 입력하세요"
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">2자 이상 입력해주세요</p>
            </div>

            {/* 비밀번호 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="8자 이상 입력하세요"
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              
              {/* 비밀번호 강도 표시 */}
              {formData.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-600">비밀번호 강도:</span>
                    <span className={`font-medium ${
                      passwordStrength.strength < 40 ? 'text-red-500' :
                      passwordStrength.strength < 60 ? 'text-yellow-500' :
                      passwordStrength.strength < 80 ? 'text-blue-500' :
                      'text-green-500'
                    }`}>
                      {passwordStrength.message}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        passwordStrength.strength < 40 ? 'bg-red-500' :
                        passwordStrength.strength < 60 ? 'bg-yellow-500' :
                        passwordStrength.strength < 80 ? 'bg-blue-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${passwordStrength.strength}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* 비밀번호 확인 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호 확인 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="비밀번호를 다시 입력하세요"
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
                {formData.confirmPassword && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    {formData.password === formData.confirmPassword ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                )}
              </div>
              {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                <p className="text-xs text-red-500 mt-1">비밀번호가 일치하지 않습니다</p>
              )}
            </div>

            {/* 회원가입 버튼 */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-red-500 text-white rounded-lg font-semibold
                       hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2 mt-6"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  처리 중...
                </>
              ) : (
                <>
                  <UserPlus className="w-5 h-5" />
                  회원가입
                </>
              )}
            </button>
          </form>

          {/* 로그인 링크 */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              이미 계정이 있으신가요?{' '}
              <button
                onClick={() => navigate('/login')}
                className="text-red-500 font-semibold hover:text-red-600"
              >
                로그인
              </button>
            </p>
          </div>

          {/* 홈으로 돌아가기 */}
          <div className="mt-4 text-center">
            <button
              onClick={() => navigate('/')}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              홈으로 돌아가기
            </button>
          </div>
        </div>

        {/* 약관 동의 (선택사항) */}
        <p className="text-xs text-center text-gray-500 mt-4">
          회원가입 시 <button className="underline">이용약관</button> 및{' '}
          <button className="underline">개인정보처리방침</button>에 동의하게 됩니다.
        </p>
      </div>
    </div>
  );
};

export default Register;