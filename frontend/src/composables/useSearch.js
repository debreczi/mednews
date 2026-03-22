import { ref, watch } from 'vue'
import client from '../api/client.js'

export function useSearch() {
  const query = ref('')
  const dateFrom = ref('')
  const results = ref([])
  const searching = ref(false)

  async function doSearch() {
    if (!query.value && !dateFrom.value) {
      results.value = []
      return
    }
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

  // Date filter triggers immediately
  watch(dateFrom, () => doSearch())

  // Auto-search after 3+ chars with 2s debounce; clear when emptied
  let debounceTimer = null
  watch(query, (val) => {
    clearTimeout(debounceTimer)
    if (!val) { results.value = []; return }
    if (val.length >= 3) {
      debounceTimer = setTimeout(doSearch, 1000)
    }
  })

  function clear() {
    query.value = ''
    dateFrom.value = ''
    results.value = []
  }

  return { query, dateFrom, results, searching, doSearch, clear }
}
