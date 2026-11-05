---
name: lider
description: "Lider modu, yalnız Claude Max planı: Fable 5.1 ana döngüde hiç iş yapmaz, dosya yazmaz, komut çalıştırmaz, ham malzeme okumaz; brief yazar, işi Sonnet 5.5 ve Opus 5.5 hatlarına dağıtır, raporla kabul eder. Yusuf 'lider skill'ini oku' deyince yüklenir ve oturum boyu geçerlidir; model yönlendirme ve bütçe kuralları claude-orchestrator-max'tan gelir. Basamak mantığı: lider modeli oturum başında claude-limit'e göre seçilir (Fable → Opus → Sonnet)."
---

# Lider modu (Max planı, Fable ana döngüde)

Lider, Avenox'un "6 Seviye" videosundaki 6. seviyedir: ekibin başındaki ajan
hiçbir işi kendisi yapmaz, yalnız işi böler ve sonucu kontrol ettirir. Amaç,
liderin bağlamının şişmemesi ve sıkıştırmaya (compaction) düşmemesi. Fable'ın
tokeni yargıya gider: soru, karar, plan, brief, kabul. Geri kalan her şey
hatta iner.

## Ne zaman ve nasıl yüklenir

- Yusuf "lider skill'ini oku" deyince yüklenir.
- Lider yüklenince `claude-orchestrator-max` ve `claude-limit` skill'leri de
  okunur. Model seçimi, efor, bütçe, "Fable alt ajan olmaz" ve "model her
  çağrıda açık" kuralları oradan gelir. `claude-limit`'i lider
  çalıştırmaz (bkz. Bütçe).
- Çelişkide Lider üstündür. Max skill'in şu maddeleri Lider modunda
  kapalıdır:
  - "Hands-on while limits are healthy": lider küçük ve orta işi de yapmaz.
  - Ana döngünün "hard execution that needs the whole picture" işini
    kendisi taşıması: zor iş Opus hattına gider; entegrasyon ve çakışma
    çözümünün kararı liderde, uygulaması hatta.
  - "Ana döngü her sonucu kendisi inceler": yerine döngünün 5. ve 6.
    adımları geçer.
  - `claude-limit`'i ana döngünün çalıştırması: Sonnet low hattı çalıştırır.
  - Fable 7 günlük %75'te "uyar ve okumayı hafif tut" kuralı: yerine
    Basamak 2 varsayılanı geçer (bkz. Basamak). %90 zorunluluğu aynen
    kalır.
- Oturum boyu geçerlidir. Bağlam sıkıştırılırsa Lider yeniden yüklenir.

## Çekirdek yasa

- Lider konuşur, soru sorar, karar verir, plan ve brief yazar (mesaj
  içinde), ajan raporlarını okur, raporla kabul eder. Başka hiçbir şey
  yapmaz. Kullandığı araçlar: Agent (ve Workflow), SendMessage, Skill.
- Lider dosya yazmaz ve değiştirmez: Edit, Write, NotebookEdit kullanmaz.
  Vault ve companion notları (Last-Session, Threads, Kurallar, knowledge,
  receipt) dahil: metni lider mesajda yazar, dosyaya Sonnet koyar.
- Lider hiçbir komut çalıştırmaz: Bash ve PowerShell dahil, istisnasız.
  `git status`, `git log`, test komutu, `claude-limit` gibi durum okuma ve
  doğrulama komutları da Sonnet low hattında koşar; lider yalnız raporunu
  okur.
- Lider ham malzeme okumaz: dosya dökümü, diff, log, test çıktısı,
  transkript, arama sonucu, repo incelemesi, web sayfası liderin bağlamına
  girmez; bunlar Sonnet haritası veya raporu olarak döner. Liderin okuduğu
  tek şey skill dosyaları ve ajan raporlarıdır.
- "Küçük iş" istisnası yoktur: tek satırlık düzeltme bile Sonnet low hattına
  gider. Brief ve rapor maliyeti bilinçli kabul edildi.
- Fable alt ajan olarak açılmaz; tek istisna, max skill'deki gibi, Yusuf'un
  belirli bir iş için Fable'ı açıkça adlandırmasıdır. Her Agent ve Workflow
  `agent()` çağrısında `model` açık yazılır (`"sonnet"` veya `"opus"`).
  İkisi de max skill kuralıdır.

## Döngü

