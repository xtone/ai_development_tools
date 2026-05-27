# JWT 認可 concern。契約の根拠: firebase-auth-setup スキル + references/rails.md
#   - authenticate!: トークン検証で current_auth_user を確立。
#                    current_user は「ローカル DB に登録済みなら」のみ設定（初回ログインは nil）。
#   - require_registered_user!: 登録済みユーザー必須のエンドポイントで before_action として併用。
#                               セッション確立コントローラ（upsert する側）には付けない。
module Authenticatable
  extend ActiveSupport::Concern

  included do
    before_action :authenticate!
    attr_reader :current_user, :current_auth_user
  end

  private

  def authenticate!
    token = request.headers["Authorization"].to_s.delete_prefix("Bearer ")
    return render(json: { error: "no token" }, status: :unauthorized) if token.blank?

    @current_auth_user = AppAuth.adapter.verify_token(token)
    @current_user = User.active.find_by(uid: @current_auth_user.uid)

    # 失効判定は DB 参照のみ（毎リクエスト HTTP を叩かない）
    if @current_user && !@current_user.token_valid?(@current_auth_user.claims["auth_time"])
      render(json: { error: "token revoked" }, status: :unauthorized)
    end
  rescue Auth::InvalidToken => e
    render json: { error: e.message }, status: :unauthorized
  end

  def require_registered_user!
    return if @current_user
    render json: { error: "user not found" }, status: :unauthorized
  end
end
