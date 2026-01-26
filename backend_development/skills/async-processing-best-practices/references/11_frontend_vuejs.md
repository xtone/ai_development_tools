# Vue.js フロントエンド非同期処理実装ガイド

このドキュメントでは、Vue.js 3（Composition API）を使用したフロントエンドでの非同期処理実装のベストプラクティスを解説します。

## 目次

1. [非同期処理の呼び出し方](#非同期処理の呼び出し方)
2. [状態管理と表示](#状態管理と表示)
3. [WebSocket/SSE接続の復帰処理](#websocketsse接続の復帰処理)
4. [エラーハンドリング](#エラーハンドリング)
5. [実装例：ファイルインポート機能](#実装例ファイルインポート機能)
6. [リファレンス](#リファレンス)

## 非同期処理の呼び出し方

### Composableによる非同期処理の管理

```typescript
// composables/useAsyncTask.ts
import { ref, computed } from 'vue'

interface AsyncTaskState<T> {
  data: T | null
  isLoading: boolean
  isError: boolean
  error: Error | null
}

export function useAsyncTask<T, P extends unknown[]>(
  asyncFn: (...args: P) => Promise<T>
) {
  const data = ref<T | null>(null) as Ref<T | null>
  const isLoading = ref(false)
  const isError = ref(false)
  const error = ref<Error | null>(null)

  const execute = async (...args: P): Promise<T | null> => {
    isLoading.value = true
    isError.value = false
    error.value = null

    try {
      const result = await asyncFn(...args)
      data.value = result
      return result
    } catch (e) {
      isError.value = true
      error.value = e as Error
      return null
    } finally {
      isLoading.value = false
    }
  }

  const reset = () => {
    data.value = null
    isLoading.value = false
    isError.value = false
    error.value = null
  }

  return {
    data,
    isLoading,
    isError,
    error,
    execute,
    reset,
  }
}
```

### VueUseのuseAsyncStateを使用

```typescript
// composables/useImportTask.ts
import { useAsyncState } from '@vueuse/core'

interface ImportResult {
  taskId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message?: string
}

export function useStartImport() {
  const startImport = async (file: File): Promise<ImportResult> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/imports', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  const { state, isLoading, isReady, error, execute } = useAsyncState(
    (file: File) => startImport(file),
    null,
    {
      immediate: false,
      resetOnExecute: true,
    }
  )

  return {
    result: state,
    isLoading,
    isReady,
    error,
    startImport: execute,
  }
}
```

### フォームコンポーネントでの使用

```vue
<!-- components/ImportForm.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { useStartImport } from '@/composables/useImportTask'
import { useRouter } from 'vue-router'

const router = useRouter()
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)

const { result, isLoading, error, startImport } = useStartImport()

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  selectedFile.value = target.files?.[0] ?? null
}

const handleSubmit = async () => {
  if (!selectedFile.value) return

  await startImport(0, selectedFile.value)

  if (result.value?.taskId) {
    router.push(`/imports/${result.value.taskId}`)
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="import-form">
    <div class="form-group">
      <input
        ref="fileInput"
        type="file"
        accept=".csv"
        :disabled="isLoading"
        @change="handleFileChange"
      />
    </div>

    <button type="submit" :disabled="isLoading || !selectedFile">
      {{ isLoading ? 'アップロード中...' : 'インポート開始' }}
    </button>

    <p v-if="error" class="error">{{ error.message }}</p>
  </form>
</template>
```

### Axiosを使用したAPI呼び出し

```typescript
// api/imports.ts
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    // 認証トークンの追加など
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // グローバルエラーハンドリング
    if (error.response?.status === 401) {
      // 認証エラー処理
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const importApi = {
  start: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<ImportResult>('/imports', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getStatus: (taskId: string) => {
    return apiClient.get<ImportStatus>(`/imports/${taskId}`)
  },

  cancel: (taskId: string) => {
    return apiClient.post(`/imports/${taskId}/cancel`)
  },
}
```

## 状態管理と表示

### Piniaによる状態管理

```typescript
// stores/importStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { importApi } from '@/api/imports'

interface ImportTask {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  processedCount: number
  totalCount: number
  errorMessage?: string
}

export const useImportStore = defineStore('import', () => {
  const tasks = ref<Map<string, ImportTask>>(new Map())
  const activeTaskId = ref<string | null>(null)
  const isPolling = ref(false)
  const pollingInterval = ref<number | null>(null)

  // Getters
  const activeTask = computed(() => {
    if (!activeTaskId.value) return null
    return tasks.value.get(activeTaskId.value) ?? null
  })

  const isTaskCompleted = computed(() => {
    return activeTask.value?.status === 'completed' ||
           activeTask.value?.status === 'failed'
  })

  // Actions
  const updateTask = (taskId: string, updates: Partial<ImportTask>) => {
    const existing = tasks.value.get(taskId)
    if (existing) {
      tasks.value.set(taskId, { ...existing, ...updates })
    } else {
      tasks.value.set(taskId, updates as ImportTask)
    }
  }

  const fetchTaskStatus = async (taskId: string) => {
    try {
      const response = await importApi.getStatus(taskId)
      updateTask(taskId, response.data)
      return response.data
    } catch (error) {
      console.error('Failed to fetch task status:', error)
      throw error
    }
  }

  const startPolling = (taskId: string, interval = 2000) => {
    if (isPolling.value) return

    activeTaskId.value = taskId
    isPolling.value = true

    const poll = async () => {
      try {
        const status = await fetchTaskStatus(taskId)

        if (status.status === 'completed' || status.status === 'failed') {
          stopPolling()
        }
      } catch (error) {
        // エラー時は間隔を延長してリトライ
        interval = Math.min(interval * 2, 30000)
      }
    }

    poll() // 即座に1回実行
    pollingInterval.value = window.setInterval(poll, interval)
  }

  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
    isPolling.value = false
  }

  const cancelTask = async (taskId: string) => {
    try {
      await importApi.cancel(taskId)
      updateTask(taskId, { status: 'failed', errorMessage: 'キャンセルされました' })
    } catch (error) {
      console.error('Failed to cancel task:', error)
      throw error
    }
  }

  // Cleanup
  const $reset = () => {
    stopPolling()
    tasks.value.clear()
    activeTaskId.value = null
  }

  return {
    tasks,
    activeTaskId,
    activeTask,
    isTaskCompleted,
    isPolling,
    updateTask,
    fetchTaskStatus,
    startPolling,
    stopPolling,
    cancelTask,
    $reset,
  }
})
```

### 進捗表示コンポーネント

```vue
<!-- components/ImportProgress.vue -->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useImportStore } from '@/stores/importStore'
import { storeToRefs } from 'pinia'

const props = defineProps<{
  taskId: string
}>()

const importStore = useImportStore()
const { activeTask, isTaskCompleted, isPolling } = storeToRefs(importStore)

const progressStyle = computed(() => ({
  width: `${activeTask.value?.progress ?? 0}%`,
}))

const statusText = computed(() => {
  switch (activeTask.value?.status) {
    case 'pending':
      return '処理待機中...'
    case 'processing':
      return `処理中: ${activeTask.value.processedCount} / ${activeTask.value.totalCount} 件`
    case 'completed':
      return '完了しました！'
    case 'failed':
      return `エラー: ${activeTask.value.errorMessage}`
    default:
      return ''
  }
})

onMounted(() => {
  importStore.startPolling(props.taskId)
})

onUnmounted(() => {
  importStore.stopPolling()
})

// 完了時の処理
watch(isTaskCompleted, (completed) => {
  if (completed) {
    // 完了通知など
  }
})

const handleCancel = async () => {
  await importStore.cancelTask(props.taskId)
}
</script>

<template>
  <div class="import-progress">
    <div class="progress-bar">
      <div class="progress-fill" :style="progressStyle" />
    </div>

    <div class="progress-info">
      <span class="progress-text">{{ activeTask?.progress ?? 0 }}%</span>
      <span class="status-text">{{ statusText }}</span>
    </div>

    <button
      v-if="activeTask?.status === 'processing'"
      @click="handleCancel"
      class="cancel-button"
    >
      キャンセル
    </button>
  </div>
</template>
```

### VueQueryによるサーバー状態管理

```typescript
// composables/useImportQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { importApi } from '@/api/imports'
import { computed } from 'vue'

export function useImportStatus(taskId: string) {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['import', taskId],
    queryFn: () => importApi.getStatus(taskId).then((res) => res.data),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') {
        return false
      }
      return 2000
    },
    refetchIntervalInBackground: true,
  })

  const isCompleted = computed(() => {
    return query.data.value?.status === 'completed' ||
           query.data.value?.status === 'failed'
  })

  return {
    ...query,
    isCompleted,
  }
}

export function useCancelImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (taskId: string) => importApi.cancel(taskId),
    onMutate: async (taskId) => {
      await queryClient.cancelQueries({ queryKey: ['import', taskId] })

      const previousData = queryClient.getQueryData(['import', taskId])

      queryClient.setQueryData(['import', taskId], (old: any) => ({
        ...old,
        status: 'cancelling',
      }))

      return { previousData }
    },
    onError: (err, taskId, context) => {
      queryClient.setQueryData(['import', taskId], context?.previousData)
    },
    onSettled: (data, error, taskId) => {
      queryClient.invalidateQueries({ queryKey: ['import', taskId] })
    },
  })
}
```

## WebSocket/SSE接続の復帰処理

### VueUseのuseWebSocketを使用

```typescript
// composables/useRealtimeUpdates.ts
import { useWebSocket, useEventSource } from '@vueuse/core'
import { watch, ref, onUnmounted } from 'vue'
import { useImportStore } from '@/stores/importStore'

interface ImportUpdate {
  taskId: string
  status: string
  progress: number
  processedCount: number
  totalCount: number
  errorMessage?: string
}

export function useRealtimeImportUpdates(taskId: string) {
  const importStore = useImportStore()
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 10

  const { status, data, close, open } = useWebSocket(
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/imports/${taskId}`,
    {
      autoReconnect: {
        retries: maxReconnectAttempts,
        delay: 1000,
        onFailed() {
          console.error('WebSocket reconnection failed after max retries')
        },
      },
      heartbeat: {
        message: JSON.stringify({ type: 'ping' }),
        interval: 30000,
        pongTimeout: 5000,
      },
      onConnected() {
        console.log('WebSocket connected')
        reconnectAttempts.value = 0
      },
      onDisconnected(ws, event) {
        console.log('WebSocket disconnected:', event.code, event.reason)
        reconnectAttempts.value++
      },
      onError(ws, event) {
        console.error('WebSocket error:', event)
      },
    }
  )

  // メッセージ受信時にストアを更新
  watch(data, (newData) => {
    if (!newData) return

    try {
      const update = JSON.parse(newData) as ImportUpdate
      if (update.type === 'pong') return

      importStore.updateTask(update.taskId, update)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  })

  const isConnected = computed(() => status.value === 'OPEN')
  const isReconnecting = computed(() =>
    status.value === 'CONNECTING' && reconnectAttempts.value > 0
  )

  onUnmounted(() => {
    close()
  })

  return {
    status,
    isConnected,
    isReconnecting,
    reconnectAttempts,
    connect: open,
    disconnect: close,
  }
}
```

### SSE用Composable

```typescript
// composables/useSSE.ts
import { useEventSource } from '@vueuse/core'
import { watch, computed, ref } from 'vue'

interface UseSSEOptions<T> {
  url: string
  onMessage: (data: T) => void
  onError?: (error: Event) => void
}

export function useSSE<T>({ url, onMessage, onError }: UseSSEOptions<T>) {
  const reconnectAttempts = ref(0)

  const { status, data, error, close, eventSource } = useEventSource(url, [], {
    autoReconnect: {
      retries: 10,
      delay: 1000,
      onFailed() {
        console.error('SSE reconnection failed')
        onError?.(new Event('max-retries-exceeded'))
      },
    },
  })

  watch(data, (newData) => {
    if (!newData) return

    try {
      const parsed = JSON.parse(newData) as T
      onMessage(parsed)
    } catch (e) {
      console.error('Failed to parse SSE data:', e)
    }
  })

  watch(error, (newError) => {
    if (newError) {
      console.error('SSE error:', newError)
      reconnectAttempts.value++
      onError?.(new Event('sse-error'))
    }
  })

  watch(status, (newStatus) => {
    if (newStatus === 'OPEN') {
      reconnectAttempts.value = 0
    }
  })

  const isConnected = computed(() => status.value === 'OPEN')
  const isReconnecting = computed(() =>
    status.value === 'CONNECTING' && reconnectAttempts.value > 0
  )

  return {
    status,
    isConnected,
    isReconnecting,
    reconnectAttempts,
    close,
  }
}
```

### Visibility APIとの連携

```typescript
// composables/useVisibilityAwareRefresh.ts
import { useDocumentVisibility } from '@vueuse/core'
import { watch } from 'vue'

interface UseVisibilityAwareRefreshOptions {
  onVisible: () => void
  onHidden?: () => void
}

export function useVisibilityAwareRefresh({
  onVisible,
  onHidden,
}: UseVisibilityAwareRefreshOptions) {
  const visibility = useDocumentVisibility()

  watch(visibility, (newVisibility, oldVisibility) => {
    if (newVisibility === 'visible' && oldVisibility === 'hidden') {
      onVisible()
    } else if (newVisibility === 'hidden' && oldVisibility === 'visible') {
      onHidden?.()
    }
  })

  return { visibility }
}
```

### 接続状態管理ストア

```typescript
// stores/connectionStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useOnline } from '@vueuse/core'

export const useConnectionStore = defineStore('connection', () => {
  const isOnline = useOnline()
  const isWebSocketConnected = ref(false)
  const lastSyncTime = ref<Date | null>(null)
  const reconnectAttempts = ref(0)

  const connectionStatus = computed(() => {
    if (!isOnline.value) return 'offline'
    if (!isWebSocketConnected.value) return 'disconnected'
    return 'connected'
  })

  const setWebSocketConnected = (connected: boolean) => {
    isWebSocketConnected.value = connected
    if (connected) {
      reconnectAttempts.value = 0
      lastSyncTime.value = new Date()
    }
  }

  const incrementReconnectAttempts = () => {
    reconnectAttempts.value++
  }

  const updateLastSyncTime = () => {
    lastSyncTime.value = new Date()
  }

  return {
    isOnline,
    isWebSocketConnected,
    lastSyncTime,
    reconnectAttempts,
    connectionStatus,
    setWebSocketConnected,
    incrementReconnectAttempts,
    updateLastSyncTime,
  }
})
```

### 接続状態表示コンポーネント

```vue
<!-- components/ConnectionStatus.vue -->
<script setup lang="ts">
import { useConnectionStore } from '@/stores/connectionStore'
import { storeToRefs } from 'pinia'

const connectionStore = useConnectionStore()
const { connectionStatus, reconnectAttempts, lastSyncTime } = storeToRefs(connectionStore)

const statusConfig = {
  connected: { text: '接続中', class: 'status-connected' },
  disconnected: { text: '再接続中...', class: 'status-reconnecting' },
  offline: { text: 'オフライン', class: 'status-offline' },
}
</script>

<template>
  <div
    class="connection-status"
    :class="statusConfig[connectionStatus].class"
  >
    <span class="status-indicator" />
    <span class="status-text">{{ statusConfig[connectionStatus].text }}</span>
    <span v-if="reconnectAttempts > 0" class="reconnect-count">
      ({{ reconnectAttempts }}回目)
    </span>
  </div>
</template>

<style scoped>
.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-connected .status-indicator {
  background-color: #22c55e;
}

.status-reconnecting .status-indicator {
  background-color: #f59e0b;
  animation: pulse 1s infinite;
}

.status-offline .status-indicator {
  background-color: #ef4444;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
```

## エラーハンドリング

### グローバルエラーハンドラー

```typescript
// plugins/errorHandler.ts
import type { App } from 'vue'
import { useToast } from '@/composables/useToast'

export function setupErrorHandler(app: App) {
  const { showError } = useToast()

  // Vue コンポーネント内のエラー
  app.config.errorHandler = (err, instance, info) => {
    console.error('Vue error:', err, info)

    // 開発環境では詳細表示
    if (import.meta.env.DEV) {
      console.error('Component:', instance)
    }

    showError('予期しないエラーが発生しました')

    // エラートラッキングサービスに送信
    // Sentry.captureException(err)
  }

  // Promiseの未処理エラー
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason)

    // ネットワークエラーの場合
    if (event.reason?.message?.includes('fetch')) {
      showError('通信エラーが発生しました')
    } else {
      showError('予期しないエラーが発生しました')
    }
  })

  // ネットワーク状態の監視
  window.addEventListener('offline', () => {
    showError('インターネット接続が切断されました', { duration: 0 })
  })

  window.addEventListener('online', () => {
    showError('インターネット接続が復帰しました', { type: 'success' })
  })
}
```

### Error Boundary コンポーネント

```vue
<!-- components/ErrorBoundary.vue -->
<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'

const props = withDefaults(defineProps<{
  fallback?: string
}>(), {
  fallback: 'エラーが発生しました',
})

const emit = defineEmits<{
  error: [error: Error, info: string]
}>()

const error = ref<Error | null>(null)
const errorInfo = ref<string>('')

onErrorCaptured((err, instance, info) => {
  error.value = err
  errorInfo.value = info
  emit('error', err, info)

  // エラーの伝播を停止
  return false
})

const reset = () => {
  error.value = null
  errorInfo.value = ''
}
</script>

<template>
  <slot v-if="!error" />
  <div v-else class="error-boundary">
    <slot name="error" :error="error" :reset="reset">
      <div class="error-content">
        <p>{{ fallback }}</p>
        <button @click="reset">再試行</button>
      </div>
    </slot>
  </div>
</template>
```

### 使用例

```vue
<!-- pages/ImportPage.vue -->
<script setup lang="ts">
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import ImportProgress from '@/components/ImportProgress.vue'

const handleError = (error: Error, info: string) => {
  console.error('Caught error:', error, info)
  // エラーログ送信など
}
</script>

<template>
  <ErrorBoundary @error="handleError">
    <ImportProgress :task-id="taskId" />

    <template #error="{ error, reset }">
      <div class="error-state">
        <h3>エラーが発生しました</h3>
        <p>{{ error.message }}</p>
        <button @click="reset">再試行</button>
      </div>
    </template>
  </ErrorBoundary>
</template>
```

### Piniaでのエラーハンドリング

```typescript
// stores/importStore.ts (エラーハンドリング部分)
import { defineStore } from 'pinia'
import { useToast } from '@/composables/useToast'

export const useImportStore = defineStore('import', () => {
  const { showError } = useToast()
  const lastError = ref<Error | null>(null)

  // アクションにエラーハンドリングを追加
  const fetchTaskStatus = async (taskId: string) => {
    try {
      const response = await importApi.getStatus(taskId)
      lastError.value = null
      return response.data
    } catch (error) {
      lastError.value = error as Error

      if (axios.isAxiosError(error)) {
        if (error.response?.status === 404) {
          showError('タスクが見つかりません')
        } else if (error.response?.status === 500) {
          showError('サーバーエラーが発生しました')
        } else if (error.code === 'NETWORK_ERROR') {
          showError('ネットワークエラーが発生しました')
        }
      }

      throw error
    }
  }

  // グローバルなアクションエラー監視
  // main.tsで設定
  return {
    lastError,
    fetchTaskStatus,
    // ...
  }
})

// main.ts
const pinia = createPinia()

pinia.use(({ store }) => {
  store.$onAction(({ name, store, args, after, onError }) => {
    onError((error) => {
      console.error(`Action ${name} in store ${store.$id} failed:`, error)
      // グローバルエラートラッキング
    })
  })
})
```

### リトライ機能付きComposable

```typescript
// composables/useRetry.ts
import { ref } from 'vue'

interface UseRetryOptions {
  maxRetries?: number
  retryDelay?: number
  backoffMultiplier?: number
}

export function useRetry<T>(
  fn: () => Promise<T>,
  options: UseRetryOptions = {}
) {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    backoffMultiplier = 2,
  } = options

  const attempts = ref(0)
  const isRetrying = ref(false)
  const lastError = ref<Error | null>(null)

  const execute = async (): Promise<T> => {
    attempts.value = 0
    lastError.value = null

    while (attempts.value <= maxRetries) {
      try {
        isRetrying.value = attempts.value > 0
        const result = await fn()
        isRetrying.value = false
        return result
      } catch (error) {
        lastError.value = error as Error
        attempts.value++

        if (attempts.value > maxRetries) {
          isRetrying.value = false
          throw error
        }

        const delay = retryDelay * Math.pow(backoffMultiplier, attempts.value - 1)
        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    }

    throw lastError.value
  }

  return {
    execute,
    attempts,
    isRetrying,
    lastError,
  }
}
```

### フォームバリデーションエラー

```vue
<!-- components/ImportForm.vue (バリデーション部分) -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useVuelidate } from '@vuelidate/core'
import { required, helpers } from '@vuelidate/validators'

const file = ref<File | null>(null)

const rules = {
  file: {
    required: helpers.withMessage('ファイルを選択してください', required),
    maxSize: helpers.withMessage(
      'ファイルサイズは10MB以下にしてください',
      (value: File | null) => !value || value.size <= 10 * 1024 * 1024
    ),
    fileType: helpers.withMessage(
      'CSVファイルを選択してください',
      (value: File | null) => !value || value.type === 'text/csv' || value.name.endsWith('.csv')
    ),
  },
}

const v$ = useVuelidate(rules, { file })

const handleSubmit = async () => {
  const isValid = await v$.value.$validate()
  if (!isValid) return

  // 送信処理
}

const errors = computed(() => {
  return v$.value.file.$errors.map((e) => e.$message)
})
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div class="form-group" :class="{ 'has-error': v$.file.$error }">
      <input
        type="file"
        accept=".csv"
        @change="(e) => file = (e.target as HTMLInputElement).files?.[0] ?? null"
      />
      <ul v-if="errors.length" class="error-list">
        <li v-for="error in errors" :key="error">{{ error }}</li>
      </ul>
    </div>

    <button type="submit" :disabled="v$.$invalid">
      インポート開始
    </button>
  </form>
</template>
```

## 実装例：ファイルインポート機能

### 完全な実装例

```vue
<!-- pages/imports/[id].vue -->
<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useImportStore } from '@/stores/importStore'
import { useConnectionStore } from '@/stores/connectionStore'
import { useRealtimeImportUpdates } from '@/composables/useRealtimeUpdates'
import { useVisibilityAwareRefresh } from '@/composables/useVisibilityAwareRefresh'
import { storeToRefs } from 'pinia'

import ErrorBoundary from '@/components/ErrorBoundary.vue'
import ImportProgress from '@/components/ImportProgress.vue'
import ConnectionStatus from '@/components/ConnectionStatus.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id as string

const importStore = useImportStore()
const connectionStore = useConnectionStore()

const { activeTask, isTaskCompleted } = storeToRefs(importStore)
const { connectionStatus } = storeToRefs(connectionStore)

// WebSocket接続
const { isConnected, isReconnecting, connect } = useRealtimeImportUpdates(taskId)

// 接続状態をストアに反映
watch(isConnected, (connected) => {
  connectionStore.setWebSocketConnected(connected)
})

// ページ表示時に最新状態を取得
useVisibilityAwareRefresh({
  onVisible: () => {
    importStore.fetchTaskStatus(taskId)
  },
})

// 完了時の処理
watch(isTaskCompleted, (completed) => {
  if (completed && activeTask.value?.status === 'completed') {
    // 成功通知
    router.push('/imports')
  }
})

onMounted(() => {
  importStore.fetchTaskStatus(taskId)
})

onUnmounted(() => {
  importStore.stopPolling()
})

const handleCancel = async () => {
  await importStore.cancelTask(taskId)
}

const handleRetry = () => {
  connect()
  importStore.fetchTaskStatus(taskId)
}
</script>

<template>
  <div class="import-detail-page">
    <header>
      <h1>インポート詳細</h1>
      <ConnectionStatus />
    </header>

    <ErrorBoundary @error="console.error">
      <template #default>
        <div v-if="activeTask" class="import-content">
          <ImportProgress :task-id="taskId" />

          <div class="actions">
            <button
              v-if="activeTask.status === 'processing'"
              @click="handleCancel"
              class="btn-cancel"
            >
              キャンセル
            </button>

            <router-link
              v-if="isTaskCompleted"
              to="/imports"
              class="btn-back"
            >
              一覧に戻る
            </router-link>
          </div>
        </div>

        <div v-else class="loading">
          読み込み中...
        </div>
      </template>

      <template #error="{ error, reset }">
        <div class="error-state">
          <h2>エラーが発生しました</h2>
          <p>{{ error.message }}</p>
          <button @click="reset">再試行</button>
        </div>
      </template>
    </ErrorBoundary>
  </div>
</template>

<style scoped>
.import-detail-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.actions {
  margin-top: 24px;
  display: flex;
  gap: 16px;
}

.loading {
  text-align: center;
  padding: 48px;
  color: #666;
}

.error-state {
  text-align: center;
  padding: 48px;
  background: #fef2f2;
  border-radius: 8px;
}
</style>
```

## リファレンス

### 公式ドキュメント

- [Vue.js 3 Documentation](https://vuejs.org/)
- [Vue.js Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vue Router Documentation](https://router.vuejs.org/)

### VueUse

- [VueUse Documentation](https://vueuse.org/)
- [useWebSocket](https://vueuse.org/core/useWebSocket/)
- [useEventSource](https://vueuse.org/core/useEventSource/)
- [useAsyncState](https://vueuse.org/core/useAsyncState/)
- [useDocumentVisibility](https://vueuse.org/core/useDocumentVisibility/)
- [useOnline](https://vueuse.org/core/useOnline/)

### TanStack Query (Vue Query)

- [TanStack Query Vue Documentation](https://tanstack.com/query/latest/docs/vue/overview)
- [Queries](https://tanstack.com/query/latest/docs/vue/guides/queries)
- [Mutations](https://tanstack.com/query/latest/docs/vue/guides/mutations)

### バリデーション

- [Vuelidate](https://vuelidate-next.netlify.app/)
- [VeeValidate](https://vee-validate.logaretm.com/v4/)

### エラーハンドリング

- [Vue Error Handling](https://vuejs.org/api/application.html#app-config-errorhandler)
- [onErrorCaptured](https://vuejs.org/api/composition-api-lifecycle.html#onerrorcaptured)
