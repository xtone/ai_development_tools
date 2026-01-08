# ステップ5: Stimulusコントローラ

## 目次

- [概要](#概要)
- [フラッシュメッセージ](#フラッシュメッセージ)
- [確認ダイアログ](#確認ダイアログ)
- [動的フォーム](#動的フォーム)
- [ファイルアップロードプレビュー](#ファイルアップロードプレビュー)
- [検索フォーム](#検索フォーム)

---

## 概要

Stimulusを使用して、管理画面で必要なインタラクティブな機能を実装します。

## フラッシュメッセージ

自動消去とクローズボタン付きのフラッシュメッセージ：

`app/javascript/controllers/flash_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = {
    autoDismiss: { type: Boolean, default: true },
    dismissAfter: { type: Number, default: 5000 }
  }

  connect() {
    if (this.autoDismissValue) {
      this.timeout = setTimeout(() => {
        this.dismiss()
      }, this.dismissAfterValue)
    }
  }

  disconnect() {
    if (this.timeout) {
      clearTimeout(this.timeout)
    }
  }

  dismiss() {
    this.element.classList.add('opacity-0', 'transition-opacity', 'duration-300')
    setTimeout(() => {
      this.element.remove()
    }, 300)
  }
}
```

使用例：

```erb
<div class="bg-green-50 border border-green-200 rounded-md p-4"
     data-controller="flash"
     data-flash-auto-dismiss-value="true"
     data-flash-dismiss-after-value="5000">
  <div class="flex items-center justify-between">
    <span>保存しました</span>
    <button type="button" data-action="flash#dismiss" class="text-green-600 hover:text-green-800">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
      </svg>
    </button>
  </div>
</div>
```

## 確認ダイアログ

カスタムスタイルの確認ダイアログ：

`app/javascript/controllers/confirm_dialog_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = {
    title: { type: String, default: '確認' },
    message: String,
    confirmText: { type: String, default: '実行' },
    cancelText: { type: String, default: 'キャンセル' },
    confirmClass: { type: String, default: 'bg-blue-600 hover:bg-blue-700' }
  }

  confirm(event) {
    event.preventDefault()

    const dialog = document.createElement('div')
    dialog.className = 'fixed inset-0 z-50 flex items-center justify-center'
    dialog.innerHTML = `
      <div class="fixed inset-0 bg-black bg-opacity-50" data-action="click->confirm-dialog#cancel"></div>
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 z-10">
        <div class="px-6 py-4 border-b">
          <h3 class="text-lg font-medium text-gray-900">${this.titleValue}</h3>
        </div>
        <div class="px-6 py-4">
          <p class="text-gray-600">${this.messageValue}</p>
        </div>
        <div class="px-6 py-4 bg-gray-50 flex justify-end space-x-3 rounded-b-lg">
          <button type="button" class="px-4 py-2 text-gray-700 hover:text-gray-900 cancel-btn">
            ${this.cancelTextValue}
          </button>
          <button type="button" class="px-4 py-2 text-white rounded-md confirm-btn ${this.confirmClassValue}">
            ${this.confirmTextValue}
          </button>
        </div>
      </div>
    `

    document.body.appendChild(dialog)

    dialog.querySelector('.cancel-btn').addEventListener('click', () => {
      dialog.remove()
    })

    dialog.querySelector('.confirm-btn').addEventListener('click', () => {
      dialog.remove()
      // フォームの場合はsubmit、リンクの場合はナビゲート
      if (this.element.tagName === 'FORM') {
        this.element.requestSubmit()
      } else if (this.element.href) {
        window.location.href = this.element.href
      }
    })

    // ESCキーでキャンセル
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        dialog.remove()
        document.removeEventListener('keydown', handleEscape)
      }
    }
    document.addEventListener('keydown', handleEscape)
  }

  cancel() {
    this.element.closest('[data-controller="confirm-dialog"]')?.remove()
  }
}
```

## 動的フォーム

### 条件付きフィールド表示

`app/javascript/controllers/conditional_fields_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["trigger", "conditional"]
  static values = {
    showWhen: String
  }

  connect() {
    this.toggle()
  }

  toggle() {
    const triggerValue = this.triggerTarget.value
    const shouldShow = triggerValue === this.showWhenValue

    this.conditionalTargets.forEach(el => {
      if (shouldShow) {
        el.classList.remove('hidden')
        el.querySelectorAll('input, select, textarea').forEach(input => {
          input.disabled = false
        })
      } else {
        el.classList.add('hidden')
        el.querySelectorAll('input, select, textarea').forEach(input => {
          input.disabled = true
        })
      }
    })
  }
}
```

使用例：

```erb
<div data-controller="conditional-fields" data-conditional-fields-show-when-value="other">
  <div>
    <%= f.label :category %>
    <%= f.select :category, [['通常', 'normal'], ['特別', 'special'], ['その他', 'other']],
        {}, data: { conditional_fields_target: 'trigger', action: 'conditional-fields#toggle' } %>
  </div>

  <div data-conditional-fields-target="conditional" class="hidden">
    <%= f.label :category_other, 'その他の詳細' %>
    <%= f.text_field :category_other %>
  </div>
</div>
```

### 動的項目追加

`app/javascript/controllers/nested_form_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["template", "container"]
  static values = {
    index: Number
  }

  connect() {
    this.indexValue = this.containerTarget.children.length
  }

  add(event) {
    event.preventDefault()
    const content = this.templateTarget.innerHTML.replace(/NEW_RECORD/g, this.indexValue)
    this.containerTarget.insertAdjacentHTML('beforeend', content)
    this.indexValue++
  }

  remove(event) {
    event.preventDefault()
    const item = event.target.closest('[data-nested-form-item]')

    // 既存レコードの場合は_destroy=1をセット
    const destroyInput = item.querySelector('[data-destroy-field]')
    if (destroyInput) {
      destroyInput.value = '1'
      item.classList.add('hidden')
    } else {
      item.remove()
    }
  }
}
```

## ファイルアップロードプレビュー

`app/javascript/controllers/file_preview_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input", "preview", "placeholder"]

  preview() {
    const file = this.inputTarget.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      if (this.hasPlaceholderTarget) {
        this.placeholderTarget.classList.add('hidden')
      }

      if (file.type.startsWith('image/')) {
        this.previewTarget.innerHTML = `
          <img src="${e.target.result}" class="max-h-48 rounded-lg" alt="Preview">
        `
      } else {
        this.previewTarget.innerHTML = `
          <div class="flex items-center space-x-2 text-gray-600">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <span>${file.name}</span>
          </div>
        `
      }
      this.previewTarget.classList.remove('hidden')
    }
    reader.readAsDataURL(file)
  }
}
```

使用例：

```erb
<div data-controller="file-preview">
  <label class="block">
    <span class="text-sm font-medium text-gray-700">画像</span>
    <div class="mt-1">
      <%= f.file_field :image,
          accept: 'image/*',
          class: 'hidden',
          data: { file_preview_target: 'input', action: 'file-preview#preview' } %>
      <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-gray-400"
           data-file-preview-target="placeholder"
           onclick="this.previousElementSibling.click()">
        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p class="mt-2 text-sm text-gray-600">クリックして画像を選択</p>
      </div>
    </div>
  </label>
  <div data-file-preview-target="preview" class="mt-4 hidden"></div>
</div>
```

## 検索フォーム

デバウンス付きリアルタイム検索：

`app/javascript/controllers/search_form_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input"]
  static values = {
    debounce: { type: Number, default: 300 }
  }

  connect() {
    this.timeout = null
  }

  search() {
    clearTimeout(this.timeout)
    this.timeout = setTimeout(() => {
      this.element.requestSubmit()
    }, this.debounceValue)
  }

  reset() {
    this.inputTarget.value = ''
    this.element.requestSubmit()
  }
}
```

使用例：

```erb
<%= form_with url: admin_users_path, method: :get,
    data: { controller: 'search-form', turbo_frame: 'users-table' } do |f| %>
  <div class="relative">
    <%= f.text_field :q,
        value: params[:q],
        placeholder: '検索...',
        class: 'w-full pl-10 pr-10 rounded-md border-gray-300',
        data: { search_form_target: 'input', action: 'input->search-form#search' } %>
    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
      <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
      </svg>
    </div>
    <% if params[:q].present? %>
      <button type="button"
              class="absolute inset-y-0 right-0 pr-3 flex items-center"
              data-action="search-form#reset">
        <svg class="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    <% end %>
  </div>
<% end %>
```

## 次のステップ

E2Eテスト設計に進みます → @steps/06_e2e_test_design.md
