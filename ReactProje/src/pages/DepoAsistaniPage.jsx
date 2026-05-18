import { useCallback, useEffect, useRef, useState } from 'react';
import { motion as Motion } from 'framer-motion';
import { Plus, Sparkles } from 'lucide-react';
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

  return (
    <div className="flex h-full flex-col bg-surface-secondary">
      {/* Sayfa basligi */}
      <header className="border-b border-border bg-surface px-6 py-4">
        <div className="mx-auto flex max-w-4xl flex-col gap-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50">
                <Sparkles
                  className="h-5 w-5 text-primary-700"
                  strokeWidth={2}
                  aria-hidden
                />
              </div>
              <div>
                <h1 className="text-base font-semibold text-text-primary">
                  Depo Asistani
                </h1>
                <p className="text-xs text-zinc-500">
                  Aksiyonlar oneri olarak doner; onayinizla uygulanir.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleYeniSohbet}
              disabled={messages.length === 0}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-medium text-text-primary transition-colors duration-200 hover:bg-surface-tertiary disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Yeni sohbet baslat"
            >
              <Plus className="h-3.5 w-3.5" aria-hidden strokeWidth={2.25} />
              Yeni sohbet
            </button>
          </div>
          <BaglamRozeti
            rol={user?.rol}
            aktifEkran="depo-asistani"
            aktifGorevId={null}
          />
        </div>
      </header>

      {/* Sohbet alani */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        <div className="mx-auto max-w-4xl">
          {messages.length === 0 ? (
            <BosDurum onOrnekSec={(soru) => sendQuestion(soru)} />
          ) : (
            <Motion.div layout className="flex flex-col gap-6">
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

      {/* Input */}
      <div className="border-t border-border bg-surface px-6 py-4">
        <div className="mx-auto max-w-4xl">
          <MesajInput
            value={input}
            onChange={setInput}
            onSubmit={() => sendQuestion(input)}
            disabled={isLoading}
          />
          <p className="mt-2 text-center font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-400">
            HITL onerileri kullanici onayindan once veritabanina uygulanmaz
          </p>
        </div>
      </div>
    </div>
  );
}
