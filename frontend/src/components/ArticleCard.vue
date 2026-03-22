<template>
  <article
    class="bg-bg-card rounded-card overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 flex flex-row group h-56"
    :class="{ 'border-l-4 border-red-400': article.is_tragic }"
  >
    <!-- Image -->
    <div class="relative w-56 flex-shrink-0 self-stretch bg-gray-100 overflow-hidden">
      <img
        v-if="article.image_url"
        :src="article.image_url"
        :alt="article.original_title"
        class="w-full h-full object-cover transition-opacity duration-500 group-hover:scale-105 transition-transform"
        loading="lazy"
        @error="imageError = true"
        v-show="!imageError"
      />
      <div
        v-if="!article.image_url || imageError"
        class="w-full h-full flex items-center justify-center bg-gradient-to-br from-accent-teal/20 to-accent-teal-dark/30"
      >
        <svg class="w-16 h-16 text-accent-teal/40" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
        </svg>
      </div>
      <!-- Date badge -->
      <div class="absolute top-3 left-3">
        <span class="bg-bg-header/90 text-white text-xs font-mono px-2 py-1 rounded-card-sm backdrop-blur-sm">
          {{ formatDate(article.date_published || article.date_collected) }}
        </span>
      </div>
    </div>

    <!-- Card body -->
    <div class="p-5 flex flex-col flex-1">
      <!-- Original title -->
      <p class="text-text-muted text-xs font-mono uppercase tracking-wider mb-2 line-clamp-1">
        {{ article.original_title }}
      </p>

      <!-- MedNews title -->
      <h2 class="font-serif text-lg font-bold text-text-primary leading-snug mb-2 line-clamp-3 group-hover:text-accent-teal transition-colors">
        {{ article.mednews_title || article.original_title }}
      </h2>

      <!-- Star rating -->
      <div class="flex items-center gap-1 mb-3" :aria-label="`Relevancia: ${starCount} / 5`">
        <span
          v-for="n in 5"
          :key="n"
          class="text-sm"
          :class="n <= starCount ? 'text-amber-400' : 'text-gray-200'"
        >★</span>
      </div>

      <!-- Summary -->
      <p class="text-text-secondary text-sm leading-relaxed flex-1 line-clamp-4">
        {{ article.summary }}
      </p>

      <!-- Source link -->
      <div class="mt-4 pt-3 border-t border-gray-100">
        <a
          :href="article.url"
          target="_blank"
          rel="noopener noreferrer"
          class="text-accent-teal text-xs hover:text-accent-teal-dark transition-colors underline-offset-2 hover:underline line-clamp-2"
        >
          {{ article.link_text || 'Az eredeti cikk itt olvasható' }}
        </a>
      </div>

      <!-- Share buttons -->
      <ShareButtons :article="article" />
    </div>
  </article>
</template>

<script setup>
import { ref, computed } from 'vue'
import ShareButtons from './ShareButtons.vue'

const props = defineProps({ article: { type: Object, required: true } })
const imageError = ref(false)

const starCount = computed(() => Math.min(5, Math.max(1, Math.round(props.article.relevance_score / 2))))

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}.`
}
</script>
