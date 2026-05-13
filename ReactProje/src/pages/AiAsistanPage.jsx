import { useEffect, useRef, useState, useCallback } from 'react';
import { motion as Motion } from 'framer-motion';
import { Sparkles, Plus, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import {
  useAiChatMutation,
  useAiOturumSifirlaMutation,
} from '../queries/aiAsistanQueries';
import EmptyState from '../components/aiAsistan/EmptyState';
import ChatMessage from '../components/aiAsistan/ChatMessage';
import MessageInput from '../components/aiAsistan/MessageInput';
import { hataMetni } from '../utils/hata';

const CHAT_SAMPLES = [
  'Aktif palet sayÄ±sÄ± kaÃ§?',
  '/docs FEFO mantÄ±ÄŸÄ± nedir?',
  'Son 7 gÃ¼nde gelen mal kabul sayÄ±sÄ±',
  '/docs Docker compose ile proje nasÄ±l baÅŸlatÄ±lÄ±r?',
  'SKT\'si 30 gÃ¼nden az kalan lotlar',
  '/docs DocAiService hangi sÄ±nÄ±rlara sahip?',
];

export default function AiAsistanPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const scrollRef = useRef(null);

  const chatMutation = useAiChatMutation();
  const sifirlaMutation = useAiOturumSifirlaMutation();
  const isLoading = chatMutation.isPending;

  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendQuestion = useCallback(
    async (rawSoru) => {
      const soru = rawSoru.trim();
      if (!soru || isLoading) return;

      const userId = `u-${Date.now()}`;
      const assistantId = `a-${Date.now()}`;

      setMessages((prev) => [
        ...prev,
        { id: userId, role: 'user', content: soru },
        { id: assistantId, role: 'assistant', content: '', pending: true },
      ]);
      setInput('');

      try {
        const res = await chatMutation.mutateAsync({
          soru,
          session_id: sessionId,
          debug: true,
          verbose: false,
        });
        if (res?.session_id && !sessionId) setSessionId(res.session_id);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: res?.cevap ?? '—',
                  pending: false,
                  uretilenSql: res?.uretilen_sql,
                  debug: res?.debug,
                  route: res?.route,
                  routeSource: res?.route_source,
                  confidence: res?.confidence,
                  sources: res?.sources ?? [],
                }
              : m
          )
        );
      } catch (err) {
        const msg = hataMetni(err, 'AI servisi yanıt vermedi.');
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: msg, pending: false, error: true } : m
          )
        );
        toast.error(msg);
      }
    },
    [isLoading, sessionId, chatMutation]
  );

  const handleSubmit = () => sendQuestion(input);
  const handlePickSample = (q) => sendQuestion(q);

  const handleNewSession = async () => {
    if (sessionId) {
      try {
        await sifirlaMutation.mutateAsync(sessionId);
      } catch {
        // sessizce devam — UI zaten temizleniyor
      }
    }
    setSessionId(null);
    setMessages([]);
    setInput('');
  };

  const samples = CHAT_SAMPLES;
  const hasMessages = messages.length > 0;

  return (
    <div className="relative h-[calc(100vh-72px)] overflow-hidden">
      {/* Soft animated background */}
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-32 -left-24 h-[420px] w-[420px] rounded-full bg-indigo-300/30 blur-[120px] dark:bg-indigo-500/20" />
        <div className="absolute -bottom-32 -right-24 h-[420px] w-[420px] rounded-full bg-fuchsia-300/30 blur-[120px] dark:bg-fuchsia-500/20" />
        <div className="absolute top-1/3 left-1/2 h-[320px] w-[320px] -translate-x-1/2 rounded-full bg-cyan-200/30 blur-[120px] dark:bg-cyan-500/15" />
      </div>

      <div className="mx-auto flex h-full max-w-4xl flex-col px-4 sm:px-6">
        {/* Header */}
        <Motion.header
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex items-center justify-between py-4"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/40 bg-gradient-to-br from-indigo-500/90 via-violet-500/90 to-fuchsia-500/90 text-white shadow-[0_6px_20px_-8px_rgba(99,102,241,0.6)]">
              <Sparkles className="h-4.5 w-4.5" />
            </div>
            <div>
              <h1 className="text-[15px] font-semibold tracking-tight text-slate-800 dark:text-white">
                AI Asistan
              </h1>
              <p className="text-[11.5px] text-slate-500 dark:text-slate-400">
                Doğal dilde sor, anında veriden cevap al
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleNewSession}
            disabled={!hasMessages || isLoading}
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200/80 bg-white/60 px-3.5 py-1.5 text-[12px] font-medium text-slate-600 backdrop-blur transition hover:border-slate-300 hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
          >
            {sifirlaMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Plus className="h-3.5 w-3.5" />
            )}
            Yeni sohbet
          </button>
        </Motion.header>

        {/* Messages */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto pb-2 [scrollbar-width:thin] [scrollbar-color:rgba(148,163,184,0.4)_transparent]"
        >
          {!hasMessages ? (
            <EmptyState samples={samples} onPick={handlePickSample} disabled={isLoading} />
          ) : (
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-5 py-6">
              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="mx-auto w-full max-w-3xl pb-4 pt-2">
          <MessageInput
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
}
