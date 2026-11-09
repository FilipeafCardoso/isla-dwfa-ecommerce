<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, ApiError, unwrap } from '@/api/client'
import { useFetch } from '@/composables/useFetch'
import type { Product } from '@/types'

const router = useRouter()

// Catálogo completo para o <select>: segue as páginas até ao fim (página = 20, seed = 40)
const {
  data: products,
  status,
  error,
  reload,
} = useFetch(async () => {
  const all: Product[] = []
  for (let page = 1; ; page++) {
    const res = await unwrap(
      api.GET('/api/v1/products/', { params: { query: { is_active: true, page } } }),
    )
    all.push(...res.results)
    if (!res.next) return all
  }
})

interface Line {
  product: number | null
  quantity: number
  error: string | null
  done: boolean // já aceite pela API (201): não se volta a enviar
}

const newLine = (): Line => ({ product: null, quantity: 1, error: null, done: false })
const lines = ref<Line[]>([newLine()])

function addLine() {
  lines.value.push(newLine())
}

function removeLine(index: number) {
  if (lines.value.length > 1) lines.value.splice(index, 1)
}

/** "12.34" → 1234: soma em cêntimos inteiros, sem erros de vírgula flutuante. */
function toCents(price: string): number {
  const [int = '0', frac = ''] = price.split('.')
  return Number(int) * 100 + Number(frac.padEnd(2, '0').slice(0, 2))
}

const euros = new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' })

// Só para mostrar: o total que conta é o da API (Decimal no servidor)
const estimate = computed(() => {
  const byId = new Map((products.value ?? []).map((p) => [p.id, p]))
  let cents = 0
  for (const line of lines.value) {
    const product = line.product === null ? undefined : byId.get(line.product)
    if (product && line.quantity > 0) cents += toCents(product.price) * line.quantity
  }
  return euros.format(cents / 100)
})

const submitting = ref(false)
const formError = ref<string | null>(null)
// A encomenda é criada só uma vez; ao corrigir uma linha, reaproveita-se
const orderId = ref<number | null>(null)

async function submit() {
  submitting.value = true
  formError.value = null
  for (const line of lines.value) line.error = null
  try {
    if (orderId.value === null) {
      // customer vem do token; status começa em pending
      orderId.value = (await unwrap(api.POST('/api/v1/orders/'))).id
    }
    const order = orderId.value
    for (const line of lines.value) {
      if (line.done || line.product === null) continue
      try {
        await unwrap(
          api.POST('/api/v1/order-items/', {
            body: { order, product: line.product, quantity: line.quantity },
          }),
        )
        line.done = true
      } catch (e) {
        if (e instanceof ApiError && e.status === 400) {
          line.error = e.field('quantity') ?? e.field('product') ?? e.detail
        } else {
          throw e
        }
      }
    }
    if (lines.value.every((line) => line.done)) {
      await router.push({ name: 'orders' })
    }
  } catch (e) {
    formError.value = e instanceof ApiError ? e.detail : 'Não foi possível contactar a API.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section>
    <h1>Nova encomenda</h1>

    <p v-if="status === 'loading'">A carregar produtos…</p>
    <p v-else-if="status === 'error'" class="error">
      {{ error }} <button type="button" @click="reload">Tentar de novo</button>
    </p>
    <form v-else-if="products" @submit.prevent="submit">
      <p v-if="formError" role="alert" class="error">{{ formError }}</p>

      <fieldset
        v-for="(line, index) in lines"
        :key="index"
        class="line"
        :class="{ invalid: line.error }"
        :disabled="line.done"
      >
        <label :for="`product-${index}`">Produto</label>
        <select :id="`product-${index}`" v-model="line.product" required>
          <option :value="null" disabled>Escolha um produto…</option>
          <option v-for="p in products" :key="p.id" :value="p.id">
            {{ p.name }} — {{ p.price }} €
          </option>
        </select>

        <label :for="`quantity-${index}`">Quantidade</label>
        <input
          :id="`quantity-${index}`"
          v-model.number="line.quantity"
          type="number"
          min="1"
          required
        />

        <span v-if="line.done" class="ok">✓ Adicionada</span>
        <button v-else type="button" :disabled="lines.length === 1" @click="removeLine(index)">
          Remover
        </button>

        <p v-if="line.error" class="field-error">{{ line.error }}</p>
      </fieldset>

      <button type="button" @click="addLine">Acrescentar linha</button>

      <p class="total">Total (estimativa): {{ estimate }}</p>

      <button type="submit" :disabled="submitting">
        {{ submitting ? 'A enviar…' : 'Encomendar' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
form {
  display: grid;
  gap: 0.75rem;
  justify-items: start;
}
.line {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 0.75rem;
}
.line select {
  flex: 1;
  min-width: 12rem;
}
.line input {
  width: 5rem;
}
.invalid {
  border-color: #c0392b;
}
.field-error {
  flex-basis: 100%;
  margin: 0;
  color: #c0392b;
}
.ok {
  color: #1e8449;
}
.total {
  font-weight: bold;
}
.error {
  color: #c0392b;
}
</style>
