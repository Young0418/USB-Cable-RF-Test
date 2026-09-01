<template>
  <div>
    <el-alert
      v-if="store.error"
      :title="store.error"
      type="error"
      show-icon
      :closable="false"
      class="mb"
    />
    <AgentChat />
  </div>
</template>

<script setup lang="ts">
import AgentChat from '@/components/AgentChat.vue'
import { useAiStore } from '@/stores/aiStore'

const store = useAiStore()
</script>

<style scoped>
.mb {
  margin-bottom: 12px;
}
</style>
