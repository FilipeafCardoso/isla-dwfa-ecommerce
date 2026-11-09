/// <reference types="vite/client" />

// Variáveis VITE_* tipadas (sem isto, import.meta.env.VITE_API_URL é `any`)
interface ImportMetaEnv {
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
