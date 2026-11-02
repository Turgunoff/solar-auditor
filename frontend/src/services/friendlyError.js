// Map raw backend/network errors to a short title + next-step hint.
export function friendlyError(raw) {
  const msg = String(raw?.message || raw || '').trim()
  const low = msg.toLowerCase()
  if (low.includes('no usable roof') || low.includes('no roof')) {
    return {
      title: 'Tom topilmadi',
      hint: 'Rasmda tom aniqlanmadi. Bitta binoga yaqinroq kesma yuklang yoki tayyor presetdan boshlang.',
      raw: msg,
    }
  }
  if (low.includes('zoom too far') || low.includes('zoom')) {
    return {
      title: 'Masshtab juda kichik',
      hint: 'Xaritada bitta binoni kattalashtiring (zoom 19+) va qayta urining.',
      raw: msg,
    }
  }
  if (low.includes('too large') || low.includes('too small') || low.includes('corrupt')) {
    return {
      title: 'Rasm qabul qilinmadi',
      hint: 'JPEG/PNG, kamida 64px va 15MB dan kichik rasm yuklang.',
      raw: msg,
    }
  }
  if (low.includes('battery') || low.includes('offgrid') || low.includes('off-grid')) {
    return {
      title: 'Batareya kerak',
      hint: 'Off-grid rejim uchun Estimate settings da batareya hajmini (kWh) kiriting.',
      raw: msg,
    }
  }
  if (low.includes('region')) {
    return {
      title: 'Noma’lum region',
      hint: 'Estimate settings da ro‘yxatdagi regionni tanlang.',
      raw: msg,
    }
  }
  if (low.includes('project not found')) {
    return {
      title: 'Loyiha serverda topilmadi',
      hint: 'Bu audit server yangilanishidan oldin qilingan bo‘lishi mumkin. Auditni qayta yurgizing — yangi loyiha saqlanadi va PDF ishlaydi.',
      raw: msg,
    }
  }
  if (low.includes('fetch') || low.includes('network') || low.includes('failed to fetch')) {
    return {
      title: 'Server bilan aloqa uzildi',
      hint: 'Backend ishlayotganini tekshirib, qayta urining. Demo uchun presetlar oflayn ham ishlaydi.',
      raw: msg,
    }
  }
  return { title: 'Xatolik yuz berdi', hint: 'Qayta urining yoki presetdan boshlang.', raw: msg }
}
