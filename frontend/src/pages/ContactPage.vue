<script setup>
import { ref } from 'vue'
import { submitLead } from '../services/api'

const form = ref({ name: '', email: '', company: '', message: '' })
const done = ref(false)
const storedWhere = ref('server')
const sending = ref(false)
const sendError = ref('')

function saveLocal(payload) {
  const key = 'solar_auditor_leads'
  const leads = JSON.parse(localStorage.getItem(key) || '[]')
  leads.push({ ...payload, at: new Date().toISOString() })
  localStorage.setItem(key, JSON.stringify(leads))
}

async function submit() {
  sending.value = true
  sendError.value = ''
  const payload = { ...form.value }
  try {
    await submitLead(payload)
    storedWhere.value = 'server'
  } catch {
    // Backend unreachable (static preview, offline) — keep browser copy.
    saveLocal(payload)
    storedWhere.value = 'this browser only (server unreachable)'
  } finally {
    sending.value = false
  }
  done.value = true
  form.value = { name: '', email: '', company: '', message: '' }
}
</script>

<template>
  <div class="page">
    <header>
      <p class="eyebrow">Contact</p>
      <h1>Tell us about your rooftops</h1>
      <p class="lead">
        Installers, EPCs, and founders — if you want to pilot Solar Auditor on real sites, leave a note.
        Messages go to the server when it's running, otherwise stay in this browser.
      </p>
    </header>

    <form v-if="!done" class="form" @submit.prevent="submit">
      <label>
        Name
        <input v-model="form.name" required />
      </label>
      <label>
        Email
        <input v-model="form.email" type="email" required />
      </label>
      <label>
        Company
        <input v-model="form.company" />
      </label>
      <label class="full">
        Message
        <textarea v-model="form.message" rows="5" required />
      </label>
      <button type="submit" class="btn">Send message</button>
    </form>

    <p v-else class="thanks">
      Received — stored {{ storedWhere }}.
    </p>
  </div>
</template>

<style scoped>
.page {
  max-width: 720px;
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
  margin: 0 0 1.75rem;
  color: #3f5248;
  line-height: 1.55;
}

.form {
  display: grid;
  gap: 0.9rem;
}

@media (min-width: 640px) {
  .form {
    grid-template-columns: 1fr 1fr;
  }
  .full { grid-column: 1 / -1; }
}

label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #0b3d2e;
}

input,
textarea {
  border-radius: 12px;
  border: 1.5px solid rgba(11, 61, 46, 0.2);
  padding: 0.7rem 0.85rem;
  font: inherit;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.85);
}

.btn {
  grid-column: 1 / -1;
  justify-self: start;
  border: none;
  cursor: pointer;
  background: #0b3d2e;
  color: #f4faf6;
  font-weight: 700;
  padding: 0.75rem 1.2rem;
  border-radius: 999px;
}

.thanks {
  padding: 1.2rem 1.3rem;
  border-radius: 14px;
  background: rgba(31, 168, 122, 0.12);
  color: #0b3d2e;
  line-height: 1.5;
}

code {
  font-size: 0.85em;
}
</style>
