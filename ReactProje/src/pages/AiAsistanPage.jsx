import { useEffect, useRef, useState, useCallback } from 'react';
import { motion as Motion } from 'framer-motion';
import { Plus, Loader2 } from 'lucide-react';
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
  'Aktif palet sayısı kaç?',
  '/docs FEFO mantığı nedir?',
  'Son 7 günde gelen mal kabul sayısı',
  '/docs Docker compose ile proje nasıl başlatılır?',
  'SKT\'si 30 günden az kalan lotlar',
  '/docs DocAiService hangi sınırlara sahip?',
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
    <div className="relative h-[calc(100vh-72px)] overflow-hidden bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      {/* Tek nokta vurgusu: üst hairline + amber spotlight */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/60 to-transparent dark:via-amber-400/50"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[260px] w-[680px] -translate-x-1/2 -translate-y-1/3 rounded-full bg-amber-200/30 blur-[120px] dark:bg-amber-500/[0.08]"
      />

      <div className="mx-auto flex h-full max-w-3xl flex-col px-4 sm:px-6">
        {/* Header — editorial, mono monogram + serif italic accent */}
        <Motion.header
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center justify-between border-b border-zinc-200/80 py-4 dark:border-white/[0.06] sm:py-5"
        >
          <div className="flex items-center gap-3 sm:gap-4">
            <span className="select-none font-['JetBrains_Mono'] text-[13px] font-medium tracking-tight text-zinc-400 dark:text-zinc-500">
              [&nbsp;<span className="text-amber-600 dark:text-amber-400">ai</span>&nbsp;]
            </span>
            <div className="flex items-baseline gap-2.5">
              <h1 className="text-[17px] font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-[18px]">
                Asistan
              </h1>
              <span className="font-['Instrument_Serif'] text-[16px] italic leading-none text-zinc-400 dark:text-zinc-500 sm:text-[17px]">
                — depo verisi, doğal dilde
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleNewSession}
            disabled={!hasMessages || isLoading}
            className="group inline-flex items-center gap-1.5 rounded-md border border-zinc-200 bg-white px-2.5 py-1.5 font-['JetBrains_Mono'] text-[11.5px] font-medium uppercase tracking-wider text-zinc-600 transition hover:border-amber-400 hover:text-amber-700 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-zinc-200 disabled:hover:text-zinc-600 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:border-amber-400/40 dark:hover:text-amber-300"
          >
            {sifirlaMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Plus className="h-3.5 w-3.5" strokeWidth={2.25} />
            )}
            yeni
          </button>
        </Motion.header>

        {/* Messages */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto [scrollbar-color:rgba(161,161,170,0.4)_transparent] [scrollbar-width:thin]"
        >
          {!hasMessages ? (
            <EmptyState samples={samples} onPick={handlePickSample} disabled={isLoading} />
          ) : (
            <div className="flex w-full flex-col gap-7 py-7 sm:gap-8 sm:py-9">
              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="w-full border-t border-zinc-200/80 pb-4 pt-3 dark:border-white/[0.06] sm:pb-5 sm:pt-4">
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
