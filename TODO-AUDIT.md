# Solar Auditor — Kamchiliklar va Qilinishi Kerak Ishlar

Tahlil sanasi: 2026-10-28. Manba: repo kodi, `README.md`, `INTEGRATION.md`, testlar.

## 1. Umumiy holat

MVP yaxlit ishlaydi: preset/upload → segmentatsiya → Shapely layout → ROI → render → PDF.
AI qatlam mock-first, jonli Meta API adapterlari yozilgan, lekin jonli kalit bilan
uchidan-ucchegacha tasdiqlanmagan.

## 2. Kritik (demo/bloklovchi)

- [x] `.env` tekshirildi: `USE_MOCK=false` + jonli `META_API_KEY` mavjud (tuzatish:
      avvalgi "kalit yo'q" xulosasi noto'g'ri edi — `.env` gitignored bo'lgani uchun
      ko'rinmagandi). Demak rejim ataylab jonli. Qolgan ish: jonli rejimni
      `/api/status?probe=true` + smoke bilan tasdiqlash (sandbox port bind'ni
      taqiqlagani uchun server o'rniga `smoke_pipeline.py` bilan tekshirilmoqda).
- [x] Ishchi daraxt commit qilindi (1-vazifa) — keyingi barcha fixlar ham har
      qadamda commit qilinmoqda.
- [x] `pytest` o'rnatildi, 5/5 test yashil (`test_layout_sun_face` + yangi
      `test_mock_presets_panels`). CI ga qo'shish qolgan.
- [x] Mock 0-panel regressiyasi tuzatildi (2026-10-28): eski layout 46/53/194 panel
      berardi, yangi SAM-AABB logikasi (20% shrink + south-cut + 1 tom) 0/0/2 ga
      tushirgandi. `place_panels`/`usable_area_m2` ga `sam_overbox` flagi qo'shildi;
      endpoint mock provider'da uni o'chiradi. Mock smoke: 26/29/193, PASS.
      Jonli yo'l o'zgarmadi (complex_hip jonli 30 panel saqlanadi).
- [x] `feature-hip.jpg`: `frontend/src` va `public` da hech qanday murojaat yo'q
      (grep bo'sh) — 404 xavfi yo'q, o'chirish xavfsiz.

## 3. Backend kamchiliklar

- [!] Sintetik presetlarda SAM jonli rejimda bo'sh qaytadi → mock fallback
      (kutilgan holat, `INTEGRATION.md` da qayd etilgan). Jonli demo uchun real sun'iy
      yo'ldosh kesmasi kerak — bu tashqi ma'lumot masalasi, kod bilan yechilmaydi.
- [x] Fail-closed upload'lar (2026-10-28): jonli SAM tom topolmasa, generik qutiga
      panel chizish o'rniga 422 qaytadi (`segmentation.py` + `endpoints.py`).
      Pipeline regression test (`test_pipeline_no_roof.py`) + production'da jonli
      tekshiruv: tom-bo'lmagan rasmga halol xato, panel yo'q. 38/38 yashil.
- [x] Analitikaga `derate` qo'shildi (2026-10-28): `DERATE=0.85` default
      (inverter/ifloslanish/sim yo'qotishlari), `.env.example` da. Frontend formulani
      takrorlamaydi — faqat API sonlarini ko'rsatadi. Soya/qiyalik hali yo'q.
- [x] Chegara testlari qo'shildi (2026-10-28): `COMMERCIAL_FLAT_M2` osti/usti
      (south-half vs full), shrink tarmoqlari (20% vs setback). 13/13 test yashil,
      mock smoke PASS.
- [x] `meta_client` kontrakt testlari qo'shildi (2026-10-28):
      `test_meta_client_contract.py` — 15 test, tarmoqqa chiqmaydi. Gating
      (`NotReady` holatlari), SAM box parse, `_sam_concept` wiring (soxta response),
      filtr chegaralari (speckle/full-frame/canopy), dedupe, IoU, image-bytes
      ekstraksiya, mime-sniff, JPEG konvert. 28/28 yashil.
- [x] HTTP xato-xaritasi qoplandi (2026-10-28): `MetaModelClient` ga `transport`
      parametri qo'shildi (default `None` = jonli tarmoq, xatti-harakat o'zgarmadi);
      `MockTransport` bilan 502/non-JSON/upload-400/missing-id testlari. 31/31
      yashil, mock smoke PASS.
- [x] Render retention yuqoridagi tozalash bilan yopildi (startup hook + script).
- [x] Upload validatsiya kuchaytirildi (2026-10-28): bo'sh fayl rad etiladi,
      min 64px / max 50MP o'lcham chegarasi, limit `Settings` ga ko'chdi
      (`MAX_UPLOAD_MB` va boshqalar `.env.example` da). Rate-limit hali yo'q.
- [x] Retention tozalash qo'shildi (2026-10-28): `services/cleanup.py` +
      startup hook (`main.py`) + `scripts/cleanup_static.py`. 7 kundan eski
      uploads/renders/exports o'chadi, `.gitkeep` saqlanadi. Hozir 82 fayl/~25MB
      yig'ilgan — barchasi yangi bo'lgani uchun 0 o'chdi. 8/8 test yashil,
      mock smoke PASS.

## 4. Frontend kamchiliklar

- [x] Frontend testlari qo'shildi (5-bo'limga qarang): vitest + `api.test.js`, 3/3 yashil.
- [x] Kalitsiz Maps fallback tekshirildi va yaxshilandi (5-bo'limga qarang).
- [x] three.js lazy-load qilindi, build o'lchandi (5-bo'limga qarang).
- [x] Contact formasi backend'ga ulandi (5-bo'limga qarang).

