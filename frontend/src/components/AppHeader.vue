<template>
  <header class="bg-bg-header sticky top-0 z-50" style="box-shadow: 0 4px 24px rgba(0,0,0,0.2)">
    <div class="max-w-screen-xl mx-auto px-4 sm:px-8 flex items-center justify-between gap-4 py-4" style="min-height: 88px">
      <!-- Logo -->
      <RouterLink to="/" class="flex items-center gap-3 flex-shrink-0 no-underline">
        <div class="w-12 h-12 flex items-center justify-center rounded-xl overflow-hidden" style="background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%); box-shadow: 0 2px 8px rgba(13,148,136,0.3)">
          <span class="text-white font-mono font-bold text-xl leading-none">M</span>
        </div>
        <div>
          <span class="text-white font-serif text-xl font-bold tracking-tight block">
            M<span style="text-decoration: line-through; opacity: 0.6">a</span>edNews
          </span>
          <span class="text-white/50 text-xs font-mono hidden sm:block">Magyar Egészségügyi IT Hírösszefoglaló</span>
        </div>
      </RouterLink>

      <!-- Search -->
      <div class="flex-1 max-w-md">
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Keresés a hírek között..."
          class="w-full px-4 py-2 text-sm text-white placeholder-white/40 rounded-card-sm border border-white/20 focus:outline-none focus:border-accent-teal transition bg-white/10"
          @keydown.enter="$emit('search')"
        />
      </div>

      <!-- Date filter -->
      <div class="flex items-center gap-2 flex-shrink-0">
        <input
          v-model="dateFrom"
          type="date"
          class="text-sm text-white/80 border border-white/20 rounded-card-sm px-3 py-2 focus:outline-none focus:border-accent-teal transition bg-white/10"
        />
        <button
          v-if="dateFrom || searchQuery"
          @click="clearFilters"
          class="text-white/60 hover:text-white text-sm px-2 py-2 transition"
          title="Szűrők törlése"
        >✕</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { useArticlesStore } from '../stores/articles.js'

const store = useArticlesStore()
const searchQuery = defineModel('searchQuery', { default: '' })
const dateFrom = defineModel('dateFrom', { default: '' })

defineEmits(['search'])

function clearFilters() {
  searchQuery.value = ''
  dateFrom.value = ''
}
</script>
