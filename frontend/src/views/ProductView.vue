<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { api, unwrap } from '@/api/client'
import { useFetch } from '@/composables/useFetch'

// true na rota -> o :id do URL chega aqui como prop (sempre string)
const props = defineProps<{ id: string }>()

// props.id lido de forma síncrona dentro do fetcher: o watchEffect segue-o
const {
  data: product,
  status,
  error,
} = useFetch(() =>
  unwrap(api.GET('/api/v1/products/{id}/', { params: { path: { id: Number(props.id) } } })),
)

// JSONField sai como `unknown` no schema: só se mostra se for um objeto
const attributes = computed((): Record<string, unknown> => {
  const value: unknown = product.value?.attributes
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? Object.fromEntries(Object.entries(value))
    : {}
})
</script>

<template>
  <section>
    <RouterLink :to="{ name: 'products' }">‹ Todos os produtos</RouterLink>

    <p v-if="status === 'loading'">A carregar…</p>
    <p v-else-if="status === 'error'" class="error">{{ error }}</p>
    <article v-else-if="product">
      <h1>{{ product.name }}</h1>
      <p class="meta">{{ product.sku }} · {{ product.category_name }}</p>
      <p class="price">{{ product.price }} €</p>
      <p>Stock: {{ product.stock }}</p>

      <dl v-if="Object.keys(attributes).length">
        <template v-for="(value, key) in attributes" :key="key">
          <dt>{{ key }}</dt>
          <dd>{{ value }}</dd>
        </template>
      </dl>
      <p v-else class="meta">Sem atributos.</p>
    </article>
  </section>
</template>

<style scoped>
.meta {
  opacity: 0.7;
}
.price {
  font-size: 1.3rem;
  font-weight: bold;
}
.error {
  color: #c0392b;
}
dl {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.25rem 1rem;
  margin-top: 1rem;
}
dt {
  font-weight: bold;
}
</style>