const KEY = 'solar_auditor_projects_v1'

export function listProjects() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

export function saveProject(result, label = '') {
  const items = listProjects()
  const entry = {
    id: result.project_id,
    label: label || result.project_id,
    savedAt: new Date().toISOString(),
    image_url: result.image_url,
    render_url: result.render_url,
    analytics: result.analytics,
    layout: { total_panels: result.layout?.total_panels },
    provider: result.provider,
    snapshot: result,
  }
  const next = [entry, ...items.filter((p) => p.id !== entry.id)].slice(0, 40)
  localStorage.setItem(KEY, JSON.stringify(next))
  return next
}

export function getProject(id) {
  return listProjects().find((p) => p.id === id) || null
}

export function deleteProject(id) {
  const next = listProjects().filter((p) => p.id !== id)
  localStorage.setItem(KEY, JSON.stringify(next))
  return next
}

export function clearProjects() {
  localStorage.removeItem(KEY)
}
