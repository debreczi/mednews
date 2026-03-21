import { ref, watch } from 'vue'
import client from '../api/client.js'

export function useSearch() {
  const query = ref('')
  const dateFrom = ref('')
  const results = ref([])
  const searching = ref(false)
  let debounceTimer = null

  async function doSearch() {
    searching.value = true
    try {
      const params = {}
      if (query.value) params.q = query.value
      if (dateFrom.value) params.from_date = dateFrom.value
      const { data } = await client.get('/search', { params })
      results.value = data
    } catch (e) {
      console.error('Search failed', e)
    } finally {
      searching.value = false
    }
  }

  watch([query, dateFrom], () => {
    clearTimeout(debounceTimer)
    if (!query.value && !dateFrom.value) {
      results.value = []
      return
    }
    debounceTimer = setTimeout(doSearch, 300)
  })

  function clear() {
    query.value = ''
    dateFrom.value = ''
    results.value = []
  }

  return { query, dateFrom, results, searching, clear }
}
