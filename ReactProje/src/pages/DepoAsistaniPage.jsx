import { useCallback, useEffect, useRef, useState } from 'react';
import { motion as Motion } from 'framer-motion';
import { Plus, Sparkles, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';

import { useAuth } from '../contexts/AuthContext';
import { useDepoAsistaniChatMutation } from '../queries/depoAsistaniQueries';
import BaglamRozeti from '../components/depoAsistani/BaglamRozeti';
import BosDurum from '../components/depoAsistani/BosDurum';
import ChatMesaj from '../components/depoAsistani/ChatMesaj';
import MesajInput from '../components/depoAsistani/MesajInput';
import { hataMetni } from '../utils/hata';

/**
 * Depo Asistani sayfasi.
 *
 * Mimari:
 * - Sohbet state'i sayfaya ait (useState). Backend tarafinda LangGraph
 *   SqliteSaver thread_id={kullanici}:{session} ile mesaj gecmisini saklar;
 *   frontend `session_id`'yi koruyarak ayni thread'e devam eder.
 * - LLM bir HITL aleti onerirse `chat` cevabinda `taslak` alani dolar;
 *   asistan mesaj balonu altina `TaslakKart` render edilir.
 * - Aksiyon onaylandiginda BackendProje use case'i veritabanini gunceller;
 *   query invalidasyonu kart durumunu otomatik tazeler.
 *
 * Yukseklik stratejisi:
 *   DashboardLayout — Header sticky 64-72px + main padding p-3/p-5/p-8.
 *   Sayfa viewport'tan bu chrome'u dusen `calc(100dvh - X)` ile sabit
 *   yukseklik aliyor; ic ic header/sohbet/input kendi flex column'unda
 *   tek scroll'a (sadece sohbet listesi) sigiyor.
 */
export default function DepoAsistaniPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const scrollRef = useRef(null);

  const chatMutation = useDepoAsistaniChatMutation();
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
      if (!soru || isLoading) return false;

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
          aktif_gorev_id: null,
          aktif_ekran: 'depo-asistani',
        });
        if (res?.session_id && !sessionId) setSessionId(res.session_id);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: res?.cevap ?? '—',
                  pending: false,
                  taslak: res?.taslak ?? null,
                  debug: res?.debug ?? null,
                }
              : m,
          ),
        );
        return true;
      } catch (err) {
        const mesaj = hataMetni(err) || 'Asistan cevap veremedi.';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: mesaj, pending: false, error: true }
              : m,
          ),
        );
        toast.error(mesaj);
        return false;
      }
    },
    [chatMutation, isLoading, sessionId],
  );

  const handleTaslakUndo = useCallback(
    async (soru) => {
      return sendQuestion(soru);
    },
    [sendQuestion],
  );

  const handleYeniSohbet = () => {
    setMessages([]);
    setSessionId(null);
    setInput('');
  };

  const hasMessages = messages.length > 0;

  return (
    <div
      className="relative flex flex-col overflow-hidden rounded-2xl border border-white/60 bg-gradient-to-b from-surface-secondary via-surface-secondary to-surface shadow-sm
                 h-[calc(100dvh-88px)] sm:h-[calc(100dvh-104px)] lg:h-[calc(100dvh-136px)]"
    >
      {/* Dekoratif arka plan orb'lar */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -left-24 -top-28 h-[320px] w-[320px] rounded-full bg-primary-200/30 blur-3xl" />
        <div className="absolute -right-24 top-28 h-[280px] w-[280px] rounded-full bg-accent-400/15 blur-3xl" />
        <div className="absolute -bottom-20 left-1/3 h-[220px] w-[420px] rounded-full bg-primary-100/40 blur-3xl" />
      </div>

      {/* Header — kompakt glass */}
      <header className="relative z-10 shrink-0 border-b border-white/40 bg-white/65 px-4 py-3 backdrop-blur-xl sm:px-6 sm:py-3.5">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-3">
          {/* Sol: avatar + title + alt satir */}
          <div className="flex min-w-0 items-center gap-3">
            <div className="relative shrink-0">
              <div
                aria-hidden
                className="absolute inset-0 -m-0.5 rounded-2xl bg-gradient-to-br from-primary-400/40 to-accent-500/30 blur-md"
              />
              <Motion.div
                animate={{
                  boxShadow: [
                    '0 0 0 0 rgba(59,130,246,0.0)',
                    '0 0 0 6px rgba(59,130,246,0.10)',
                    '0 0 0 0 rgba(59,130,246,0.0)',
                  ],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                className="relative inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-md shadow-primary-500/25 ring-1 ring-white/40"
              >
                <Sparkles className="h-4.5 w-4.5" strokeWidth={2.25} aria-hidden />
              </Motion.div>
            </div>
            <div className="flex min-w-0 flex-col leading-tight">
              <div className="flex items-center gap-2">
                <h1 className="bg-gradient-to-r from-text-primary to-primary-700 bg-clip-text text-base font-semibold tracking-tight text-transparent">
                  Depo Asistanı
                </h1>
                <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-success-600">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-success-500" />
                  canlı
                </span>
              </div>
              <p className="hidden items-center gap-1.5 text-[11px] text-text-secondary sm:flex">
                <ShieldCheck
                  className="h-3 w-3 text-primary-600"
                  strokeWidth={2}
                  aria-hidden
                />
                Aksiyonlar önce öneri olarak gelir, onayınızla uygulanır.
              </p>
            </div>
          </div>

          {/* Sag: baglam rozetleri + yeni sohbet */}
          <div className="flex flex-wrap items-center justify-end gap-2">
            <BaglamRozeti
              rol={user?.rol}
              aktifEkran="depo-asistani"
              aktifGorevId={null}
            />
            <button
              type="button"
              onClick={handleYeniSohbet}
              disabled={!hasMessages}
              className="group inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-xl border border-white/60 bg-white/70 px-3 py-1.5 text-xs font-semibold text-text-primary shadow-sm backdrop-blur transition-all duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:bg-white hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 disabled:hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
              aria-label="Yeni sohbet baslat"
            >
              <Plus
                className="h-3.5 w-3.5 transition-transform duration-200 group-hover:rotate-90 group-disabled:rotate-0"
                aria-hidden
                strokeWidth={2.25}
              />
              <span className="hidden sm:inline">Yeni sohbet</span>
              <span className="sm:hidden">Yeni</span>
            </button>
          </div>
        </div>
      </header>

      {/* Sohbet alani — tek scroll noktası */}
      <div
        ref={scrollRef}
        className="relative z-10 min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6"
      >
        <div className="mx-auto max-w-4xl">
          {!hasMessages ? (
            <BosDurum onOrnekSec={(soru) => sendQuestion(soru)} />
          ) : (
            <Motion.div layout className="flex flex-col gap-5 sm:gap-6">
              {messages.map((m) => (
                <ChatMesaj
                  key={m.id}
                  message={m}
                  onTaslakUndo={handleTaslakUndo}
                />
              ))}
            </Motion.div>
          )}
        </div>
      </div>

      {/* Input bant — kompakt glass */}
      <div className="relative z-10 shrink-0 border-t border-white/40 bg-white/70 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="mx-auto max-w-4xl">
          <MesajInput
            value={input}
            onChange={setInput}
            onSubmit={() => sendQuestion(input)}
            disabled={isLoading}
          />
          <p className="mt-1.5 text-center font-mono text-[10px] uppercase tracking-[0.22em] text-text-tertiary">
            HITL · onay öncesi DB'ye uygulanmaz
          </p>
        </div>
      </div>
    </div>
  );
}
