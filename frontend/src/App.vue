<template>
  <el-config-provider>
    <AppLayout />
  </el-config-provider>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
</script>

<style>
/* 全局字号：原字号的 1.6 倍（此前放大一倍，现改为其 0.8），如需回退直接改这里 */
:root {
  --el-font-size-extra-large: 32px;
  --el-font-size-large: 29px;
  --el-font-size-medium: 26px;
  --el-font-size-base: 22px;
  --el-font-size-small: 21px;
  --el-font-size-extra-small: 19px;
}
html,
body,
#app {
  height: 100%;
  margin: 0;
}
body {
  background: #f5f7fa;
  font-size: 22px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}
</style>
