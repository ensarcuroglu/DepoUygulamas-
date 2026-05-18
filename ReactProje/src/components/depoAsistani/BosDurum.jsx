import { Sparkles } from 'lucide-react';

const ORNEK_SORULAR = [
  'Su an saat kac?',
  'Bekleyen yerlestirme gorevimi B-12-3 konumuna tasi.',
  'Hangi yetkilere sahibim?',
  'Bugun hangi gun?',
];

/**
 * Sayfa ilk acildiginda gosterilen bos durum. Ornek sorular tiklanabilir
 * cip'ler olarak sunulur. Sibling AiAsistan EmptyState ile ayni dili
 * konusur ama daha kompakt.
 */
export default function BosDurum({ onOrnekSec }) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-6 px-4 py-12 text-center">
      <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-50">
        <Sparkles
          className="h-6 w-6 text-primary-700"
          strokeWidth={2}
          aria-hidden
        />
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-text-primary">
          Depo Asistani'na hos geldiniz
        </h2>
        <p className="text-sm leading-relaxed text-zinc-600">
          Sorunuzu yazin veya asagidaki orneklerden birini seciniz. Asistanin
          oneri ettigi her aksiyon kullanici onayindan once veritabanina
          uygulanmaz.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-2">
        {ORNEK_SORULAR.map((soru) => (
          <button
            key={soru}
            type="button"
            onClick={() => onOrnekSec?.(soru)}
            className="cursor-pointer rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-medium text-text-primary transition-colors duration-200 hover:border-primary-500 hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            {soru}
          </button>
        ))}
      </div>
    </div>
  );
}
