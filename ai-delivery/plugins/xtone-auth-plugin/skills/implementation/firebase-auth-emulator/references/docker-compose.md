# レシピ: Docker Compose で Auth Emulator を起動

`firebase-auth-emulator` スキルの **環境構築レシピ**。SKILL.md の接続パラメータ（`FIREBASE_AUTH_EMULATOR_HOST=host:port`、port 9099）を満たす最小構成を Docker で作る。

- 対象: Docker / docker-compose / firebase-tools — **いずれも公式の最新安定版**（バージョン方針は `ai-delivery/docs/environment-setup.md`）
- 構成: emulator サービス（`firebase-tools` 入り）＋ backend ＋ frontend を1つの compose で起動。

## 1. firebase.json（最小）

emulator のポートだけ指定。auth と UI のみ。

```json
{
  "emulators": {
    "auth": { "host": "0.0.0.0", "port": 9099 },
    "ui":   { "enabled": true, "port": 4000 }
  }
}
```

> `host: 0.0.0.0` にしておかないと、Docker コンテナ外から接続できない。

## 2. emulator サービスの Dockerfile

`firebase-tools` の公式 Docker イメージは無いため、自前で組む（Node + JRE）。最小：

```dockerfile
# emulator/Dockerfile
FROM node:22-bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
RUN npm install -g firebase-tools
WORKDIR /app
COPY firebase.json ./
EXPOSE 9099 4000
# project は何でも良い（emulator 内で完結）。auth のみ起動。
CMD ["firebase", "emulators:start", "--only", "auth", "--project", "demo-telemed"]
```

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
