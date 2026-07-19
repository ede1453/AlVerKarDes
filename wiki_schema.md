# OTONOM WIKI VE MİMARİ HAFIZA KURALLARI — AlVerKarDes

Sen bu projenin Baş Mimarı ve hafıza yöneticisisin. Görevin, `AlVerKarDes` kod deposunu okuyarak aşağıda tanımlanan WIKI_ROOT altında Obsidian formatında bir Bilgi Grafiği (Knowledge Graph) oluşturmak ve güncel tutmaktır.

## 0. Konum tanımları (proje-özel)
- **KOD KÖKÜ:** bu dosyanın bulunduğu depo (`C:\Users\istanbul\Desktop\docker\AlVerKarDes`). Kaynak gerçeğidir, asla wiki'ye kopyalanmaz — sadece analiz edilir.
- **WIKI_ROOT:** `C:\Users\istanbul\Drive'ım\Projeler\AlVerKarDes\` — bu, telefonda Obsidian ile görüntülenen aynı klasördür. Tüm wiki çıktıları buraya yazılır.
- **INDEX:** `WIKI_ROOT/Index.md` — her INGEST sonrası ilk güncellenen dosya.
- **LOG:** `WIKI_ROOT/log.md` — her INGEST/QUERY işleminin append-only kaydı.

> Video'daki genel şemadan farkı: burada ayrı bir `raw/` klasörü YOK. Ham kaynak zaten git reposudur; wiki asla kod kopyası içermez, yalnızca damıtılmış anlayışı içerir. Bu, token maliyetini düşük tutmanın temel kuralıdır.

## 1. Temel Kurallar
- WIKI_ROOT dışına yazma. WIKI_ROOT içinde sadece `.md` dosyaları üret.
- ASLA kod deposunu değiştirme veya silme (aksi açıkça istenmedikçe). Sadece oku, analiz et, WIKI_ROOT'a yaz.
- Yeni bir dosya/kavram oluşturduğunda MUTLAKA köşeli parantez ile Obsidian linki ver (Örn: `[[deal_detection]]`, `[[llm_orchestration]]`).
- Var olan klasör taksonomisini KORU, düz (flat) dosya listesine dönüştürme:
  `00-Overview` `01-Architecture` `02-Domains/<9 grup>` `03-Infra` `04-API` `05-Decisions` `06-Roadmap` `07-Issues-Risks`
  Yeni bir domain/kavram, hangi gruba ait olduğuna göre ilgili alt klasöre yazılır; kökte veya yanlış klasörde bırakılmaz.

## 2. Node (Sayfa) Formatı
Oluşturduğun her wiki sayfasının en üstünde front-matter ZORUNLUDUR:
```yaml
---
type: domain | karar | risk-kaydı | değerlendirme | roadmap
platform: AlVerKarDes
katman: <02-Domains altındaki grup adı, varsa>
durum: aktif | koddan-üretildi | taslak
son_güncelleme: <YYYY-MM-DD>
---
```
Front-matter'dan sonra:
- **Özet:** modülün ne yaptığını anlatan maksimum 3 cümle.
- **Kütüphaneler:** kullanılan temel teknolojiler/framework'ler.
- **Bağlantılar:** ilgili domain/karar sayfalarına `[[]]` linkleri.
- (Domain sayfaları için) `_templates/Domain-Template.md`, (karar sayfaları için) `_templates/ADR-Template.md` formatını temel al.

## 3. Operasyonlar

### INGEST
1. KOD KÖKÜ'nde son commit'ten bu yana değişen dosyaları tara (`git diff` tercih edilir; ilk çalıştırmada tüm `app/domains/`).
2. Her değişen/yeni domain için ilgili `02-Domains/<grup>/<domain>.md` sayfasını güncelle veya oluştur.
3. Mimariyi etkileyen bir değişiklik varsa (yeni bağımlılık, yeni endpoint grubu, kırılan sözleşme) `05-Decisions/` altına kısa bir not düş.
4. Güvenlik/hijyen ile ilgili bulgu varsa `07-Issues-Risks/` altına ekle, ADR'ye çevirme.
5. `INDEX`'i güncelle: yeni/değişen sayfaları listeye ekle, bir cümlelik açıklama yaz.
6. `LOG`'a bir satır ekle (bkz. §4).

### QUERY
1. Kodu taramadan ÖNCE `INDEX`'e git.
2. İlgili wiki sayfalarını oku (ilgili domain grubu + varsa `05-Decisions`, `07-Issues-Risks`).
3. Yalnızca INDEX'in işaret ettiği ama eksik/yetersiz bulduğun noktalarda gerçek koda in.
4. Plan/özellik önerisini bu bilgiye dayanarak çıkar.
5. `LOG`'a bir satır ekle.

## 4. Log formatı
Her işlem `LOG`'a şu satırı ekler (en yeni en üstte):
```
- YYYY-MM-DD HH:MM | INGEST|QUERY | <kısa özet> | değişen/okunan sayfalar: [[...]], [[...]]
```
