# DP-007: 認証 IaaS 差し替え可能設計の共通定数（namespace 定義）
#
# Zeitwerk 規約: 「1 ファイル 1 定数」。本ファイルは `app/adapters/auth/` ディレクトリ
# の namespace `Auth` を定義する「ディレクトリと同名のファイル」であり、
# 同一 namespace に属する補助定数（AuthUser / Error / InvalidToken / NotFoundError）の
# 集約場所として規約に準拠する。
#
# `Auth::Adapter` / `Auth::FirebaseAdapter` / `Auth::TestAdapter` は別ファイル
# （`auth/adapter.rb` / `auth/firebase_adapter.rb` / `auth/test_adapter.rb`）に分離する。
module Auth
  AuthUser = Struct.new(:uid, :email, :provider, :claims, keyword_init: true)

  class Error < StandardError; end
  class InvalidToken < Error; end
  class NotFoundError < Error; end
end
