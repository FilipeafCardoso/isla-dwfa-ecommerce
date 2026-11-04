<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <section>
    <h1>Página não encontrada</h1>
    <p>O endereço não corresponde a nenhuma página.</p>
    <RouterLink :to="{ name: 'products' }">Ir para os produtos</RouterLink>
  </section>
</template>