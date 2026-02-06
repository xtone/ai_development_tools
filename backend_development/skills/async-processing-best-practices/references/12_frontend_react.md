# React フロントエンド実装ベストプラクティス

Rails + React（Webpacker/Shakapacker）構成における非同期処理のフロントエンド実装ガイドです。

## 目次

1. [ActionCable接続の設定](#actioncable接続の設定)
2. [非同期タスクコンポーネント](#非同期タスクコンポーネント)
3. [カスタムフックによる実装](#カスタムフックによる実装)
4. [モーダルダイアログパターン](#モーダルダイアログパターン)
5. [エラーハンドリング](#エラーハンドリング)
6. [接続復帰処理](#接続復帰処理)

---

## ActionCable接続の設定

### consumer.jsの設定

```javascript
// app/javascript/channels/consumer.js
import { createConsumer } from "@rails/actioncable"

// CSRFトークンを取得
const getCSRFToken = () => {
  const meta = document.querySelector('meta[name="csrf-token"]')
  return meta ? meta.getAttribute('content') : null
}

// 環境に応じたWebSocket URLを取得
const getWebSocketURL = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/cable`
}

export default createConsumer(getWebSocketURL())
```

### Solid Cable使用時の設定

```javascript
// app/javascript/channels/consumer.js
import { createConsumer } from "@rails/actioncable"

// Solid Cableはpolling方式のため、通常のHTTPエンドポイントを使用
export default createConsumer("/cable")
```

---

## 非同期タスクコンポーネント

### クラスコンポーネント版

```jsx
// app/javascript/components/AsyncTaskProcessor.jsx
import React, { Component } from 'react'
import consumer from '../channels/consumer'

class AsyncTaskProcessor extends Component {
  constructor(props) {
    super(props)
    this.state = {
      status: 'idle',        // idle, pending, processing, completed, failed
      progress: 0,
      totalItems: 0,
      processedItems: 0,
      error: null,
      taskId: null,
      isSubmitting: false
    }
    this.subscription = null
  }

  componentDidMount() {
    // ページ表示状態の監視
    document.addEventListener('visibilitychange', this.handleVisibilityChange)
  }

  componentWillUnmount() {
    this.unsubscribe()
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
  }

  handleVisibilityChange = () => {
    if (document.visibilityState === 'visible' && this.state.taskId) {
      // ページが再表示されたら状態を再取得
      this.fetchTaskStatus()
    }
  }

  subscribe = (taskId) => {
    this.unsubscribe()

    this.subscription = consumer.subscriptions.create(
      { channel: 'TaskStatusChannel', task_id: taskId },
      {
        connected: () => {
          console.log('TaskStatusChannel connected')
        },
        disconnected: () => {
          console.log('TaskStatusChannel disconnected')
          // 自動再接続を試みる
          setTimeout(() => {
            if (this.state.status === 'processing') {
              this.subscribe(taskId)
            }
          }, 3000)
        },
        received: (data) => {
          this.handleStatusUpdate(data)
        }
      }
    )
  }

  unsubscribe = () => {
    if (this.subscription) {
      this.subscription.unsubscribe()
      this.subscription = null
    }
  }

  handleStatusUpdate = (data) => {
    const { status, progress, total_items, processed_items, error, result } = data

    this.setState({
      status,
      progress: progress || 0,
      totalItems: total_items || 0,
      processedItems: processed_items || 0,
      error: error || null
    })

    if (status === 'completed' || status === 'failed') {
      this.unsubscribe()
      if (this.props.onComplete) {
        this.props.onComplete({ status, result, error })
      }
    }
  }

  fetchTaskStatus = async () => {
    const { taskId } = this.state
    if (!taskId) return

    try {
      const response = await fetch(`/api/async_tasks/${taskId}`, {
        headers: {
          'Accept': 'application/json',
          'X-CSRF-Token': this.getCSRFToken()
        }
      })

      if (response.ok) {
        const data = await response.json()
        this.handleStatusUpdate(data)
      }
    } catch (error) {
      console.error('Failed to fetch task status:', error)
    }
  }

  getCSRFToken = () => {
    const meta = document.querySelector('meta[name="csrf-token"]')
    return meta ? meta.getAttribute('content') : ''
  }

  handleSubmit = async (formData) => {
    if (this.state.isSubmitting) return

    this.setState({ isSubmitting: true, error: null })

    try {
      const response = await fetch(this.props.submitUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-Token': this.getCSRFToken()
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        this.setState({
          status: 'pending',
          taskId: data.task_id,
          isSubmitting: false
        })
        this.subscribe(data.task_id)
      } else {
        this.setState({
          error: data.error || 'リクエストに失敗しました',
          isSubmitting: false
        })
      }
    } catch (error) {
      this.setState({
        error: 'ネットワークエラーが発生しました',
        isSubmitting: false
      })
    }
  }

  renderProgress() {
    const { status, progress, processedItems, totalItems } = this.state

    if (status === 'idle') return null

    const statusLabels = {
      pending: '準備中...',
      processing: `処理中: ${processedItems} / ${totalItems} 件`,
      completed: '完了',
      failed: 'エラー'
    }

    return (
      <div className="progress-container">
        <div className="progress-status">{statusLabels[status]}</div>
        <div className="progress-bar-wrapper">
          <div
            className="progress-bar"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="progress-percentage">{progress}%</div>
      </div>
    )
  }

  render() {
    const { status, error, isSubmitting } = this.state

    return (
      <div className="async-task-processor">
        {this.props.children({
          status,
          error,
          isSubmitting,
          onSubmit: this.handleSubmit,
          progress: this.renderProgress()
        })}
      </div>
    )
  }
}

export default AsyncTaskProcessor
```

### 使用例

```jsx
// app/javascript/components/BulkRegistrationForm.jsx
import React, { Component } from 'react'
import AsyncTaskProcessor from './AsyncTaskProcessor'

class BulkRegistrationForm extends Component {
  state = {
    userId: '',
    startDate: '',
    endDate: ''
  }

  handleChange = (e) => {
    this.setState({ [e.target.name]: e.target.value })
  }

  render() {
    return (
      <AsyncTaskProcessor
        submitUrl="/system_admin/retirement_processings"
        onComplete={({ status, result }) => {
          if (status === 'completed') {
            alert('処理が完了しました')
          }
        }}
      >
        {({ status, error, isSubmitting, onSubmit, progress }) => (
          <div className="panel panel-default">
            <div className="panel-heading">
              <h3 className="panel-title">休み一括登録</h3>
            </div>
            <div className="panel-body">
              <p>開始日から終了日までの営業日を「休み 100%」で埋めます。</p>

              {error && (
                <div className="alert alert-danger">{error}</div>
              )}

              <form onSubmit={(e) => {
                e.preventDefault()
                onSubmit(this.state)
              }}>
                <div className="form-group">
                  <label>対象ユーザー</label>
                  <select
                    name="userId"
                    className="form-control"
                    value={this.state.userId}
                    onChange={this.handleChange}
                    disabled={status === 'processing'}
                  >
                    <option value="">選択してください</option>
                    {this.props.users.map(user => (
                      <option key={user.id} value={user.id}>
                        {user.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>開始日</label>
                  <input
                    type="date"
                    name="startDate"
                    className="form-control"
                    value={this.state.startDate}
                    onChange={this.handleChange}
                    disabled={status === 'processing'}
                  />
                </div>

                <div className="form-group">
                  <label>終了日</label>
                  <input
                    type="date"
                    name="endDate"
                    className="form-control"
                    value={this.state.endDate}
                    onChange={this.handleChange}
                    disabled={status === 'processing'}
                  />
                </div>

                {progress}

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting || status === 'processing'}
                >
                  {isSubmitting ? '送信中...' : '実行'}
                </button>
              </form>
            </div>
          </div>
        )}
      </AsyncTaskProcessor>
    )
  }
}

export default BulkRegistrationForm
```

---

## カスタムフックによる実装

### useAsyncTask フック

```javascript
// app/javascript/hooks/useAsyncTask.js
import { useState, useEffect, useCallback, useRef } from 'react'
import consumer from '../channels/consumer'

const getCSRFToken = () => {
  const meta = document.querySelector('meta[name="csrf-token"]')
  return meta ? meta.getAttribute('content') : ''
}

export const useAsyncTask = (options = {}) => {
  const { onComplete, onError } = options

  const [state, setState] = useState({
    status: 'idle',
    progress: 0,
    totalItems: 0,
    processedItems: 0,
    error: null,
    taskId: null,
    isSubmitting: false
  })

  const subscriptionRef = useRef(null)
  const isMountedRef = useRef(true)

  // クリーンアップ
  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      if (subscriptionRef.current) {
        subscriptionRef.current.unsubscribe()
      }
    }
  }, [])

  // ページ表示状態の監視
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && state.taskId && state.status === 'processing') {
        fetchTaskStatus(state.taskId)
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [state.taskId, state.status])

  const handleStatusUpdate = useCallback((data) => {
    if (!isMountedRef.current) return

    const { status, progress, total_items, processed_items, error, result } = data

    setState(prev => ({
      ...prev,
      status,
      progress: progress || 0,
      totalItems: total_items || 0,
      processedItems: processed_items || 0,
      error: error || null
    }))

    if (status === 'completed') {
      if (subscriptionRef.current) {
        subscriptionRef.current.unsubscribe()
        subscriptionRef.current = null
      }
      onComplete?.({ status, result })
    } else if (status === 'failed') {
      if (subscriptionRef.current) {
        subscriptionRef.current.unsubscribe()
        subscriptionRef.current = null
      }
      onError?.({ status, error })
    }
  }, [onComplete, onError])

  const subscribe = useCallback((taskId) => {
    if (subscriptionRef.current) {
      subscriptionRef.current.unsubscribe()
    }

    subscriptionRef.current = consumer.subscriptions.create(
      { channel: 'TaskStatusChannel', task_id: taskId },
      {
        connected: () => console.log('Connected to TaskStatusChannel'),
        disconnected: () => {
          console.log('Disconnected from TaskStatusChannel')
          // 自動再接続
          if (isMountedRef.current && state.status === 'processing') {
            setTimeout(() => subscribe(taskId), 3000)
          }
        },
        received: handleStatusUpdate
      }
    )
  }, [handleStatusUpdate, state.status])

  const fetchTaskStatus = useCallback(async (taskId) => {
    try {
      const response = await fetch(`/api/async_tasks/${taskId}`, {
        headers: {
          'Accept': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        }
      })

      if (response.ok) {
        const data = await response.json()
        handleStatusUpdate(data)
      }
    } catch (error) {
      console.error('Failed to fetch task status:', error)
    }
  }, [handleStatusUpdate])

  const submitTask = useCallback(async (url, formData) => {
    if (state.isSubmitting) return

    setState(prev => ({ ...prev, isSubmitting: true, error: null }))

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        setState(prev => ({
          ...prev,
          status: 'pending',
          taskId: data.task_id,
          isSubmitting: false
        }))
        subscribe(data.task_id)
        return { success: true, taskId: data.task_id }
      } else {
        setState(prev => ({
          ...prev,
          error: data.error || 'リクエストに失敗しました',
          isSubmitting: false
        }))
        return { success: false, error: data.error }
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'ネットワークエラーが発生しました',
        isSubmitting: false
      }))
      return { success: false, error: 'ネットワークエラー' }
    }
  }, [state.isSubmitting, subscribe])

  const reset = useCallback(() => {
    if (subscriptionRef.current) {
      subscriptionRef.current.unsubscribe()
      subscriptionRef.current = null
    }
    setState({
      status: 'idle',
      progress: 0,
      totalItems: 0,
      processedItems: 0,
      error: null,
      taskId: null,
      isSubmitting: false
    })
  }, [])

  return {
    ...state,
    submitTask,
    reset,
    isProcessing: state.status === 'processing' || state.status === 'pending',
    isCompleted: state.status === 'completed',
    isFailed: state.status === 'failed'
  }
}
```

### 関数コンポーネントでの使用例

```jsx
// app/javascript/components/BulkRegistrationFormHook.jsx
import React, { useState } from 'react'
import { useAsyncTask } from '../hooks/useAsyncTask'

