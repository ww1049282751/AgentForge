<!-- 合成评审片段，故意包含缺陷；不是可直接运行的项目。 -->
<script setup lang="ts">
import { ref } from 'vue'
import { api } from './api'
const props = defineProps<{ id: string }>()
const status = ref('待审批')
async function approve() {
  status.value = '已批准'
  await api.approve(props.id)
}
</script>
<template>
  <div class="panel">
    <p>{{ status }}</p>
    <div class="approve" @click="approve">批准</div>
  </div>
</template>
<style scoped>
.panel { width: 520px; }
.approve { color: #888; cursor: pointer; }
</style>
