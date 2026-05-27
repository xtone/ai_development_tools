# アダプタ選択（DP-007 差し替え可能設計）
#   AUTH_ADAPTER=firebase | test
#   既定: Rails.env.test? なら test、それ以外は firebase
module AppAuth
  def self.adapter
    @adapter ||= begin
      kind = ENV.fetch("AUTH_ADAPTER", Rails.env.test? ? "test" : "firebase")
      case kind
      when "test"     then Auth::TestAdapter.new
      when "firebase" then Auth::FirebaseAdapter.new
      else raise Auth::Error, "unknown AUTH_ADAPTER: #{kind}"
      end
    end
  end

  # テスト・初期化エラー再現時にリセットしたい場合に使う
  def self.reset!
    @adapter = nil
  end
end
