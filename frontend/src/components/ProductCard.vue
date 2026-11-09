<script setup lang="ts">
import type { Product } from '@/types'

defineProps<{ product: Product }>()
const emit = defineEmits<{ select: [id: number] }>()
</script>

<template>
  <button type="button" class="card" @click="emit('select', product.id)">
    <h2>{{ product.name }}</h2>
    <p class="meta">{{ product.sku }} · {{ product.category_name }}</p>
    <p class="price">{{ product.price }} €</p>
  </button>
</template>

<style scoped>
.card {
  display: block;
  width: 100%;
  text-align: left;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}
.card:hover {
  border-color: #42b883;
}
.card h2 {
  font-size: 1.05rem;
  margin: 0 0 0.25rem;
}
.meta {
  font-size: 0.85rem;
  opacity: 0.7;
}
.price {
  font-weight: bold;
  margin-top: 0.5rem;
}
</style>
