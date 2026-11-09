<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, unwrap } from '@/api/client'
import { useFetch } from '@/composables/useFetch'
import ProductCard from '@/components/ProductCard.vue'

const route = useRoute()
const router = useRouter()

// O estado da lista vive no URL: recarregar, voltar atrás ou partilhar o link mantém-no
const search = computed({
  get: () => (typeof route.query.search === 'string' ? route.query.search : ''),
  set: (value: string) =>
    router.push({ query: { ...route.query, search: value || undefined, page: undefined } }),
})

const page = computed(() => {
  const n = Number(route.query.page)
  return Number.isInteger(n) && n > 0 ? n : 1
})

function goTo(n: number) {
  router.push({ query: { ...route.query, page: n > 1 ? n : undefined } })
}

const { data, status, error, reload } = useFetch(() =>
  unwrap(
    api.GET('/api/v1/products/', {
      params: {
        query: {
          search: search.value || undefined,
          page: page.value > 1 ? page.value : undefined,
        },
      },
    }),
  ),
)

function open(id: number) {
  router.push({ name: 'product', params: { id } })
}
</script>

<template>
  <section>
    <input
      v-model.lazy="search"
      type="search"
      placeholder="Pesquisar por nome ou SKU…"
      aria-label="Pesquisar produtos"
    />

    <p v-if="status === 'loading'">A carregar…</p>
    <p v-else-if="status === 'error'" class="error">
      {{ error }} <button type="button" @click="reload">Tentar de novo</button>
    </p>
    <template v-else-if="data">
      <p>{{ data.count }} produtos · página {{ page }}</p>
      <div class="grid">
        <ProductCard v-for="p in data.results" :key="p.id" :product="p" @select="open" />
      </div>
      <nav class="pager">
        <button type="button" :disabled="!data.previous" @click="goTo(page - 1)">‹ Anterior</button>
        <button type="button" :disabled="!data.next" @click="goTo(page + 1)">Seguinte ›</button>
      </nav>
    </template>
  </section>
</template>

<style scoped>
input[type='search'] {
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 1rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}
.pager {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
}
.error {
  color: #c0392b;
}
</style>
