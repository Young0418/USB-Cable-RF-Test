<template>
  <el-config-provider>
    <AppLayout />
  </el-config-provider>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}
body {
  background: #f5f7fa;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}
</style>
