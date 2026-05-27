# DP-007: 認証 IaaS 差し替え可能設計の抽象（契約）
# 契約の根拠: firebase-auth-setup スキル「実装契約（言語非依存）」
module Auth
  AuthUser = Struct.new(:uid, :email, :provider, :claims, keyword_init: true)

  class Error < StandardError; end
  class InvalidToken < Error; end

  class Adapter
    def verify_token(_id_token); raise NotImplementedError; end
    def get_user(_uid);          raise NotImplementedError; end
    def delete_user(_uid);       raise NotImplementedError; end # 冪等
    def revoke(_uid);            raise NotImplementedError; end
  end
end
