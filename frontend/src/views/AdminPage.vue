<template>
  <div class="min-h-screen bg-bg-primary flex flex-col">
    <AppHeader />
    <main class="flex-1 max-w-screen-xl mx-auto w-full px-4 sm:px-8 py-8">
      <h1 class="font-serif text-3xl font-bold text-text-primary mb-8">Admin Panel</h1>

      <!-- Manual Scrape -->
      <section class="bg-bg-card rounded-card p-6 mb-6 shadow-sm">
        <h2 class="font-serif text-xl font-bold mb-4">Scrape vezérlés</h2>
        <div class="flex items-center gap-4">
          <button
            @click="triggerScrape"
            :disabled="scraping"
            class="px-6 py-2 bg-accent-teal text-white rounded-card-sm font-semibold hover:bg-accent-teal-dark transition disabled:opacity-50"
          >
            {{ scraping ? 'Futtatás folyamatban...' : 'Scrape futtatása most' }}
          </button>
          <span v-if="scrapeMessage" class="text-sm" :class="scrapeError ? 'text-red-500' : 'text-green-600'">
            {{ scrapeMessage }}
          </span>
        </div>
        <p class="text-text-muted text-sm mt-3 font-mono">Admin API kulcs szükséges az X-Admin-Key fejlécben.</p>
      </section>

      <!-- Log Viewer -->
      <section class="bg-bg-card rounded-card p-6 mb-6 shadow-sm">
        <h2 class="font-serif text-xl font-bold mb-4">Audit napló</h2>
        <div v-if="logs.length === 0" class="text-text-muted text-sm">Nincsenek naplóbejegyzések.</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm font-mono">
            <thead class="text-text-muted border-b">
              <tr>
                <th class="text-left py-2 pr-4">Időpont</th>
                <th class="text-left py-2 pr-4">Esemény</th>
                <th class="text-left py-2 pr-4">Cikkek</th>
                <th class="text-left py-2">Hiba</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id" class="border-b border-gray-50 hover:bg-gray-50">
                <td class="py-2 pr-4 text-text-muted text-xs">{{ formatTs(log.timestamp) }}</td>
                <td class="py-2 pr-4">{{ log.event_type }}</td>
                <td class="py-2 pr-4">{{ log.articles_saved ?? '—' }}</td>
                <td class="py-2 text-red-400 text-xs truncate max-w-xs">{{ log.error_message ?? '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Source List -->
      <section class="bg-bg-card rounded-card p-6 shadow-sm">
        <h2 class="font-serif text-xl font-bold mb-4">Források ({{ sources.length }})</h2>
        <div v-if="sources.length === 0" class="text-text-muted text-sm">Nincsenek forrás bejegyzések.</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-text-muted border-b font-mono">
              <tr>
                <th class="text-left py-2 pr-4">Forrás</th>
                <th class="text-left py-2 pr-4">Típus</th>
                <th class="text-left py-2 pr-4">Utolsó scrape</th>
                <th class="text-left py-2">Aktív</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="src in sources" :key="src.id" class="border-b border-gray-50 hover:bg-gray-50">
                <td class="py-2 pr-4">
                  <a :href="src.url" target="_blank" class="text-accent-teal hover:underline">{{ src.name }}</a>
                </td>
                <td class="py-2 pr-4 font-mono text-xs text-text-muted">{{ src.type }}</td>
                <td class="py-2 pr-4 font-mono text-xs text-text-muted">{{ src.last_scraped ? formatTs(src.last_scraped) : 'soha' }}</td>
                <td class="py-2">
                  <span
                    class="px-2 py-0.5 rounded text-xs font-mono"
                    :class="src.active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-500'"
                  >{{ src.active ? 'aktív' : 'inaktív' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
    <AppFooter />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import AppFooter from '../components/AppFooter.vue'
import client from '../api/client.js'

const ADMIN_KEY = import.meta.env.VITE_ADMIN_API_KEY || ''
const adminHeaders = { 'X-Admin-Key': ADMIN_KEY }

const logs = ref([])
const sources = ref([])
const scraping = ref(false)
const scrapeMessage = ref('')
const scrapeError = ref(false)

function formatTs(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getFullYear()}.${String(d.getMonth()+1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

async function loadLogs() {
  try {
    const { data } = await client.get('/admin/logs', { headers: adminHeaders })
    logs.value = data.logs || []
  } catch { logs.value = [] }
}

async function loadSources() {
  try {
    const { data } = await client.get('/admin/sources', { headers: adminHeaders })
    sources.value = data || []
  } catch { sources.value = [] }
}

async function triggerScrape() {
  scraping.value = true
  scrapeMessage.value = ''
  scrapeError.value = false
  try {
    await client.post('/admin/trigger-scrape', {}, { headers: adminHeaders })
    scrapeMessage.value = 'Scrape feladat elindítva!'
  } catch (e) {
    scrapeError.value = true
    scrapeMessage.value = e.response?.status === 403 ? 'Érvénytelen admin kulcs.' : 'Hiba a scrape indításakor.'
  } finally {
    scraping.value = false
  }
}

onMounted(() => { loadLogs(); loadSources() })
</script>
