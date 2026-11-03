// Map raw backend/network errors to a short title + next-step hint.
export function friendlyError(raw) {
  const msg = String(raw?.message || raw || '').trim()
  const low = msg.toLowerCase()
  if (low.includes('no usable roof') || low.includes('no roof')) {
    return {
      title: 'No roof found',
      hint: 'No roof was detected in the image. Upload a tighter crop of a single building or start with a preset.',
      raw: msg,
    }
  }
  if (low.includes('zoom too far') || low.includes('zoom')) {
    return {
      title: 'Scale too small',
      hint: 'Zoom in on a single building on the map (zoom 19+) and try again.',
      raw: msg,
    }
  }
  if (low.includes('too large') || low.includes('too small') || low.includes('corrupt')) {
    return {
      title: 'Image not accepted',
      hint: 'Upload a JPEG/PNG image at least 64px and under 15 MB.',
      raw: msg,
    }
  }
  if (low.includes('battery') || low.includes('offgrid') || low.includes('off-grid')) {
    return {
      title: 'Battery required',
      hint: 'For off-grid mode, enter a battery size (kWh) in Estimate settings.',
      raw: msg,
    }
  }
  if (low.includes('region')) {
    return {
      title: 'Unknown region',
      hint: 'Select a region from the list in Estimate settings.',
      raw: msg,
    }
  }
  if (low.includes('project not found')) {
    return {
      title: 'Project not found on server',
      hint: 'This audit may predate a server update. Run the audit again — the new project will be saved and the PDF will work.',
      raw: msg,
    }
  }
  if (low.includes('fetch') || low.includes('network') || low.includes('failed to fetch')) {
    return {
      title: 'Connection to server lost',
      hint: 'Check that the backend is running and try again. Presets work offline for the demo.',
      raw: msg,
    }
  }
  return { title: 'Something went wrong', hint: 'Try again or start with a preset.', raw: msg }
}
