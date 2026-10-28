<script setup>
import { onMounted, ref } from 'vue'
import { getStatus } from '../services/api'

const status = ref(null)
const error = ref('')
const probing = ref(false)

async function load(probe = false) {
  probing.value = probe
  error.value = ''
  try {
    status.value = await getStatus(probe)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    probing.value = false
  }
}

onMounted(() => load(false))
</script>

<template>
  <div class="page">
    <header>
      <p class="eyebrow">Integration</p>
      <h1>API setup — mock today, Meta tomorrow</h1>
      <p class="lead">
        The product runs fully offline. When Meta Model API credentials arrive, flip three env vars —
        no UI rewrite required.
      </p>
    </header>

    <div v-if="error" class="banner bad">{{ error }}</div>

    <section v-if="status" class="card">
      <div class="row">
        <span class="label">Runtime mode</span>
        <strong :class="status.mode === 'live' ? 'live' : 'mock'">{{ status.mode }}</strong>
      </div>
      <div class="row">
        <span class="label">API key present</span>
        <strong>{{ status.api_key_present ? 'yes' : 'no' }}</strong>
      </div>
      <div class="row">
        <span class="label">Mock fallback</span>
        <strong>{{ status.allow_mock_fallback ? 'enabled' : 'disabled' }}</strong>
      </div>
      <div class="row">
        <span class="label">Pipeline</span>
        <strong>{{ status.pipeline }}</strong>
      </div>
      <p class="msg">{{ status.message }}</p>
      <div class="actions">
        <button type="button" class="btn" :disabled="probing" @click="load(true)">
          {{ probing ? 'Probing…' : 'Probe Meta endpoint' }}
        </button>
        <RouterLink to="/app" class="btn ghost">Open auditor</RouterLink>
      </div>
      <pre v-if="status.ping" class="ping">{{ JSON.stringify(status.ping, null, 2) }}</pre>
    </section>

    <section class="steps">
      <h2>When the API key arrives</h2>
      <ol>
        <li>Put the key in project <code>.env</code> as <code>META_API_KEY</code>.</li>
        <li>Set <code>USE_MOCK=false</code> (keep <code>ALLOW_MOCK_FALLBACK=true</code> at first).</li>
        <li>Confirm <code>META_API_BASE_URL</code> against Meta docs.</li>
        <li>Restart backend · open this page · click <em>Probe Meta endpoint</em>.</li>
        <li>If schema differs, edit only <code>backend/app/services/meta_client.py</code> (see <code>INTEGRATION.md</code>).</li>
      </ol>
    </section>

    <section class="steps">
      <h2>What already works without API</h2>
      <ul>
        <li>Preset + upload audits</li>
        <li>Roof / obstacle polygons (mock SAM)</li>
        <li>Panel packing + ROI</li>
        <li>Composite “after” render + PDF</li>
        <li>Marketing site, projects history, waitlist/leads</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 760px;
  margin: 0 auto;
  padding: 3rem 1.5rem 4rem;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  font-weight: 700;
  color: #1fa87a;
  margin: 0 0 0.5rem;
}

h1 {
  font-family: 'Syne', sans-serif;
  font-size: clamp(1.7rem, 3vw, 2.3rem);
  letter-spacing: -0.03em;
  color: #0b3d2e;
  margin: 0 0 0.75rem;
}

.lead {
  margin: 0 0 1.5rem;
  color: #3f5248;
  line-height: 1.55;
}

.card,
.steps {
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(11, 61, 46, 0.1);
  border-radius: 16px;
  padding: 1.2rem 1.25rem;
  margin-bottom: 1rem;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid rgba(11, 61, 46, 0.08);
  font-size: 0.95rem;
}

.label { color: #6b7a72; }
.mock { color: #0b6e99; }
.live { color: #14664c; }

.msg {
  margin: 0.9rem 0;
  color: #3f5248;
  line-height: 1.45;
  font-size: 0.92rem;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn {
  display: inline-flex;
  text-decoration: none;
  border: none;
  cursor: pointer;
  background: #0b3d2e;
  color: #f4faf6;
  font-weight: 700;
  font-size: 0.88rem;
  padding: 0.65rem 1rem;
  border-radius: 999px;
}

.btn:disabled { opacity: 0.6; cursor: wait; }

.btn.ghost {
  background: transparent;
  border: 1.5px solid rgba(11, 61, 46, 0.25);
  color: #0b3d2e;
}

.ping {
  margin: 1rem 0 0;
  padding: 0.85rem;
  border-radius: 10px;
  background: #14201b;
  color: #d7e6dc;
  font-size: 0.78rem;
  overflow: auto;
}

.steps h2 {
  font-family: 'Syne', sans-serif;
  font-size: 1.15rem;
  color: #0b3d2e;
  margin: 0 0 0.65rem;
}

ol, ul {
  margin: 0;
  padding-left: 1.2rem;
  color: #3f5248;
  line-height: 1.55;
}

code {
  font-size: 0.85em;
  background: rgba(11, 61, 46, 0.08);
  padding: 0.1em 0.35em;
  border-radius: 4px;
}

.banner.bad {
  background: #fde8e8;
  color: #8a1f1f;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  margin-bottom: 1rem;
}
</style>
