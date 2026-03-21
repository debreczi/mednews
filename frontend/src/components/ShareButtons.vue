<template>
  <div class="flex items-center gap-2 mt-3 flex-wrap">
    <!-- LinkedIn -->
    <button
      @click="shareLinkedIn(article.url, article.mednews_title)"
      class="share-btn"
      title="Megosztás LinkedIn-en"
      aria-label="LinkedIn megosztás"
    >
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
      </svg>
    </button>

    <!-- X / Twitter -->
    <button
      @click="shareX(article.url, article.mednews_title)"
      class="share-btn"
      title="Megosztás X-en"
      aria-label="X megosztás"
    >
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
      </svg>
    </button>

    <!-- Facebook -->
    <button
      @click="shareFacebook(article.url)"
      class="share-btn"
      title="Megosztás Facebook-on"
      aria-label="Facebook megosztás"
    >
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
      </svg>
    </button>

    <!-- Microsoft Teams -->
    <button
      @click="shareTeams(article.url, article.mednews_title)"
      class="share-btn teams-btn"
      title="Megosztás Microsoft Teams-ben"
      aria-label="Teams megosztás"
    >
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.625 7.313a3.188 3.188 0 100-6.376 3.188 3.188 0 000 6.376zm2.625 1.124H18v8.063c0 1.55-.7 2.938-1.8 3.874A6.75 6.75 0 0012 23.063c-3.727 0-6.75-3.023-6.75-6.75V8.437H.75v7.876C.75 20.695 5.054 25 12 25c3.45 0 6.567-1.29 8.916-3.4A6.726 6.726 0 0023.25 16.5V8.437h-.001zM12 1.313a3.937 3.937 0 100 7.874A3.937 3.937 0 0012 1.312zm-5.063 7.124H2.813v7.063a4.688 4.688 0 009.375 0V8.437H6.937z"/>
      </svg>
      <span class="text-xs ml-1 hidden sm:inline">Teams</span>
    </button>

    <!-- Copy link -->
    <button
      @click="handleCopy"
      class="share-btn"
      :title="copied ? 'Másolva!' : 'Link másolása'"
      :aria-label="copied ? 'Másolva!' : 'Link másolása'"
    >
      <svg v-if="!copied" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
        <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
      </svg>
      <svg v-else class="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useShare } from '../composables/useShare.js'

const props = defineProps({ article: { type: Object, required: true } })
const { shareLinkedIn, shareX, shareFacebook, shareTeams, copyLink } = useShare()
const copied = ref(false)

async function handleCopy() {
  await copyLink(props.article.url)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<style scoped>
.share-btn {
  @apply flex items-center justify-center p-2 rounded-card-sm text-text-muted
         hover:text-accent-teal hover:bg-accent-teal/10 transition-all duration-200
         border border-transparent hover:border-accent-teal/20;
}
.teams-btn {
  @apply text-[#6264a7] hover:text-[#6264a7] hover:bg-[#6264a7]/10 hover:border-[#6264a7]/20;
}
</style>
