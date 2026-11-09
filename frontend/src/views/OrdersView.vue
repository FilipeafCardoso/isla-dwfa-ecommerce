<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api, ApiError, unwrap } from '@/api/client'
import { useFetch } from '@/composables/useFetch'
import OrderStatusBadge from '@/components/OrderStatusBadge.vue'

const route = useRoute()
const router = useRouter()

// Página no URL, como na lista de produtos
const page = computed(() => {
  const n = Number(route.query.page)
  return Number.isInteger(n) && n > 0 ? n : 1
})

function goTo(n: number) {
  router.push({ query: { ...route.query, page: n > 1 ? n : undefined } })
}

// A API já filtra as encomendas ao cliente autenticado
const { data, status, error, reload } = useFetch(() =>
  unwrap(
    api.GET('/api/v1/orders/', {
      params: { query: { page: page.value > 1 ? page.value : undefined } },
    }),
  ),
)

const dateFormat = new Intl.DateTimeFormat('pt-PT', { dateStyle: 'short', timeStyle: 'short' })

const paying = ref<number | null>(null)
const notice = ref<string | null>(null)

async function pay(id: number) {
  paying.value = id
  notice.value = null
  try {
    await unwrap(api.POST('/api/v1/orders/{id}/pay/', { params: { path: { id } } }))
    reload()
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      // Conflito de estado (ex.: já paga noutro separador): avisar e mostrar o estado real
      notice.value = 'Esta encomenda já não está pendente — a lista foi atualizada.'
      reload()
    } else {
      notice.value = e instanceof ApiError ? e.detail : 'Não foi possível contactar a API.'
    }
  } finally {
    paying.value = null
  }
}
</script>

<template>
  <section>
    <div class="title">
      <h1>As minhas encomendas</h1>
      <RouterLink :to="{ name: 'order-new' }">Nova encomenda</RouterLink>
    </div>

    <p v-if="notice" role="alert" class="notice">{{ notice }}</p>

    <p v-if="status === 'loading' && !data">A carregar…</p>
    <p v-else-if="status === 'error'" class="error">
      {{ error }} <button type="button" @click="reload">Tentar de novo</button>
    </p>
    <p v-else-if="data && data.count === 0">
      Ainda sem encomendas.
      <RouterLink :to="{ name: 'order-new' }">Fazer a primeira encomenda</RouterLink>
    </p>
    <template v-else-if="data">
      <article v-for="order in data.results" :key="order.id" class="order">
        <header>
          <strong>Encomenda #{{ order.id }}</strong>
          <span class="meta">{{ dateFormat.format(new Date(order.created_at)) }}</span>
          <OrderStatusBadge :status="order.status" />
        </header>
        <table>
          <tbody>
            <tr v-for="item in order.items" :key="item.id">
              <td>{{ item.product_name }}</td>
              <td class="num">× {{ item.quantity }}</td>
              <td class="num">{{ item.line_total }} €</td>
            </tr>
          </tbody>
        </table>
        <footer>
          <!-- Total calculado pela API (Decimal), mostrado tal como vem -->
          <strong>Total: {{ order.total }} €</strong>
          <button
            v-if="order.status === 'pending'"
            type="button"
            :disabled="paying !== null"
            @click="pay(order.id)"
          >
            {{ paying === order.id ? 'A pagar…' : 'Pagar' }}
          </button>
        </footer>
      </article>

      <nav v-if="data.previous || data.next" class="pager">
        <button type="button" :disabled="!data.previous" @click="goTo(page - 1)">‹ Anterior</button>
        <button type="button" :disabled="!data.next" @click="goTo(page + 1)">Seguinte ›</button>
      </nav>
    </template>
  </section>
</template>

<style scoped>
.title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.order {
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}
.order header,
.order footer {
  display: flex;
  gap: 1rem;
  align-items: center;
}
.order footer {
  justify-content: space-between;
  margin-top: 0.5rem;
}
table {
  width: 100%;
  margin-top: 0.5rem;
  border-collapse: collapse;
}
.num {
  text-align: right;
  white-space: nowrap;
}
.meta {
  opacity: 0.7;
}
.notice {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background: #fdebd0;
  color: #784212;
}
.error {
  color: #c0392b;
}
.pager {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
</style>
