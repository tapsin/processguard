# ProcessGuard

Windows için hafif görev yöneticisi. Tüm çalışan süreçleri listeler, her sürecin hangi programa ait olduğunu ve hangi üst programın ağacından türediğini gösterir, tek tıkla sonlandırma sağlar.

> Türkçe arayüz. Yönetici hakları ile çalışır (UAC onayı ister).

## Özellikler

- **Tüm süreçler** — PID, işlem adı, CPU %, bellek (MB), dosya yolu/komut satırı
- **Bağlı Program** — her sürecin görünen program adı (Windows dosya açıklaması veya pencere başlığından)
- **Üst Program Ağacı** — sürecin hangi ana programdan türediği, örn. `chrome.exe › explorer.exe`, `services.exe › wininit.exe`
- **Sonlandır** — seçili süreci tek tıkla terminate etme; sonlandırılamayanlar için açıklayıcı uyarı
- **Filtrele** — işlem adı, program adı veya üst ağaca göre anlık arama
- **Sıralama** — her kolon başlığına tıklayarak artan/azalan sıralama
- **Yenile** — anlık process listesi güncelleme
- **Görev Yöneticisi** — Windows'un kendi görev yöneticisine hızlı erişim
- **Tek exe** — kurulum gerektirmez, `ProcessGuard.exe` dosyasını çalıştırın
- İndir : https://files.fm/f/sf7spysrvggq3zmb
## Kullanım

1. `ProcessGuard.exe` dosyasını indirin ve çift tıklayın.
2. Windows "Bu uygulamaya izin vermek istiyor musunuz?" sorusuna **Evet** deyin (yönetici hakları gerekir).
3. Listeden bir süreç seçin ve **Seçiliyi Sonlandır** düğmesine basın.

> Sistem süreçlerini sonlandırmak Windows tarafından engellenebilir; uygulama bu durumu açıkça bildirir.

## Kaynaktan derleme

Gereksinimler: Python 3.12+ ve `pip`.

```bash
pip install psutil pyinstaller
pyinstaller --onefile --noconsole --name ProcessGuard process_guard.py
```

Çıktı: `dist/ProcessGuard.exe`

## Teknoloji

- Python 3.12, tkinter (arayüz), psutil (süreç bilgisi), ctypes (Windows sürüm kaynağı ve pencere başlığı API'si)
- PyInstaller ile tek dosyaya paketlenir

## Lisans

MIT — bkz. [LICENSE](LICENSE).

## DONATE

<table border="1">
<tr><td>USDT TRC20</td><td><code>TYCK6ZyMS6UDt787foPH2QwFuvkdqMw1Jv</code></td></tr>
<tr><td>USDT BSC20</td><td><code>0x15aac92a1945ddbe5c79304bfa388d6be99b26a3</code></td></tr>
</table>

Created by TAPSIN
