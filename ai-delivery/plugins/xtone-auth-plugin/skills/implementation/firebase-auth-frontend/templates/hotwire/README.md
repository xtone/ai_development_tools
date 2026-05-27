# firebase-auth-frontend テンプレ: Rails + Hotwire

`firebase-auth-frontend` スキルの **Rails + Hotwire 用** 最小実装テンプレ。新規 Rails アプリにファイル単位でコピーすれば、Propshaft + importmap-rails 構成で **そのまま動く状態** から始められる。

> **このテンプレが存在する理由**: references/hotwire.md の写経で `import "./controllers"` のような相対パスを書いてしまい、Propshaft が 503 を返して Stimulus が起動しない事故が発生していた（Issue #179）。テンプレを「動く構成のスナップショット」として固定し、コピーで導入できるようにする。

## 大原則: Propshaft + importmap では **bare specifier 必須**

Rails 標準の Propshaft + importmap-rails では、`<script type="importmap">` に登録された **論理名（bare specifier）だけ** をブラウザが解決できる。相対パス import はフィンガープリント無しパスを fetch しに行き、Propshaft が解決できず **503** を返す。結果:

- Stimulus が起動しない
- `data-controller="auth"` の submit ハンドラが動かない
- 認証フォームが「ボタンを押しても何も起きない」状態になる

| ❌ NG（相対パス・503） | ✅ OK（bare specifier） |
|---|---|
| `import "./controllers"` | `import "controllers"` |
| `import "./firebase_init"` | `import "auth/firebase_init"` |
| `import "../auth/client"` | `import "auth/client"` |

本テンプレの JS ファイルはすべて bare specifier に統一済み。**追加で書く Stimulus controller / 認証関連モジュールも、必ず bare specifier で書くこと**（さもなければ pin を追加する）。

## ファイル構成（コピー先）

```
app/javascript/
├── application.js                       # ← templates/hotwire/app/javascript/application.js
├── controllers/
│   ├── application.js                   # Stimulus シングルトン
│   ├── index.js                         # eagerLoadControllersFrom("controllers", ...)
│   └── auth_controller.js               # サインイン + /auth/session
└── auth/
    ├── client.js                        # AuthClient（契約実装）
    └── firebase_init.js                 # initializeApp / getAuth のシングルトン

config/
└── importmap.rb                         # pin 一覧（既存ファイルとマージ）
```

## pin と物理パスの対応表（**必ず同期させる**）

| `config/importmap.rb` の pin | 物理パス | bare specifier の例 |
|---|---|---|
| `pin "application"` | `app/javascript/application.js` | `<script type="module"><%= javascript_importmap_tags %>` 経由 |
| `pin "@hotwired/turbo-rails", to: "turbo.min.js"` | （gem 同梱） | `import "@hotwired/turbo-rails"` |
| `pin "@hotwired/stimulus", to: "stimulus.min.js"` | （gem 同梱） | `import { Application } from "@hotwired/stimulus"` |
| `pin "@hotwired/stimulus-loading", to: "stimulus-loading.js"` | （gem 同梱） | `import { eagerLoadControllersFrom } from "@hotwired/stimulus-loading"` |
| `pin_all_from "app/javascript/controllers", under: "controllers"` | `app/javascript/controllers/*.js` | `import "controllers"` / `import "controllers/auth_controller"` |
| `pin_all_from "app/javascript/auth", under: "auth"` | `app/javascript/auth/*.js` | `import "auth/client"` / `import "auth/firebase_init"` |
| `pin "firebase/app", to: "https://www.gstatic.com/firebasejs/<latest>/firebase-app.js"` | CDN | `import { initializeApp } from "firebase/app"` |
| `pin "firebase/auth", to: "https://www.gstatic.com/firebasejs/<latest>/firebase-auth.js"` | CDN | `import { signInWithEmailAndPassword } from "firebase/auth"` |

> どれかを編集したら必ず対応する側も合わせる。**「pin にあるが物理ファイルが無い」「物理ファイルはあるが pin が無い」の片側欠落が 503 の典型原因**。

## 導入手順（まっさらな Rails アプリへ）

前提: `rails new` で作成済み（Propshaft + importmap-rails が既定）。Sprockets を選んだ場合は本テンプレの対象外。

```bash
# 1. テンプレを app/ / config/ に展開
cp -R ai-delivery/plugins/xtone-auth-plugin/skills/implementation/firebase-auth-frontend/templates/hotwire/app/javascript/* app/javascript/
cat ai-delivery/plugins/xtone-auth-plugin/skills/implementation/firebase-auth-frontend/templates/hotwire/config/importmap.rb >> config/importmap.rb

# 2. firebase JS SDK のバージョンを埋める（tech-version-check の出力 delivery/version-matrix.md を参照）
#    config/importmap.rb の <latest> を実際のバージョン文字列に置換する

# 3. Firebase Web 設定をビューに注入（apiKey 等は公開前提）
#    app/views/layouts/application.html.erb の <head> 内に追加:
#      <script>
#        window.FIREBASE_CONFIG = <%= raw Rails.application.credentials.firebase.to_json %>
#      </script>

# 4. /login のビュー（最小）。auth_controller を data-controller でバインド
#    <form data-controller="auth" data-action="submit->auth#signIn">
#      <input data-auth-target="email"    type="email"    name="email">
#      <input data-auth-target="password" type="password" name="password">
#      <div   data-auth-target="flash"    hidden></div>
#      <button type="submit">サインイン</button>
#    </form>

# 5. 起動
bin/dev
```

## 受け入れ確認（Issue #179 受け入れ基準）

1. `bin/dev` で puma が立ち上がる
2. ブラウザで `http://localhost:3000/login` を開く
3. DevTools の Network タブで **`/assets/*` 系がすべて 200** （503 が無い）
4. Console に `[stimulus] application started` 等の起動ログが出る（`application.debug = true` にすると詳細）
5. `data-controller="auth"` の DOM 要素に対し `window.Stimulus.controllers` で controller インスタンスが取れる
6. メールとパスワードを入れて submit → `signIn` ハンドラが走る（Firebase 設定が正しければ実際にサインインまで完了する）

3 の段階で `app/javascript/*` の 503 が見えたら、**該当ファイルの import が bare specifier か** と **対応する pin が `config/importmap.rb` にあるか** をこの順で確認する。

## references/hotwire.md との関係

- **references/hotwire.md**: 「契約・手順・既知の制約・判断ポイント」の説明とコード片（写経用）
- **templates/hotwire/**（本ディレクトリ）: 「動く構成のスナップショット」（コピー用・ファイル単位で同期済み）

どちらの導入経路でも動くように、両者は bare specifier 統一・pin 名統一を維持する。references を更新するときは templates も同期する（その逆も）。
