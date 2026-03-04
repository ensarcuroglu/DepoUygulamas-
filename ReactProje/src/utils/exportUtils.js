import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import toast from 'react-hot-toast';

/**
 * Dinamik veriyi Excel formatında (xlsx) dışa aktarır.
 * @param {Array<Object>} data - İndirilecek olan veriler (liste). Tablo içeriği.
 * @param {String} fileName - Oluşturulacak dosyanın ismi (örn: 'Urunler_Raporu').
 */
export const exportToExcel = (data, fileName = 'Rapor') => {
    try {
        if (!data || data.length === 0) {
            toast.error('Dışa aktarılacak veri bulunamadı.');
            return;
        }

        // JS objelerini Excel sayfasına (worksheet) çevir (json_to_sheet)
        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();

        XLSX.utils.book_append_sheet(workbook, worksheet, 'Rapor Sayfasi 1');

        // Otomatik sütun genişliği ayarı eklenebilir
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
 * Tabuları, kurumsal tasarımla (jspdf-autotable kullanarak) PDF olarak dışa aktarır.
 * @param {Array<Object>} data - İndirilecek ana tablo verisi.
 * @param {Array<String>} columns - Tablonun üst (header) kısımları (örn: ['Ürün Adı', 'Stok']).
 * @param {String} fileName - Oluşturulacak dosyanın indirme adı (örn: 'Stok_Hareketleri').
 * @param {String} documentTitle - PDF içinde en üstte görünecek Kurumsal Başlık.
 */
export const exportToPDF = (data, columns, fileName = 'Rapor', documentTitle = 'Sistem Raporu') => {
    try {
        if (!data || data.length === 0) {
            toast.error('Dışa aktarılacak veri bulunamadı.');
            return;
        }

        const doc = new jsPDF('landscape'); // Özellikle çok sütunlu raporlar için yatay.

        // 1. Türkçe karakter vb. standart ayarlamalar
        // jsPDF'in default fontları standart utf-8'i her zaman düzgün göstermeyebilir
        // (Helvetica gibi base fontlar tr'de nadir patlar ancak genelde yeterlidir,
        //  gerekirse projeye bir VFS font eklenebilir, şimdilik autoTable bunu handle eder büyük ölçüde)

        // 2. Sayfa Anteti (Kurumsal Başlık Tasarımı)
        doc.setFillColor(30, 58, 138); // Kurumsal Koyu Mavi bg (Tailwind indigo-900)
        doc.rect(0, 0, doc.internal.pageSize.width, 35, 'F');

        doc.setFontSize(20);
        doc.setTextColor(255, 255, 255);
        doc.text("Lojistik & Depo Yönetimi", 14, 20);

        doc.setFontSize(11);
        doc.setTextColor(200, 200, 255);
        doc.text(`Belge Konusu: ${documentTitle}`, 14, 28);

        const generatedDate = new Date().toLocaleString('tr-TR');
        doc.setFontSize(10);
        doc.text(`Oluşturma: ${generatedDate}`, doc.internal.pageSize.width - 15, 22, { align: 'right' });

        // 3. Veriyi dönüştürme: obj objesinden sadece array değerlerini çıkartır
        const tableRows = data.map(obj => Object.values(obj));

        // 4. Tablo Stilizasyonu (autoTable)
        doc.autoTable({
            head: [columns],
            body: tableRows,
            startY: 45,        // Header altından başlasın
            theme: 'grid',     // Çizgili görünüm
            styles: {
                font: 'helvetica',
                fontSize: 9,
                cellPadding: 4,
                lineColor: [226, 232, 240], // slate-200 border
                lineWidth: 0.1,
            },
            headStyles: {
                fillColor: [79, 70, 229], // indigo-600
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                halign: 'center'
            },
            alternateRowStyles: {
                fillColor: [248, 250, 252] // slate-50 zebralı tasarım
            },
            // Sayfa altı bilgisi (Footer)
            didDrawPage: function (data) {
                let str = 'Sayfa ' + doc.internal.getNumberOfPages();
                doc.setFontSize(8);
                doc.setTextColor(150, 150, 150);
                // bottom pozisyon
                doc.text(str, data.settings.margin.left, doc.internal.pageSize.height - 10);
            }
        });

        doc.save(`${fileName}_${new Date().getTime()}.pdf`);
        toast.success(`${fileName} başarıyla indirildi.`, { icon: '📄' });

    } catch (error) {
        console.error('PDF export hatası:', error);
        toast.error('PDF dosyası oluşturulurken bir hata oluştu.');
    }
};
