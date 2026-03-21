import { ref, onMounted, onUnmounted } from 'vue'
import { useArticlesStore } from '../stores/articles.js'

export function useArticles() {
  const store = useArticlesStore()
  const sentinel = ref(null)
  let observer = null

  function setupInfiniteScroll() {
    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && store.hasMore && !store.loading) {
          store.fetchArticles()
        }
      },
      { threshold: 0.8 }
    )
    if (sentinel.value) observer.observe(sentinel.value)
  }

  onMounted(() => {
    store.fetchArticles(true)
    setupInfiniteScroll()
  })

  onUnmounted(() => {
    if (observer) observer.disconnect()
  })

  return { store, sentinel }
}
