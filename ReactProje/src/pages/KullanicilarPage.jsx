import React, { useState, useEffect } from 'react';
import {
    Users, Plus, Edit3, Trash2, X, Shield, ShieldCheck, Eye,
    User, Lock, Mail, ChevronRight, AlertTriangle, CheckCircle2, Loader2,
    Truck, Phone, Building, Briefcase, CreditCard
} from 'lucide-react';
import toast from 'react-hot-toast';
import { getKullanicilar, createKullanici, updateKullanici, deleteKullanici } from '../services/api';
import { hataMetni } from '../utils/hata';
import { useAuth } from '../contexts/AuthContext';

const ROL_CONFIG = {
    admin: { label: 'Yönetici', color: 'bg-red-50 text-red-700 border-red-200', icon: ShieldCheck },
    depocu: { label: 'Depo Sorumlusu', color: 'bg-blue-50 text-blue-700 border-blue-200', icon: Shield },
    lojistik: { label: 'Lojistik', color: 'bg-amber-50 text-amber-700 border-amber-200', icon: Truck },
    goruntuleyen: { label: 'Görüntüleyici', color: 'bg-slate-100 text-slate-600 border-slate-200', icon: Eye },
};

function RolBadge({ rol }) {
    const config = ROL_CONFIG[rol] || ROL_CONFIG.depocu;
    const Icon = config.icon;
    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-extrabold tracking-wider uppercase border ${config.color}`}>
            <Icon className="w-3 h-3" />
            {config.label}
        </span>
    );
}

// Kullanıcı Formu Modal
function KullaniciModal({ isOpen, onClose, onSave, kullanici }) {
    const [form, setForm] = useState({
        kullanici_adi: '', ad_soyad: '', rol: 'depocu', sifre: '',
        telefon: '', email: '', departman: '', sicil_no: '', kart_numarasi: ''
    });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (kullanici) {
            setForm({
                kullanici_adi: kullanici.kullanici_adi || '',
                ad_soyad: kullanici.ad_soyad || '',
                rol: kullanici.rol || 'depocu',
                sifre: '',
                telefon: kullanici.telefon || '',
                email: kullanici.email || '',
                departman: kullanici.departman || '',
                sicil_no: kullanici.sicil_no || '',
                kart_numarasi: kullanici.kart_numarasi || ''
            });
        } else {
            setForm({
                kullanici_adi: '', ad_soyad: '', rol: 'depocu', sifre: '',
                telefon: '', email: '', departman: '', sicil_no: '', kart_numarasi: ''
            });
        }
    }, [kullanici, isOpen]);

    useEffect(() => {
        if (isOpen) document.body.style.overflow = 'hidden';
        else document.body.style.overflow = 'unset';
        return () => { document.body.style.overflow = 'unset'; };
    }, [isOpen]);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.kullanici_adi.trim() || !form.ad_soyad.trim()) {
            toast.error('Kullanıcı adı ve ad soyad zorunludur.');
            return;
        }
        if (!kullanici && !form.sifre.trim()) {
            toast.error('Yeni kullanıcı için şifre zorunludur.');
            return;
        }
        setSaving(true);
        try {
            const data = { ...form };
            if (kullanici && !data.sifre) delete data.sifre;
            await onSave(data);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center sm:p-6">
            <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={onClose} />
            <div className="relative bg-white w-full max-w-[520px] h-auto max-h-[90vh] flex flex-col shadow-2xl overflow-hidden
                           rounded-t-[2rem] sm:rounded-[2rem] ring-1 ring-slate-900/5 
                           animate-[scaleIn_0.3s_ease-out]"
                onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="flex items-center justify-between px-6 sm:px-8 py-5 bg-white border-b border-slate-200/80 shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-50 to-indigo-50 border border-violet-100/60 flex items-center justify-center">
                            {kullanici ? <Edit3 className="w-6 h-6 text-violet-600" /> : <Users className="w-6 h-6 text-violet-600" />}
                        </div>
                        <div>
                            <h3 className="text-[18px] font-extrabold text-slate-900">{kullanici ? 'Kullanıcıyı Düzenle' : 'Yeni Kullanıcı Oluştur'}</h3>
                            <p className="text-[13px] text-slate-500 font-medium mt-0.5">{kullanici ? 'Mevcut bilgileri güncelleyin.' : 'Sisteme yeni bir kullanıcı ekleyin.'}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="w-10 h-10 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Form */}
                <form id="kullanici-form" onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-5">
                    {/* Kullanıcı Adı */}
                    <div className="space-y-1.5">
                        <label className="text-[13px] font-semibold text-slate-700 ml-1">Kullanıcı Adı <span className="text-red-500">*</span></label>
                        <div className="relative group">
                            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><User className="w-4.5 h-4.5" /></div>
                            <input value={form.kullanici_adi} onChange={e => setForm({ ...form, kullanici_adi: e.target.value })}
                                placeholder="Kullanıcı adı" autoFocus
                                className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-11 pr-4" />
                        </div>
                    </div>

                    {/* Ad Soyad */}
                    <div className="space-y-1.5">
                        <label className="text-[13px] font-semibold text-slate-700 ml-1">Ad Soyad <span className="text-red-500">*</span></label>
                        <div className="relative group">
                            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><Mail className="w-4.5 h-4.5" /></div>
                            <input value={form.ad_soyad} onChange={e => setForm({ ...form, ad_soyad: e.target.value })}
                                placeholder="Ad Soyad"
                                className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-11 pr-4" />
                        </div>
                    </div>

                    {/* Rol */}
                    <div className="space-y-1.5">
                        <label className="text-[13px] font-semibold text-slate-700 ml-1">Sistem Rolü</label>
                        <div className="relative group">
                            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><Shield className="w-4.5 h-4.5" /></div>
                            <select value={form.rol} onChange={e => setForm({ ...form, rol: e.target.value })}
                                className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all appearance-none cursor-pointer pl-11 pr-10">
                                <option value="admin">Yönetici (Admin)</option>
                                <option value="depocu">Depo Sorumlusu</option>
                                <option value="lojistik">Lojistik Personeli</option>
                                <option value="goruntuleyen">Görüntüleyici</option>
                            </select>
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400"><ChevronRight className="w-4 h-4 rotate-90" /></div>
                        </div>
                    </div>

                    {/* Şifre */}
                    <div className="space-y-1.5">
                        <label className="text-[13px] font-semibold text-slate-700 ml-1">
                            Şifre {!kullanici && <span className="text-red-500">*</span>}
                        </label>
                        <div className="relative group">
                            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><Lock className="w-4.5 h-4.5" /></div>
                            <input type="password" value={form.sifre} onChange={e => setForm({ ...form, sifre: e.target.value })}
                                placeholder={kullanici ? "Değiştirmek istemiyorsanız boş bırakın" : "Güçlü bir şifre belirleyin"}
                                className="w-full h-12 bg-slate-50 border border-slate-200 text-slate-800 text-[14px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-11 pr-4" />
                        </div>
                        {kullanici && <p className="text-[12px] text-slate-400 ml-1">Boş bırakılırsa mevcut şifre korunur.</p>}
                    </div>

                    {/* Ekstra Bilgiler Başlığı */}
                    <div className="pt-2">
                        <div className="flex items-center gap-3">
                            <div className="h-px bg-slate-200 flex-1"></div>
                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">İsteğe Bağlı Bilgiler</span>
                            <div className="h-px bg-slate-200 flex-1"></div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        {/* Telefon */}
                        <div className="space-y-1.5">
                            <label className="text-[12px] font-semibold text-slate-700 ml-1">Telefon</label>
                            <div className="relative group">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><Phone className="w-4 h-4" /></div>
                                <input value={form.telefon} onChange={e => setForm({ ...form, telefon: e.target.value })}
                                    placeholder="0555..."
                                    className="w-full h-11 bg-slate-50 border border-slate-200 text-slate-800 text-[13px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-10 pr-4" />
                            </div>
                        </div>

                        {/* Email */}
                        <div className="space-y-1.5">
                            <label className="text-[12px] font-semibold text-slate-700 ml-1">E-Posta</label>
                            <div className="relative group">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><Mail className="w-4 h-4" /></div>
                                <input value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} type="email"
                                    placeholder="ornek@sirket.com"
                                    className="w-full h-11 bg-slate-50 border border-slate-200 text-slate-800 text-[13px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-10 pr-4" />
                            </div>
                        </div>

                        {/* Departman */}
                        <div className="space-y-1.5">
                            <label className="text-[12px] font-semibold text-slate-700 ml-1">Departman</label>
                            <div className="relative group">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><Building className="w-4 h-4" /></div>
                                <input value={form.departman} onChange={e => setForm({ ...form, departman: e.target.value })}
                                    placeholder="Örn: Sevkiyat"
                                    className="w-full h-11 bg-slate-50 border border-slate-200 text-slate-800 text-[13px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-10 pr-4" />
                            </div>
                        </div>

                        {/* Sicil No */}
                        <div className="space-y-1.5">
                            <label className="text-[12px] font-semibold text-slate-700 ml-1">Sicil No</label>
                            <div className="relative group">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><Briefcase className="w-4 h-4" /></div>
                                <input value={form.sicil_no} onChange={e => setForm({ ...form, sicil_no: e.target.value })}
                                    placeholder="Sicil numarası"
                                    className="w-full h-11 bg-slate-50 border border-slate-200 text-slate-800 text-[13px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-10 pr-4" />
                            </div>
                        </div>

                        {/* Kart Numarası */}
                        <div className="space-y-1.5 sm:col-span-2">
                            <label className="text-[12px] font-semibold text-slate-700 ml-1">Kart Numarası (RFID/Barkod)</label>
                            <div className="relative group">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"><CreditCard className="w-4 h-4" /></div>
                                <input value={form.kart_numarasi} onChange={e => setForm({ ...form, kart_numarasi: e.target.value })}
                                    placeholder="Personele atanan kart id"
                                    className="w-full h-11 bg-slate-50 border border-slate-200 text-slate-800 text-[13px] rounded-xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all pl-10 pr-4" />
                            </div>
                        </div>
                    </div>
                </form>

                {/* Footer */}
                <div className="bg-white border-t border-slate-200/80 p-5 sm:px-8 flex flex-col-reverse sm:flex-row items-center justify-end gap-3 shrink-0">
                    <button type="button" onClick={onClose}
                        className="w-full sm:w-[130px] h-11 rounded-xl border-2 border-slate-200 text-[14px] font-bold text-slate-600 hover:border-slate-300 hover:bg-slate-50 transition-all active:scale-95">
                        İptal
                    </button>
                    <button type="submit" form="kullanici-form" disabled={saving}
                        className="group relative w-full sm:w-[200px] h-11 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-[14px] font-bold text-white
                                 hover:from-violet-500 hover:to-indigo-500 transition-all shadow-md hover:shadow-lg overflow-hidden active:scale-95 disabled:opacity-70">
                        <span className="relative z-10 flex items-center justify-center gap-2">
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                            {kullanici ? 'Değişiklikleri Kaydet' : 'Kullanıcı Oluştur'}
                        </span>
                    </button>
                </div>
            </div>
        </div>
    );
}

// Ana Sayfa
export default function KullanicilarPage() {
    const [kullanicilar, setKullanicilar] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [editKullanici, setEditKullanici] = useState(null);
    const { user: currentUser } = useAuth();

    const fetchData = () => {
        setLoading(true);
        getKullanicilar()
            .then(res => setKullanicilar(res.data))
            .catch(() => toast.error('Kullanıcı listesi yüklenemedi.'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, []);

    const handleDelete = async (id, isim) => {
        if (id === currentUser?.id) {
            toast.error('Kendi hesabınızı silemezsiniz.');
            return;
        }
        if (!confirm(`"${isim}" kullanıcısını kalıcı olarak silmek istediğinize emin misiniz?`)) return;
        try {
            await deleteKullanici(id);
            toast.success('Kullanıcı silindi');
            fetchData();
        } catch (err) {
            toast.error(hataMetni(err, 'Silme işlemi başarısız'));
        }
    };

    const handleSave = async (data) => {
        try {
            if (editKullanici) {
                await updateKullanici(editKullanici.id, data);
                toast.success('Kullanıcı güncellendi');
            } else {
                await createKullanici(data);
                toast.success('Yeni kullanıcı oluşturuldu');
            }
            setModalOpen(false);
            setEditKullanici(null);
            fetchData();
        } catch (err) {
            toast.error(hataMetni(err, 'İşlem başarısız'));
        }
    };

    return (
        <>
            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
            `}} />

            <div className="space-y-6 max-w-[1400px] mx-auto p-4 sm:p-6 animate-[scaleIn_0.3s_ease-out]">

                {/* Toolbar */}
                <div className="bg-white p-4 sm:p-5 rounded-3xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-[18px] font-extrabold text-slate-900 tracking-tight">Sistem Kullanıcıları</h2>
                        <p className="text-[13px] text-slate-500 font-medium mt-0.5">Toplam {kullanicilar.length} kayıtlı kullanıcı</p>
                    </div>
                    <button onClick={() => { setEditKullanici(null); setModalOpen(true); }}
                        className="group relative h-11 px-6 bg-gradient-to-r from-violet-600 to-indigo-600 text-white text-[14px] font-bold rounded-2xl whitespace-nowrap
                        hover:from-violet-500 hover:to-indigo-500 transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5
                        flex items-center justify-center gap-2 w-full sm:w-auto overflow-hidden flex-shrink-0 active:scale-95">
                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
                        <Plus className="relative z-10 w-5 h-5 stroke-[2.5px] transition-transform group-hover:rotate-90 duration-300" />
                        <span className="relative z-10">Yeni Kullanıcı</span>
                    </button>
                </div>

                {/* Kullanıcı Kartları */}
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {loading ? (
                        [...Array(3)].map((_, i) => (
                            <div key={i} className="bg-white rounded-2xl border border-slate-200/80 p-6 animate-pulse">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="w-12 h-12 bg-slate-200 rounded-full" />
                                    <div className="flex-1"><div className="h-4 bg-slate-200 rounded w-32 mb-2" /><div className="h-3 bg-slate-100 rounded w-24" /></div>
                                </div>
                                <div className="h-6 bg-slate-100 rounded-full w-24" />
                            </div>
                        ))
                    ) : kullanicilar.length === 0 ? (
                        <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
                            <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center mb-4 border border-slate-100">
                                <Users className="w-10 h-10 text-slate-300" />
                            </div>
                            <h3 className="text-[16px] font-bold text-slate-800 mb-1">Henüz kullanıcı yok</h3>
                            <p className="text-[13px] text-slate-500 font-medium">"Yeni Kullanıcı" butonu ile eklemeye başlayın.</p>
                        </div>
                    ) : (
                        kullanicilar.map(k => {
                            const isSelf = k.id === currentUser?.id;
                            const initials = k.ad_soyad ? k.ad_soyad.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : 'U';
                            const gradients = [
                                'from-blue-500 to-indigo-600',
                                'from-violet-500 to-purple-600',
                                'from-emerald-500 to-teal-600',
                                'from-amber-500 to-orange-600',
                                'from-rose-500 to-pink-600',
                            ];
                            const gradient = gradients[k.id % gradients.length];

                            return (
                                <div key={k.id} className="group bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md hover:border-slate-300/80 transition-all p-6">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-4">
                                            <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${gradient} flex items-center justify-center shadow-md border-2 border-white`}>
                                                <span className="text-[14px] font-extrabold text-white">{initials}</span>
                                            </div>
                                            <div>
                                                <p className="text-[15px] font-bold text-slate-900 leading-tight">{k.ad_soyad}</p>
                                                <p className="text-[13px] font-medium text-slate-500 mt-0.5">@{k.kullanici_adi}</p>
                                            </div>
                                        </div>

                                        {/* Aksiyon Butonları */}
                                        <div className="flex items-center gap-1.5 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => { setEditKullanici(k); setModalOpen(true); }}
                                                className="w-8 h-8 rounded-xl bg-white border border-slate-200 hover:border-blue-300 hover:bg-blue-50 text-slate-500 hover:text-blue-600 flex items-center justify-center transition-all shadow-sm"
                                                title="Düzenle">
                                                <Edit3 className="w-4 h-4" />
                                            </button>
                                            {!isSelf && (
                                                <button onClick={() => handleDelete(k.id, k.ad_soyad)}
                                                    className="w-8 h-8 rounded-xl bg-white border border-slate-200 hover:border-red-300 hover:bg-red-50 text-slate-500 hover:text-red-600 flex items-center justify-center transition-all shadow-sm"
                                                    title="Sil">
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <RolBadge rol={k.rol} />
                                        {isSelf && (
                                            <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                                                Siz
                                            </span>
                                        )}
                                    </div>

                                    {/* Kayıt Tarihi */}
                                    <div className="mt-4 pt-3 border-t border-slate-100">
                                        <p className="text-[11px] text-slate-400 font-medium">
                                            Kayıt: {new Date(k.olusturma_tarihi).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })}
                                        </p>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>

            <KullaniciModal
                isOpen={modalOpen}
                onClose={() => { setModalOpen(false); setEditKullanici(null); }}
                onSave={handleSave}
                kullanici={editKullanici}
            />
        </>
    );
}
