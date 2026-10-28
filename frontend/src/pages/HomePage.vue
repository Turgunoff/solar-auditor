<script setup>
</script>

<template>
  <div class="home">
    <!-- Full-bleed hero: brand + headline + line + CTAs on real aerial -->
    <section class="hero">
      <img
        class="hero-img"
        src="/hero-roof.jpg?v=4"
        alt="Aerial view of a residential roof with solar panels on the sunlit face"
      />
      <div class="hero-veil" aria-hidden="true" />
      <div class="hero-copy">
        <p class="brand">Solar Auditor</p>
        <h1>Rooftop photo in. Feasibility sketch out.</h1>
        <p class="sub">
          Segment the roof, keep clear of obstacles, pack modules, and export a first-pass plan —
          built for installers who need speed before the site survey.
        </p>
        <div class="cta-row">
          <RouterLink to="/app" class="cta-primary">Open auditor</RouterLink>
          <RouterLink to="/how-it-works" class="cta-ghost">How it works</RouterLink>
        </div>
      </div>
    </section>

    <section class="band">
      <div class="band-inner">
        <h2>For people who sell and install solar</h2>
        <p>
          Homeowners get a clear story. Installers get a faster first pass. Founders get a real audit
          workflow — not another chatbot wrapper.
        </p>
      </div>
    </section>

    <section class="shot">
      <img src="/feature-pitch.jpg?v=3" alt="Pitched campus roofs with panels on sunlit slopes" />
      <div class="shot-copy">
        <h2>Respect the roof geometry</h2>
        <p>
          Prefer sunlit planes, keep trees and yards out of the array, and treat Muse as concept art —
          the layout engine owns the module count.
        </p>
      </div>
    </section>

    <section class="shot reverse">
      <img src="/feature-commercial.jpg?v=3" alt="Commercial flat roof packed with solar modules" />
      <div class="shot-copy">
        <h2>Layout and money math together</h2>
        <p>
          Oriented packing, kWp, annual kWh, installed cost, and simple payback — labeled as
          feasibility estimates, not a bankable report.
        </p>
      </div>
    </section>

    <section class="shot">
      <img src="/feature-report.jpg?v=3" alt="Installer reviewing a solar feasibility report" />
      <div class="shot-copy">
        <h2>A PDF you can walk into a meeting with</h2>
        <p>
          Aerial, layout overlay, Muse concept, and a clear disclaimer — ready for a client
          conversation, then refine on site.
        </p>
        <RouterLink to="/app" class="cta-primary">Run a free audit</RouterLink>
      </div>
    </section>

    <section class="close">
      <div class="close-inner">
        <h2>Start with a real roof</h2>
        <p>Pick a building on the map or drop an aerial — get a layout sketch in one pass.</p>
        <div class="cta-row">
          <RouterLink to="/app" class="cta-primary light">Open auditor</RouterLink>
          <RouterLink to="/pricing" class="cta-ghost light">Early plans</RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  --ink: #0c1f18;
  --foam: #f2f7f4;
  --mist: #c5d6cc;
  --leaf: #1a6b4f;
  --sun: #e8a317;
  margin-top: -4.25rem; /* pull under sticky nav */
}

.hero {
  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
  display: grid;
  align-items: end;
  overflow: hidden;
  color: var(--foam);
}

.hero-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 40%;
  transform: scale(1.06);
  animation: drift 18s ease-in-out alternate infinite;
}

.hero-veil {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(8, 22, 16, 0.42) 0%, rgba(8, 22, 16, 0.12) 42%, rgba(8, 22, 16, 0.72) 100%),
    linear-gradient(90deg, rgba(8, 22, 16, 0.4) 0%, transparent 58%);
  pointer-events: none;
}

.hero-copy {
  position: relative;
  z-index: 1;
  width: min(640px, 100%);
  padding: 7.5rem 1.5rem 3.25rem;
  padding-left: max(1.5rem, calc((100vw - 1120px) / 2 + 1.5rem));
  animation: rise 0.85s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.brand {
  margin: 0 0 0.85rem;
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: clamp(2.4rem, 6vw, 3.75rem);
  letter-spacing: -0.045em;
  line-height: 0.95;
  color: #fff;
  text-shadow: 0 2px 24px rgba(0, 0, 0, 0.35);
}

h1 {
  margin: 0 0 0.85rem;
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: clamp(1.25rem, 2.4vw, 1.65rem);
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: rgba(242, 247, 244, 0.92);
  max-width: 22ch;
}

.sub {
  margin: 0 0 1.6rem;
  font-size: 1.05rem;
  line-height: 1.55;
  color: rgba(242, 247, 244, 0.78);
  max-width: 40ch;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.cta-primary,
.cta-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-weight: 700;
  font-size: 0.95rem;
  padding: 0.8rem 1.2rem;
  border-radius: 4px;
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.cta-primary {
  background: var(--sun);
  color: #1a1405;
}

.cta-primary:hover {
  transform: translateY(-2px);
  background: #f0b429;
}

.cta-primary.light {
  background: var(--foam);
  color: var(--ink);
}

.cta-ghost {
  border: 1.5px solid rgba(242, 247, 244, 0.45);
  color: var(--foam);
  background: rgba(8, 22, 16, 0.25);
  backdrop-filter: blur(6px);
}

.cta-ghost:hover {
  border-color: #fff;
}

.cta-ghost.light {
  border-color: rgba(242, 247, 244, 0.4);
  color: var(--foam);
}

.band {
  background: #0f2a20;
  color: var(--foam);
  padding: 3.75rem 1.5rem;
}

.band-inner {
  max-width: 720px;
  margin: 0 auto;
  animation: rise 0.7s ease both;
}

.band h2,
.shot-copy h2,
.close h2 {
  margin: 0 0 0.75rem;
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: clamp(1.45rem, 2.6vw, 1.95rem);
  letter-spacing: -0.03em;
}

.band p,
.shot-copy p,
.close p {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.6;
  color: rgba(242, 247, 244, 0.78);
}

.shot {
  display: grid;
  background: #0a1a14;
  color: var(--foam);
}

@media (min-width: 900px) {
  .shot {
    grid-template-columns: 1.15fr 0.85fr;
    min-height: 420px;
  }
  .shot.reverse {
    grid-template-columns: 0.85fr 1.15fr;
  }
  .shot.reverse img {
    order: 2;
  }
}

.shot img {
  width: 100%;
  height: 100%;
  min-height: 280px;
  object-fit: cover;
  display: block;
}

.shot-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.35rem;
  padding: 2.5rem 1.5rem;
  max-width: 520px;
}

@media (min-width: 900px) {
  .shot-copy {
    padding: 3rem 2.5rem;
  }
}

.shot-copy .cta-primary {
  margin-top: 1.25rem;
  align-self: flex-start;
}

.close {
  background:
    radial-gradient(600px 280px at 20% 0%, rgba(232, 163, 23, 0.18), transparent 60%),
    #07140f;
  padding: 4.5rem 1.5rem;
}

.close-inner {
  max-width: 640px;
  margin: 0 auto;
  text-align: left;
}

.close .cta-row {
  margin-top: 1.5rem;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes drift {
  from {
    transform: scale(1.06) translate3d(0, 0, 0);
  }
  to {
    transform: scale(1.12) translate3d(-1.5%, -1%, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-img,
  .hero-copy {
    animation: none;
  }
  .hero-img {
    transform: none;
  }
}
</style>
