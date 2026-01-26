# Next.js フロントエンド非同期処理実装ガイド

このドキュメントでは、Next.js（App Router / React）を使用したフロントエンドでの非同期処理実装のベストプラクティスを解説します。

> **対応バージョン**: このドキュメントは **Next.js 15 / React 19** を対象としています。Next.js 15では`params`が`Promise`型に変更されるなど、破壊的変更があります。

## 目次

1. [非同期処理の呼び出し方](#非同期処理の呼び出し方)
2. [状態管理と表示](#状態管理と表示)
3. [WebSocket/SSE接続の復帰処理](#websocketsse接続の復帰処理)
4. [エラーハンドリング](#エラーハンドリング)
5. [実装例：ファイルインポート機能](#実装例ファイルインポート機能)
6. [リファレンス](#リファレンス)

## 非同期処理の呼び出し方

### Server Actionsによる非同期処理の開始

Next.js 14以降では、Server Actionsを使用して非同期処理を開始できます。

```typescript
// app/actions/import.ts
'use server'

import { revalidatePath } from 'next/cache'

export interface ImportResult {
  taskId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message?: string
}

// useActionStateと組み合わせる場合、第1引数にprevStateが必要
export async function startImport(
  prevState: ImportResult,
  formData: FormData
): Promise<ImportResult> {
  const file = formData.get('file') as File

  if (!file || file.size === 0) {
    return { taskId: '', status: 'failed', message: 'ファイルを選択してください' }
  }

  try {
    // バックエンドAPIを呼び出してジョブを開始
    const response = await fetch(`${process.env.API_URL}/imports`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()

    revalidatePath('/imports')

    return {
      taskId: result.id,
      status: 'pending',
    }
  } catch (error) {
    console.error('Import failed:', error)
    return {
      taskId: '',
      status: 'failed',
      message: 'インポートの開始に失敗しました',
    }
  }
}
```

### useActionStateを使用したフォーム送信

```typescript
// app/imports/new/page.tsx
'use client'

import { useActionState } from 'react'
import { startImport, type ImportResult } from '@/app/actions/import'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

const initialState: ImportResult = {
  taskId: '',
  status: 'pending',
}

export default function ImportPage() {
  const [state, formAction, isPending] = useActionState(startImport, initialState)
  const router = useRouter()

  useEffect(() => {
    if (state.taskId) {
      // タスクが開始されたら進捗ページにリダイレクト
      router.push(`/imports/${state.taskId}`)
    }
  }, [state.taskId, router])

  return (
    <form action={formAction}>
      <input
        type="file"
        name="file"
        accept=".csv"
        disabled={isPending}
      />

      <button type="submit" disabled={isPending}>
        {isPending ? 'アップロード中...' : 'インポート開始'}
      </button>

      {state.status === 'failed' && (
        <p className="error">{state.message}</p>
      )}
    </form>
  )
}
```

### Route Handlersを使用したAPI呼び出し

```typescript
// app/api/imports/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'

// Next.js 15: params は Promise 型
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  try {
    const response = await fetch(`${process.env.API_URL}/imports/${id}`)

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Import not found' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
```

### TanStack Queryを使用した非同期呼び出し

```typescript
// hooks/useImport.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'

interface StartImportParams {
  file: File
}

export function useStartImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ file }: StartImportParams) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/imports', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Import failed')
      }

      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['imports'] })
    },
  })
}
```

## 状態管理と表示

### TanStack Queryによるポーリング

```typescript
// hooks/useImportStatus.ts
import { useQuery } from '@tanstack/react-query'

interface ImportStatus {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  processedCount: number
  totalCount: number
  errorMessage?: string
}

export function useImportStatus(taskId: string) {
  return useQuery<ImportStatus>({
    queryKey: ['import', taskId],
    queryFn: async () => {
      const response = await fetch(`/api/imports/${taskId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch status')
      }
      return response.json()
    },
    // 完了するまでポーリング
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') {
        return false // ポーリング停止
      }
      return 2000 // 2秒間隔
    },
    // バックグラウンドでも更新
    refetchIntervalInBackground: true,
  })
}
```

### 進捗表示コンポーネント

```typescript
// components/ImportProgress.tsx
'use client'

import { useImportStatus } from '@/hooks/useImportStatus'

interface ImportProgressProps {
  taskId: string
}

