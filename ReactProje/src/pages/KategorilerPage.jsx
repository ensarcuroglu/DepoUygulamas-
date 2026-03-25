import { useState, useEffect, useRef } from 'react';
import {
    FolderOpen, Plus, Edit3, Trash2, X, Package, Search,
    LayoutGrid, List, ChevronDown, Sparkles, Tag, Box,
    Layers, Archive, Bookmark, Star, Zap, Shield, Heart,
    Globe, Cpu, Settings, Truck, Home, Music, Camera,
    Coffee, Briefcase, ShoppingBag, Monitor, Smartphone,
    Watch, Headphones, Wrench, Palette, Leaf, Flame,
    Anchor, Crown, Diamond, Gem, Key, Lock, Map,
    Award, Target, TrendingUp, Users, AlertCircle
} from 'lucide-react';
import { getKategoriler, createKategori, updateKategori, deleteKategori } from '../services/api';
import toast from 'react-hot-toast';
import { useAsync } from '../hooks/useAsync';
import { hataMetni } from '../utils/hata';

/* ─── İkon Kütüphanesi ─── */
const ICON_MAP = {
    'FolderOpen': FolderOpen, 'Package': Package, 'Tag': Tag, 'Box': Box,
    'Layers': Layers, 'Archive': Archive, 'Bookmark': Bookmark, 'Star': Star,
    'Zap': Zap, 'Shield': Shield, 'Heart': Heart, 'Globe': Globe,
    'Cpu': Cpu, 'Settings': Settings, 'Truck': Truck, 'Home': Home,
    'Music': Music, 'Camera': Camera, 'Coffee': Coffee, 'Briefcase': Briefcase,
    'ShoppingBag': ShoppingBag, 'Monitor': Monitor, 'Smartphone': Smartphone,
    'Watch': Watch, 'Headphones': Headphones, 'Wrench': Wrench, 'Palette': Palette,
    'Leaf': Leaf, 'Flame': Flame, 'Anchor': Anchor, 'Crown': Crown,
    'Diamond': Diamond, 'Gem': Gem, 'Key': Key, 'Lock': Lock,
    'Map': Map, 'Award': Award, 'Target': Target, 'TrendingUp': TrendingUp,
    'Users': Users, 'Sparkles': Sparkles,
};

const ICON_NAMES = Object.keys(ICON_MAP);

function getIcon(name) {
    return ICON_MAP[name] || FolderOpen;
}

/* ─── Renk Paleti ─── */
const COLORS = [
    { bg: 'bg-blue-50', text: 'text-blue-600', accent: 'bg-blue-600', ring: 'ring-blue-100', dot: 'bg-blue-500' },
    { bg: 'bg-emerald-50', text: 'text-emerald-600', accent: 'bg-emerald-600', ring: 'ring-emerald-100', dot: 'bg-emerald-500' },
    { bg: 'bg-amber-50', text: 'text-amber-600', accent: 'bg-amber-600', ring: 'ring-amber-100', dot: 'bg-amber-500' },
    { bg: 'bg-rose-50', text: 'text-rose-600', accent: 'bg-rose-600', ring: 'ring-rose-100', dot: 'bg-rose-500' },
    { bg: 'bg-violet-50', text: 'text-violet-600', accent: 'bg-violet-600', ring: 'ring-violet-100', dot: 'bg-violet-500' },
    { bg: 'bg-cyan-50', text: 'text-cyan-600', accent: 'bg-cyan-600', ring: 'ring-cyan-100', dot: 'bg-cyan-500' },
    { bg: 'bg-slate-100', text: 'text-slate-600', accent: 'bg-slate-600', ring: 'ring-slate-200', dot: 'bg-slate-500' },
];

