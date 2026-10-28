<script setup>
const year = new Date().getFullYear()
</script>

<template>
  <footer class="site-footer">
    <div class="inner">
      <div>
        <div class="foot-brand">Solar Auditor</div>
        <p>AI rooftop feasibility sketches for installers, founders, and homeowners.</p>
      </div>
      <div class="cols">
        <RouterLink to="/how-it-works">How it works</RouterLink>
        <RouterLink to="/app">Auditor</RouterLink>
        <RouterLink to="/setup">API setup</RouterLink>
        <RouterLink to="/pricing">Pricing</RouterLink>
        <RouterLink to="/contact">Contact</RouterLink>
      </div>
    </div>
    <p class="copy">
      © {{ year }} Solar Auditor · Demo feasibility — not a bankable engineering report.
    </p>
  </footer>
</template>

<style scoped>
.site-footer {
  margin-top: 0;
  border-top: 1px solid rgba(242, 247, 244, 0.08);
  padding: 2.75rem 1.5rem 2rem;
  background: #050e0b;
  color: #c5d6cc;
}

.inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1.5rem;
}

.foot-brand {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 1.15rem;
  color: #f2f7f4;
  margin-bottom: 0.4rem;
}

.inner p {
  margin: 0;
  max-width: 38ch;
  color: rgba(197, 214, 204, 0.85);
  font-size: 0.92rem;
  line-height: 1.5;
}

.cols {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem 1.4rem;
}

.cols a {
  color: #f2f7f4;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
}

.cols a:hover {
  color: #e8a317;
}

.copy {
  max-width: 1120px;
  margin: 1.75rem auto 0;
  color: rgba(197, 214, 204, 0.55);
  font-size: 0.8rem;
}
</style>
