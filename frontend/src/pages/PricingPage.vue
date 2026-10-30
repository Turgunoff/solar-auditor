<script setup>
import { ref } from 'vue'

const email = ref('')
const sent = ref(false)
const waitlistEl = ref(null)

function joinWaitlist() {
  if (!email.value.includes('@')) return
  const key = 'solar_auditor_waitlist'
  const list = JSON.parse(localStorage.getItem(key) || '[]')
  list.push({ email: email.value, at: new Date().toISOString() })
  localStorage.setItem(key, JSON.stringify(list))
  sent.value = true
  email.value = ''
}

function scrollWaitlist() {
  waitlistEl.value?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <div class="page">
    <header>
      <p class="eyebrow">Early access <span class="track-pill">Push the Frontier · Indie Track</span></p>
      <h1>Simple plans for a product you can keep shipping</h1>
      <p class="lead">
        Start free while you validate. Paid tiers unlock higher volume, team seats, and production Meta API usage.
      </p>
    </header>

    <div class="grid">
      <article class="plan highlight">
        <h2>Starter</h2>
        <p class="price">Free</p>
        <ul>
          <li>Local auditor &amp; mock AI</li>
          <li>3 presets + uploads</li>
          <li>PDF export</li>
          <li>Project history in browser</li>
        </ul>
        <RouterLink to="/app" class="btn">Open auditor</RouterLink>
      </article>

      <article class="plan">
        <h2>Pro</h2>
        <p class="price">$49<span>/mo</span></p>
        <ul>
          <li>Live Meta SAM + Muse adapters</li>
          <li>Higher audit volume</li>
          <li>Saved cloud projects*</li>
          <li>Priority render queue*</li>
        </ul>
        <p class="note">*Roadmap — join waitlist</p>
        <button class="btn ghost" type="button" @click="scrollWaitlist">
          Join waitlist
        </button>
      </article>

      <article class="plan">
        <h2>Installer desk</h2>
        <p class="price">Custom</p>
        <ul>
          <li>Team seats</li>
          <li>Branded PDF</li>
          <li>Region tariffs &amp; irradiance</li>
          <li>API access</li>
        </ul>
        <RouterLink to="/contact" class="btn ghost">Talk to us</RouterLink>
      </article>
    </div>

    <section id="waitlist" ref="waitlistEl" class="waitlist">
      <h2>Get notified when Pro goes live</h2>
      <form v-if="!sent" class="form" @submit.prevent="joinWaitlist">
        <input v-model="email" type="email" required placeholder="you@company.com" />
        <button type="submit" class="btn">Join waitlist</button>
      </form>
      <p v-else class="thanks">You’re on the list. We’ll email when Pro opens.</p>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 1120px;
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
  max-width: 18ch;
}

.lead {
  margin: 0;
  color: #3f5248;
  max-width: 52ch;
  line-height: 1.55;
}

.grid {
  display: grid;
  gap: 1rem;
  margin-top: 2.25rem;
}

@media (min-width: 860px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}

.plan {
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(11, 61, 46, 0.1);
  border-radius: 18px;
  padding: 1.35rem 1.25rem 1.4rem;
  display: flex;
  flex-direction: column;
}

.plan.highlight {
  background: #0b3d2e;
  color: #e8f4ee;
  border-color: transparent;
}

.plan.highlight h2,
.plan.highlight .price { color: #f4faf6; }

.plan.highlight li { color: rgba(244, 250, 246, 0.85); }

h2 {
  font-family: 'Syne', sans-serif;
  margin: 0;
  font-size: 1.2rem;
  color: #0b3d2e;
}

.price {
  font-family: 'Syne', sans-serif;
  font-size: 2rem;
  margin: 0.5rem 0 1rem;
  color: #0b3d2e;
}

.price span {
  font-size: 0.95rem;
  font-weight: 600;
  opacity: 0.7;
}

ul {
  margin: 0 0 1.25rem;
  padding-left: 1.1rem;
  color: #4d5c54;
  line-height: 1.55;
  flex: 1;
}

.note {
  font-size: 0.8rem;
  opacity: 0.75;
  margin: -0.5rem 0 0.85rem;
}

.btn {
  display: inline-flex;
  justify-content: center;
  text-decoration: none;
  border: none;
  cursor: pointer;
  background: #f0b429;
  color: #14201b;
  font-weight: 700;
  padding: 0.7rem 1rem;
  border-radius: 999px;
}

.plan.highlight .btn {
  background: #f0b429;
}

.btn.ghost {
  background: transparent;
  border: 1.5px solid rgba(11, 61, 46, 0.3);
  color: #0b3d2e;
}

.plan.highlight .btn.ghost {
  border-color: rgba(244, 250, 246, 0.4);
  color: #f4faf6;
}

.waitlist {
  margin-top: 2.75rem;
  padding: 1.5rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(11, 61, 46, 0.1);
}

.waitlist h2 {
  margin-bottom: 0.85rem;
}

.form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

input {
  flex: 1;
  min-width: 220px;
  border-radius: 999px;
  border: 1.5px solid rgba(11, 61, 46, 0.2);
  padding: 0.7rem 1rem;
  font: inherit;
  background: #fff;
}

.thanks {
  margin: 0;
  color: #14664c;
  font-weight: 600;
}
</style>
