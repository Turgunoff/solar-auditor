import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'
import AuditorPage from '../pages/AuditorPage.vue'
import HowItWorksPage from '../pages/HowItWorksPage.vue'
import PricingPage from '../pages/PricingPage.vue'
import ProjectsPage from '../pages/ProjectsPage.vue'
import ContactPage from '../pages/ContactPage.vue'
import SetupPage from '../pages/SetupPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomePage, meta: { layout: 'site' } },
    { path: '/app', name: 'auditor', component: AuditorPage, meta: { layout: 'app' } },
    { path: '/how-it-works', name: 'how', component: HowItWorksPage, meta: { layout: 'site' } },
    { path: '/pricing', name: 'pricing', component: PricingPage, meta: { layout: 'site' } },
    { path: '/projects', name: 'projects', component: ProjectsPage, meta: { layout: 'site' } },
    { path: '/contact', name: 'contact', component: ContactPage, meta: { layout: 'site' } },
    { path: '/setup', name: 'setup', component: SetupPage, meta: { layout: 'site' } },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