const BulkRegistrationFormHook = ({ users, submitUrl }) => {
  const [formData, setFormData] = useState({
    userId: '',
    startDate: '',
    endDate: ''
  })

  const {
    status,
    progress,
    processedItems,
    totalItems,
    error,
    isSubmitting,
    isProcessing,
    isCompleted,
    submitTask,
    reset
  } = useAsyncTask({
    onComplete: ({ result }) => {
      alert('処理が完了しました')
    },
    onError: ({ error }) => {
      console.error('Task failed:', error)
    }
  })

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    await submitTask(submitUrl, formData)
  }

  const statusLabels = {
    idle: '',
    pending: '準備中...',
    processing: `処理中: ${processedItems} / ${totalItems} 件`,
    completed: '完了',
    failed: 'エラー'
  }

  return (
    <div className="panel panel-default">
      <div className="panel-heading">
        <h3 className="panel-title">休み一括登録</h3>
      </div>
      <div className="panel-body">
        <p>開始日から終了日までの営業日を「休み 100%」で埋めます。</p>

        {error && (
          <div className="alert alert-danger">{error}</div>
        )}

        {isCompleted && (
          <div className="alert alert-success">
            処理が完了しました
            <button className="btn btn-link" onClick={reset}>
              新しいタスクを開始
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>対象ユーザー</label>
            <select
              name="userId"
              className="form-control"
              value={formData.userId}
              onChange={handleChange}
              disabled={isProcessing}
            >
              <option value="">選択してください</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>
                  {user.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>開始日</label>
            <input
              type="date"
              name="startDate"
              className="form-control"
              value={formData.startDate}
              onChange={handleChange}
              disabled={isProcessing}
            />
          </div>

          <div className="form-group">
            <label>終了日</label>
            <input
              type="date"
              name="endDate"
              className="form-control"
              value={formData.endDate}
              onChange={handleChange}
              disabled={isProcessing}
            />
          </div>

          {status !== 'idle' && (
            <div className="progress-container" style={{ marginBottom: '15px' }}>
              <div className="progress-status">{statusLabels[status]}</div>
              <div className="progress">
                <div
                  className="progress-bar"
                  role="progressbar"
                  style={{ width: `${progress}%` }}
                  aria-valuenow={progress}
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  {progress}%
                </div>
              </div>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting || isProcessing}
          >
            {isSubmitting ? '送信中...' : '実行'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default BulkRegistrationFormHook
```

---

## モーダルダイアログパターン

既存のページにモーダルダイアログとして非同期タスク機能を追加するパターンです。

```jsx
// app/javascript/components/AsyncTaskModal.jsx
import React, { Component } from 'react'
import consumer from '../channels/consumer'

class AsyncTaskModal extends Component {
  constructor(props) {
    super(props)
    this.state = {
      isOpen: false,
      status: 'idle',
      progress: 0,
      totalItems: 0,
      processedItems: 0,
      error: null,
      taskId: null,
      isSubmitting: false,
      formData: this.getInitialFormData()
    }
    this.subscription = null
  }

  getInitialFormData() {
    return this.props.initialFormData || {}
  }

  componentWillUnmount() {
    this.unsubscribe()
  }

  open = (additionalData = {}) => {
    this.setState({
      isOpen: true,
      status: 'idle',
      progress: 0,
      error: null,
      formData: { ...this.getInitialFormData(), ...additionalData }
    })
  }

  close = () => {
    if (this.state.status === 'processing') {
      if (!confirm('処理中です。本当に閉じますか？')) {
        return
      }
    }
    this.unsubscribe()
    this.setState({ isOpen: false })
  }

  subscribe = (taskId) => {
    this.unsubscribe()

    this.subscription = consumer.subscriptions.create(
      { channel: 'TaskStatusChannel', task_id: taskId },
      {
        received: (data) => {
          this.setState({
            status: data.status,
            progress: data.progress || 0,
            totalItems: data.total_items || 0,
            processedItems: data.processed_items || 0,
            error: data.error
          })

          if (data.status === 'completed' || data.status === 'failed') {
            this.unsubscribe()
            if (data.status === 'completed' && this.props.onComplete) {
              this.props.onComplete(data)
            }
          }
        }
      }
    )
  }

  unsubscribe = () => {
    if (this.subscription) {
      this.subscription.unsubscribe()
      this.subscription = null
    }
  }

  getCSRFToken = () => {
    const meta = document.querySelector('meta[name="csrf-token"]')
    return meta ? meta.getAttribute('content') : ''
  }

  handleSubmit = async (e) => {
    e.preventDefault()
    if (this.state.isSubmitting) return

    this.setState({ isSubmitting: true, error: null })

    try {
      const response = await fetch(this.props.submitUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-Token': this.getCSRFToken()
        },
        body: JSON.stringify(this.state.formData)
      })

      const data = await response.json()

      if (response.ok) {
        this.setState({
          status: 'pending',
          taskId: data.task_id,
          isSubmitting: false
        })
        this.subscribe(data.task_id)
      } else {
        this.setState({
          error: data.error || 'リクエストに失敗しました',
          isSubmitting: false
        })
      }
    } catch (error) {
      this.setState({
        error: 'ネットワークエラーが発生しました',
        isSubmitting: false
      })
    }
  }

  handleChange = (e) => {
    const { name, value } = e.target
    this.setState(prev => ({
      formData: { ...prev.formData, [name]: value }
    }))
  }

  renderModalContent() {
    const { status, progress, processedItems, totalItems, error, isSubmitting, formData } = this.state
    const { title, description, fields } = this.props

    const isProcessing = status === 'processing' || status === 'pending'
    const isCompleted = status === 'completed'

    return (
      <div className="modal-content">
        <div className="modal-header">
          <button type="button" className="close" onClick={this.close}>
            <span>&times;</span>
          </button>
          <h4 className="modal-title">{title}</h4>
        </div>

        <div className="modal-body">
          {description && <p>{description}</p>}

          {error && (
            <div className="alert alert-danger">{error}</div>
          )}

          {isCompleted ? (
            <div className="alert alert-success">
              処理が完了しました
            </div>
          ) : (
            <form onSubmit={this.handleSubmit}>
              {fields.map(field => (
                <div className="form-group" key={field.name}>
                  <label>{field.label}</label>
                  {field.type === 'select' ? (
                    <select
                      name={field.name}
                      className="form-control"
                      value={formData[field.name] || ''}
                      onChange={this.handleChange}
                      disabled={isProcessing}
                      required={field.required}
                    >
                      <option value="">選択してください</option>
                      {field.options.map(opt => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type={field.type || 'text'}
                      name={field.name}
                      className="form-control"
                      value={formData[field.name] || ''}
                      onChange={this.handleChange}
                      disabled={isProcessing}
                      required={field.required}
                    />
                  )}
                </div>
              ))}

              {status !== 'idle' && (
                <div className="progress-section">
                  <div className="progress-label">
                    {status === 'pending' && '準備中...'}
                    {status === 'processing' && `処理中: ${processedItems} / ${totalItems} 件`}
                  </div>
                  <div className="progress">
                    <div
                      className="progress-bar progress-bar-striped active"
                      style={{ width: `${progress}%` }}
                    >
                      {progress}%
                    </div>
                  </div>
                </div>
              )}

              <div className="modal-footer" style={{ paddingLeft: 0, paddingRight: 0 }}>
                <button
                  type="button"
                  className="btn btn-default"
                  onClick={this.close}
                >
                  閉じる
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting || isProcessing}
                >
                  {isSubmitting ? '送信中...' : '実行'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    )
  }

  render() {
    if (!this.state.isOpen) return null

    return (
      <div className="modal fade in" style={{ display: 'block' }}>
        <div className="modal-backdrop fade in" onClick={this.close} />
        <div className="modal-dialog">
          {this.renderModalContent()}
        </div>
      </div>
    )
  }
}

export default AsyncTaskModal
```

### モーダルの使用例

```jsx
// app/javascript/components/UserEditPage.jsx
import React, { Component, createRef } from 'react'
import AsyncTaskModal from './AsyncTaskModal'

class UserEditPage extends Component {
  modalRef = createRef()

  handleOpenModal = () => {
    this.modalRef.current.open({
      userId: this.props.user.id
    })
  }

  handleComplete = (data) => {
    // 完了後の処理（ページリロードなど）
    window.location.reload()
  }

  render() {
    const { user, users } = this.props

    return (
      <div>
        <h1>ユーザー編集: {user.name}</h1>

        {/* 他の編集フォーム */}

        <div className="action-buttons">
          <button
            className="btn btn-warning"
            onClick={this.handleOpenModal}
          >
            <span className="glyphicon glyphicon-calendar" />
            休み一括登録
          </button>
        </div>

        <AsyncTaskModal
          ref={this.modalRef}
          title="休み一括登録"
          description={`${user.name} さんの開始日から終了日までの営業日を「休み 100%」で埋めます。`}
          submitUrl="/system_admin/retirement_processings"
          initialFormData={{ userId: user.id }}
          fields={[
            {
              name: 'startDate',
              label: '開始日',
              type: 'date',
              required: true
            },
            {
              name: 'endDate',
              label: '終了日',
              type: 'date',
              required: true
            }
          ]}
          onComplete={this.handleComplete}
        />
      </div>
    )
  }
}

export default UserEditPage
```

---

## エラーハンドリング

### Error Boundaryの実装

```jsx
// app/javascript/components/AsyncTaskErrorBoundary.jsx
import React, { Component } from 'react'

class AsyncTaskErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('AsyncTask Error:', error, errorInfo)

    // エラーレポートサービスに送信
    if (window.Sentry) {
      window.Sentry.captureException(error, { extra: errorInfo })
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="alert alert-danger">
          <h4>エラーが発生しました</h4>
          <p>{this.state.error?.message || '予期しないエラーが発生しました'}</p>
          <button className="btn btn-default" onClick={this.handleRetry}>
            再試行
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default AsyncTaskErrorBoundary
```

### グローバルエラーハンドリング

```javascript
// app/javascript/utils/errorHandler.js
export const setupGlobalErrorHandler = () => {
  // 未処理のPromiseエラー
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise rejection:', event.reason)

    // ユーザーに通知
    showErrorNotification('ネットワークエラーが発生しました。再度お試しください。')
  })

  // ActionCable接続エラー
  if (window.ActionCable) {
    const originalCreateConsumer = window.ActionCable.createConsumer
    window.ActionCable.createConsumer = function(...args) {
      const consumer = originalCreateConsumer.apply(this, args)

      consumer.connection.events.error = (error) => {
        console.error('ActionCable connection error:', error)
        showErrorNotification('リアルタイム接続でエラーが発生しました')
      }

      return consumer
    }
  }
}

const showErrorNotification = (message) => {
  // トースト通知やアラートを表示
  const notification = document.createElement('div')
  notification.className = 'error-notification alert alert-danger'
  notification.textContent = message
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    animation: fadeIn 0.3s ease-in;
  `
  document.body.appendChild(notification)

  setTimeout(() => {
    notification.remove()
  }, 5000)
}
```

---

## 接続復帰処理

### Visibility APIを使用した状態同期

```javascript
// app/javascript/hooks/useConnectionRecovery.js
import { useEffect, useRef, useCallback } from 'react'

export const useConnectionRecovery = (taskId, onRecover) => {
  const lastVisibleTimeRef = useRef(Date.now())
  const isOnlineRef = useRef(navigator.onLine)

  const handleVisibilityChange = useCallback(() => {
    if (document.visibilityState === 'visible') {
      const hiddenDuration = Date.now() - lastVisibleTimeRef.current

      // 30秒以上非表示だった場合は状態を再取得
      if (hiddenDuration > 30000 && taskId) {
        onRecover?.()
      }
    } else {
      lastVisibleTimeRef.current = Date.now()
    }
  }, [taskId, onRecover])

  const handleOnline = useCallback(() => {
    if (!isOnlineRef.current) {
      isOnlineRef.current = true
      // オフラインからオンラインに復帰した場合
      if (taskId) {
        onRecover?.()
      }
    }
  }, [taskId, onRecover])

  const handleOffline = useCallback(() => {
    isOnlineRef.current = false
  }, [])

  useEffect(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [handleVisibilityChange, handleOnline, handleOffline])

  return {
    isOnline: isOnlineRef.current
  }
}
```

### 使用例

```jsx
import { useAsyncTask } from '../hooks/useAsyncTask'
import { useConnectionRecovery } from '../hooks/useConnectionRecovery'

const TaskComponent = () => {
  const { taskId, status, fetchTaskStatus } = useAsyncTask()

  useConnectionRecovery(taskId, () => {
    if (status === 'processing' || status === 'pending') {
      fetchTaskStatus(taskId)
    }
  })

  // ...
}
```

---

## スタイリング

```css
/* app/assets/stylesheets/async_task.css */
.progress-container {
  margin: 15px 0;
}

.progress-status {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.progress {
  height: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: #337ab7;
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
}

.progress-bar.progress-bar-striped {
  background-image: linear-gradient(
    45deg,
    rgba(255,255,255,.15) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255,255,255,.15) 50%,
    rgba(255,255,255,.15) 75%,
    transparent 75%,
    transparent
  );
  background-size: 40px 40px;
}

.progress-bar.active {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  from { background-position: 40px 0; }
  to { background-position: 0 0; }
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-dialog {
  position: relative;
  margin: 100px auto;
  max-width: 500px;
  z-index: 1050;
}

.error-notification {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

---

## 参照

- [Rails ActionCable Guide](https://guides.rubyonrails.org/action_cable_overview.html)
- [React Documentation](https://react.dev/)
- [Shakapacker](https://github.com/shakacode/shakapacker)
