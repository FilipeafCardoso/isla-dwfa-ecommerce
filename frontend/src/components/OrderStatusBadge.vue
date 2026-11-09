<script setup lang="ts">
import { computed } from 'vue'
import type { OrderStatus } from '@/types'

const props = defineProps<{ status: OrderStatus }>()

const label = computed((): string => {
  switch (props.status) {
    case 'pending':
      return 'Pendente'
    case 'paid':
      return 'Paga'
    case 'cancelled':
      return 'Cancelada'
  }
  // Sem default: um estado novo no enum da API deixa de compilar
  return props.status satisfies never
})
</script>

<template>
  <span class="badge" :class="props.status">{{ label }}</span>
</template>

<style scoped>
.badge {
  display: inline-block;
  padding: 0.1rem 0.6rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: bold;
  color: #fff;
}
.pending {
  background: #b9770e;
}
.paid {
  background: #1e8449;
}
.cancelled {
  background: #7f8c8d;
}
</style>
