import { useState, useEffect } from 'react';
import { FolderOpen, Plus, Edit3, Trash2, X, Package } from 'lucide-react';
import { getKategoriler, createKategori, updateKategori, deleteKategori } from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';

function KategoriModal({ isOpen, onClose, onSave, kategori }) {
    const [form, setForm] = useState({ isim: '', aciklama: '' });

    useEffect(() => {
        setForm(kategori ? { isim: kategori.isim, aciklama: kategori.aciklama || '' } : { isim: '', aciklama: '' });
    }, [kategori, isOpen]);

    if (!isOpen) return null;

    const inputClass = `w-full h-11 px-4 text-[14px] font-medium rounded-xl border border-slate-200 bg-slate-50/50
    text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/10
    focus:border-blue-500 focus:bg-white transition-all duration-300 ease-out shadow-inner`;

    const labelClass = "text-[12px] font-bold text-slate-700 mb-2 block tracking-wide uppercase";

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity" />
            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md animate-fade-in ring-1 ring-slate-900/5" onClick={e => e.stopPropagation()}>

                <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-slate-50/50 rounded-t-2xl">
                    <div>
                        <h3 className="text-[18px] font-extrabold text-slate-900 leading-tight">
                            {kategori ? 'Sınıflandırma Düzenle' : 'Yeni Sınıflandırma Alanı'}
                        </h3>
                        <p className="text-[12px] font-medium text-slate-500 mt-0.5">Ürün kategorisi oluşturma paneli</p>
                    </div>
                    <button onClick={onClose} className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-sm hover:bg-slate-100 hover:text-slate-800 flex items-center justify-center transition-all">
                        <X className="w-5 h-5 text-slate-500" />
                    </button>
                </div>

                <form onSubmit={e => { e.preventDefault(); onSave(form); }} className="p-6 space-y-6">
                    <div>
                        <label className={labelClass}>Kategori İsmi *</label>
                        <input className={inputClass} value={form.isim}
                            onChange={e => setForm({ ...form, isim: e.target.value })} placeholder="Örn: Endüstriyel Motorlar" required />
                    </div>
                    <div>
                        <label className={labelClass}>Alt Açıklama Metni</label>
                        <textarea className={`${inputClass} h-28 resize-none py-3`} value={form.aciklama}
                            onChange={e => setForm({ ...form, aciklama: e.target.value })} placeholder="Bu kategoriye dair sistem içi yönlendirme notları..." />
                    </div>
                    <div className="flex gap-3 pt-4 border-t border-slate-100">
                        <button type="button" onClick={onClose}
                            className="flex-1 h-11 rounded-xl border border-slate-200 text-[14px] font-bold text-slate-600 hover:bg-slate-50 transition-colors">
                            İptal Et
                        </button>
                        <button type="submit"
                            className="flex-1 h-11 rounded-xl bg-blue-600 text-[14px] font-bold text-white hover:bg-blue-700 transition-all shadow-[0_4px_14px_0_rgba(37,99,235,0.39)] hover:shadow-[0_6px_20px_rgba(37,99,235,0.23)] hover:-translate-y-0.5">
                            {kategori ? 'Güncelle' : 'Kategori Yarat'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// Renk paleti — her kategoriye farklı kurumsal gradient
const COLORS = [
    'from-blue-500 to-indigo-600 shadow-blue-500/30 border-blue-400/20',
    'from-emerald-500 to-teal-600 shadow-emerald-500/30 border-emerald-400/20',
    'from-amber-500 to-orange-600 shadow-amber-500/30 border-amber-400/20',
    'from-rose-500 to-red-600 shadow-rose-500/30 border-rose-400/20',
    'from-violet-500 to-purple-600 shadow-violet-500/30 border-violet-400/20',
    'from-cyan-500 to-sky-600 shadow-cyan-500/30 border-cyan-400/20',
    'from-slate-600 to-slate-800 shadow-slate-500/30 border-slate-500/20',
];

export default function KategorilerPage() {
    const [kategoriler, setKategoriler] = useState([]);
    const { loading, run } = useAsync(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [editKategori, setEditKategori] = useState(null);

    const fetchData = async () => {
        try {
            const res = await run(() => getKategoriler());
            setKategoriler(res.data);
        } catch {
            toast.error('Kategoriler yüklenemedi');
        }
    };

    useEffect(() => { fetchData(); }, []);

    const handleDelete = async (id, isim) => {
        if (!confirm(`Tüm bağlı ürünlerle ilişkisini kopararak "${isim}" isimli sınıfı silmek istiyor musunuz?`)) return;
        try {
            await deleteKategori(id);
            toast.success('Kategori kayıtları sistemden silindi.');
            fetchData();
        } catch (err) {
            toast.error(hataMetni(err, 'İçerisinde ürün bulunan kategoriler silinemez'));
        }
    };

    const handleSave = async (data) => {
        try {
            if (editKategori) {
                await updateKategori(editKategori.id, data);
                toast.success('Güncelleme sistem veritabanına işlendi.');
            } else {
                await createKategori(data);
                toast.success('Yeni kategori kaydı oluşturuldu.');
            }
            setModalOpen(false);
            setEditKategori(null);
            fetchData();
        } catch (err) {
            toast.error(hataMetni(err, 'İşlem başarısız'));
        }
    };

    return (
        <div className="space-y-6 max-w-[1400px]">

            {/* Header Actions */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/80 shadow-sm">
                <div>
                    <h2 className="text-[15px] sm:text-[16px] font-extrabold text-slate-800">Organizasyon Şeması</h2>
                    <p className="text-[12px] sm:text-[13px] font-medium text-slate-500 mt-0.5">Mevcut tanımlı <span className="font-bold text-blue-600">{kategoriler.length} adet</span> ana sınıflandırma var.</p>
                </div>
                <button onClick={() => { setEditKategori(null); setModalOpen(true); }}
                    className="h-11 px-6 bg-blue-600 text-white text-[14px] font-bold rounded-xl whitespace-nowrap
            hover:bg-blue-700 transition-all shadow-[0_4px_14px_0_rgba(37,99,235,0.39)] hover:shadow-[0_6px_20px_rgba(37,99,235,0.23)] hover:-translate-y-0.5
            flex items-center justify-center gap-2 w-full sm:w-auto">
                    <Plus className="w-5 h-5 stroke-[2.5px]" /> Yeni Oluştur
                </button>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {[...Array(8)].map((_, i) => <div key={i} className="bg-slate-200 animate-pulse h-44 rounded-2xl" />)}
                </div>
            ) : kategoriler.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 text-center bg-white rounded-2xl border border-dashed border-slate-300">
                    <FolderOpen className="w-16 h-16 text-slate-300 mb-4" />
                    <h3 className="text-[18px] font-bold text-slate-800 mb-2">Henüz Kategori Tanımlanmamış</h3>
                    <p className="text-[14px] text-slate-500 font-medium max-w-sm">
                        Deponuzdaki ürünleri organize etmek için yukarıdan "Yeni Oluştur" diyerek ilk sınıflandırmanızı yapın.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {kategoriler.map((kat, i) => {
                        const colorClass = COLORS[i % COLORS.length];
                        return (
                            <div key={kat.id}
                                className="group bg-white rounded-2xl border border-slate-200/80 p-4 sm:p-6 flex flex-col justify-between
                  shadow-sm hover:shadow-xl hover:border-slate-300 hover:-translate-y-1 transition-all duration-300 animate-fade-in relative overflow-hidden"
                                style={{ animationDelay: `${i * 40}ms` }}>

                                {/* Decoration blob */}
                                <div className="absolute -right-12 -top-12 w-32 h-32 bg-slate-50 rounded-full blur-3xl group-hover:bg-blue-50/50 transition-colors duration-500 -z-10" />

                                <div>
                                    <div className="flex items-start justify-between mb-5">
                                        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClass}
                      flex items-center justify-center shadow-lg border border-white/20 group-hover:scale-110 transition-transform duration-500 ease-out`}>
                                            <FolderOpen className="w-6 h-6 text-white" />
                                        </div>

                                        <div className="flex items-center gap-1.5 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity duration-300 bg-white/80 backdrop-blur-sm rounded-lg py-1 px-1 -mr-2">
                                            <button onClick={() => { setEditKategori(kat); setModalOpen(true); }}
                                                className="w-8 h-8 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-300 flex items-center justify-center shadow-sm"
                                                title="İsmi veya Açıklamayı Değiştir">
                                                <Edit3 className="w-4 h-4" />
                                            </button>
                                            <button onClick={() => handleDelete(kat.id, kat.isim)}
                                                className="w-8 h-8 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-red-600 hover:border-red-300 flex items-center justify-center shadow-sm"
                                                title="Kaydı Tamamen Sil">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                    <h3 className="text-[16px] sm:text-[18px] font-extrabold text-slate-900 leading-tight mb-2 tracking-tight group-hover:text-blue-700 transition-colors">{kat.isim}</h3>
                                    <p className="text-[13px] font-medium text-slate-500 line-clamp-3 leading-relaxed">
                                        {kat.aciklama || 'Bu klasörme yapısına dair ek bir detay veya kural opsiyonel olarak tanımlanmamıştır.'}
                                    </p>
                                </div>

                                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">ID Ref: {kat.id.toString().padStart(4, '0')}</span>
                                    <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-md border border-slate-100">
                                        <Package className="w-3.5 h-3.5 text-slate-400" />
                                        <span className="text-[11px] font-bold text-slate-600">Aktif</span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            <KategoriModal isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditKategori(null); }}
                onSave={handleSave} kategori={editKategori} />
        </div>
    );
}
