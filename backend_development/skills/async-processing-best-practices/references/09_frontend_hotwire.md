# Rails Hotwire フロントエンド非同期処理実装ガイド

このドキュメントでは、Rails Hotwire（Turbo + Stimulus + ActionCable）を使用したフロントエンドでの非同期処理実装のベストプラクティスを解説します。

## 目次

1. [非同期処理の呼び出し方](#非同期処理の呼び出し方)
2. [状態管理と表示](#状態管理と表示)
3. [WebSocket接続の復帰処理](#websocket接続の復帰処理)
4. [エラーハンドリング](#エラーハンドリング)
5. [実装例：ファイルインポート機能](#実装例ファイルインポート機能)
6. [リファレンス](#リファレンス)

## 非同期処理の呼び出し方

### Turbo Formによる非同期リクエスト

Turboを使用すると、フォーム送信が自動的に非同期化されます。

```erb
<%# app/views/imports/new.html.erb %>
<%= form_with model: @import, data: { turbo: true, controller: "async-task" } do |f| %>
  <%= f.file_field :file, data: { async_task_target: "fileInput" } %>

  <button type="submit"
          data-async-task-target="submitButton"
          data-action="click->async-task#showLoading">
    インポート開始
  </button>

  <div data-async-task-target="loadingIndicator" class="hidden">
    処理中...
  </div>
<% end %>
```

### Stimulus Controllerでの呼び出し管理

```javascript
// app/javascript/controllers/async_task_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["submitButton", "loadingIndicator", "fileInput"]
  static values = {
    submitting: { type: Boolean, default: false }
  }

  showLoading(event) {
    if (this.submittingValue) {
      event.preventDefault()
      return
    }

    this.submittingValue = true
    this.submitButtonTarget.disabled = true
    this.loadingIndicatorTarget.classList.remove("hidden")
  }

  // Turbo Stream レスポンス受信時に呼ばれる
  resetForm() {
    this.submittingValue = false
    this.submitButtonTarget.disabled = false
    this.loadingIndicatorTarget.classList.add("hidden")
  }
}
```

### Turbo Frame内での非同期リクエスト

特定の領域のみを更新する場合：

```erb
<%# app/views/tasks/index.html.erb %>
<turbo-frame id="task_list" data-controller="polling" data-polling-interval-value="5000">
  <%= render @tasks %>
</turbo-frame>

<%= link_to "更新", tasks_path, data: { turbo_frame: "task_list" } %>
```

### fetch APIを使用したカスタムリクエスト

Stimulusコントローラ内でfetchを使用する場合：

```javascript
// app/javascript/controllers/custom_async_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { url: String }

  async startTask() {
    try {
      const response = await fetch(this.urlValue, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content,
          'Accept': 'text/vnd.turbo-stream.html'
        },
        body: JSON.stringify({ /* params */ })
      })

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

      // Turbo Streamレスポンスを手動で処理
      const html = await response.text()
      Turbo.renderStreamMessage(html)
    } catch (error) {
      this.handleError(error)
    }
  }

  handleError(error) {
    console.error('Task failed:', error)
    // エラー表示処理
  }
}
```

## 状態管理と表示

### ActionCableによるリアルタイム更新

バックエンドでジョブの進捗をブロードキャストし、フロントエンドで受信します。

#### バックエンドのブロードキャスト設定

```ruby
# app/models/import_task.rb
class ImportTask < ApplicationRecord
  broadcasts_to ->(task) { "import_task_#{task.id}" }

  # または明示的なブロードキャスト
  after_update_commit :broadcast_progress

  private

  def broadcast_progress
    broadcast_replace_to(
      "import_task_#{id}",
      target: "import_task_#{id}_progress",
      partial: "import_tasks/progress",
      locals: { task: self }
    )
  end
end
```

#### フロントエンドのサブスクリプション

```erb
<%# app/views/import_tasks/show.html.erb %>
<div id="import_task_<%= @task.id %>">
  <%= turbo_stream_from "import_task_#{@task.id}" %>

  <div id="import_task_<%= @task.id %>_progress"
       data-controller="progress"
       data-progress-task-id-value="<%= @task.id %>">
    <%= render "progress", task: @task %>
  </div>
</div>
```

#### 進捗表示のパーシャル

```erb
<%# app/views/import_tasks/_progress.html.erb %>
<div class="progress-container">
  <div class="progress-bar" style="width: <%= task.progress_percentage %>%"></div>
  <span class="progress-text"><%= task.progress_percentage %>%</span>

  <% case task.status %>
  <% when 'pending' %>
    <p>処理待機中...</p>
  <% when 'processing' %>
    <p><%= task.processed_count %> / <%= task.total_count %> 件処理中</p>
  <% when 'completed' %>
    <p>完了しました！</p>
  <% when 'failed' %>
    <p class="error">エラーが発生しました: <%= task.error_message %></p>
  <% end %>
</div>
```

### Stimulus Controllerでの状態管理

```javascript
// app/javascript/controllers/progress_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = {
    taskId: String,
    status: { type: String, default: "pending" },
    progress: { type: Number, default: 0 }
  }

  static targets = ["progressBar", "statusText", "cancelButton"]

  connect() {
    // ActionCableからの更新を監視
    this.subscription = this.createSubscription()
  }

  disconnect() {
    if (this.subscription) {
      this.subscription.unsubscribe()
    }
  }

  createSubscription() {
    return consumer.subscriptions.create(
      { channel: "ImportTaskChannel", task_id: this.taskIdValue },
      {
        received: (data) => this.handleUpdate(data)
      }
    )
  }

  handleUpdate(data) {
    this.statusValue = data.status
    this.progressValue = data.progress

    this.updateUI()
  }

  updateUI() {
    if (this.hasProgressBarTarget) {
      this.progressBarTarget.style.width = `${this.progressValue}%`
    }

    if (this.hasStatusTextTarget) {
      this.statusTextTarget.textContent = this.getStatusText()
    }

    // 完了時の処理
    if (this.statusValue === 'completed') {
      this.onComplete()
    }
  }

  getStatusText() {
    const statusMap = {
      pending: '処理待機中...',
      processing: `処理中: ${this.progressValue}%`,
      completed: '完了',
      failed: 'エラー'
    }
    return statusMap[this.statusValue] || this.statusValue
  }

  onComplete() {
    // 完了時のアニメーションやリダイレクト
    this.element.classList.add('completed')
  }

  cancel() {
    // キャンセル処理
    fetch(`/import_tasks/${this.taskIdValue}/cancel`, {
      method: 'POST',
      headers: {
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
      }
    })
  }
}
```

### ポーリングによる状態更新

ActionCableを使用しない場合のフォールバック：

```javascript
// app/javascript/controllers/polling_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = {
    url: String,
    interval: { type: Number, default: 3000 },
    active: { type: Boolean, default: true }
  }

  connect() {
    if (this.activeValue) {
      this.startPolling()
    }
  }

  disconnect() {
    this.stopPolling()
  }

  startPolling() {
    this.poll()
    this.intervalId = setInterval(() => this.poll(), this.intervalValue)
  }

  stopPolling() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }

  async poll() {
    try {
      const response = await fetch(this.urlValue, {
        headers: { 'Accept': 'text/vnd.turbo-stream.html' }
      })

      if (response.ok) {
        const html = await response.text()
        Turbo.renderStreamMessage(html)

        // 完了したらポーリング停止
        if (this.isCompleted()) {
          this.stopPolling()
        }
      }
    } catch (error) {
      console.error('Polling error:', error)
      // エラー時はポーリング間隔を延長
      this.intervalValue = Math.min(this.intervalValue * 2, 30000)
    }
  }

  isCompleted() {
    return this.element.dataset.status === 'completed' ||
           this.element.dataset.status === 'failed'
  }
}
```

## WebSocket接続の復帰処理

### ActionCable自動再接続の設定

Rails 7.1以降では、ActionCableの再接続時にコールバックを受け取れます。

```javascript
// app/javascript/channels/import_task_channel.js
import consumer from "./consumer"

const createImportTaskSubscription = (taskId, callbacks) => {
  return consumer.subscriptions.create(
    { channel: "ImportTaskChannel", task_id: taskId },
    {
      connected({ reconnected }) {
        console.log('Connected to ImportTaskChannel')

        if (reconnected) {
          // 再接続時：最新状態を取得
          console.log('Reconnected - fetching latest state')
          callbacks.onReconnected?.()
        }

        callbacks.onConnected?.()
      },

      disconnected() {
        console.log('Disconnected from ImportTaskChannel')
        callbacks.onDisconnected?.()
      },

      rejected() {
        console.log('Subscription rejected')
        callbacks.onRejected?.()
      },

      received(data) {
        callbacks.onReceived?.(data)
      }
    }
  )
}

export { createImportTaskSubscription }
```

### Stimulus Controllerでの再接続処理

```javascript
// app/javascript/controllers/realtime_task_controller.js
import { Controller } from "@hotwired/stimulus"
import { createImportTaskSubscription } from "../channels/import_task_channel"

export default class extends Controller {
  static values = {
    taskId: String,
    refreshUrl: String
  }

  static targets = ["connectionStatus", "content"]

  connect() {
    this.setupSubscription()
  }

  disconnect() {
    this.subscription?.unsubscribe()
  }

  setupSubscription() {
    this.subscription = createImportTaskSubscription(this.taskIdValue, {
      onConnected: () => this.showConnected(),
      onDisconnected: () => this.showDisconnected(),
      onReconnected: () => this.handleReconnection(),
      onReceived: (data) => this.handleUpdate(data),
      onRejected: () => this.handleRejected()
    })
  }

  showConnected() {
    if (this.hasConnectionStatusTarget) {
      this.connectionStatusTarget.textContent = '接続中'
      this.connectionStatusTarget.classList.remove('disconnected')
      this.connectionStatusTarget.classList.add('connected')
    }
  }

  showDisconnected() {
    if (this.hasConnectionStatusTarget) {
      this.connectionStatusTarget.textContent = '再接続中...'
      this.connectionStatusTarget.classList.remove('connected')
      this.connectionStatusTarget.classList.add('disconnected')
    }
  }

  async handleReconnection() {
    // 再接続時に最新の状態を取得
    try {
      const response = await fetch(this.refreshUrlValue, {
        headers: { 'Accept': 'text/vnd.turbo-stream.html' }
      })

      if (response.ok) {
        const html = await response.text()
        Turbo.renderStreamMessage(html)
      }
    } catch (error) {
      console.error('Failed to refresh state after reconnection:', error)
    }

    this.showConnected()
  }

  handleRejected() {
    // サブスクリプションが拒否された場合（認証エラーなど）
    console.error('Subscription rejected')
    // 必要に応じてユーザーに通知
  }

  handleUpdate(data) {
    // リアルタイム更新の処理
    console.log('Received update:', data)
  }
}
```

### 接続状態のVisibility対応

ページがバックグラウンドになった際の処理：

```javascript
// app/javascript/controllers/visibility_aware_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { refreshUrl: String }

  connect() {
    this.boundHandleVisibilityChange = this.handleVisibilityChange.bind(this)
    document.addEventListener('visibilitychange', this.boundHandleVisibilityChange)
  }

  disconnect() {
    document.removeEventListener('visibilitychange', this.boundHandleVisibilityChange)
  }

  async handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      // ページがアクティブになった時に状態を更新
      await this.refreshState()
    }
  }

  async refreshState() {
    try {
      const response = await fetch(this.refreshUrlValue, {
        headers: { 'Accept': 'text/vnd.turbo-stream.html' }
      })

      if (response.ok) {
        const html = await response.text()
        Turbo.renderStreamMessage(html)
      }
    } catch (error) {
      console.error('Failed to refresh state:', error)
    }
  }
}
```

## エラーハンドリング

### Turboイベントによるエラーハンドリング

```javascript
// app/javascript/controllers/turbo_error_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["errorContainer"]

  connect() {
    // Turbo フォーム送信エラー
    document.addEventListener('turbo:submit-end', this.handleSubmitEnd.bind(this))

    // Turbo フェッチエラー
    document.addEventListener('turbo:fetch-request-error', this.handleFetchError.bind(this))

    // Turbo Frame読み込みエラー
    document.addEventListener('turbo:frame-missing', this.handleFrameMissing.bind(this))
  }

  disconnect() {
    document.removeEventListener('turbo:submit-end', this.handleSubmitEnd.bind(this))
    document.removeEventListener('turbo:fetch-request-error', this.handleFetchError.bind(this))
    document.removeEventListener('turbo:frame-missing', this.handleFrameMissing.bind(this))
  }

  handleSubmitEnd(event) {
    const { fetchResponse } = event.detail

    if (!fetchResponse.succeeded) {
      this.showError(`送信エラー: ${fetchResponse.statusCode}`)

      // 422 Unprocessable Entity の場合はバリデーションエラー
      if (fetchResponse.statusCode === 422) {
        // バリデーションエラーはTurbo Streamで処理される想定
        return
      }

      // サーバーエラーの場合
      if (fetchResponse.statusCode >= 500) {
        this.showError('サーバーエラーが発生しました。しばらく待ってから再試行してください。')
      }
    }
  }

  handleFetchError(event) {
    console.error('Turbo fetch error:', event)
    this.showError('通信エラーが発生しました。ネットワーク接続を確認してください。')

    // デフォルトのエラー処理を防ぐ
    event.preventDefault()
  }

  handleFrameMissing(event) {
    const { response } = event.detail
    console.error('Turbo frame missing:', event)

    // フレームが見つからない場合の処理
    this.showError('ページの一部を読み込めませんでした。')

    // 必要に応じてフルページリロード
    // event.detail.visit(response.url)
  }

  showError(message) {
    if (this.hasErrorContainerTarget) {
      this.errorContainerTarget.textContent = message
      this.errorContainerTarget.classList.remove('hidden')

      // 一定時間後に非表示
      setTimeout(() => {
        this.errorContainerTarget.classList.add('hidden')
      }, 5000)
    } else {
      // フォールバック：アラート表示
      alert(message)
    }
  }
}
```

### グローバルエラーハンドリング

```javascript
// app/javascript/application.js
import { Turbo } from "@hotwired/turbo-rails"

// グローバルなTurboエラーハンドリング
document.addEventListener('turbo:fetch-request-error', (event) => {
  const { request, error } = event.detail

  console.error('Global Turbo fetch error:', error)

  // ネットワークエラーの場合
  if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
    showGlobalNotification('ネットワーク接続を確認してください', 'error')
    event.preventDefault()
  }
})

// ActionCableの接続エラー
window.addEventListener('online', () => {
  showGlobalNotification('オンラインに復帰しました', 'success')
})

window.addEventListener('offline', () => {
  showGlobalNotification('オフラインです', 'warning')
})

function showGlobalNotification(message, type) {
  const container = document.getElementById('global-notifications')
  if (!container) return

  const notification = document.createElement('div')
  notification.className = `notification notification-${type}`
  notification.textContent = message

  container.appendChild(notification)

  setTimeout(() => notification.remove(), 5000)
}
```

### リトライ機能付きのfetch

```javascript
// app/javascript/utils/fetch_with_retry.js
export async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  const { retryDelay = 1000, retryMultiplier = 2 } = options

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options)

      // リトライ可能なエラー
      if (response.status === 503 || response.status === 429) {
        if (attempt < maxRetries) {
          const delay = retryDelay * Math.pow(retryMultiplier, attempt)
          console.log(`Retrying in ${delay}ms...`)
          await sleep(delay)
          continue
        }
      }

      return response
    } catch (error) {
      // ネットワークエラーの場合はリトライ
      if (attempt < maxRetries && error.name === 'TypeError') {
        const delay = retryDelay * Math.pow(retryMultiplier, attempt)
        console.log(`Network error, retrying in ${delay}ms...`)
        await sleep(delay)
        continue
      }

      throw error
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
```

### バリデーションエラーの表示

```erb
<%# app/views/import_tasks/_form.html.erb %>
<%= form_with model: @import_task,
              data: { controller: "form-validation", turbo: true } do |f| %>

  <div id="import_task_errors" data-form-validation-target="errors">
    <% if @import_task.errors.any? %>
      <div class="error-summary">
        <h4><%= pluralize(@import_task.errors.count, "error") %> が発生しました:</h4>
        <ul>
          <% @import_task.errors.full_messages.each do |message| %>
            <li><%= message %></li>
          <% end %>
        </ul>
      </div>
    <% end %>
  </div>

  <!-- フォームフィールド -->
<% end %>
```

```ruby
# app/controllers/import_tasks_controller.rb
class ImportTasksController < ApplicationController
  def create
    @import_task = ImportTask.new(import_task_params)

    if @import_task.save
      ImportJob.perform_later(@import_task.id)

      respond_to do |format|
        format.turbo_stream {
          render turbo_stream: turbo_stream.replace(
            "import_task_form",
            partial: "import_tasks/processing",
            locals: { task: @import_task }
          )
        }
        format.html { redirect_to @import_task }
      end
    else
      respond_to do |format|
        format.turbo_stream {
          render turbo_stream: turbo_stream.replace(
            "import_task_errors",
            partial: "import_tasks/errors",
            locals: { task: @import_task }
          ), status: :unprocessable_entity
        }
        format.html { render :new, status: :unprocessable_entity }
      end
    end
  end
end
```

## 実装例：ファイルインポート機能

### 完全な実装例

```erb
<%# app/views/imports/new.html.erb %>
<div data-controller="import-task visibility-aware turbo-error"
     data-visibility-aware-refresh-url-value="<%= import_path(@import) if @import&.persisted? %>">

  <div id="global-notifications"></div>

  <div data-turbo-error-target="errorContainer" class="error-container hidden"></div>

  <turbo-frame id="import_form">
    <%= render "form", import: @import %>
  </turbo-frame>

  <% if @import&.persisted? %>
    <div id="import_<%= @import.id %>_status"
         data-controller="realtime-task"
         data-realtime-task-task-id-value="<%= @import.id %>"
         data-realtime-task-refresh-url-value="<%= import_status_path(@import) %>">

      <%= turbo_stream_from "import_#{@import.id}" %>

      <div data-realtime-task-target="connectionStatus" class="connection-status">
        接続中
      </div>

      <div data-realtime-task-target="content">
        <%= render "status", import: @import %>
      </div>
    </div>
  <% end %>
</div>
```

```javascript
// app/javascript/controllers/import_task_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["form", "fileInput", "submitButton", "progress"]
  static values = {
    maxFileSize: { type: Number, default: 10 * 1024 * 1024 }, // 10MB
    allowedTypes: { type: Array, default: ['text/csv', 'application/vnd.ms-excel'] }
  }

  validateFile(event) {
    const file = this.fileInputTarget.files[0]

    if (!file) return

    // ファイルサイズチェック
    if (file.size > this.maxFileSizeValue) {
      this.showValidationError('ファイルサイズが大きすぎます（最大10MB）')
      this.fileInputTarget.value = ''
      event.preventDefault()
      return false
    }

    // ファイルタイプチェック
    if (!this.allowedTypesValue.includes(file.type)) {
      this.showValidationError('CSVファイルを選択してください')
      this.fileInputTarget.value = ''
      event.preventDefault()
      return false
    }

    return true
  }

  submit(event) {
    if (!this.validateFile(event)) return

    this.submitButtonTarget.disabled = true
    this.submitButtonTarget.textContent = 'アップロード中...'
  }

  showValidationError(message) {
    // エラー表示
    const errorDiv = document.createElement('div')
    errorDiv.className = 'validation-error'
    errorDiv.textContent = message
    this.formTarget.prepend(errorDiv)

    setTimeout(() => errorDiv.remove(), 5000)
  }
}
```

## リファレンス

### 公式ドキュメント

- [Turbo Handbook](https://turbo.hotwired.dev/handbook/introduction)
- [Stimulus Handbook](https://stimulus.hotwired.dev/handbook/introduction)
- [Action Cable Overview - Rails Guides](https://guides.rubyonrails.org/action_cable_overview.html)
- [Turbo Rails Documentation](https://github.com/hotwired/turbo-rails)

### Turbo関連

- [Turbo Streams](https://turbo.hotwired.dev/handbook/streams)
- [Turbo Frames](https://turbo.hotwired.dev/handbook/frames)
- [Turbo Drive](https://turbo.hotwired.dev/handbook/drive)

### ActionCable関連

- [ActionCable JavaScript API](https://guides.rubyonrails.org/action_cable_overview.html#client-side-components)
- [Broadcasting in Action Cable](https://guides.rubyonrails.org/action_cable_overview.html#broadcasting)

### パターンとベストプラクティス

- [Hotwire Cookbook](https://www.hotrails.dev/)
- [Better Stimulus](https://www.betterstimulus.com/)
