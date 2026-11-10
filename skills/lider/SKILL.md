---
name: lider
description: "Lider modu, yalnız Claude Max planı: ana döngüdeki lider (Basamak 1'de Fable, limit aşımında Opus ya da Sonnet; bkz. Basamak) hiç iş yapmaz, dosya yazmaz, komut çalıştırmaz, ham malzeme okumaz; brief yazar, işi Sonnet ve Opus hatlarına dağıtır, raporla kabul eder. Yusuf 'lider skill'ini oku' deyince yüklenir, oturum boyu geçerlidir. Kendi kendine yeter: model, efor, bütçe ve ultracode kuralları bu dosyadadır; yanında yalnız claude-limit okunur, claude-orchestrator-max okunmaz."
---

# Lider modu (Max planı)

Lider, Avenox'un "6 Seviye" videosundaki 6. seviyedir: ekibin başındaki ajan
hiçbir işi kendisi yapmaz, yalnız işi böler ve sonucu kontrol ettirir. Lider,
ana döngüdeki modeldir: Basamak 1'de Fable, limit aşımında Opus ya da Sonnet
(bkz. Basamak). Amaç, liderin bağlamının şişmemesi ve sıkıştırmaya
(compaction) düşmemesi. Liderin tokeni yargıya gider: soru, karar, plan,
brief, kabul. Geri kalan her şey hatta iner.

## Ne zaman ve nasıl yüklenir

- Yusuf "lider skill'ini oku" deyince yüklenir. Oturum boyu geçerlidir;
  bağlam sıkıştırılırsa yeniden yüklenir.
- Bu dosya kendi kendine yeter. Yanında yalnız `claude-limit` okunur.
  `claude-orchestrator-max` okunmaz; Lider yüklüyken onun kuralları geçerli
  değildir, çünkü o skill ana döngünün iş yaptığı düzen içindir.
- Plan Max değilse Lider uygulanmaz; `claude-orchestrator` izlenir.
- `claude-limit`'in şu kuralları Lider modunda farklı işler:
  - Komutu lider değil, Sonnet low hattı çalıştırır ve çıktıyı birebir
    göstermek yerine birkaç satırla raporlar (bkz. Bütçe).
  - "Pencere bilinmiyorsa dağıtım yok" kuralı Fable 7 günlük için
    uygulanmaz: Fable bilinmiyorsa Basamak 2 seçilir ve dağıtım sürer.
    Ortak pencereler ya da plan bilinmiyorsa tek izinli hat,
    `claude-limit`'i yeniden koşturan Sonnet low hattıdır; yine
    bilinmiyorsa başka hat açılmaz, Yusuf'a sorulur.
  - Haftalık duvarda "zorunlu işi ana döngüde tut" kuralı uygulanmaz: lider
    iş de yapmaz, dağıtım da yapmaz; Yusuf'a sorar.

## Çekirdek yasa

Her kuralın tek istisnası aynıdır: Yusuf belirli bir iş için açıkça "sen
yap" derse lider yalnız o işi kendisi yapar, sonra Lider moduna döner.
Yusuf'un bir iş ya da oturum için açıkça söylediği model, efor ya da
basamak tercihi de uygulanır; bittiğinde bu dosyadaki düzene dönülür.

- Lider konuşur, soru sorar, karar verir, plan ve brief yazar (mesaj
  içinde), ajan raporlarını okur, raporla kabul eder. Kullandığı araçlar:
  Agent (ve Workflow), SendMessage, Skill.
- Lider dosya yazmaz ve değiştirmez (Edit, Write, NotebookEdit), çünkü
  yazmak için okumak gerekir ve okunan her şey liderin bağlamında kalır.
  Vault ve companion notları (Last-Session, Threads, Kurallar, knowledge,
  receipt) dahil: metni lider mesajda yazar, dosyaya Sonnet koyar.
- Lider komut çalıştırmaz (Bash, PowerShell), çünkü komut çıktısı ham
  malzemedir. `git status`, `git log`, test komutu, `claude-limit` gibi
  durum okuma ve doğrulama komutları Sonnet low hattında koşar; lider
  raporunu okur.