export function ImportProgress({ taskId }: ImportProgressProps) {
  const { data, isLoading, isError, error } = useImportStatus(taskId)

  if (isLoading) {
    return <div className="loading">読み込み中...</div>
  }

  if (isError) {
    return <div className="error">エラー: {error.message}</div>
  }

  if (!data) {
    return null
  }

  return (
    <div className="import-progress">
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${data.progress}%` }}
        />
      </div>

      <div className="progress-info">
        <span className="progress-text">{data.progress}%</span>
        <span className="progress-count">
          {data.processedCount} / {data.totalCount} 件
        </span>
      </div>

      <StatusMessage status={data.status} errorMessage={data.errorMessage} />
    </div>
  )
}

function StatusMessage({
  status,
  errorMessage,
}: {
  status: string
  errorMessage?: string
}) {
  switch (status) {
    case 'pending':
      return <p className="status">処理待機中...</p>
    case 'processing':
      return <p className="status">処理中...</p>
    case 'completed':
      return <p className="status success">完了しました！</p>
    case 'failed':
      return <p className="status error">エラー: {errorMessage}</p>
    default:
      return null
  }
}
```

### Optimistic Updates

```typescript
// hooks/useCancelImport.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'

export function useCancelImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await fetch(`/api/imports/${taskId}/cancel`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('Cancel failed')
      }

      return response.json()
    },
    // Optimistic Update
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
      // エラー時はロールバック
      queryClient.setQueryData(['import', taskId], context?.previousData)
    },
    onSettled: (data, error, taskId) => {
      // 最終的に最新データを取得
      queryClient.invalidateQueries({ queryKey: ['import', taskId] })
    },
  })
}
```

## WebSocket/SSE接続の復帰処理

### SSE用カスタムフック

```typescript
// hooks/useSSE.ts
import { useEffect, useRef, useState, useCallback } from 'react'

interface UseSSEOptions<T> {
  url: string
  onMessage: (data: T) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

interface UseSSEReturn {
  isConnected: boolean
  isReconnecting: boolean
  reconnectAttempts: number
  connect: () => void
  disconnect: () => void
}

export function useSSE<T>({
  url,
  onMessage,
  onError,
  onOpen,
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
}: UseSSEOptions<T>): UseSSEReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  // コールバックをrefに保存して最新の値を参照できるようにする
  const reconnectAttemptsRef = useRef(reconnectAttempts)

  // reconnectAttemptsが変わるたびにrefを更新
  useEffect(() => {
    reconnectAttemptsRef.current = reconnectAttempts
  }, [reconnectAttempts])

  // コールバックをrefに保存してstale closure問題を回避
  // useEffectの依存配列に関数を含めると無限ループになるため、
  // 常に最新の関数を参照できるようrefパターンを使用
  const callbacksRef = useRef({ onMessage, onError, onOpen })
  useEffect(() => {
    callbacksRef.current = { onMessage, onError, onOpen }
  }, [onMessage, onError, onOpen])

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsConnected(true)
      setIsReconnecting(false)
      setReconnectAttempts(0)
      callbacksRef.current.onOpen?.()
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T
        callbacksRef.current.onMessage(data)
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      setIsConnected(false)
      callbacksRef.current.onError?.(error)

      // 自動再接続（refから最新の値を取得）
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        setIsReconnecting(true)
        const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current)

        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectAttempts((prev) => prev + 1)
          connect()
        }, Math.min(delay, 30000)) // 最大30秒
      }
    }
  }, [url, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    setIsConnected(false)
    setIsReconnecting(false)
  }, [])

  // 初回接続とURL変更時の再接続
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    isConnected,
    isReconnecting,
    reconnectAttempts,
    connect,
    disconnect,
  }
}
```

### WebSocket用カスタムフック

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react'

interface UseWebSocketOptions<T> {
  url: string
  onMessage: (data: T) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: (event: CloseEvent) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
}

export function useWebSocket<T>({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
  heartbeatInterval = 30000,
}: UseWebSocketOptions<T>) {
  const [isConnected, setIsConnected] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null)

  // コールバックをrefに保存してstale closure問題を回避
  // useEffectの依存配列に関数を含めると無限ループになるため、
  // 常に最新の関数を参照できるようrefパターンを使用
  const callbacksRef = useRef({ onMessage, onError, onOpen, onClose })
  useEffect(() => {
    callbacksRef.current = { onMessage, onError, onOpen, onClose }
  }, [onMessage, onError, onOpen, onClose])

  const startHeartbeat = useCallback(() => {
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, heartbeatInterval)
  }, [heartbeatInterval])

  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
    }
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      setIsReconnecting(false)
      reconnectAttemptsRef.current = 0
      startHeartbeat()
      callbacksRef.current.onOpen?.()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T
        // pongメッセージは無視
        if ((data as any).type === 'pong') return
        callbacksRef.current.onMessage(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      callbacksRef.current.onError?.(error)
    }

    ws.onclose = (event) => {
      setIsConnected(false)
      stopHeartbeat()
      callbacksRef.current.onClose?.(event)

      // 正常終了でない場合は再接続
      if (!event.wasClean && reconnectAttemptsRef.current < maxReconnectAttempts) {
        setIsReconnecting(true)
        const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current)

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current += 1
          connect()
        }, Math.min(delay, 30000))
      }
    }
  }, [url, reconnectInterval, maxReconnectAttempts, startHeartbeat, stopHeartbeat])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    stopHeartbeat()
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect')
    }
    setIsConnected(false)
    setIsReconnecting(false)
  }, [stopHeartbeat])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  // 初回接続とURL変更時の再接続
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    isConnected,
    isReconnecting,
    connect,
    disconnect,
    send,
  }
}
```

### Visibility APIとの連携

```typescript
// hooks/useVisibilityAwareConnection.ts
import { useEffect, useCallback } from 'react'

