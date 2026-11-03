# Interra — Home Assistant entegrasyonu

Interra Pro akıllı ev panelini Home Assistant'a bağlar. Panelin yerel TCP/JSON
protokolüyle **sürekli bağlı** kalır; cihazları otomatik bulur, durumu anlık
gösterir (tablettan değişince de) ve HA'dan komutları panele iletir.

- **Aç/kapat cihazları** (aydınlatma, genel röleler, değersiz iklim, alarm) → `switch`
- **Panjur / perde** → `cover` (yukarı / dur / aşağı)
- Her cihaz Interra odasının adıyla **HA alanına** önerilir (`suggested_area`).
- Yüzde/sıcaklık yalnızca cihaz gerçekten destekliyorsa gösterilir.

## Kurulum (HACS)

1. HACS → ⋮ → **Özel depolar** → `https://github.com/aygkhn/interra-ha`, tür **Integration**.
2. **Interra**'yı indir, Home Assistant'ı yeniden başlat.
3. **Ayarlar → Cihazlar ve hizmetler → Entegrasyon ekle → Interra**.
4. Panel IP, port, kullanıcı ve şifreyi gir.

## Notlar

- Tek panel desteklenir (single config entry).
- Protokol notları ve tersine mühendislik: ayrı dokümanda.
