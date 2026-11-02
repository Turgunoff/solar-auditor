# AI Rooftop Solar Auditor — hakaton tayyorgarligi tahlili va qolgan ishlar rejasi

Sana: 2026-10-31. Manbalar: repo kodi, `README.md`, `SPEC.html`, `INTEGRATION.md`, `TODO-AUDIT.md`, `DEPLOY.md`, testlar va shu kuni qayta yurgizilgan tekshiruvlar (backend `45 passed`, mock smoke `PASS`, frontend `4 passed`, build muvaffaqiyatli).

## Xulosa — hakaton uchun yetarlimi?

**MVP demo sifatida: HA, yetarli. Jonli Meta mezonini isbotlash sharti bilan.**

Loyiha to'liq zanjirni yopadi: preset/upload/Google Map → segmentatsiya → Shapely panel joylashuvi → ROI → agent izohi → koncept render → PDF. Testlar yashil, Docker deploy va jonli URL infratuzilmasi tayyor, hujjatlar sinxron. Shuning uchun hakamlar oldida 2–3 daqiqalik ssenariyni uzilishsiz ko'rsatish mumkin.

Asosiy xatar kodda emas, **isbotda**: `SPEC.html` talabi — «haqiqiy Meta Model API (SAM 3.1 + kamida bitta Muse)» — hozircha sintetik presetlarda jonli SAM bo'sh qaytib mock fallbackga tushadi (`INTEGRATION.md`, `TODO-AUDIT.md` §5b: jonli rejimda `residential_gable` FAIL, 502/timeout kuzatilgan). Agar hakamlar jonli rejimni real sun'iy yo'ldosh kesmasida tekshirsa va faqat `mock`/`+mock-fallback` chiplarini ko'rsa, «Push the Frontier» da'vosi zaiflashadi. Shu bitta bo'shliq yopilsa, loyiha ishonchli hakaton MVP darajasiga chiqadi; yopilmasa — kuchli mock-demo bo'lib qoladi.

Baholash (10 ballik, demo kunidagi holat):

| Mezon | Ball | Izoh |
|---|---|---|
| Demo oqimi to'liqligi | 9/10 | Staged flow, refine, assumptions, PDF, Projects — hammasi bor |
| Muhandislik ishonchliligi | 7/10 | Shapely + derate + fail-closed bor; qiyalik/azimut/soya yo'q, disclaimer halol |
| Jonli Meta isboti | 4/10 | Adapter va kontrakt testlari bor, real kesmada jonli dalil yo'q |
| Barqarorlik / testlar | 9/10 | 45 backend + 4 frontend yashil, CI, rate-limit, retention |
| Taqdimot / deploy | 7/10 | VPS + nginx tayyor; HTTPS (certbot) va demo video hali yo'q |

## Hozirgi holat (tasdiqlangan)