interface UseVisibilityAwareConnectionOptions {
  onVisible: () => void
  onHidden?: () => void
  refreshOnVisible?: boolean
}

export function useVisibilityAwareConnection({
  onVisible,
  onHidden,
  refreshOnVisible = true,
}: UseVisibilityAwareConnectionOptions) {
  const handleVisibilityChange = useCallback(() => {
    if (document.visibilityState === 'visible') {
      if (refreshOnVisible) {
        onVisible()
      }
    } else {
      onHidden?.()
    }
  }, [onVisible, onHidden, refreshOnVisible])

  useEffect(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [handleVisibilityChange])
}
```

### 接続状態のコンテキスト管理

```typescript
// contexts/ConnectionContext.tsx
'use client'

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'

interface ConnectionState {
  isOnline: boolean
  isSSEConnected: boolean
  lastSyncTime: Date | null
}

interface ConnectionContextValue extends ConnectionState {
  setSSEConnected: (connected: boolean) => void
  updateLastSyncTime: () => void
}

const ConnectionContext = createContext<ConnectionContextValue | null>(null)

export function ConnectionProvider({ children }: { children: ReactNode }) {
  // Lazy State Initialization: 初期値の計算は初回レンダー時のみ実行
  const [state, setState] = useState<ConnectionState>(() => ({
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    isSSEConnected: false,
    lastSyncTime: null,
  }))

  const setSSEConnected = useCallback((connected: boolean) => {
    setState((prev) => ({ ...prev, isSSEConnected: connected }))
  }, [])

  const updateLastSyncTime = useCallback(() => {
    setState((prev) => ({ ...prev, lastSyncTime: new Date() }))
  }, [])

  // オンライン/オフライン監視
  useEffect(() => {
    const handleOnline = () => setState((prev) => ({ ...prev, isOnline: true }))
    const handleOffline = () => setState((prev) => ({ ...prev, isOnline: false }))

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return (
    <ConnectionContext.Provider
      value={{ ...state, setSSEConnected, updateLastSyncTime }}
    >
      {children}
    </ConnectionContext.Provider>
  )
}

export function useConnection() {
  const context = useContext(ConnectionContext)
  if (!context) {
    throw new Error('useConnection must be used within ConnectionProvider')
  }
  return context
}
```

## エラーハンドリング

### Error Boundary（App Router）

```typescript
// app/imports/[id]/error.tsx
'use client'

import { useEffect } from 'react'

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function ImportError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // エラーログ送信
    console.error('Import error:', error)
  }, [error])

  return (
    <div className="error-container">
      <h2>エラーが発生しました</h2>
      <p>{error.message || '予期しないエラーが発生しました'}</p>

      <div className="error-actions">
        <button onClick={reset}>再試行</button>
        <a href="/imports">インポート一覧に戻る</a>
      </div>
    </div>
  )
}
```

### グローバルエラーハンドリング

```typescript
// app/global-error.tsx
'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <div className="global-error">
          <h1>予期しないエラーが発生しました</h1>
          <p>申し訳ございません。問題が発生しました。</p>
          <button onClick={reset}>再試行</button>
        </div>
      </body>
    </html>
  )
}
```

### TanStack Queryのエラーハンドリング

```typescript
// providers/QueryProvider.tsx
'use client'

