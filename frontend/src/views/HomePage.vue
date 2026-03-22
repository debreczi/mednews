<template>
  <div class="min-h-screen bg-bg-primary flex flex-col">
    <AppHeader v-model:searchQuery="search.query.value" v-model:dateFrom="search.dateFrom.value" />

    <main class="flex-1 max-w-[1100px] mx-auto w-full px-6 py-8">
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

const search = useSearch()
const isFiltering = computed(() => !!search.query.value || !!search.dateFrom.value)
</script>