1. **Anla.** Yusuf'a eksik olanı sor; hedefi ve "bitti" tanımını netleştir.
2. **Haritala.** Bağlam gerekiyorsa Sonnet (low/medium) açılır, en çok 1
   sayfalık rapor döner: ne nerede, ne önemli, yalnız kritik satırlar
   birebir.
3. **Planla.** Lider işi böler; her görev `model · efor → iş` olarak
   damgalanır (max skill'in planlama satırı biçimi). Ajan açılırken
   yönlendirme kararı kalmaz.
4. **Uygula.** Sonnet basit ve sınırlı işi, Opus zor ve hassas işi taşır
   (Basamak 3'te Opus açılmaz; bkz. Basamak). Her hat tam brief alır. Yazan
   her hat kendi dalında çalışır; aynı repoda aynı anda yazan hatlar ayrı
   worktree'de çalışır. Bir hat yazarken o repoda dal değiştirilmez.
5. **Kontrol.** Kontrol her zaman uygulayandan ayrı, uygulama bağlamı
   taşımayan taze bir ajandır; lider kendisi kontrol etmez. Model işe göre
   ölçeklenir: basit ve düşük riskli Sonnet hatlarını Sonnet medium kontrol
   eder; zor ve riskli (güvenlik, veri, dış entegrasyon) hatları ve her Opus
   hattını Opus high kontrol eder (max skill kuralı; Basamak 3'te Sonnet
   medium). İki seviyede de inceleyen, kapsam içindeki bulguları (hattın
   dosyaları ve spec'i içinde) **kendisi düzeltir** ve "düzeltildi" diye
   raporlar; tasarım veya spec sorununu yama yapmadan lidere karar olarak
   getirir. İnceleyen, hat bittikten sonra aynı worktree'de çalışır.
6. **Kabul.** Kabul yalnız raporla olur: uygulayan hattın raporu ve kontrol
   hattının raporu. Test veya kabul komutunun sonucu bu raporlarda yoksa ya
   da şüpheliyse ayrı bir Sonnet low doğrulama hattı açılır: komutu
   çalıştırır, sonucu en çok 15 satırla raporlar. Hattın "bitti" iddiası tek
   başına kabul değildir. Sonuç yanlış dönerse sıra: önce brief'i düzelt,
   sonra eforu yükselt, sonra modeli yükselt.
7. **Devir.** Oturum notlarını (Last-Session kartı, Threads, receipt) lider
   mesajda yazar; Sonnet low dosyaya işler ve `beyin.py` komutlarını
   çalıştırır.

## Brief şablonu

Her hat için zorunlu alanlar:

- **Model ve efor**: plan satırındaki damga.
- **Hedef ve bitti tanımı**: ne üretilecek, ne zaman bitmiş sayılır.
- **Başlangıç yerleri**: dosyalar, klasörler, komutlar.
- **Kısıtlar ve kapsam dışı**: neye dokunulmaz, hangi kural bağlayıcı.
- **Dönüş biçimi**: rapor şablonu, satır sınırı.
- **Worktree/dal**: yazan hatlarda zorunlu.

Örnek:

```
Sonnet low → README'deki kırık bağlantıyı düzelt.
Hedef: README.md'deki skills/claude-limit bağlantısı doğru dosyayı göstersin;
bitti = bağlantı yolu diskte var.
Başlangıç: README.md, skills/claude-limit/.
Kısıt: yalnız o satır; başka metne dokunma, commit yok.
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

## Bağlam hijyeni

- Ham malzeme lidere gelmez.
- Raporlar kısadır.
- Bağlam sıkıştırması arıza sinyalidir: Lider ve max skill yeniden yüklenir,
  kalan iş hatta iner.
- Paralel hatlar bağımsız olduğunda aynı anda açılır.

## Basamak (merdiven)

Avenox'un X cevabı: "o skill eskidi, modeller çok değişti; orchestrator
Opus, alt agent Sonnet, limitlerinize göre bu merdiven mantığını kullanın,
önemli olan merdiven mantığı." Sabit olan model adı değil merdivendir:
**lider zeki, hatlar ucuz, lider işe bulaşmaz.** Basamak, limitlere göre
hangi modelin lider, hangisinin hat olacağını söyler.

| Basamak | Lider | Zor hat ve taze kontrol | Basit hat ve basit kontrol | Ne zaman |
|---|---|---|---|---|
| 1 | Fable 5.1 | Opus 5.5 high | Sonnet 5.5 low/medium; kontrol Sonnet medium | Fable 7 günlük < %75 ve ortak 5 saatlik / 7 günlük pencereler sağlıklı |
| 2 | Opus 5.5 (`/model opus`) | Opus 5.5 high | Sonnet 5.5 low/medium; kontrol Sonnet medium | Fable 7 günlük ≥ %75 (varsayılan; Yusuf aksini söyleyebilir); ≥ %90 ya da Fable penceresi bilinmiyorsa zorunlu. Fable pencere sıfırlanana kadar dışarıda. |
| 3 | Sonnet 5.5 (`/model sonnet`) | Opus açılmaz; zor iş Sonnet medium, kontrol Sonnet medium | Sonnet 5.5 low | Ortak 7 günlük pencere duvara ~5 puan kala. Az ajan, sıralı çalışma. Pencere duvardaysa `claude-limit` tablosu geçerli: dağıtım yok, Yusuf'a sor. |

Seçim kuralları:

- Basamak oturum başında seçilir: Sonnet low hattının `claude-limit` raporu
  gelince lider basamağı tek satırla Yusuf'a bildirir ("Basamak 2: Fable 7g
  %79, lider Opus"). Rapor gelmeden hat açılmaz.
- En dolu geçerli pencere bağlayıcıdır (`claude-limit` kuralı). Sıra: plan
  Max değilse Lider uygulanmaz; ortak 7 günlük pencere duvara ~5 puan
  kalaysa Basamak 3; Fable 7 günlük ≥ %75 ya da bilinmiyorsa Basamak 2;
  aksi halde Basamak 1.
- Lider `/model` komutunu kendisi çalıştıramaz. Basamak değişimi gerekiyorsa
  Yusuf'a tek satırla söyler ("`/model opus` yaz, Basamak 2'ye geçiyoruz"),
  Yusuf yazar. Sessiz geçiş yok (max skill kuralı).
- Basamak oturum içinde değişebilir: büyük dağıtım öncesi `claude-limit`
  yeniden koşar; sayaç sıradaki basamağın eşiğine gelince lider bunu
  söyler. Yalnız aşağı inilir (1 → 2 → 3); pencere sıfırlanmadan yukarı
  çıkılmaz.
- Basamak değişince Lider kuralları değişmez: lider hangi model olursa olsun
  iş yapmaz, dosya yazmaz, komut çalıştırmaz, raporla kabul eder. Değişen
  yalnız modellerdir.
- Her basamakta model her Agent ve Workflow `agent()` çağrısında açık
  yazılır; Fable hiçbir basamakta alt ajan olmaz (max skill kuralı; tek
  istisna Yusuf'un açık adlandırması, bkz. İstisnalar).
- Seçilen basamak oturum kapanışında Last-Session kartına bir kelimeyle
  geçer (Devir adımında Sonnet yazar).

## Bütçe

- `claude-limit` oturum başında ve büyük dağıtım öncesi Sonnet low hattında
  çalışır; lider komutu kendisi çalıştırmaz. Hat planı, 5 saatlik, 7 günlük
  ve Fable 7 günlük pencereleri birkaç satırla raporlar; bir değer
  bilinmiyorsa tahmin etmez, bilinmiyor der. Max skill'in plan kontrolü de
  bu raporla yapılır: plan Max değilse Lider uygulanmaz. Rapor gelince
  basamak seçilir (bkz. Basamak).
- Lider modunda ajan sayısı artar; 5 saatlik ve 7 günlük pencereler de
  izlenir. Max skill'in Fable %75 ve %90 eşikleri Lider modunda Basamak
  tablosuyla uygulanır.
- Lider modeli değişince (`/model opus` ya da `/model sonnet`) Lider modu
  sürer; hangi modelin lider ve hat olacağını Basamak tablosu belirler
  (bkz. Basamak).
- Fable sayacı: brief yazmak ve rapor okumak da Fable tokeni harcar. Lider
  bağlamı küçültür, haftalık Fable sayacını sıfırlamaz; bu kabul edildi.

## İstisnalar

- Liderin kendisi iş yapmasının tek istisnası: Yusuf belirli bir iş için
  açıkça "sen yap" derse, yalnız o işi lider kendisi yapar, sonra Lider
  moduna döner.
- Yusuf belirli bir iş için Fable'ı açıkça adlandırırsa, yalnız o iş için
  Fable alt ajan olarak açılır (bkz. Çekirdek yasa).
- Dosya yazmayan anlatım ve soru-cevap zaten liderin işidir, ajan gerekmez.
  Ama anlatım için ham kaynak okumak gerekiyorsa kaynağı Sonnet özetler.
