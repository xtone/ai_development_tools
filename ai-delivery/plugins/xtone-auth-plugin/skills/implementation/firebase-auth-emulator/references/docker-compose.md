# レシピ: Docker Compose で Auth Emulator を起動

`firebase-auth-emulator` スキルの **環境構築レシピ**。SKILL.md の接続パラメータ（`FIREBASE_AUTH_EMULATOR_HOST=host:port`、port 9099）を満たす最小構成を Docker で作る。

- 対象: Docker / docker-compose / firebase-tools — **いずれも公式の最新安定版**（バージョン方針は `ai-delivery/docs/environment-setup.md`）
- 構成: emulator サービス（`firebase-tools` 入り）＋ backend ＋ frontend を1つの compose で起動。

> **前提（コンテナ内 emulator は必ず `0.0.0.0` バインド）**: `firebase.json` の `emulators.*.host` を **全サブサービス（`auth` / `ui` / `hub` / `logging`）** で `"0.0.0.0"` にすること。省略するとデフォルトは `127.0.0.1` バインドになり、Docker コンテナ外（ホスト OS のブラウザ / curl）からは **接続リセット**になる（`auth` だけ指定しても UI の `http://localhost:4000` は開けない）。詳細は SKILL.md「既知の制約」も参照。

## 1. firebase.json（最小）

emulator のポートとバインドアドレスを **全サブサービスで明示**する（前提の繰り返し: 省略不可）。

```json
{
  "emulators": {
    "auth":    { "host": "0.0.0.0", "port": 9099 },
    "ui":      { "host": "0.0.0.0", "enabled": true, "port": 4000 },
    "hub":     { "host": "0.0.0.0", "port": 4400 },
    "logging": { "host": "0.0.0.0", "port": 4500 }
  }
}
```

> `host: "0.0.0.0"` を全 emulator サブサービスで揃えないと、Docker コンテナ外から接続できない。`auth` だけ指定したパイロット案件で `http://localhost:4000`（Emulator UI）が接続リセットになりデバッグ工数を消費した実例あり。`hub`（4400）と `logging`（4500）は UI が裏で叩く管理ポート — UI を使うなら一緒に `0.0.0.0` で公開する。

## 2. emulator サービスの Dockerfile

`firebase-tools` の公式 Docker イメージは無いため、自前で組む（Node + JRE）。最小：

```dockerfile
# emulator/Dockerfile
FROM node:22-bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# firebase-tools: バージョン固定（再現性のため）。
# 採用時点の最新安定版を ARG のデフォルトに置く。更新は公式リリースで確認:
#   https://github.com/firebase/firebase-tools/releases （B-06: 数値ハードコードは避け公式最新を採る）
ARG FIREBASE_TOOLS_VERSION=14.4.0
RUN npm install -g "firebase-tools@${FIREBASE_TOOLS_VERSION}"

WORKDIR /app
COPY firebase.json ./
EXPOSE 9099 4000
# project は何でも良い（emulator 内で完結）。auth のみ起動。
CMD ["firebase", "emulators:start", "--only", "auth", "--project", "demo-telemed"]
```

> ピン留めは `docker compose build` の再現性のため。**バージョン更新は B-06 の手順に従い公式リリースを確認**して `--build-arg FIREBASE_TOOLS_VERSION=...` または ARG のデフォルトを更新する。固定値の陳腐化を避けるため、定期的に最新安定版へ追従する判断ポイント。

## 3. docker-compose.yml

