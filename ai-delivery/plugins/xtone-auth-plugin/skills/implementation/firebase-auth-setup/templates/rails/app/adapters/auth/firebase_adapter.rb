# DP-007 Firebase 実装。契約の根拠: firebase-auth-setup スキル + references/rails.md
require "jwt"
require "googleauth"
require "net/http"
require "json"
require "openssl"
require "stringio"

module Auth
  class FirebaseAdapter < Adapter
    CERTS_URI = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com".freeze

    def initialize(project_id: ENV["FIREBASE_PROJECT_ID"])
      @project_id = project_id.to_s
      raise Auth::Error, "FIREBASE_PROJECT_ID が未設定です" if @project_id.empty?
      @cache = nil  # 公開鍵キャッシュ（{pem:, expires_at:}）— 初回 certs() で fetch
      @token = nil  # OAuth2 アクセストークンキャッシュ（{value:, expires_at:}）— 初回 access_token() で fetch
    end

    def verify_token(id_token)
      decoded, _ = JWT.decode(
        id_token, nil, true,
        algorithms: ["RS256"],
        iss: "https://securetoken.google.com/#{@project_id}", verify_iss: true,
        aud: @project_id, verify_aud: true,
        verify_expiration: true, verify_iat: true
      ) { |h| public_key_for(h["kid"]) }

      # Firebase 検証要件: uid (sub) が非空
      raise Auth::InvalidToken, "empty sub" if decoded["sub"].to_s.empty?

      Auth::AuthUser.new(
        uid: decoded["sub"],
        email: decoded["email"],
        provider: decoded.dig("firebase", "sign_in_provider"),
        claims: decoded
      )
    rescue JWT::DecodeError, OpenSSL::X509::CertificateError => e
      raise Auth::InvalidToken, e.message
    end

    def get_user(uid)
      res = identitytoolkit_post("accounts:lookup", localId: [uid])
      user = res.dig("users", 0)
      raise Auth::Error, "user not found" unless user
      Auth::AuthUser.new(
        uid: user["localId"],
        email: user["email"],
        provider: user.dig("providerUserInfo", 0, "providerId"),
        claims: user
      )
    end

    # 冪等: 既に存在しなくても成功扱い
    def delete_user(uid)
      identitytoolkit_post("accounts:delete", localId: uid)
      true
    rescue Auth::NotFoundError
      true
    end

    # IaaS の refresh トークン失効（hard / soft どちらの呼び出し元からも使う）
    def revoke(uid)
      identitytoolkit_post("accounts:update", localId: uid, validSince: Time.now.to_i.to_s)
      true
    rescue Auth::NotFoundError
      true
    end

    private

    # Cache-Control: max-age に従って証明書をキャッシュ。kid 不一致時は強制再取得（ローテーション追従）
    def certs
      return @cache[:pem] if @cache && Time.now < @cache[:expires_at]
      res = Net::HTTP.get_response(URI(CERTS_URI))
      raise Auth::Error, "failed to fetch Firebase certs: #{res.code} #{res.message}" unless res.is_a?(Net::HTTPSuccess)
      ttl = res["cache-control"].to_s[/max-age=(\d+)/, 1]&.to_i || 3600
      @cache = { pem: JSON.parse(res.body), expires_at: Time.now + ttl }
      @cache[:pem]
    end

    def public_key_for(kid)
      pem = certs[kid]
      unless pem
        # kid 不一致は強制再取得（ローテーション追従）
        @cache = nil
        pem = certs[kid]
      end
      raise Auth::InvalidToken, "unknown kid" unless pem
      OpenSSL::X509::Certificate.new(pem).public_key
    end

    # サービスアカウント鍵 → OAuth2 アクセストークン。短命なのでキャッシュ
    def access_token
      return @token[:value] if @token && Time.now < @token[:expires_at]
      cred = Google::Auth::ServiceAccountCredentials.make_creds(
        json_key_io: StringIO.new(File.read(ENV.fetch("GOOGLE_APPLICATION_CREDENTIALS"))),
        scope: "https://www.googleapis.com/auth/identitytoolkit"
      )
      t = cred.fetch_access_token!
      @token = { value: t["access_token"], expires_at: Time.now + t["expires_in"].to_i - 30 }
      @token[:value]
    end

    def identitytoolkit_post(method, **body)
      uri = URI("https://identitytoolkit.googleapis.com/v1/projects/#{@project_id}/#{method}")
      req = Net::HTTP::Post.new(uri)
      req["Authorization"] = "Bearer #{access_token}"
      req["Content-Type"]  = "application/json"
      req.body = JSON.dump(body)
      res = Net::HTTP.start(uri.host, uri.port, use_ssl: true) { |h| h.request(req) }
      raise Auth::NotFoundError if res.code == "404"
      raise Auth::Error, "identitytoolkit #{method}: #{res.code}" unless res.is_a?(Net::HTTPSuccess)
      res.body.to_s.empty? ? {} : JSON.parse(res.body)
    end
  end
end
