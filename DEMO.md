# Demo paketi — AI Rooftop Solar Auditor

Hakaton: Meta Global AI Developer Hackathon · Track: Indie developer · Theme: Push the Frontier.
Jonli manzil: https://cyberpitch.uz (zaxira: http://51.12.209.235:8080).
One-liner: “Upload a rooftop photo → Meta SAM segments usable area → auto panel layout + Muse photoreal after + ROI PDF in under a minute.”

## Tayyorgarlik (demo dan 10 daqiqa oldin)

1. `https://cyberpitch.uz/api/v1/health` oching: `mode: live`, uchala model `meta-*` bo'lsin.
2. Brauzerda `/app` ni yangilab, Preset 1 staged holatda tursin (hali Run bosilmagan).
3. Zaxira: shu fayldagi ssenariy bo'yicha oldindan yozilgan video + lokal `USE_MOCK=true` nusxa.

## Jonli dalil (2026-10-31, shu repo)

- `GET https://api.meta.ai/v1/models` → 200, ro'yxatda `sam-3.1`, `muse-spark-1.3`, `muse-wonder-1.0`.
- Jonli smoke (`USE_MOCK=false`): uchala preset `seg=meta-sam-3.1` (sof jonli, fallback siz) — 124 / 160 / 988 panel, `PASS`.
- Bitta to'liq audit (`solar_proj_0dcc2d3c`): segmentation `meta-sam-3.1`, render `meta-muse-image-1.0`, agent `meta-muse-spark-1.3`; 124 panel, 49.6 kWp.
- Ishlab chiqarish: `https://cyberpitch.uz/api/v1/health` → 200, `mode: live`.

## 90–120 soniyalik video / jonli ssenariy

| Vaqt | Ekran | Aytiladigan matn |
|---|---|---|
| 0:00–0:15 | Landing → **Open auditor** | “Tom suratidan quyosh stansiyasi eskizigacha — bir daqiqadan kam. Orqada Meta SAM 3.1 va Muse modellari.” |
| 0:15–0:35 | Preset 1 tanlash → **Run AI Audit** | “SAM tom va to'siqlarni ajratadi. Yashil — tom, qizil — to'siq, ko'k — hisob-kitob dvigateli joylagan panellar. Bu rasm generatsiyasi emas, Shapely geometriyasi.” |
| 0:35–0:55 | Canvas + Engineering metrics | “Panellar soni, kWp, yillik kWh va o'zini oqlash muddati — hammasi layout dan keladi. Muse surati faqat koncept; ishonchli son — overlay da.” |
| 0:55–1:20 | **Draw exclusion zone** → **Place panels** | “Foydalanuvchi taqiqlangan zonani chizadi — dvigatel panellarni qayta joylaydi. Bu sotuvchi va mijoz suhbati uchun interaktiv qism.” |
| 1:20–1:40 | **Estimate settings** → region/tarif/batareya → **Recalculate** | “Taxminlar shaffof: panel quvvati, tarif, quyosh soati, batareya va on/off-grid jonli qayta hisoblanadi. Off-grid batareyasiz rad etiladi.” |
| 1:40–2:00 | **Preview Concept Render** → **Download PDF Report** | “Yakunda — mijozga beriladigan PDF: oldin/keyin rasmlari, materiallar ro'yxati va halol disclaimer bilan. Keyingi qadam — joyida o'lchov.” |

Muvaffaqiyatsiz sahna bo'lsa: tom topilmasa tizim panel uydirmaydi — 422 bilan halol xato beradi. Bu zaiflik emas, dizayn qarori sifatida aytilsin.

## Pitch matni (1 sahifa)

**Muammo.** Quyosh paneli sotuvchisi har bir tom uchun soatlab qo'lda o'lchov qiladi; mijoz esa taklifni haftalab kutadi.

**Yechim.** AI Rooftop Solar Auditor: bitta aerofoto yoki xarita kesmasi yuklanadi. Meta SAM 3.1 tom va to'siqlarni segmentlaydi, geometrik dvigatel (Shapely) panellarni janubiy yuzaga, chekinishlar bilan joylaydi, Muse Image «keyin» holatini fotoreal ko'rsatadi, Muse Spark esa ehtiyotkor muhandislik izohini yozadi. Natija — panel soni, kWp, yillik ishlab chiqarish, narx, o'zini oqlash va PDF hisobot.

**Nega endi / nega Meta.** SAM ning zero-shot segmentatsiyasi o'qitilgan maxsus modelsiz har qanday tomda ishlaydi; Muse esa sotuv suhbatini vizual qiladi. Uchala model bitta adapter qatlamida (`meta_client.py`), mock rejimda esa internetsiz ham to'liq demo ishlaydi.

**Halollik.** Bu bank hisoboti emas: sonlar qat'iy taxminlarga tayanadi, disclaimer har ekranda va PDF da bor. Tom topilmasa, tizim jim panel chizmaydi.

**Keyingi qadam.** Mintaqaviy quyosh/tarif presetlari (bor), installer bilan joyida tekshiruv, keyin taklif (quote) oqimi.

## Hakam savollariga qisqa javoblar

- “Sonlarni AI o'ylab topadimi?” — Yo'q. Panellarni deterministik geometriya joylaydi; AI segmentatsiya, vizual va matn uchun.
- “Jonlimi yoki mock?” — Standart rejim jonli (`meta-sam-3.1` chiplari ekranda). Tarmoq uzilsa, fallback yorlig'i ochiq ko'rinadi.
- “Aniqlik qancha?” — Bu feasibility eskizi: masshtab xarita/preset dan, ishlab chiqarish quyosh soati taxminidan. Bankable hisob uchun joyida o'lchov shart — mahsulot buni yashirmaydi.