- **Backend (FastAPI):** `app/api/endpoints.py` (550 qator) — health/status/presets, `process/preset|upload|map-upload|refine`, `assumptions/defaults`, `leads`, `export-pdf`. Servislar: `meta_client.py` (SAM/Muse adapter, injectable transport), `segmentation.py` (mock shablonlar + jonli SAM + fallback), `layout_engine.py` (janub yarmi kesimi, flat vs pitched, setback, markaziy tom tanlash, yo'nalishga mos packing), `analytics.py` (quvvat/ishlab chiqarish/`DERATE=0.85`/narx/tejamkorlik/payback, off-grid batareyasiz 400), `render_engine.py` (deterministik overlay + Muse fotoreal), `agent_report.py`, `pdf_export.py`.
- **Frontend (Vue 3 + Vite):** 7 sahifa (landing, `/app`, how-it-works, pricing, projects, contact, setup), canvas qatlamlari (tom/to'siq/panel), exclusion-zone chizish, assumptions muharriri, RenderModal, MapPicker. Build: ~149 KB (gzip ~54 KB).
- **Tekshiruv (2026-10-31, shu mashinada):** backend `45 passed`, `USE_MOCK=true` smoke `PASS` (mockda 327/419/710 panel — sonlar preset masshtabiga bog'liq, sifat mezoni emas), frontend `4 passed`, `npm run build` OK.
- **Xavfsizlik/ops:** upload guardlar (15 MB, 64 px–50 MP), IP rate-limit 60/min, 7 kunlik static retention, fail-closed 422 (jonli SAM tom topolmasa panel chizilmaydi).
- **Kamchiliklar (kod darajasida):** loyiha saqlash faqat xotirada (`app/store.py`) va brauzerda (Projects) — server restartida PDF topilmasligi mumkin; narx/Quyosh soati bitta global konstant, joylashuvga bog'liq emas; pitch/azimut/soya/tilt hisobga olinmaydi; `backend/static` 37 MB ga o'sgan; HTTPS hali yo'q (`DEPLOY.md`: DNS + certbot kutilmoqda).

## Kuchli tomonlar (hakamlar oldida ta'kidlash)

- Halol muhandislik: disclaimer, fail-closed, «Muse — koncept, layout — haqiqat» prinsipi, soxta aniqlik yo'q.
- Adapter arxitekturasi: jonli/mock almashinuvi faqat `meta_client.py` da, UI/layout/analytics kontrakti o'zgarmaydi; 15+ kontrakt testi tarmoqsiz ishlaydi.
- Interaktiv farqlovchilar: exclusion-zone → qayta packing, jonli assumptions (batareya, on/off-grid), MapPicker (Mercator `meters_per_pixel`).

## Bo'shliqlar va nima qo'shish kerak (ustuvorlik bo'yicha)

### P0 — demo bloklovchi (hakaton oldidan shart)

1. **Jonli SAM dalili:** real sun'iy yo'ldosh kesmasida (sintetik emas) `USE_MOCK=false` bilan bitta to'liq yugurish: provider chiplari `meta-sam-3.1` + `meta-muse-*`, overlay skrinshoti va `/api/v1/status?probe=true` javobi dalil sifatida saqlansin. Bo'lmasa, pitchda rejim ochiq aytilsin («live-first, fallback shaffof») — yashirish yomonroq.
2. **Demo ssenariysi va video:** 90–120 soniyalik yozib olingan oqim (preset → Run AI Audit → zona chizish → Recalculate → PDF) + 1 sahifalik pitch matni (`SPEC.html` one-lineri asosida). Jonli server ishlamasa, video najot beradi.
3. **HTTPS:** DNS `cyberpitch.uz` ni serverga yo'naltirish + certbot; health-check `https://cyberpitch.uz/api/v1/health` bilan tasdiqlansin (`DEPLOY.md` Server map yangilansin).

### P1 — ishonchlilik (vaqt qolsa, tartib bilan)

4. **Joylashuvga bog'liq taxminlar:** shahar/region tanlovi → `peak_sun_hours` va tarif presetlari (hech bo'lmasa O'zbekiston + global default); assumptions formasida ko'rinsin, backend defaultlari bilan sinxron (`test_env_sync` buzilmasin).
5. **PDF mustahkamlash:** layout rasmi + jadval + disclaimer bitta faylda ekanini jonli tekshirish; `store.py` xotira cheklovi hujjatda ochiq yozilsin (yoki eng kichik disk-persist: mavjud static papkaga JSON).
6. **Bo'sh/xato holatlar:** «tom topilmadi», «0 panel», tarmoq xatosi uchun foydalanuvchi tilidagi xabarlar va presetga qaytish tugmasi (hakam tasodifiy rasm yuklasa, demo sinmasin).

### P2 — farqlovchi (faqat P0/P1 yopilgach)

7. Before/after slayder (asl rasm vs koncept render), CO2 tejash va oylik ishlab chiqarish egri chizig'i (mavjud analitikadan, yangi backend shart emas).
8. Kuchaytirilgan soya/pitch evristikasi — faqat oddiy, tushuntirib bo'ladigan qoida bilan; murakkab 3D yoki yangi model qo'shilmasin.

Qo'shilmasin (scope himoyasi): auth/to'lov, to'liq DB, mobil ilova, yangi AI modellar, layout dvigatelini qayta yozish.

## Goal

Hakaton kunigacha loyihani «ishlaydigan mock-demo»dan «jonli Meta dalili bor, yozib olingan va HTTPS orqali ochiladigan demo» darajasiga ko'tarish, muhandislik halolligini saqlagan holda.

## Success Criteria

- Real kesmada jonli SAM + kamida bitta Muse chaqiruvi dalillangan (chip + overlay + status javobi).
- 90–120 s demo video va pitch matni tayyor; asosiy oqim videoda uzilishsiz.
- `https://cyberpitch.uz/api/v1/health` 200 qaytaradi.
- Backend `45+` test va frontend test/build yashil; mock smoke `PASS`.
- Tasodifiy (tom bo'lmagan) rasm yuklanganda foydalanuvchi tushunarli xato ko'radi, panel chizilmaydi.

## Approach

Yangi funksiya emas, **isbot va qadoqlash** ustuvor. Avval jonli yo'l real ma'lumotda tasdiqlanadi, keyin shu oqim videoga yoziladi, so'ng HTTPS bilan yopiladi. P1 faqat P0 dalili bor bo'lsa boshlanadi. Har qadam `AGENTS.md` qoidasiga bo'ysunadi: xatti-harakat o'zgarsa, hujjatlar o'sha commitda yangilanadi (endpoint/env → `README.md`/`.env.example`, deploy → `DEPLOY.md` Server map, dars bo'lsa `TODO-AUDIT.md`).

## Steps

1. **Jonli tekshiruv (P0-1):** serverda yoki lokalda `USE_MOCK=false` + haqiqiy kalit bilan real sun'iy yo'ldosh kesmasini (Google Map orqali olingan, zoom 19+) `process/map-upload` dan o'tkazish; `status?probe=true`, provider chiplari va overlayni saqlash. Muvaffaqiyatsiz bo'lsa: `meta_client.py` kontraktini jonli javobga moslash (faqat shu fayl), fallback sababini `TODO-AUDIT.md` ga yozish. Bog'liqlik: keyingi qadamlar shunga tayanadi.
2. **Demo qadoqlash (P0-2):** tasdiqlangan oqim bo'yicha ssenariy yozish, video yozish, pitch matnini `SPEC.html` bilan moslash (theme/track/model satrlari). Yangi kod kerak emas.
3. **HTTPS (P0-3):** DNS → certbot → health tekshiruvi; `DEPLOY.md` yangilanadi.
4. **Region presetlari (P1-4):** `Assumptions` ga region maydoni (ixtiyoriy), backend defaultlar, frontend forma; `test_env_sync` va mavjud testlar yashil qolishi shart. Yangi env bo'lsa `.env.example` + `README.md` jadvali.
5. **PDF/persist tekshiruvi (P1-5):** jonli PDF ochib ko'rish; kerak bo'lsa eng kichik disk-persist (`store.py` o'rniga static JSON), alohida test bilan.
6. **Xato holatlari (P1-6):** 422/0-panel/tarmoq xatolari uchun UI xabarlari; qo'lda uch ssenariy tekshiruvi.
7. **P2 (ixtiyoriy):** before/after slayder va CO2/oylik egri chiziq — faqat mavjud JSON dan, yangi endpoint siz.

## Validation Plan

- Backend: `cd backend && ../.venv/bin/python -m pytest tests -q` — yashil (hozir 45).
- Mock smoke: `cd backend && USE_MOCK=true ../.venv/bin/python scripts/smoke_pipeline.py` — `PASS`.
- Frontend: `cd frontend && npm test` va `npm run build` — yashil.
- Jonli: `GET /api/v1/status?probe=true` + real kesmada audit — chiplar va overlay ko'z bilan.
- Deploy: `curl https://cyberpitch.uz/api/v1/health` — 200.
- Qo'lda: tom bo'lmagan rasm → tushunarli xato; off-grid batareyasiz → 400 xabari.

## Risks / Open Questions

- Meta API sxemasi o'zgargan bo'lishi mumkin: moslash faqat `meta_client.py` da, kontrakt testlari yangilanadi; vaqt yetmasa, pitchda fallback ochiq aytiladi.
- DNS/certbot hakaton tashkilotchisiga emas, domen egasiga bog'liq — kechiksa, `http://51.12.209.235:8080` zaxira URL sifatida pitchga yoziladi.
- Savol (bloklamaydi): demo jonli serverda mi yoki lokalda mi ko'rsatiladi? Standart taxmin — server asosiy, lokal + video zaxira. Javob P0 tartibini o'zgartirmaydi, faqat qaysi muhitda jonli dalil olinishini belgilaydi.
