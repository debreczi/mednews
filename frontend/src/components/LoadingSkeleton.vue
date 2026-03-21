<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
    <div
      v-for="n in count"
      :key="n"
      class="bg-bg-card rounded-card p-0 overflow-hidden shadow animate-pulse"
    >
      <div class="h-48 bg-gray-200"></div>
      <div class="p-5 space-y-3">
        <div class="h-3 bg-gray-200 rounded w-1/3"></div>
        <div class="h-5 bg-gray-200 rounded w-full"></div>
        <div class="h-5 bg-gray-200 rounded w-4/5"></div>
        <div class="space-y-2 pt-1">
          <div class="h-3 bg-gray-200 rounded"></div>
          <div class="h-3 bg-gray-200 rounded w-5/6"></div>
          <div class="h-3 bg-gray-200 rounded w-4/6"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ count: { type: Number, default: 6 } })
</script>
