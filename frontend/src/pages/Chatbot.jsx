// src/pages/Chatbot.jsx
import { useState, useRef, useEffect } from 'react';
import { X, Send, Minimize2, Maximize2, Sparkles } from 'lucide-react';
import { chatAPI } from '../services/api';

const IMG_SRC = '/images/bearchat.jpg';
const IMG_FALLBACK = '/images/bearchat.jpg';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  // 🔴 [삭제됨] const [useGPT, setUseGPT] = useState(true);

  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: '안녕하세요! AI 편의점 도우미입니다. 🤖\n무엇을 도와드릴까요?',
      timestamp: new Date(),
    },
  ]);

  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ✅ GPT 스트리밍 핸들러 (이제 유일한 핸들러)
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const handleGPTMessage = async (question) => {
    const baseId = messages.length + 1;

    // 1) 사용자 메시지
    setMessages(prev => [...prev, {
      id: baseId,
      type: 'user',
      text: question,
      timestamp: new Date(),
    }]);

    setSending(true);
    setIsTyping(true); // 🔴 [수정됨] 항상 true로 설정

    // 2) 봇 응답 메시지 (빈 텍스트로 시작)
    const botMsgId = baseId + 1;
    setMessages(prev => [...prev, {
      id: botMsgId,
      type: 'bot',
      text: '',
      isLoading: true,
      timestamp: new Date(),
    }]);

    let accumulatedText = '';
    let receivedProducts = [];

    try {
      await chatAPI.askGPT(question, (chunk) => {
        if (chunk.type === 'text') {
          // 텍스트 스트리밍
          accumulatedText += chunk.content;
          setMessages(prev => prev.map(msg =>
            msg.id === botMsgId
              ? { ...msg, text: accumulatedText }
              : msg
          ));
        } else if (chunk.type === 'products') {
          // 상품 데이터 즉시 추가 (누적)
          receivedProducts = [...receivedProducts, ...chunk.products];
          
          setMessages(prev => {
            const hasCard = prev.some(m => m.id === botMsgId + 1);
            if (hasCard) {
              return prev.map(m =>
                m.id === botMsgId + 1
                  ? { ...m, items: receivedProducts }
                  : m
              );
            } else {
              return [...prev, {
                id: botMsgId + 1,
                type: 'bot-items',
                items: receivedProducts,
                timestamp: new Date(),
              }];
            }
          });
        } else if (chunk.type === 'error') {
          accumulatedText += `\n\n⚠️ ${chunk.content}`;
          setMessages(prev => prev.map(msg =>
            msg.id === botMsgId
              ? { ...msg, text: accumulatedText, isLoading: false }
              : msg
          ));
        }
      });

      // 스트리밍 완료 후 로딩 해제
      setMessages(prev => prev.map(msg =>
        msg.id === botMsgId
          ? { ...msg, isLoading: false }
          : msg
      ));

    } catch (e) {
      console.error('[GPT] error:', e);
      setMessages(prev => prev.map(msg =>
        msg.id === botMsgId
          ? { ...msg, text: '죄송해요, 오류가 발생했어요. 😢', isLoading: false } // 🔴 isLoading 추가
          : msg
      ));
    } finally {
      setSending(false);
      setIsTyping(false); // 🔴 [수정됨] GPT 모드에서도 타이핑 종료
    }
  };

  // 🔴 [삭제됨] Elasticsearch 검색 핸들러 (handleESMessage)
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ( ... 기존 handleESMessage 함수 전체 삭제 ... )
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 통합 전송 핸들러 (단순화됨)
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const handleSendMessage = async () => {
    if (!inputText.trim() || sending) return;

    const question = inputText.trim();
    setInputText('');

    // 🔴 [수정됨] 항상 handleGPTMessage 호출
    await handleGPTMessage(question);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date) =>
    date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });

  return (
    <>
      {/* 플로팅 버튼 (기존과 동일) */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-10 right-12 w-20 h-20 bg-white rounded-full shadow-2xl
                     hover:scale-110 transition-transform duration-200 z-50
                     flex items-center justify-center border-2 border-red-500"
          aria-label="챗봇 열기"
        >
          <img
            src={IMG_SRC}
            alt="챗봇"
            className="w-14 h-14 object-cover rounded-full select-none"
            onError={(e) => {
              if (e.currentTarget.dataset.fallback === '1') return;
              e.currentTarget.dataset.fallback = '1';
              e.currentTarget.src = IMG_FALLBACK;
            }}
          />
        </button>
      )}

      {/* 챗봇 창 */}
      {isOpen && (
        <div
          className={`fixed bottom-6 right-6 bg-white rounded-2xl shadow-2xl z-50
                      flex flex-col transition-all duration-300
                      ${isMinimized ? 'w-80 h-16' : 'w-96 h-[600px]'}`}
        >
          {/* 헤더 */}
          <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white
                          px-4 py-3 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img
                src={IMG_SRC}
                alt="챗봇"
                className="w-10 h-10 rounded-full border-2 border-white select-none"
                onError={(e) => {
                  if (e.currentTarget.dataset.fallback === '1') return;
                  e.currentTarget.dataset.fallback = '1';
                  e.currentTarget.src = IMG_FALLBACK;
                }}
              />
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-lg">편의점 도우미</h3>
                  <Sparkles className="w-4 h-4" /> {/* 🔴 항상 AI 모드이므로 스파클 고정 */}
                </div>
                {/* 🔴 [수정됨] 상태 텍스트 고정 */}
                <p className="text-xs text-red-100">
                  AI로 똑똑하게 검색 🤖
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* 🔴 [삭제됨] GPT 토글 버튼 */}
              
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
              >
                {isMinimized ? <Maximize2 className="w-5 h-5" /> : <Minimize2 className="w-5 h-5" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* 메시지 영역 (기존과 동일) */}
          {!isMinimized && (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                        message.type === 'user'
                          ? 'bg-red-500 text-white rounded-br-none'
                          : 'bg-white text-gray-800 shadow-sm rounded-bl-none'
                      }`}
                    >
                      {message.type === 'bot-items' ? (
                        <div className="space-y-2">
                          <div className="grid grid-cols-2 gap-2">
                            {message.items.map((it, idx) => (
                              <div key={it.id ?? idx} className="border rounded-lg overflow-hidden">
                                <div className="w-full h-24 bg-gray-100">
                                  {it.image_url || it.item_img_src || it.img ? (
                                    <img
                                      src={it.image_url || it.item_img_src || it.img}
                                      alt={it.name ?? '상품'}
                                      className="w-full h-24 object-cover"
                                      loading="lazy"
                                    />
                                  ) : (
                                    <div className="w-full h-24 flex items-center justify-center text-xs text-gray-400">
                                      이미지 없음
                                    </div>
                                  )}
                                </div>
                                <div className="p-2">
                                  <p className="text-xs font-semibold line-clamp-2">
                                    {it.name ?? '-'}
                                  </p>
                                  <p className="text-xs text-gray-600 mt-1">
                                    {Number.isFinite(Number(it.price)) ? `${Number(it.price).toLocaleString()}원` : (it.price ?? '-')}
                                  </p>
                                  {(it.promotionType || it.promotion_type) && (
                                    <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-red-50 text-red-600 border border-red-200">
                                      {it.promotionType || it.promotion_type}
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <>
                          {message.isLoading && !message.text && (
                            <div className="flex gap-1 py-2">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                            </div>
                          )}
                          
                          {message.text && (
                            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
                          )}
                          
                          {message.isLoading && message.text && (
                            <div className="flex gap-1 mt-2">
                              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                            </div>
                          )}
                        </>
                      )}
                      <span
                        className={`text-xs mt-1 block ${
                          message.type === 'user' ? 'text-red-100' : 'text-gray-400'
                        }`}
                      >
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                  </div>
                ))}

                <div ref={messagesEndRef} />
              </div>

              {/* 입력 영역 */}
              <div className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={handleKeyPress}
                    // 🔴 [수정됨] placeholder 고정
                    placeholder={sending ? '처리 중...' : 'AI에게 물어보세요...'}
                    disabled={sending}
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-full
                               focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent
                               text-sm disabled:bg-gray-100"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputText.trim() || sending}
                    className="p-2.5 bg-red-500 text-white rounded-full
                               hover:bg-red-600 transition-colors disabled:opacity-50
                               disabled:cursor-not-allowed flex-shrink-0"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>

                {/* 빠른 답변 버튼 */}
                <div className="flex gap-2 mt-3 flex-wrap">
                  {/* 🔴 [수정됨] 버튼 리스트 고정 */}
                  {[
                    'CU 1+1 추천', '만원 이하 가성비', 'GS vs CU 비교', '신상품 알려줘'
                  ].map((quick) => (
                    <button
                      key={quick}
                      onClick={() => setInputText(quick)}
                      disabled={sending}
                      className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-full
                                 hover:bg-gray-200 transition-colors disabled:opacity-50"
                    >
                      {quick}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};

export default Chatbot;