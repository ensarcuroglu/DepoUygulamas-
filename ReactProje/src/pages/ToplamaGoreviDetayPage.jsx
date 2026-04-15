/**
 * ToplamaGoreviDetayPage — Toplama görevi detay, başlatma ve tamamlama ekranı.
 * MVP: Tam koli zorunludur; kısmi toplama reddedilir.
 * Admin: FEFO Override diyaloğu görünür.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Package, CheckCircle, XCircle, PlayCircle, RefreshCw,
  AlertTriangle, ArrowLeft, ShieldAlert,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { hataMetni } from '../utils/hata';
import { toplamaGorevleriApi } from '../services/toplamaGorevleriApi';
import { useAuth } from '../contexts/AuthContext';

/* ─── Sabitler ──────────────────────────────────────── */

const DURUM_RENK = {
  Beklemede:   'bg-amber-50 text-amber-700',
  Atandi:      'bg-sky-50 text-sky-700',
  DevamEdiyor: 'bg-indigo-50 text-indigo-700',
  Tamamlandi:  'bg-emerald-50 text-emerald-700',
  IptalEdildi: 'bg-slate-100 text-slate-500',
};

/* ─── FEFO Override Diyaloğu ────────────────────────── */

function FefoOverrideDialog({ gorevId, onKapat, onBasarili }) {
  const [yeniPaletId, setYeniPaletId] = useState('');
  const [neden, setNeden] = useState('');
  const [yukleniyor, setYukleniyor] = useState(false);

  const gonder = async () => {
    if (!yeniPaletId || isNaN(+yeniPaletId)) {
      toast.error('Geçerli bir palet ID giriniz.');
      return;
    }
    if (neden.trim().length < 10) {
      toast.error('Override gerekçesi en az 10 karakter olmalıdır.');
      return;
    }
    setYukleniyor(true);
    try {
      await toplamaGorevleriApi.fefoOverride(gorevId, +yeniPaletId, neden.trim());
      toast.success('FEFO override uygulandı.');
      onBasarili();
    } catch (err) {
      toast.error(hataMetni(err, 'Override başarısız.'));
    } finally {
      setYukleniyor(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-center gap-2 text-rose-600">
          <ShieldAlert className="w-5 h-5" />
          <h2 className="font-semibold text-base">FEFO Override (Admin)</h2>
        </div>
        <p className="text-sm text-gray-600">
          FEFO kuralını geçersiz kılarak göreve farklı bir palet atayabilirsiniz.
          Bu işlem audit log'a kaydedilir.
        </p>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Yeni Palet ID</label>
            <input
              type="number"
              value={yeniPaletId}
              onChange={e => setYeniPaletId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-400"
              placeholder="Palet ID"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Override Gerekçesi <span className="text-gray-400">(min 10 karakter)</span>
            </label>
            <textarea
              value={neden}
              onChange={e => setNeden(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-rose-400"
              placeholder="Neden farklı palet seçilmesi gerekiyor?"
            />
            <p className="text-xs text-gray-400 mt-1">{neden.length}/10 min</p>
          </div>
        </div>
        <div className="flex gap-2 pt-2">
          <button
            onClick={onKapat}
            className="flex-1 px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            İptal
          </button>
          <button
            onClick={gonder}
            disabled={yukleniyor}
            className="flex-1 px-4 py-2 text-sm bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 transition-colors font-medium"
          >
            {yukleniyor ? 'Uygulanıyor...' : 'Override Uygula'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Bilgi Kartı ───────────────────────────────────── */

function BilgiKart({ etiket, deger, vurgu = false }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
      <p className="text-xs text-gray-500 mb-1">{etiket}</p>
      <p className={`font-semibold ${vurgu ? 'text-indigo-700 text-lg' : 'text-gray-800 text-sm'}`}>
        {deger || '-'}
      </p>
    </div>
  );
}

/* ─── Ana Sayfa ─────────────────────────────────────── */

export default function ToplamaGoreviDetayPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.rol === 'admin';

  const [gorev, setGorev] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [islemYukleniyor, setIslemYukleniyor] = useState(false);
  const [overrideAcik, setOverrideAcik] = useState(false);
  const [iptalAcik, setIptalAcik] = useState(false);
  const [iptalNeden, setIptalNeden] = useState('');

  const yukle = async () => {
    setYukleniyor(true);
    try {
      const data = await toplamaGorevleriApi.getir(+id);
      setGorev(data);
    } catch (err) {
      toast.error(hataMetni(err, 'Görev yüklenemedi.'));
    } finally {
      setYukleniyor(false);
    }
  };

  useEffect(() => { yukle(); }, [id]);

  const islem = async (fn, basariMesaji) => {
    setIslemYukleniyor(true);
    try {
      const guncellenen = await fn();
      setGorev(guncellenen);
      toast.success(basariMesaji);
    } catch (err) {
      toast.error(hataMetni(err, 'İşlem başarısız.'));
    } finally {
      setIslemYukleniyor(false);
    }
  };

  const baslat = () => islem(
    () => toplamaGorevleriApi.baslat(+id),
    'Görev başlatıldı.'
  );

  const tamamla = () => {
    if (!window.confirm(`Paletteki tüm ${gorev?.koli_adedi ?? ''} koliyi topladığınızı onaylıyor musunuz? Kısmi toplama kabul edilmez.`)) return;
    islem(
      () => toplamaGorevleriApi.tamamla(+id),
      'Görev tamamlandı!'
    );
  };

  const iptalEt = async () => {
    setIslemYukleniyor(true);
    try {
      const guncellenen = await toplamaGorevleriApi.iptalEt(+id, iptalNeden || null);
      setGorev(guncellenen);
      toast.success('Görev iptal edildi.');
      setIptalAcik(false);
    } catch (err) {
      toast.error(hataMetni(err, 'İptal başarısız.'));
    } finally {
      setIslemYukleniyor(false);
    }
  };

  if (yukleniyor) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!gorev) {
    return (
      <div className="p-6 text-center text-gray-500">
        <AlertTriangle className="w-10 h-10 mx-auto mb-2 opacity-40" />
        <p>Görev bulunamadı.</p>
      </div>
    );
  }

  const durumRenk = DURUM_RENK[gorev.durum] || 'bg-gray-100 text-gray-600';
  const aktif = !['Tamamlandi', 'IptalEdildi'].includes(gorev.durum);

  return (
    <div className="p-4 md:p-6 max-w-2xl mx-auto space-y-5">
      {/* Geri + Başlık */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/toplama-gorevleri')} className="text-gray-400 hover:text-gray-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-lg font-semibold text-gray-900">Toplama Görevi #{gorev.sira_no}</h1>
          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium mt-0.5 ${durumRenk}`}>
            {gorev.durum}
          </span>
        </div>
        {gorev.fefo_override && (
          <span className="text-xs bg-rose-50 text-rose-600 border border-rose-200 px-2 py-0.5 rounded-full font-medium">
            FEFO Override
          </span>
        )}
      </div>

      {/* Bilgi Kartları */}
      <div className="grid grid-cols-2 gap-3">
        <BilgiKart etiket="Ürün" deger={gorev.urun_adi} />
        <BilgiKart etiket="Lot No" deger={gorev.lot_no} />
        <BilgiKart etiket="Palet No" deger={gorev.palet_no} />
        <BilgiKart etiket="Koli Adedi" deger={gorev.koli_adedi != null ? `${gorev.koli_adedi} koli` : '-'} vurgu />
      </div>

      {gorev.atanan_kullanici_adi && (
        <div className="bg-indigo-50 rounded-xl p-3 text-sm text-indigo-700 border border-indigo-100">
          Atanan Operatör: <span className="font-semibold">{gorev.atanan_kullanici_adi}</span>
        </div>
      )}

      {gorev.override_neden && (
        <div className="bg-rose-50 rounded-xl p-3 text-sm text-rose-700 border border-rose-100">
          <p className="font-medium mb-0.5">Override Gerekçesi</p>
          <p>{gorev.override_neden}</p>
        </div>
      )}

      {/* Aksiyon Butonları */}
      {aktif && (
        <div className="space-y-2 pt-2">
          {gorev.durum === 'Atandi' && (
            <button
              onClick={baslat}
              disabled={islemYukleniyor}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              <PlayCircle className="w-5 h-5" />
              Görevi Başlat
            </button>
          )}

          {gorev.durum === 'DevamEdiyor' && (
            <button
              onClick={tamamla}
              disabled={islemYukleniyor}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              <CheckCircle className="w-5 h-5" />
              Tamamla ({gorev.koli_adedi} koli — tam)
            </button>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => setIptalAcik(true)}
              disabled={islemYukleniyor}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-red-200 text-red-600 rounded-xl text-sm hover:bg-red-50 disabled:opacity-50 transition-colors"
            >
              <XCircle className="w-4 h-4" />
              İptal Et
            </button>

            {isAdmin && (gorev.durum === 'Beklemede' || gorev.durum === 'Atandi') && (
              <button
                onClick={() => setOverrideAcik(true)}
                disabled={islemYukleniyor}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border border-rose-300 text-rose-600 rounded-xl text-sm hover:bg-rose-50 disabled:opacity-50 transition-colors"
              >
                <ShieldAlert className="w-4 h-4" />
                FEFO Override
              </button>
            )}
          </div>
        </div>
      )}

      {/* İptal Diyaloğu (inline) */}
      {iptalAcik && (
        <div className="border border-red-200 rounded-xl p-4 bg-red-50 space-y-3">
          <p className="text-sm font-medium text-red-700">Görevi iptal etmek istiyor musunuz?</p>
          <textarea
            value={iptalNeden}
            onChange={e => setIptalNeden(e.target.value)}
            rows={2}
            placeholder="İptal nedeni (opsiyonel)"
            className="w-full border border-red-200 rounded-lg px-3 py-2 text-sm resize-none bg-white"
          />
          <div className="flex gap-2">
            <button
              onClick={() => setIptalAcik(false)}
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              Vazgeç
            </button>
            <button
              onClick={iptalEt}
              disabled={islemYukleniyor}
              className="flex-1 px-3 py-2 bg-red-600 text-white rounded-lg text-sm font-medium disabled:opacity-50"
            >
              İptal Et
            </button>
          </div>
        </div>
      )}

      {/* FEFO Override Diyaloğu */}
      {overrideAcik && (
        <FefoOverrideDialog
          gorevId={+id}
          onKapat={() => setOverrideAcik(false)}
          onBasarili={() => { setOverrideAcik(false); yukle(); }}
        />
      )}
    </div>
  );
}
