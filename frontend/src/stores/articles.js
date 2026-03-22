import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '../api/client.js'

export const useArticlesStore = defineStore('articles', () => {
  const articles = ref([])
  const nextCursor = ref(null)
  const totalCount = ref(0)
  const loading = ref(false)
  const hasMore = ref(true)
  const searchQuery = ref('')
  const filterDate = ref(null)
  const regionFilter = ref(null) // null = mixed, 'HU', 'EU', 'INTL'

  async function fetchArticles(reset = false) {
    if (loading.value || (!hasMore.value && !reset)) return
    loading.value = true

    if (reset) {
      articles.value = []
      nextCursor.value = null
      hasMore.value = true
    }

    try {
      const params = {}
      if (nextCursor.value) params.after = nextCursor.value
      if (regionFilter.value) params.region = regionFilter.value

      const { data } = await client.get('/articles', { params })
      articles.value.push(...data.articles)
      nextCursor.value = data.next_cursor
      totalCount.value = data.total_count
      hasMore.value = !!data.next_cursor
    } finally {
      loading.value = false
    }
  }

  function setRegionFilter(region) {
    regionFilter.value = region
    fetchArticles(true)
  }

  return { articles, nextCursor, totalCount, loading, hasMore, searchQuery, filterDate, regionFilter, fetchArticles, setRegionFilter }
})
