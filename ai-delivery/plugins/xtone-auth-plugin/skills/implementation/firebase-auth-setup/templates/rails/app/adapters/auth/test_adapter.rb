# 実 Firebase 不要のテスト用アダプタ。契約は同一（DP-007）。
# トークン書式: "test|<uid>|<email>|<provider>"（例: "test|u-1|alice@example.com|password"）
module Auth
  class TestAdapter < Adapter
    def initialize
      @store = {} # uid => AuthUser
    end

    def verify_token(id_token)
      kind, uid, email, provider = id_token.to_s.split("|", 4)
      raise Auth::InvalidToken, "bad token" if kind != "test" || uid.to_s.empty?
      user = @store[uid] ||= Auth::AuthUser.new(uid: uid, email: email, provider: provider, claims: {})
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
