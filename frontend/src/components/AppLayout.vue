<template>
  <el-container class="app-layout">
    <el-aside width="240px" class="app-aside">
      <div class="brand">
        <div class="brand-title">USB 线缆射频测试</div>
        <div class="brand-sub">RF Cable Test</div>
      </div>
      <el-menu :default-active="active" router class="app-menu">
        <el-menu-item index="/detection">单次检测</el-menu-item>
        <el-menu-item index="/batch">批量检测</el-menu-item>
        <el-menu-item index="/agent">AI 助手</el-menu-item>
        <el-menu-item index="/history">历史记录</el-menu-item>
        <el-menu-item index="/thresholds">阈值标准</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header" height="52px">
        <span class="page-title">{{ title }}</span>
        <el-tag size="small" :type="backendOk ? 'success' : 'danger'">
          {{ backendOk ? '后端在线' : '后端离线' }}
        </el-tag>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => String(route.meta.title ?? ''))
const active = computed(() => route.path)
const backendOk = ref(true)

async function ping(): Promise<void> {
  try {
    const resp = await fetch('/api/health')
    backendOk.value = resp.ok
  } catch {
    backendOk.value = false
  }
}

let timer: number | undefined
onMounted(() => {
  ping()
  timer = window.setInterval(ping, 15_000)
})
onUnmounted(() => window.clearInterval(timer))
</script>

<style scoped>
.app-layout {
  height: 100%;
}
.app-aside {
  background: #001529;
}
.brand {
  padding: 18px 16px;
  color: #fff;
}
.brand-title {
  font-size: 24px;
  font-weight: 600;
  white-space: nowrap;
}
.brand-sub {
  font-size: 18px;
  opacity: 0.6;
  letter-spacing: 0.5px;
  margin-top: 2px;
}
.app-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: rgba(255, 255, 255, 0.72);
  --el-menu-active-color: #fff;
  --el-menu-hover-bg-color: rgba(255, 255, 255, 0.08);
  --el-menu-item-height: 46px;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.page-title {
  font-size: 26px;
  font-weight: 600;
}
.app-main {
  padding: 20px;
  overflow: auto;
}
</style>
