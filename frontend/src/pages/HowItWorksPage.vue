<template>
  <div class="page">
    <header class="intro">
      <p class="eyebrow">Product</p>
      <h1>How Solar Auditor works</h1>
      <p>
        Four steps from aerial image to a feasibility pack you can discuss with a customer.
      </p>
    </header>

    <ol class="steps">
      <li>
        <span class="n">1</span>
        <div>
          <h2>Ingest the roof</h2>
          <p>Upload an aerial/satellite photo or start from a built-in residential or commercial preset.</p>
        </div>
      </li>
      <li>
        <span class="n">2</span>
        <div>
          <h2>Segment with Meta SAM 3.1</h2>
          <p>
            Roof planes and obstacles (chimneys, skylights, HVAC) become vector polygons.
            Live Meta Model API adapters ship with a local mock fallback.
          </p>
        </div>
      </li>
      <li>
        <span class="n">3</span>
        <div>
          <h2>Place the array</h2>
          <p>
            Shapely computes usable area (roof minus buffered obstacles) and packs standard 1.7×1.0 m modules
            with setbacks.
          </p>
        </div>
      </li>
      <li>
        <span class="n">4</span>
        <div>
          <h2>Score &amp; ship the report</h2>
          <p>
            Capacity, generation, cost, savings, and payback appear instantly. Muse-style render + PDF
            give you a shareable before/after package.
          </p>
        </div>
      </li>
    </ol>

    <div class="cta-band">
      <RouterLink to="/app" class="btn">Try the auditor now</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 800px;
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
  font-size: clamp(1.8rem, 3vw, 2.4rem);
  letter-spacing: -0.03em;
  color: #0b3d2e;
  margin: 0 0 0.75rem;
}

.intro p {
  color: #3f5248;
  font-size: 1.05rem;
  line-height: 1.55;
  margin: 0;
}

.steps {
  list-style: none;
  padding: 0;
  margin: 2.5rem 0 0;
  display: grid;
  gap: 1rem;
}

.steps li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1rem;
  padding: 1.15rem 1.2rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(11, 61, 46, 0.1);
}

.n {
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #0b3d2e;
  color: #f4faf6;
  font-weight: 700;
  font-family: 'Syne', sans-serif;
}

h2 {
  font-family: 'Syne', sans-serif;
  font-size: 1.15rem;
  margin: 0 0 0.35rem;
  color: #0b3d2e;
}

.steps p {
  margin: 0;
  color: #4d5c54;
  line-height: 1.5;
  font-size: 0.95rem;
}

.cta-band {
  margin-top: 2rem;
}

.btn {
  display: inline-flex;
  text-decoration: none;
  background: #0b3d2e;
  color: #f4faf6;
  font-weight: 700;
  padding: 0.75rem 1.2rem;
  border-radius: 999px;
}
</style>