## 5. Hujjat/konfig

- [x] Hujjat ziddiyati bartaraf etildi (2026-10-28): README endi live-first +
      fallback deydi, `.env.example` izohi ikkala rejimni tushuntiradi.
      `INTEGRATION.md` dagi "kalit `.env` da" holati tasdiqlandi.
- [x] Frontend: three.js lazy-load (`RenderModal` → async 3D tab). Asosiy chunk
      680KB → 138KB (gzip 188→50KB); 3D alohida 545KB chunk'da, faqat kerakda yuklanadi.
- [x] Kalitsiz Maps: tugma yashirin (`mapsEnabled`), majburiy xabar foydalanuvchi
      tilida — preset/upload'ga yo'naltiradi.
- [x] Contact formasi backend'ga ulandi (2026-10-28): `POST /api/leads` →
      `exports/leads.jsonl`; frontend serverga yuboradi, offline'da localStorage
      fallback. `test_leads.py` bilan qoplangan. 33/33 test yashil, frontend build OK.
- [x] `.env` sinxronligi: `test_env_sync.py` — `.env.example` dagi har bir kalit
      `Settings` maydoniga mos kelishi shart (frontend-only kalitlar allowlist'da).
- [x] `SPEC.html` yengil tekshirildi: ko'rsatgan `/api/*` yo'llari routerga mos
      (`health`, `presets`, `process`, `export-pdf`). Chuqur semantik audit qolinmadi.
- [x] Rate-limit qo'shildi (2026-10-28): `RateLimitMiddleware` — `/api/process/*`
      va `/api/leads` da IP boshiga 60/min (sozlanadigan), 429 qaytaradi.
      `test_rate_limit.py` bilan qoplangan.
- [x] CI qo'shildi (2026-10-28): `.github/workflows/ci.yml` — backend pytest +
      mock smoke + frontend build/test.
- [x] Frontend testlari (2026-10-28): vitest + `api.test.js` (3 test: health,
      submitLead, xato xabari). `npm test` yashil. 36/36 backend, smoke PASS.

## 5b. Smoke natijasi (2026-10-28)

`scripts/smoke_pipeline.py` to'liq chiqishi (2026-10-28):
`mode: live`, kalit o'rnatilgan, fallback yoqilgan.
- `complex_hip`: 30 panel, 12.0 kVt, `seg=meta-sam-3.1` (sof jonli!) — OK.
- `commercial_flat_hvac`: 2 panel (shubhali kam), mock-fallback — OK.
- `residential_gable`: 0 panel, `ok=False` — FAIL. Sababi: jonli SAM sintetik
  rasmda tom topolmayapti ("no usable roof boxes"), fallback ham 0 panel bermoqda.
  Jonli API chaqiruvlarida `502 Bad Gateway` / timeout xatolari ham kuzatildi
  (Muse text/image, obstacle promptlar).
- Umumiy: **FAIL (1)**. `pytest` o'rnatilmagani uchun unit-testlar ishga tushmadi.

## 6. Tavsiya etilgan tartib

1. Demo rejimini qulflash (`USE_MOCK` qarori) + iflos daraxtni commit qilish.
2. `pytest` o'rnatib testlarni yashil qilish; `smoke_pipeline.py` ni CI ga.
3. Upload validatsiya + render tozalash.
4. Analitikaga `derate` va chegara testlari.
5. `meta_client` uchun mock-serverda jonli kontrakt testi.
6. Frontend build hajmi + kalitsiz Maps fallback tekshiruvi.
