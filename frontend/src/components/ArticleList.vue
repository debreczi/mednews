<template>
  <div>
    <!-- Result count -->
    <p class="text-text-muted font-mono text-sm mb-6">
      <span v-if="!isSearching">{{ store.totalCount }} cikk összesen</span>
      <span v-else>{{ articles.length }} találat</span>
    </p>

    <!-- Article grid -->
    <div class="flex flex-col gap-8">
      <ArticleCard v-for="article in articles" :key="article.id" :article="article" />
    </div>

    <!-- Loading skeleton -->
    <LoadingSkeleton v-if="store.loading" :count="6" class="mt-6" />

    <!-- Infinite scroll sentinel -->
    <div ref="sentinel" class="h-4 mt-8" aria-hidden="true" />

    <!-- End of feed -->
    <div v-if="!store.hasMore && articles.length > 0 && !store.loading" class="text-center py-12 text-text-muted text-sm font-mono">
      — Elolvastad az összes cikket. Gratulálunk a kitartáshoz. —
    </div>

    <!-- Empty state -->
    <div v-if="!store.loading && articles.length === 0" class="text-center py-20">
      <p class="text-text-muted text-lg font-serif">Nincs megjeleníthető cikk.</p>
      <p class="text-text-muted text-sm mt-2">Próbálj más keresési feltételeket.</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ArticleCard from './ArticleCard.vue'
import LoadingSkeleton from './LoadingSkeleton.vue'
import { useArticles } from '../composables/useArticles.js'

const props = defineProps({
  searchResults: { type: Array, default: null },
  isSearching: { type: Boolean, default: false },
})

const { store, sentinel } = useArticles()

const articles = computed(() => props.searchResults ?? store.articles)
</script>
