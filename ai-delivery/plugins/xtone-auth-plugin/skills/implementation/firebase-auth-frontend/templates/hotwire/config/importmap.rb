# config/importmap.rb
#
# Propshaft + importmap-rails 前提。app/javascript/ 配下を bare specifier で
# 参照するための pin 一覧。templates/hotwire/app/javascript/ のディレクトリ構成と
# 1:1 で対応している（どちらかだけ変えると Propshaft が解決できず 503 になる）。
#
# <latest> は固定値ではなく、tech-version-check で取得した公式最新安定版を埋める。
# 案件で特定バージョン固定が必要な場合は判断ポイント（docs/pending-decisions.md）に起票。

# Rails / Hotwire の基本セット
pin "application"
pin "@hotwired/turbo-rails", to: "turbo.min.js"
pin "@hotwired/stimulus",    to: "stimulus.min.js"
pin "@hotwired/stimulus-loading", to: "stimulus-loading.js"

# controllers/ 配下を "controllers/<name>_controller" として登録
#   → import "controllers" / "controllers/auth_controller"
pin_all_from "app/javascript/controllers", under: "controllers"

# auth/ 配下を "auth/<file>" として登録
#   → import "auth/client" / "auth/firebase_init"
pin_all_from "app/javascript/auth", under: "auth"

# Firebase JS SDK（v9+ modular CDN）
#   → import { ... } from "firebase/app" / "firebase/auth"
pin "firebase/app",  to: "https://www.gstatic.com/firebasejs/<latest>/firebase-app.js"
pin "firebase/auth", to: "https://www.gstatic.com/firebasejs/<latest>/firebase-auth.js"