```yaml
services:
  auth-emulator:
    build: ./emulator
    ports:
      - "9099:9099"   # Auth REST / SDK
      - "4000:4000"   # Emulator UI（http://localhost:4000）
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:9099"]
      interval: 5s
      timeout: 3s
      retries: 30

  backend:
    build: ./backend
    environment:
      AUTH_ADAPTER: "firebase"
      FIREBASE_PROJECT_ID: "demo-telemed"
      FIREBASE_AUTH_EMULATOR_HOST: "auth-emulator:9099"   # ★ プロトコル無しで host:port
      MFA_REQUIREMENT: "required"
    ports: ["3000:3000"]
    depends_on:
      auth-emulator:
        condition: service_healthy

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_FIREBASE_PROJECT_ID: "demo-telemed"
      NEXT_PUBLIC_FIREBASE_API_KEY: "demo-key"          # emulator は任意値で OK
      NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST: "localhost:9099"  # ブラウザは localhost:9099 へ接続
      NEXT_PUBLIC_API_BASE: "http://localhost:3000"
    ports: ["3001:3000"]
    depends_on:
      auth-emulator:
        condition: service_healthy
```

> **host の使い分け**: backend は Docker ネットワーク内なので `auth-emulator:9099`。frontend のブラウザ側コードは **ホスト OS のブラウザから** emulator に繋ぐので `localhost:9099`（コンテナ間 DNS は使えない）。NEXT_PUBLIC_ で分けるのが安全。

### Rails + Hotwire 構成（backend と frontend が同居）

Hotwire ベースの Rails アプリでは frontend を別コンテナにせず、backend サービスから ERB で window 経由でブラウザに値を渡す（[`hotwire.md`](./hotwire.md) 参照）。次のように `backend` サービスだけで完結する:

```yaml
services:
  auth-emulator:
    build: ./emulator
    ports: ["9099:9099", "4000:4000"]
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:9099"]
      interval: 5s
      timeout: 3s
      retries: 30

  rails:
    build: ./   # Rails アプリのルート（Gemfile / Dockerfile が直下）
    environment:
      AUTH_ADAPTER: "firebase"
      FIREBASE_PROJECT_ID: "demo-project"
      # Rails コンテナ内（backend 側）が emulator REST に繋ぐホスト名
      FIREBASE_AUTH_EMULATOR_HOST: "auth-emulator:9099"
      # ブラウザ（ホスト OS）が emulator に繋ぐホスト名。Rails の ERB で window に渡す
      FIREBASE_PUBLIC_EMULATOR_HOST: "localhost:9099"
      MFA_REQUIREMENT: "required"
    ports: ["3000:3000"]
    depends_on:
      auth-emulator:
        condition: service_healthy
```

> Rails 側は **2 つの ENV** を持つ点に注意（コンテナ間用 `FIREBASE_AUTH_EMULATOR_HOST` ／ ブラウザ用 `FIREBASE_PUBLIC_EMULATOR_HOST`）。両者を混同するとブラウザから繋がらない（同じ値にすると、コンテナ内の AdminClient が失敗する）。詳細は [`hotwire.md` の 1 節](./hotwire.md)。

## 4. 起動と確認

```bash
docker compose up --build
# 別ターミナルで:
curl -fsS http://localhost:9099    # emulator が起きていれば 200 系
open http://localhost:4000          # Emulator UI（mock user 管理）
```

UI の `Auth > Add User` で mock user を作成し、必要なら電話番号を設定する（SMS MFA enrollment 用）。

## 5. データの永続化（任意）

開発中は emulator を毎回作り直すと user が消える。`--import` / `--export-on-exit` で永続化できる：

```yaml
    volumes:
      - ./emulator/auth_export:/app/auth_export
    command:
      - firebase
      - emulators:start
      - --only=auth
      - --project=demo-telemed
      - --import=./auth_export
      - --export-on-exit=./auth_export
```

## 6. 既知の制約 / 注意

- `firebase-tools` 公式 Docker イメージは無い。コミュニティ製を使うこともできるが、本レシピでは自前 Dockerfile を推奨（依存が明示できる）。
- emulator は JVM ベース。JRE が必須（Dockerfile の `openjdk-17-jre-headless`）。
- emulator UI（4000）は **開発用**。プロダクションには公開しない。
- `FIREBASE_AUTH_EMULATOR_HOST` を **本番ビルドに混入させない**（プロダクションの Next.js では `NEXT_PUBLIC_*` を未設定にする）。