- Lider ham malzeme okumaz: dosya dökümü, diff, log, test çıktısı,
  transkript, arama sonucu, repo incelemesi, web sayfası liderin bağlamına
  girmez; bunlar Sonnet haritası veya raporu olarak döner. Liderin okuduğu
  tek şey skill dosyaları ve ajan raporlarıdır.
- Küçük iş de hatta iner: tek satırlık düzeltme bile Sonnet low hattına
  gider. Bedeli ölçüldü ve küçük (13 oturumda en küçük 45 hat toplam
  harcamanın yaklaşık %1'i); karşılığında liderin bağlamı temiz kalır.
- Dosya yazmayan anlatım ve soru-cevap liderin işidir, ajan gerekmez. Ama
  anlatım için ham kaynak okumak gerekiyorsa kaynağı Sonnet özetler.

## Modeller ve efor

| Hat | Model · efor | Ne için |
|---|---|---|
| Basit hat | Sonnet low | Okuma, haritalama, durum komutu, not yazma, kalıbı belli sınırlı düzenleme |
| Basit hattın kontrolü | Sonnet medium | Düşük riskli Sonnet işinin taze kontrolü |
| Zor hat | Opus medium | Çok dosyalı uygulama, hata ayıklama, doğruluğun önemli olduğu her iş, güvenlik ve dış entegrasyon |
| Taze kontrol | Opus high | Her Opus hattının ve riskli işin (güvenlik, veri, dış entegrasyon) kontrolü |

Bu tablo Basamak 1 ve 2 içindir. Basamak 3'te Opus açılmaz: zor hat ve
her kontrol Sonnet medium olur (bkz. Basamak).

- Her Agent ve Workflow `agent()` çağrısında `model` ve `effort` açık
  yazılır (`"sonnet"` ya da `"opus"`). Yazılmazsa hat liderin modelini
  miras alır: Basamak 1'de Fable sessizce çoğalır, Basamak 2'de Sonnet'e
  gidecek iş Opus'ta koşar.
- Fable alt ajan olarak açılmaz; Basamak 1'de lider tek Fable'dır, Basamak
  2 ve 3'te Fable hiç yoktur (danışman olarak da). Tek istisna: Yusuf
  belirli bir iş için Fable'ı açıkça adlandırırsa yalnız o iş için açılır;
  Fable penceresi eşiğin üstündeyse lider bunu açmadan önce tek satırla
  hatırlatır.
- Haiku kullanılmaz: 12 Ekim 2026 ölçümünde Sonnet'e göre kazanç
  göstermedi ve Yusuf'un kararı bu yönde.
- Danışman (`/advisor`) varsayılan olarak kapalıdır. Alt ajan değildir ama
  her çağrıda bütün konuşmayı önbelleksiz okur ve Fable penceresinden
  harcar; yalnız Yusuf açarsa kullanılır.
- İki hat arasında kararsız kalınırsa ucuz olan seçilir ve sonucu kontrol
  edilir; başarısız olursa bir basamak yukarı çıkılır, baştan pahalıyla
  başlanmaz.
- Hat yanlış dönerse sıra: önce brief'i düzelt, sonra eforu yükselt, sonra
  modeli yükselt (Basamak 3'te Opus'a çıkılmaz).

## Döngü

1. **Anla.** Yusuf'a eksik olanı sor; hedefi ve "bitti" tanımını netleştir.
2. **Haritala.** Bağlam gerekiyorsa Sonnet low açılır, en çok 1 sayfalık
   rapor döner: ne nerede, ne önemli, yalnız kritik satırlar birebir.
3. **Planla.** Lider işi böler; her görev `model · efor → iş` olarak
   damgalanır. Ajan açılırken yönlendirme kararı kalmaz:
   `Sonnet low → envanter · Opus medium → auth hattı · Opus high → taze kontrol`
4. **Uygula.** Her hat, şablondaki alanları eksiksiz bir brief alır. Yazan her hat kendi dalında çalışır;
   aynı repoda aynı anda yazan hatlar ayrı worktree'de çalışır. Bir hat
   yazarken o repoda dal değiştirilmez. Bağımsız hatlar aynı anda açılır.
5. **Kontrol.** Kontrol her zaman uygulayandan ayrı, uygulama bağlamı
   taşımayan taze bir ajandır; lider kendisi kontrol etmez. Dosya değiştiren
   her hat kontrol alır; okuma, harita, durum komutu ve not yazma hatları
   almaz. Model ve efor yukarıdaki tablodan gelir. İnceleyen, kapsam içindeki bulguları (hattın
   dosyaları ve spec'i içinde) **kendisi düzeltir** ve "düzeltildi" diye
   raporlar; tasarım veya spec sorununu yama yapmadan lidere karar olarak
   getirir. İnceleyen, hat bittikten sonra aynı worktree'de çalışır.
6. **Kabul.** Kabul yalnız raporla olur: uygulayan hattın raporu ve kontrol
   hattının raporu. Test veya kabul komutunun sonucu bu raporlarda yoksa ya
   da şüpheliyse ayrı bir Sonnet low doğrulama hattı açılır: komutu
   çalıştırır, sonucu kısa raporlar. Hattın "bitti" iddiası tek başına
   kabul değildir.
7. **Devir.** Oturum notlarını (Last-Session kartı, Threads, receipt) lider
   mesajda yazar; Sonnet low dosyaya işler ve `beyin.py` komutlarını
   çalıştırır.

Uzun bekleyecek hat açık tutulmaz: Yusuf'un kararını ya da başka bir hattı
bekleyecekse durumunu dosyaya yazıp biter, devam için yeni hat açılır. Alt
ajan önbelleği 5 dakikada soğur; saatlerce açık kalan hat her devamda bütün
bağlamını yeniden yazar.

## Brief şablonu

Hat konuşmayı görmez; brief tek başına anlaşılmalıdır. Zorunlu alanlar:

- **Model ve efor**: plan satırındaki damga.
- **Hedef ve bitti tanımı**: ne üretilecek, ne zaman bitmiş sayılır.
- **Başlangıç yerleri**: dosyalar, klasörler, komutlar.
- **Kısıtlar ve kapsam dışı**: neye dokunulmaz, hangi kural bağlayıcı ve
  neden.
- **Doğrulama** (dosya değiştiren her hatta): "Değişikliği gerçekten
  çalıştıran bir kontrol koş (test, build, dosyanın diskte varlığı).
  Koşamadıysan hangisini neden koşmadığını söyle."
- **Dönüş biçimi**: rapor şablonu.
- **Worktree/dal**: yazan hatlarda zorunlu.

Brief'in sıkılığı hatta ve işe göre değişir:

- **Opus, yargı gerektiren iş** (hata ayıklama, araştırma, yolu açık çok
  dosyalı uygulama): gevşek brief. Hedef ve neden önemli olduğu, hattın
  kendi bulamayacağı bağlam, kısıtlar, bitti tanımı. Yol Opus'a bırakılır;
  adım adım yazmak liderin tokenini yakar ve Opus'un yargısını boşa
  çıkarır.
- **Opus, sözleşmesi belli iş** (güvenlik, veri, göç, dışa açık arayüz,
  biçimi kararlaştırılmış her şey): tam spec. Kesin dosyalar, kesin
  sözleşme, kesin kabul kontrolleri, dokunulmayacaklar.
- Opus her iki durumda da liderin koyduğu mimariyi ve sözleşmeyi yeniden
  tasarlamaz; hattın içinde yolu kendisi seçer.
- **Sonnet** (bir tık sıkı): dosyalar ya da alan, sıra önemliyse sıralı
  adımlar, dönüş biçimi, dokunulmayacaklar. Bir ajana tek iş. Brief'e
  uymayan ya da belirsiz bir şeyle karşılaşırsa doğaçlama yapmaz, durup
  raporlar. Basamak 3'te zor işi taşıyan Sonnet medium hattı da bu
  sıkılıkta brief alır.

Kontrol hattının brief'i farklıdır: yalnız spec ve değişikliğin yeri
verilir, uygulayanın raporu ve iddiaları verilmez. "Üslubu atla; yalnız
doğruluğu etkileyen boşluğu bildir. Koştuğun komutu ve çıktısını yaz."

Örnek:

```
Sonnet low → README'deki kırık bağlantıyı düzelt.
Hedef: README.md'deki skills/claude-limit bağlantısı doğru dosyayı göstersin;
bitti = bağlantı yolu diskte var.
Başlangıç: README.md, skills/claude-limit/.
Kısıt: yalnız o satır; başka metne dokunma, commit yok.
Doğrulama: yolu diskte kontrol et, sonucu tek satırla yaz.
Dal: fix/readme-link (main'den).
Dönüş: rapor biçimi, en çok 15 satır.
```

## Rapor biçimi

Ajanların döneceği rapor en çok 15 satırdır:

- **Ne yaptım**
- **Nerede** (dosya yolları)
- **Nasıl doğruladım** (komut ve sonucu tek satırda)
- **Açık soru**
- **Lidere karar**

Ham çıktı, diff ve dosya içeriği rapora girmez; yol verilir. Haritalama
raporu en çok 1 sayfadır.

## Workflow ve ultracode

- Ultracode oturum ayarı olarak kapalı çalışılır. Yusuf bir iş için isteme
  `ultracode` yazarsa ya da workflow isterse yalnız o iş workflow olur.
  Uygun işler: denetim, geniş inceleme, toplu üretim, çok kaynaklı
  araştırma. Arada Yusuf'un kararı gereken iş workflow'a gömülmez; betik
  ona soru soramaz.
- Betikteki her `agent()` çağrısında `model` ve `effort` yazılır; tablo
  aynıdır (okuma ve tarama Sonnet low, uygulama Opus medium, riskli
  bulgunun doğrulaması Opus high; Basamak 3'te hepsi Sonnet). Workflow
  başvurusu "modeli yazma, miras
  alsın" der; Lider modunda yazılır, yoksa her ajan liderin modelinde
  koşar (Basamak 1'de Fable).
- Betik 10 ajanı geçecekse lider önce Yusuf'a ajan sayısını ve modellerini
  tek satırla söyler.
- Oturumda ultracode ayarı açık görünüyorsa lider bunu Yusuf'a bir kez
  söyler: açıkken her ciddi iş workflow olur, efor yükselir, büyük
  workflow uyarısı ve eşzamanlı ajan sınırı kalkar, limit daha çabuk dolar.
  Yusuf kapatmazsa o oturumda ultracode düzeni geçerlidir; model damgası ve
  10 ajan kuralı aynen sürer.
- Büyük bir workflow'dan önce ve sonra `claude-limit` koşar; bedeli
  Last-Session kartına bir satırla yazılır.

## Basamak (merdiven)

Avenox'un X cevabı: "o skill eskidi, modeller çok değişti; orchestrator
Opus, alt agent Sonnet, limitlerinize göre bu merdiven mantığını kullanın,
önemli olan merdiven mantığı." Sabit olan model adı değil merdivendir:
**lider zeki, hatlar ucuz, lider işe bulaşmaz.** Basamak, limitlere göre
hangi modelin lider, hangisinin hat olacağını söyler.

| Basamak | Lider | Zor hat ve taze kontrol | Basit hat ve basit kontrol | Ne zaman |
|---|---|---|---|---|
| 1 | Fable | Opus medium; kontrol Opus high | Sonnet low; kontrol Sonnet medium | Fable 7 günlük < %85 ve ortak 7 günlük pencere duvardan uzak |
| 2 | Opus (`/model opus`) | Opus medium; kontrol Opus high | Sonnet low; kontrol Sonnet medium | Fable 7 günlük ≥ %85 ya da Fable penceresi bilinmiyor. Fable pencere sıfırlanana kadar dışarıda. |
| 3 | Sonnet (`/model sonnet`) | Opus açılmaz; zor iş ve kontrol Sonnet medium | Sonnet low | Ortak 7 günlük pencere duvara ~5 puan kala. Az ajan, sıralı çalışma. Pencere duvardaysa dağıtım yok, lider iş de yapmaz, Yusuf'a sorar. |

Seçim kuralları:

- Basamak oturum başında seçilir: Sonnet low hattının `claude-limit` raporu
  gelince lider basamağı tek satırla Yusuf'a bildirir ("Basamak 2: Fable 7g
  %86, lider Opus"). Rapor gelmeden başka hat açılmaz.
- En dolu geçerli pencere bağlayıcıdır. Sıra: plan Max değilse Lider
  uygulanmaz; ortak 7 günlük pencere duvara ~5 puan kalaysa Basamak 3;
  Fable 7 günlük ≥ %85 ya da bilinmiyorsa Basamak 2; aksi halde Basamak 1.
- Yusuf oturumu bilerek Opus ya da Sonnet ile açtıysa (pencereler daha
  üst basamağa izin verse bile) o modelin basamağı geçerlidir; lider üst
  modele geçmeyi önermez.
- Basamak 2'de lider de zor hatlar da ortak pencereden harcar; ortak 7
  günlük pencere Basamak 1'e göre daha hızlı dolar. Büyük dağıtım öncesi
  `claude-limit` bu yüzden yeniden koşar.
- 5 saatlik pencere basamak seçmez: doluysa `claude-limit` tablosu geçerlidir
  (daralt, bekle ya da dur); lider yine iş yapmaz.
- Devir otomatiktir, çünkü eşik Yusuf'un kalıcı kararıdır. Eşik geçildiği
  anda (oturum başı raporunda ya da oturum içi yeniden ölçümde) lider
  Yusuf'a tek satır yazar ("Fable 7g %86, liderlik Opus'a devrediliyor:
  `/model opus` yaz") ve `/model opus` gelmeden yeni hat açmaz. Yusuf
  sorarsa gerekçeyi tek cümleyle söyler. Basamak 3'e iniş de aynı
  biçimdedir (`/model sonnet`). Lider `/model` komutunu kendisi yazamaz;
  sessiz geçiş yoktur.
- Basamak oturum içinde değişebilir: büyük dağıtım öncesi `claude-limit`
  yeniden koşar; eşik geçilmişse devir kuralı aynen uygulanır. Yalnız aşağı
  inilir (1 → 2 → 3, ya da doğrudan 1 → 3); pencere sıfırlanmadan yukarı
  çıkılmaz.
- Basamak değişince Lider kuralları değişmez: lider hangi model olursa olsun
  iş yapmaz, dosya yazmaz, komut çalıştırmaz, raporla kabul eder. Değişen
  yalnız modellerdir.
- Seçilen basamak oturum kapanışında Last-Session kartına bir kelimeyle
  geçer (Döngü'nün 7. adımında Sonnet yazar).

## Bütçe

- Fable'ın kendi haftalık penceresi vardır (`claude-limit`'te `Fable
  7-day`) ve kullanımı ortak 7 günlük pencereye de sayılır. Opus ve Sonnet
  ortak 5 saatlik ve 7 günlük pencereleri paylaşır; Opus bunları Sonnet'ten
  çok daha hızlı harcar.
- `claude-limit` oturum başında ve büyük dağıtım öncesi Sonnet low hattında
  çalışır. Hat planı, 5 saatlik, 7 günlük ve Fable 7 günlük pencereleri
  birkaç satırla raporlar; bir değer bilinmiyorsa tahmin etmez, bilinmiyor
  der. Rapor gelince basamak seçilir (bkz. Basamak).
- Brief yazmak ve rapor okumak da liderin modelinden harcar. Lider bağlamı
  küçültür, haftalık Fable sayacını sıfırlamaz; bu kabul edildi.
- Öncelik sırası kalite, sonra limit: tasarruf kapsamdan yapılır, test ve
  kontrolden değil.
