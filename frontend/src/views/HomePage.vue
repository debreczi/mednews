<template>
  <div class="min-h-screen bg-bg-primary flex flex-col">
    <AppHeader v-model:searchQuery="search.query.value" v-model:dateFrom="search.dateFrom.value" @search="search.doSearch" />

    <main class="flex-1 max-w-[1100px] mx-auto w-full px-6 py-8">
      <!-- Region filter buttons -->
      <div class="flex gap-3 mb-6">
        <button
          v-for="f in regionFilters"
          :key="f.value"
          class="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200"
          :class="store.regionFilter === f.value
            ? 'bg-accent-teal text-white shadow-md'
            : 'bg-bg-card text-text-secondary hover:bg-gray-200'"
          @click="store.setRegionFilter(f.value)"
        >
          {{ f.label }}
        </button>
      </div>

      <ArticleList
        :search-results="isFiltering ? search.results.value : null"
        :is-searching="isFiltering"
      />
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import AppFooter from '../components/AppFooter.vue'
import ArticleList from '../components/ArticleList.vue'
import { useSearch } from '../composables/useSearch.js'
import { useArticlesStore } from '../stores/articles.js'

const search = useSearch()
const store = useArticlesStore()
const isFiltering = computed(() => search.results.value.length > 0 || !!search.dateFrom.value)

const regionFilters = [
  { value: null, label: 'Minden hír' },
  { value: 'HU', label: '🇭🇺 Magyar hírek' },
  { value: 'EU', label: '🇪🇺 Cikkek az EU-ból' },
  { value: 'INTL', label: '🇺🇸 Amerikai és egyéb történések' },
]
</script>
