# 実 Firebase 不要のテスト用アダプタ。契約は同一（DP-007）。
# トークン書式（auth_time は省略可・後方互換）:
#   "test|<uid>|<email>|<provider>"                  → auth_time = 検証時の現在時刻
#   "test|<uid>|<email>|<provider>|<auth_time_unix>" → 任意の auth_time（失効テスト等で利用）
module Auth
  class TestAdapter < Adapter
    def initialize
      @store = {} # uid => AuthUser
    end

    def verify_token(id_token)
      kind, uid, email, provider, auth_time = id_token.to_s.split("|", 5)
      raise Auth::InvalidToken, "bad token" if kind != "test" || uid.to_s.empty?
      user = @store[uid] ||= Auth::AuthUser.new(uid: uid, email: email, provider: provider, claims: {})
      # token_valid?(auth_time) の判定に使うため、claims["auth_time"] は毎回更新する。
      # nil のままだと tokens_valid_after 設定済みユーザーの失効テストが非直感的になる。
      user.claims["auth_time"] = (auth_time && !auth_time.empty? ? auth_time.to_i : Time.now.to_i)
      user
    end

    def get_user(uid)
      @store[uid] || (raise Auth::Error, "user not found")
    end

    def delete_user(uid)
      @store.delete(uid)
      true
    end

    def revoke(_uid); true; end
  end
end
