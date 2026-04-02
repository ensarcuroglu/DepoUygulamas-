import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import toast from 'react-hot-toast';

/**
 * Dinamik veriyi Excel formatında (xlsx) dışa aktarır.
 * @param {Array<Object>} data - İndirilecek olan veriler (liste).
 * @param {String} fileName - Oluşturulacak dosyanın ismi.
 */
export const exportToExcel = (data, fileName = 'Rapor') => {
    try {
        if (!data || data.length === 0) {
            toast.error('Dışa aktarılacak veri bulunamadı.');
            return;
        }

        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();

        XLSX.utils.book_append_sheet(workbook, worksheet, 'Rapor Sayfasi 1');

        const cols = Object.keys(data[0]).map(key => ({ wch: Math.max(key.length + 5, 15) }));
        worksheet['!cols'] = cols;

        XLSX.writeFile(workbook, `${fileName}.xlsx`);
        toast.success(`${fileName}.xlsx başarıyla indirildi.`, { icon: '📊' });
    } catch (error) {
        console.error('Excel export hatası:', error);
        toast.error('Excel dosyası oluşturulurken bir hata oluştu.');
    }
};

/**
 * Tabloları Modern ve Kurumsal PDF olarak dışa aktarır.
 * @param {Array<Object>} data - İndirilecek ana tablo verisi.
 * @param {Array<String>} columns - Tablonun üst (header) kısımları.
 * @param {String} fileName - Oluşturulacak dosyanın indirme adı.
 * @param {String} documentTitle - Kurumsal Başlık.
 */
export const exportToPDF = (data, columns, fileName = 'Rapor', documentTitle = 'Sistem Raporu') => {
    try {
        if (!data || data.length === 0) {
            toast.error('Dışa aktarılacak veri bulunamadı.');
            return;
        }

        const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
        const pageWidth = doc.internal.pageSize.width;
        const pageHeight = doc.internal.pageSize.height;

        // --- 1. KURUMSAL HEADER TASARIMI ---
        
        // Koyu Arduvaz (Slate-900) Arka Plan
        doc.setFillColor(15, 23, 42); 
        doc.rect(0, 0, pageWidth, 40, 'F');
        
        // Mavi (Blue-500) İnce Vurgu Çizgisi
        doc.setFillColor(59, 130, 246); 
        doc.rect(0, 40, pageWidth, 1.5, 'F');

        // Ana Başlık
        doc.setFontSize(22);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(255, 255, 255);
        doc.text("DEPO YONETIM SISTEMI", 14, 22);

        // Alt Başlık (Rapor Konusu)
        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(148, 163, 184); // Slate-400
        doc.text(`Rapor: ${documentTitle}`, 14, 31);

        // Sağ Üst Bilgiler (Tarih ve Saat)
        const dateObj = new Date();
        const dateStr = dateObj.toLocaleDateString('tr-TR');
        const timeStr = dateObj.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
        
        doc.setFontSize(10);
        doc.setTextColor(248, 250, 252); // Slate-50
        doc.text(`Tarih: ${dateStr}`, pageWidth - 14, 22, { align: 'right' });
        
        doc.setTextColor(148, 163, 184); // Slate-400
        doc.text(`Saat: ${timeStr}`, pageWidth - 14, 28, { align: 'right' });

        // --- 2. VERİ HAZIRLIĞI ---
        const tableRows = data.map(obj => {
            return columns.map(colKey => {
                return obj[colKey] !== undefined && obj[colKey] !== null ? obj[colKey] : '-';
            });
        });

        // Toplam sayfa sayısı için bir placeholder tanımlıyoruz (Footer'da kullanacağız)
        const totalPagesExp = '{total_pages_count_string}';

        // --- 3. MODERN TABLO TASARIMI (autoTable) ---
        autoTable(doc, {
            head: [columns],
            body: tableRows,
            startY: 50, // Header'dan biraz daha uzak
            theme: 'grid',
            styles: {
                font: 'helvetica',
                fontSize: 9,
                cellPadding: 6, // Daha havadar hücreler
                textColor: [51, 65, 85], // Slate-700
                lineColor: [226, 232, 240], // Slate-200 border
                lineWidth: 0.1,
                valign: 'middle' // Dikey ortalama
            },
            headStyles: {
                fillColor: [30, 41, 59], // Slate-800 (Çok daha şık ve koyu bir başlık)
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                halign: 'left' // Modern tasarımlarda sola dayalı başlık daha okunaklıdır
            },
            alternateRowStyles: {
                fillColor: [248, 250, 252] // Slate-50 zebra desen
            },
            columnStyles: {
                // Sayısal değerleri içeren sütunları sağa hizalamak okunabilirliği artırır
                // Not: Sütun indeksleri senin gönderdiğin 'columns' dizisine göredir (0'dan başlar).
                5: { halign: 'right' }, // Stok sütunu
                6: { halign: 'right' }, // Fiyat sütunu
            },
            
            // --- 4. ALT BİLGİ (FOOTER) TASARIMI ---
            didDrawPage: function () {
                // Alt çizgi
                doc.setDrawColor(226, 232, 240); // Slate-200
                doc.setLineWidth(0.5);
                doc.line(14, pageHeight - 15, pageWidth - 14, pageHeight - 15);

                // Sol Alt Metin
                doc.setFontSize(8);
                doc.setFont('helvetica', 'normal');
                doc.setTextColor(148, 163, 184); // Slate-400
                doc.text('Bu belge sistem tarafindan otomatik olarak uretilmistir.', 14, pageHeight - 8);

                // Sağ Alt Metin (Sayfa X / Y)
                const pageStr = `Sayfa ${doc.internal.getNumberOfPages()} / ${totalPagesExp}`;
                doc.text(pageStr, pageWidth - 14, pageHeight - 8, { align: 'right' });
            }
        });

        // JS PDF'in toplam sayfa sayısını hesaplayıp placeholder'a yazmasını sağlıyoruz
        if (typeof doc.putTotalPages === 'function') {
            doc.putTotalPages(totalPagesExp);
        }

        // Dosyayı kaydet
        doc.save(`${fileName}_${new Date().getTime()}.pdf`);
        toast.success(`${fileName} başarıyla indirildi.`, { icon: '📄' });

    } catch (error) {
        console.error('PDF export hatası:', error);
        toast.error('PDF dosyası oluşturulurken bir hata oluştu.');
    }
};
