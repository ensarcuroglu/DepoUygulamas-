import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
// 1. DEĞİŞİKLİK: autoTable'ı doğrudan bir fonksiyon olarak import ediyoruz
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
 * Tabloları PDF olarak dışa aktarır.
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

        // 2. DEĞİŞİKLİK: Obje formatında konfigürasyon (Yeni jspdf sürümleri için daha sağlıklı)
        const doc = new jsPDF({ orientation: 'landscape' });

        doc.setFillColor(30, 58, 138); 
        doc.rect(0, 0, doc.internal.pageSize.width, 35, 'F');

        doc.setFontSize(20);
        doc.setTextColor(255, 255, 255);
        doc.text("Lojistik & Depo Yonetimi", 14, 20); // Not: jsPDF base fontlarında "Yönetimi" karakteri bazen patlayabilir, garanti olması için ö'yü o yaptım veya özel font eklenebilir.

        doc.setFontSize(11);
        doc.setTextColor(200, 200, 255);
        // Türkçe karakter hatası almamak için şimdilik base ASCII dostu karakterler kullanılabilir
        doc.text(`Belge Konusu: ${documentTitle}`, 14, 28);

        const generatedDate = new Date().toLocaleString('tr-TR');
        doc.setFontSize(10);
        doc.text(`Olusturma: ${generatedDate}`, doc.internal.pageSize.width - 15, 22, { align: 'right' });

        // 3. DEĞİŞİKLİK: Sadece "columns" dizisinde istenen sütunları veriden çekeceğiz.
        // Böylece App.js'ten gelen 10 özellikli nesneden, sadece PDF'te gösterilecek 8 tanesi sırasıyla alınır.
        const tableRows = data.map(obj => {
            return columns.map(colKey => {
                // Eğer veri o anahtarda (Örn: 'Barkod/Kod') tanımlıysa değeri al, yoksa boş bırak
                return obj[colKey] !== undefined && obj[colKey] !== null ? obj[colKey] : '-';
            });
        });

        // 4. DEĞİŞİKLİK: doc.autoTable yerine import ettiğimiz autoTable fonksiyonunu kullanıyoruz.
        autoTable(doc, {
            head: [columns],
            body: tableRows,
            startY: 45,
            theme: 'grid',
            styles: {
                font: 'helvetica',
                fontSize: 9,
                cellPadding: 4,
                lineColor: [226, 232, 240], 
                lineWidth: 0.1,
            },
            headStyles: {
                fillColor: [79, 70, 229], 
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                halign: 'center'
            },
            alternateRowStyles: {
                fillColor: [248, 250, 252] 
            },
            didDrawPage: function (hookData) {
                let str = 'Sayfa ' + doc.internal.getNumberOfPages();
                doc.setFontSize(8);
                doc.setTextColor(150, 150, 150);
                doc.text(str, hookData.settings.margin.left, doc.internal.pageSize.height - 10);
            }
        });

        doc.save(`${fileName}_${new Date().getTime()}.pdf`);
        toast.success(`${fileName} başarıyla indirildi.`, { icon: '📄' });

    } catch (error) {
        console.error('PDF export hatası:', error);
        toast.error('PDF dosyası oluşturulurken bir hata oluştu.');
    }
};