/* ─── İkon Seçici ─── */
function IconPicker({ selected, onSelect }) {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState('');
    const ref = useRef(null);
    const SelectedIcon = getIcon(selected);

    useEffect(() => {
        const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const filtered = ICON_NAMES.filter(n => n.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="relative" ref={ref}>
            <button type="button" onClick={() => setOpen(!open)}
                className="flex items-center gap-2.5 h-11 px-4 rounded-xl border border-slate-200
                bg-slate-50/50 hover:bg-white hover:border-blue-300 transition-all duration-200 w-full">
                <span className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center">
                    <SelectedIcon className="w-4 h-4 text-blue-600" />
                </span>
                <span className="text-[14px] font-medium text-slate-700 flex-1 text-left">{selected || 'FolderOpen'}</span>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
            </button>
            {open && (
                <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-xl border border-slate-200
                    shadow-lg shadow-slate-200/50 z-50 overflow-hidden animate-slideDown">
                    <div className="p-2 border-b border-slate-100">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                            <input value={search} onChange={e => setSearch(e.target.value)}
                                placeholder="İkon ara..."
                                className="w-full h-9 pl-8 pr-3 text-[13px] rounded-lg border border-slate-100
                                bg-slate-50 focus:outline-none focus:border-blue-300 focus:bg-white transition-all" />
                        </div>
                    </div>
                    <div className="grid grid-cols-7 gap-1 p-2 max-h-48 overflow-y-auto overscroll-contain">
                        {filtered.map(name => {
                            const Ico = ICON_MAP[name];
                            return (
                                <button key={name} type="button"
                                    onClick={() => { onSelect(name); setOpen(false); setSearch(''); }}
                                    title={name}
                                    className={`w-full aspect-square rounded-lg flex items-center justify-center
                                    transition-all duration-150 hover:scale-110
                                    ${selected === name
                                            ? 'bg-blue-50 text-blue-600 ring-2 ring-blue-200'
                                            : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'}`}>
                                    <Ico className="w-4 h-4" />
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

/* ─── Silme Onay Modalı ─── */
function DeleteConfirmModal({ isOpen, onClose, onConfirm, isim }) {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/30 backdrop-blur-[2px]" />
            <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 animate-scaleIn"
                onClick={e => e.stopPropagation()}>
                <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-6 h-6 text-red-500" />
                </div>
                <h3 className="text-[16px] font-bold text-slate-900 text-center mb-1">Kategoriyi Sil</h3>
                <p className="text-[13px] text-slate-500 text-center mb-6 leading-relaxed">
                    <span className="font-semibold text-slate-700">"{isim}"</span> isimli sınıfı ve tüm bağlı ürün ilişkilerini silmek istediğinize emin misiniz?
                </p>
                <div className="flex gap-3">
                    <button onClick={onClose}
                        className="flex-1 h-10 rounded-xl border border-slate-200 text-[13px] font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
                        Vazgeç
                    </button>
                    <button onClick={onConfirm}
                        className="flex-1 h-10 rounded-xl bg-red-500 text-[13px] font-semibold text-white hover:bg-red-600 transition-colors">
                        Evet, Sil
                    </button>
                </div>
            </div>
        </div>
    );
}

/* ─── Kategori Modalı ─── */
function KategoriModal({ isOpen, onClose, onSave, kategori }) {
    const [form, setForm] = useState({ isim: '', aciklama: '', ikon: 'FolderOpen' });

    useEffect(() => {
        setForm(kategori
            ? { isim: kategori.isim, aciklama: kategori.aciklama || '', ikon: kategori.ikon || 'FolderOpen' }
            : { isim: '', aciklama: '', ikon: 'FolderOpen' });
    }, [kategori, isOpen]);

    if (!isOpen) return null;

    const inputClass = `w-full h-11 px-4 text-[14px] font-medium rounded-xl border border-slate-200
    bg-slate-50/50 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-[3px]
    focus:ring-blue-500/8 focus:border-blue-400 focus:bg-white transition-all duration-200`;

    const labelClass = "text-[12px] font-semibold text-slate-500 mb-1.5 block tracking-wide uppercase";

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="absolute inset-0 bg-slate-900/30 backdrop-blur-[2px] animate-fadeIn" />
            <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md animate-scaleIn ring-1 ring-slate-900/5"
                onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
                    <div>
                        <h3 className="text-[17px] font-bold text-slate-900">
                            {kategori ? 'Kategoriyi Düzenle' : 'Yeni Kategori'}
                        </h3>
                        <p className="text-[12px] text-slate-400 mt-0.5">
                            {kategori ? 'Mevcut kategori bilgilerini güncelleyin' : 'Yeni bir ürün kategorisi oluşturun'}
                        </p>
                    </div>
                    <button onClick={onClose}
                        className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center transition-colors">
                        <X className="w-4 h-4 text-slate-400" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={e => { e.preventDefault(); onSave(form); }} className="p-6 space-y-5">
                    <div>
                        <label className={labelClass}>Kategori İsmi *</label>
                        <input className={inputClass} value={form.isim}
                            onChange={e => setForm({ ...form, isim: e.target.value })}
                            placeholder="Örn: Endüstriyel Motorlar" required />
                    </div>

                    <div>
                        <label className={labelClass}>İkon</label>
                        <IconPicker selected={form.ikon} onSelect={v => setForm({ ...form, ikon: v })} />
                    </div>

                    <div>
                        <label className={labelClass}>Açıklama</label>
                        <textarea className={`${inputClass} h-24 resize-none py-3`} value={form.aciklama}
                            onChange={e => setForm({ ...form, aciklama: e.target.value })}
                            placeholder="Kategori açıklaması (opsiyonel)..." />
                    </div>

                    <div className="flex gap-3 pt-3">
                        <button type="button" onClick={onClose}
                            className="flex-1 h-11 rounded-xl border border-slate-200 text-[13px] font-semibold
                            text-slate-600 hover:bg-slate-50 transition-colors">
                            İptal
                        </button>
                        <button type="submit"
                            className="flex-1 h-11 rounded-xl bg-blue-600 text-[13px] font-semibold text-white
                            hover:bg-blue-700 active:scale-[0.98] transition-all duration-200">
                            {kategori ? 'Güncelle' : 'Oluştur'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

/* ─── Ana Sayfa ─── */
export default function KategorilerPage() {
    const [kategoriler, setKategoriler] = useState([]);
    const { loading, run } = useAsync(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [editKategori, setEditKategori] = useState(null);
    const [viewMode, setViewMode] = useState('grid');
    const [searchTerm, setSearchTerm] = useState('');
    const [deleteTarget, setDeleteTarget] = useState(null);

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
        setDeleteTarget({ id, isim });
    };

    const confirmDelete = async () => {
        if (!deleteTarget) return;
        try {
            await deleteKategori(deleteTarget.id);
            toast.success('Kategori silindi.');
            setDeleteTarget(null);
            fetchData();
        } catch (err) {
            toast.error(hataMetni(err, 'İçerisinde ürün bulunan kategoriler silinemez'));
            setDeleteTarget(null);
        }
    };

    const handleSave = async (data) => {
        try {
            if (editKategori) {
                await updateKategori(editKategori.id, data);
                toast.success('Kategori güncellendi.');
            } else {
                await createKategori(data);
                toast.success('Yeni kategori oluşturuldu.');
            }
            setModalOpen(false);
            setEditKategori(null);
            fetchData();
        } catch (err) {
            toast.error(hataMetni(err, 'İşlem başarısız'));
        }
    };

    const filtered = kategoriler.filter(k =>
        k.isim.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (k.aciklama || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <>
            {/* CSS Animations */}
            <style>{`
                @keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
                @keyframes scaleIn { from { opacity: 0; transform: scale(0.95) translateY(4px) } to { opacity: 1; transform: scale(1) translateY(0) } }
                @keyframes slideDown { from { opacity: 0; transform: translateY(-6px) } to { opacity: 1; transform: translateY(0) } }
                @keyframes cardIn { from { opacity: 0; transform: translateY(12px) } to { opacity: 1; transform: translateY(0) } }
                .animate-fadeIn { animation: fadeIn 0.2s ease-out }
                .animate-scaleIn { animation: scaleIn 0.25s cubic-bezier(0.16,1,0.3,1) }
                .animate-slideDown { animation: slideDown 0.2s ease-out }
                .animate-cardIn { animation: cardIn 0.35s cubic-bezier(0.16,1,0.3,1) both }
            `}</style>

            <div className="space-y-5 max-w-[1400px]">

                {/* ── Header ── */}
                <div className="bg-white rounded-2xl border border-slate-200/60 p-4 sm:p-5">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                                <Layers className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                                <h2 className="text-[16px] font-bold text-slate-900">Kategoriler</h2>
                                <p className="text-[12px] text-slate-400 mt-0.5">
                                    {kategoriler.length > 0
                                        ? <><span className="font-semibold text-blue-600">{kategoriler.length}</span> kategori tanımlı</>
                                        : 'Henüz kategori yok'}
                                </p>
                            </div>
                        </div>
                        <button onClick={() => { setEditKategori(null); setModalOpen(true); }}
                            className="h-10 px-5 bg-blue-600 text-white text-[13px] font-semibold rounded-xl
                            hover:bg-blue-700 active:scale-[0.97] transition-all duration-200
                            flex items-center gap-2 w-full sm:w-auto justify-center">
                            <Plus className="w-4 h-4 stroke-[2.5px]" />
                            Yeni Kategori
                        </button>
                    </div>

                    {/* Arama & Görünüm Kontrolleri */}
                    {kategoriler.length > 0 && (
                        <div className="flex items-center gap-3 mt-4 pt-4 border-t border-slate-100">
                            <div className="relative flex-1 max-w-xs">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                                <input
                                    value={searchTerm}
                                    onChange={e => setSearchTerm(e.target.value)}
                                    placeholder="Kategori ara..."
                                    className="w-full h-9 pl-9 pr-3 text-[13px] rounded-lg border border-slate-200
                                    bg-slate-50/50 focus:outline-none focus:border-blue-300 focus:bg-white
                                    placeholder-slate-400 transition-all duration-200"
                                />
                                {searchTerm && (
                                    <button onClick={() => setSearchTerm('')}
                                        className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full
                                        bg-slate-200 hover:bg-slate-300 flex items-center justify-center transition-colors">
                                        <X className="w-2.5 h-2.5 text-slate-500" />
                                    </button>
                                )}
                            </div>
                            <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
                                <button onClick={() => setViewMode('grid')}
                                    className={`w-8 h-8 rounded-md flex items-center justify-center transition-all duration-200
                                    ${viewMode === 'grid' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}>
                                    <LayoutGrid className="w-4 h-4" />
                                </button>
                                <button onClick={() => setViewMode('list')}
                                    className={`w-8 h-8 rounded-md flex items-center justify-center transition-all duration-200
                                    ${viewMode === 'list' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}>
                                    <List className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* ── İçerik ── */}
                {loading ? (
                    <div className={viewMode === 'grid'
                        ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
                        : "space-y-2"}>
                        {[...Array(8)].map((_, i) => (
                            <div key={i} className={`bg-white border border-slate-100 animate-pulse rounded-xl
                                ${viewMode === 'grid' ? 'h-40' : 'h-16'}`} />
                        ))}
                    </div>
                ) : filtered.length === 0 && searchTerm ? (
                    <div className="flex flex-col items-center justify-center py-16 text-center bg-white rounded-2xl border border-slate-200/60">
                        <Search className="w-10 h-10 text-slate-200 mb-3" />
                        <h3 className="text-[15px] font-semibold text-slate-700 mb-1">Sonuç bulunamadı</h3>
                        <p className="text-[13px] text-slate-400">
                            "<span className="font-medium text-slate-500">{searchTerm}</span>" ile eşleşen kategori yok
                        </p>
                    </div>
                ) : kategoriler.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center bg-white rounded-2xl border border-dashed border-slate-200">
                        <div className="w-16 h-16 rounded-2xl bg-slate-50 flex items-center justify-center mb-4">
                            <FolderOpen className="w-8 h-8 text-slate-300" />
                        </div>
                        <h3 className="text-[16px] font-bold text-slate-800 mb-1.5">Henüz Kategori Yok</h3>
                        <p className="text-[13px] text-slate-400 max-w-xs leading-relaxed">
                            Ürünlerinizi organize etmek için ilk kategorinizi oluşturun
                        </p>
                    </div>
                ) : viewMode === 'grid' ? (
                    /* ── Grid View ── */
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {filtered.map((kat, i) => {
                            const color = COLORS[i % COLORS.length];
                            const Icon = getIcon(kat.ikon);
                            return (
                                <div key={kat.id}
                                    className="group bg-white rounded-xl border border-slate-200/60 p-5 flex flex-col
                                    justify-between hover:border-slate-300 transition-all duration-300 animate-cardIn
                                    hover:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.06)] relative"
                                    style={{ animationDelay: `${i * 50}ms` }}>

                                    <div>
                                        <div className="flex items-start justify-between mb-4">
                                            <div className={`w-10 h-10 rounded-xl ${color.bg} flex items-center justify-center
                                                group-hover:scale-105 transition-transform duration-300`}>
                                                <Icon className={`w-5 h-5 ${color.text}`} />
                                            </div>

                                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                                <button onClick={() => { setEditKategori(kat); setModalOpen(true); }}
                                                    className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center transition-colors"
                                                    title="Düzenle">
                                                    <Edit3 className="w-3.5 h-3.5 text-slate-400 hover:text-blue-600" />
                                                </button>
                                                <button onClick={() => handleDelete(kat.id, kat.isim)}
                                                    className="w-7 h-7 rounded-lg hover:bg-red-50 flex items-center justify-center transition-colors"
                                                    title="Sil">
                                                    <Trash2 className="w-3.5 h-3.5 text-slate-400 hover:text-red-500" />
                                                </button>
                                            </div>
                                        </div>

                                        <h3 className="text-[15px] font-bold text-slate-900 mb-1.5 leading-tight
                                            group-hover:text-blue-600 transition-colors duration-200">
                                            {kat.isim}
                                        </h3>
                                        <p className="text-[12px] text-slate-400 line-clamp-2 leading-relaxed">
                                            {kat.aciklama || 'Açıklama eklenmemiş'}
                                        </p>
                                    </div>

                                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                                        <span className="text-[10px] font-medium text-slate-300 uppercase tracking-wider">
                                            #{kat.id.toString().padStart(4, '0')}
                                        </span>
                                        <div className="flex items-center gap-1.5">
                                            <div className={`w-1.5 h-1.5 rounded-full ${color.dot}`} />
                                            <span className="text-[10px] font-semibold text-slate-400">Aktif</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    /* ── List View ── */
                    <div className="bg-white rounded-xl border border-slate-200/60 divide-y divide-slate-100 overflow-hidden">
                        {filtered.map((kat, i) => {
                            const color = COLORS[i % COLORS.length];
                            const Icon = getIcon(kat.ikon);
                            return (
                                <div key={kat.id}
                                    className="group flex items-center gap-4 px-4 sm:px-5 py-3.5
                                    hover:bg-slate-50/50 transition-colors duration-200 animate-cardIn"
                                    style={{ animationDelay: `${i * 30}ms` }}>

                                    <div className={`w-9 h-9 rounded-lg ${color.bg} flex items-center justify-center
                                        shrink-0 group-hover:scale-105 transition-transform duration-300`}>
                                        <Icon className={`w-4 h-4 ${color.text}`} />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <h3 className="text-[14px] font-semibold text-slate-800 truncate
                                            group-hover:text-blue-600 transition-colors">
                                            {kat.isim}
                                        </h3>
                                        <p className="text-[12px] text-slate-400 truncate">
                                            {kat.aciklama || 'Açıklama eklenmemiş'}
                                        </p>
                                    </div>

                                    <div className="hidden sm:flex items-center gap-1.5 mr-2">
                                        <div className={`w-1.5 h-1.5 rounded-full ${color.dot}`} />
                                        <span className="text-[11px] font-medium text-slate-400">Aktif</span>
                                    </div>

                                    <span className="hidden sm:block text-[10px] font-medium text-slate-300 uppercase tracking-wider mr-2">
                                        #{kat.id.toString().padStart(4, '0')}
                                    </span>

                                    <div className="flex items-center gap-1 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity duration-200">
                                        <button onClick={() => { setEditKategori(kat); setModalOpen(true); }}
                                            className="w-7 h-7 rounded-lg hover:bg-white hover:shadow-sm flex items-center justify-center transition-all"
                                            title="Düzenle">
                                            <Edit3 className="w-3.5 h-3.5 text-slate-400" />
                                        </button>
                                        <button onClick={() => handleDelete(kat.id, kat.isim)}
                                            className="w-7 h-7 rounded-lg hover:bg-red-50 flex items-center justify-center transition-all"
                                            title="Sil">
                                            <Trash2 className="w-3.5 h-3.5 text-slate-400" />
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* ── Modaller ── */}
            <KategoriModal isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditKategori(null); }}
                onSave={handleSave} kategori={editKategori} />

            <DeleteConfirmModal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)}
                onConfirm={confirmDelete} isim={deleteTarget?.isim || ''} />
        </>
    );
}