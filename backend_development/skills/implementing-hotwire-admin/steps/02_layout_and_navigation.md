# ステップ2: レイアウトとナビゲーション

## 目次

- [概要](#概要)
- [レイアウトファイルの作成](#レイアウトファイルの作成)
- [サイドバーナビゲーション](#サイドバーナビゲーション)
- [フラッシュメッセージ](#フラッシュメッセージ)
- [レスポンシブ対応](#レスポンシブ対応)

---

## 概要

管理画面専用のレイアウトファイルとナビゲーションを作成します。Tailwind CSSを使用したモダンなUIを構築します。

## レイアウトファイルの作成

`app/views/layouts/admin.html.erb`:

```erb
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>管理画面 | <%= content_for(:title) || 'ダッシュボード' %></title>
  <%= csrf_meta_tags %>
  <%= csp_meta_tag %>
  <%= stylesheet_link_tag 'tailwind', 'inter-font', 'data-turbo-track': 'reload' %>
  <%= javascript_importmap_tags %>
</head>
<body class="bg-gray-100">
  <div class="flex h-screen overflow-hidden">
    <!-- サイドバー -->
    <%= render 'layouts/admin/sidebar' %>

    <!-- メインコンテンツ -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- ヘッダー -->
      <%= render 'layouts/admin/header' %>

      <!-- コンテンツエリア -->
      <main class="flex-1 overflow-y-auto p-6">
        <!-- フラッシュメッセージ -->
        <%= render 'layouts/admin/flash' %>

        <!-- パンくずリスト -->
        <% if content_for?(:breadcrumbs) %>
          <nav class="mb-4" aria-label="Breadcrumb">
            <%= yield :breadcrumbs %>
          </nav>
        <% end %>

        <!-- ページコンテンツ -->
        <%= yield %>
      </main>
    </div>
  </div>
</body>
</html>
```

## サイドバーナビゲーション

`app/views/layouts/admin/_sidebar.html.erb`:

```erb
<aside class="w-64 bg-gray-800 text-white flex-shrink-0" data-testid="admin-sidebar">
  <!-- ロゴ -->
  <div class="h-16 flex items-center justify-center border-b border-gray-700">
    <%= link_to admin_root_path, class: 'text-xl font-bold text-white hover:text-gray-300' do %>
      管理画面
    <% end %>
  </div>

  <!-- ナビゲーション -->
  <nav class="p-4">
    <ul class="space-y-2">
      <%= render 'layouts/admin/nav_item', path: admin_root_path, icon: 'home', label: 'ダッシュボード', testid: 'nav-dashboard' %>
      <%= render 'layouts/admin/nav_item', path: admin_users_path, icon: 'users', label: 'ユーザー', testid: 'nav-users' %>
      <%= render 'layouts/admin/nav_item', path: admin_projects_path, icon: 'folder', label: 'プロジェクト', testid: 'nav-projects' %>
      <%= render 'layouts/admin/nav_item', path: admin_reports_path, icon: 'document', label: '日報', testid: 'nav-reports' %>
      <%= render 'layouts/admin/nav_item', path: admin_estimates_path, icon: 'calculator', label: '見積書', testid: 'nav-estimates' %>
      <%= render 'layouts/admin/nav_item', path: admin_bills_path, icon: 'receipt', label: '請求書', testid: 'nav-bills' %>
      <%= render 'layouts/admin/nav_item', path: admin_user_roles_path, icon: 'shield', label: '権限管理', testid: 'nav-roles' %>
      <%= render 'layouts/admin/nav_item', path: admin_csvs_path, icon: 'download', label: 'CSV出力', testid: 'nav-csvs' %>
    </ul>
  </nav>

  <!-- フッター -->
  <div class="absolute bottom-0 w-64 p-4 border-t border-gray-700">
    <%= link_to root_path, class: 'flex items-center text-gray-300 hover:text-white', data: { testid: 'back-to-app' } do %>
      <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
      </svg>
      アプリに戻る
    <% end %>
  </div>
</aside>
```

`app/views/layouts/admin/_nav_item.html.erb`:

```erb
<%# locals: (path:, icon:, label:, testid:) %>
<li>
  <%= link_to path,
      class: "flex items-center px-4 py-2 rounded-md transition-colors #{current_page?(path) ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}",
      data: { testid: testid } do %>
    <%= render "layouts/admin/icons/#{icon}" %>
    <span class="ml-3"><%= label %></span>
  <% end %>
</li>
```

## ヘッダー

`app/views/layouts/admin/_header.html.erb`:

```erb
<header class="h-16 bg-white shadow-sm flex items-center justify-between px-6">
  <div>
    <h1 class="text-xl font-semibold text-gray-800">
      <%= content_for?(:page_title) ? yield(:page_title) : 'ダッシュボード' %>
    </h1>
  </div>

  <div class="flex items-center space-x-4">
    <!-- ユーザー情報 -->
    <span class="text-gray-600"><%= current_user.name %></span>

    <!-- ログアウト -->
    <%= button_to 'ログアウト',
        destroy_user_session_path,
        method: :delete,
        class: 'text-gray-600 hover:text-gray-800',
        data: { testid: 'logout-button' } %>
  </div>
</header>
```

## フラッシュメッセージ

`app/views/layouts/admin/_flash.html.erb`:

```erb
<% flash.each do |type, message| %>
  <%
    base_classes = 'mb-4 px-4 py-3 rounded-md flex items-center justify-between'
    type_classes = case type.to_sym
                   when :notice, :success
                     'bg-green-50 text-green-800 border border-green-200'
                   when :alert, :error
                     'bg-red-50 text-red-800 border border-red-200'
                   when :warning
                     'bg-yellow-50 text-yellow-800 border border-yellow-200'
                   else
                     'bg-blue-50 text-blue-800 border border-blue-200'
                   end
  %>
  <div class="<%= base_classes %> <%= type_classes %>"
       data-controller="flash"
       data-flash-auto-dismiss-value="true"
       data-testid="flash-<%= type %>">
    <span><%= message %></span>
    <button type="button"
            class="text-current opacity-50 hover:opacity-100"
            data-action="flash#dismiss">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
      </svg>
    </button>
  </div>
<% end %>
```

## レスポンシブ対応

### モバイルメニュー用Stimulusコントローラ

`app/javascript/controllers/mobile_menu_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["sidebar", "overlay"]
  static values = { open: Boolean }

  toggle() {
    this.openValue = !this.openValue
  }

  close() {
    this.openValue = false
  }

  openValueChanged() {
    if (this.openValue) {
      this.sidebarTarget.classList.remove('-translate-x-full')
      this.overlayTarget.classList.remove('hidden')
    } else {
      this.sidebarTarget.classList.add('-translate-x-full')
      this.overlayTarget.classList.add('hidden')
    }
  }
}
```

### レスポンシブレイアウト

```erb
<body class="bg-gray-100" data-controller="mobile-menu">
  <!-- モバイルオーバーレイ -->
  <div class="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden hidden"
       data-mobile-menu-target="overlay"
       data-action="click->mobile-menu#close"></div>

  <div class="flex h-screen overflow-hidden">
    <!-- サイドバー（モバイルではスライドイン） -->
    <aside class="fixed lg:static inset-y-0 left-0 z-30 w-64 bg-gray-800 text-white transform -translate-x-full lg:translate-x-0 transition-transform duration-300 ease-in-out"
           data-mobile-menu-target="sidebar">
      <!-- サイドバー内容 -->
    </aside>

    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- モバイルヘッダー -->
      <header class="lg:hidden h-16 bg-white shadow-sm flex items-center px-4">
        <button type="button"
                class="p-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                data-action="mobile-menu#toggle">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
        <span class="ml-4 text-lg font-semibold">管理画面</span>
      </header>

      <!-- メインコンテンツ -->
      <main class="flex-1 overflow-y-auto p-4 lg:p-6">
        <%= yield %>
      </main>
    </div>
  </div>
</body>
```

## アイコンSVG

`app/views/layouts/admin/icons/_home.html.erb`:

```erb
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
</svg>
```

`app/views/layouts/admin/icons/_users.html.erb`:

```erb
<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
</svg>
```

## 次のステップ

CRUD画面の実装に進みます → @steps/03_crud_views.md