import { QueryClient, QueryClientProvider, QueryCache, MutationCache } from '@tanstack/react-query'
import { useState } from 'react'
import { toast } from 'sonner'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error, query) => {
            // グローバルエラーハンドリング
            console.error('Query error:', error)

            // 特定のクエリのエラーのみ通知
            if (query.meta?.showErrorToast !== false) {
              toast.error(`エラー: ${error.message}`)
            }
          },
        }),
        mutationCache: new MutationCache({
          onError: (error) => {
            console.error('Mutation error:', error)
            toast.error(`操作に失敗しました: ${error.message}`)
          },
        }),
        defaultOptions: {
          queries: {
            retry: (failureCount, error) => {
              // 4xx エラーはリトライしない
              if (error instanceof Error && error.message.includes('4')) {
                return false
              }
              return failureCount < 3
            },
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

### リトライ機能付きfetch

```typescript
// lib/fetchWithRetry.ts
interface FetchWithRetryOptions extends RequestInit {
  maxRetries?: number
  retryDelay?: number
  retryOn?: number[]
}

export async function fetchWithRetry(
  url: string,
  options: FetchWithRetryOptions = {}
): Promise<Response> {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    retryOn = [408, 429, 500, 502, 503, 504],
    ...fetchOptions
  } = options

  let lastError: Error | null = null

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, fetchOptions)

      if (retryOn.includes(response.status) && attempt < maxRetries) {
        const delay = retryDelay * Math.pow(2, attempt)
        console.log(`Retrying in ${delay}ms... (attempt ${attempt + 1}/${maxRetries})`)
        await new Promise((resolve) => setTimeout(resolve, delay))
        continue
      }

      return response
    } catch (error) {
      lastError = error as Error

      if (attempt < maxRetries) {
        const delay = retryDelay * Math.pow(2, attempt)
        console.log(`Network error, retrying in ${delay}ms...`)
        await new Promise((resolve) => setTimeout(resolve, delay))
        continue
      }
    }
  }

  throw lastError || new Error('Max retries exceeded')
}
```

### フォームエラーハンドリング

```typescript
// components/ImportForm.tsx
'use client'

import { useActionState } from 'react'
import { startImport, type ImportResult } from '@/app/actions/import'
import { useState } from 'react'

interface FormErrors {
  file?: string
  general?: string
}

const initialState: ImportResult = {
  taskId: '',
  status: 'pending',
}

export function ImportForm() {
  const [errors, setErrors] = useState<FormErrors>({})

  const validateFile = (file: File | null): FormErrors => {
    const newErrors: FormErrors = {}

    if (!file) {
      newErrors.file = 'ファイルを選択してください'
      return newErrors
    }

    if (file.size > 10 * 1024 * 1024) {
      newErrors.file = 'ファイルサイズは10MB以下にしてください'
    }

    if (!file.name.endsWith('.csv')) {
      newErrors.file = 'CSVファイルを選択してください'
    }

    return newErrors
  }

  // useActionStateのコールバックは (prevState, formData) の形式
  const handleSubmit = async (
    prevState: ImportResult,
    formData: FormData
  ): Promise<ImportResult> => {
    const file = formData.get('file') as File | null
    const validationErrors = validateFile(file)

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return prevState
    }

    setErrors({})
    // startImportもprevStateを受け取る形式なので正しく渡す
    return startImport(prevState, formData)
  }

  const [state, formAction, isPending] = useActionState(handleSubmit, initialState)

  return (
    <form action={formAction}>
      <div className="form-group">
        <input
          type="file"
          name="file"
          accept=".csv"
          onChange={() => setErrors({})}
        />
        {errors.file && <p className="field-error">{errors.file}</p>}
      </div>

      <button type="submit" disabled={isPending}>
        {isPending ? 'アップロード中...' : 'インポート開始'}
      </button>

      {state.status === 'failed' && (
        <p className="form-error">{state.message}</p>
      )}
    </form>
  )
}
```

## 実装例：ファイルインポート機能

### 完全な実装例

```typescript
// app/imports/[id]/page.tsx
import { Suspense } from 'react'
import { ImportProgressContainer } from '@/components/ImportProgressContainer'

// Next.js 15: Page の params も Promise 型
interface PageProps {
  params: Promise<{ id: string }>
}

export default async function ImportDetailPage({ params }: PageProps) {
  const { id } = await params

  return (
    <div className="import-detail">
      <h1>インポート詳細</h1>

      <Suspense fallback={<div>読み込み中...</div>}>
        <ImportProgressContainer taskId={id} />
      </Suspense>
    </div>
  )
}
```

```typescript
// components/ImportProgressContainer.tsx
// 'use client'はファイルの先頭に配置する必要がある
'use client'

import { startTransition } from 'react'
import { useImportStatus } from '@/hooks/useImportStatus'
import { useSSE } from '@/hooks/useSSE'
import { useVisibilityAwareConnection } from '@/hooks/useVisibilityAwareConnection'
import { useQueryClient } from '@tanstack/react-query'
import { useConnection } from '@/contexts/ConnectionContext'
import { ImportProgress } from './ImportProgress'
import { ConnectionStatus } from './ConnectionStatus'
import { CancelButton } from './CancelButton'
import { LoadingState, ErrorState } from './States'

interface ImportStatusUpdate {
  status: string
  progress: number
  processedCount: number
  totalCount: number
}

export function ImportProgressContainer({ taskId }: { taskId: string }) {
  const queryClient = useQueryClient()
  const { setSSEConnected, updateLastSyncTime } = useConnection()
  const { data, isLoading, isError, error, refetch } = useImportStatus(taskId)

  // SSEによるリアルタイム更新
  const { isConnected, isReconnecting } = useSSE<ImportStatusUpdate>({
    url: `/api/imports/${taskId}/events`,
    onMessage: (update) => {
      // 非緊急の更新にはstartTransitionを使用してUIをブロックしない
      startTransition(() => {
        queryClient.setQueryData(['import', taskId], (old: any) => ({
          ...old,
          ...update,
        }))
        updateLastSyncTime()
      })
    },
    onOpen: () => setSSEConnected(true),
    onError: () => setSSEConnected(false),
  })

  // ページが表示されたときに最新状態を取得
  useVisibilityAwareConnection({
    onVisible: () => refetch(),
  })

  if (isLoading) {
    return <LoadingState />
  }

  if (isError) {
    return <ErrorState error={error} onRetry={refetch} />
  }

  return (
    <div>
      <ConnectionStatus
        isConnected={isConnected}
        isReconnecting={isReconnecting}
      />
      <ImportProgress data={data} />
      {data?.status === 'processing' && (
        <CancelButton taskId={taskId} />
      )}
    </div>
  )
}
```

```typescript
// components/ConnectionStatus.tsx
interface ConnectionStatusProps {
  isConnected: boolean
  isReconnecting: boolean
}

export function ConnectionStatus({ isConnected, isReconnecting }: ConnectionStatusProps) {
  if (isReconnecting) {
    return (
      <div className="connection-status reconnecting">
        再接続中...
      </div>
    )
  }

  return (
    <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
      {isConnected ? 'リアルタイム接続中' : 'オフライン'}
    </div>
  )
}
```

## リファレンス

### 公式ドキュメント

- [Next.js App Router Documentation](https://nextjs.org/docs/app)
- [Server Actions and Mutations](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations)
- [Error Handling](https://nextjs.org/docs/app/building-your-application/routing/error-handling)
- [Route Handlers](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)

### React関連

- [React useActionState](https://react.dev/reference/react/useActionState)
- [React useOptimistic](https://react.dev/reference/react/useOptimistic)
- [React Suspense](https://react.dev/reference/react/Suspense)

### TanStack Query

- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Queries](https://tanstack.com/query/latest/docs/react/guides/queries)
- [Mutations](https://tanstack.com/query/latest/docs/react/guides/mutations)
- [Query Invalidation](https://tanstack.com/query/latest/docs/react/guides/query-invalidation)

### リアルタイム通信

- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Page Visibility API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API)
