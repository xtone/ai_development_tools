---
name: async-processing-best-practices
description: 非同期処理のバックエンドとフロントエンドを実装する際のベストプラクティスをまとめたスキルです。非同期処理が必要なWebサービスのフロントエンドおよびバックエンドを実装する際に利用されます。
---

# async-processing-best-practices

Webアプリケーションにおける非同期処理を実現するための実装ガイドです。

## いつ利用するか

次の場合にこのガイドラインを参照してください。

- 特定の処理を非同期で実現するかどうかを設計する場合
- 非同期処理を行うインフラを選定・設計する場合
- 非同期処理が必要なバックエンド処理を実装する場合
- 非同期処理のUIをフロントエンドで実装する場合

## リファレンス

### 非同期処理を利用するべきかどうかの判断

HTTPレスポンを返す際に処理が完了している必要がないものについては非同期処理で実現することを検討します。主に以下の観点で非同期処理の採用を考えます。

- ユーザー体験(UX)
  - 処理に1秒以上かかり、UIから実行する際に画面が操作不能になるケースを避けたい場合
- 外部依存
  - 外部APIやサービスなど、自分たちでコントロールできないものを呼び出す際に、相手側のシステムの障害や遅延に性能低下やユーザー体験の低下が発生することが懸念される場合
- 即時性の低さ
  - ユーザーが処理の結果を即座に知らなくてもいい場合
- リソースの保護
  - APIのコネクション数を長い処理によって占有して、接続リソースを不要に消費してしまうことが懸念される場合

### 非同期処理の実現手法

以下の要素から実現手法を選択します

- Webアプリケーションをホスティングするインフラ環境
- Webアプリケーション実装に利用するフレームワーク・ミドルウェア
- 利用するクラウドサービス(AWS/Google Cloud)
- 実現したいサービスの規模感や求められる堅牢性、予算など

主に以下のパターンによって構築します。

- Ruby on RailsのActiveJob + ActionCableによる実装
  - SidekiqもしくはSolidQueue
  - Railsを利用した非同期処理の実現手法については @references/01_infrastructure.md を参照してください
- TypeScript BullMQによる実装
  - Redisベースの高性能ジョブキュー
  - Node.js/TypeScriptでバックエンドを構築する場合に最適
  - 詳細は @references/02_typescript_bullmq.md を参照してください
- AWS SQSによるタスクキューイングとAWS AppSync Eventsによるイベント送信、DynamoDBによる状態管理
  - AWSのサーバーレスアーキテクチャで実現
  - Lambda + SQS + AppSync Events + DynamoDBの組み合わせ
  - 詳細は @references/03_aws_serverless.md を参照してください
- Google CloudのCloud Tasksを利用したタスク管理とFirestoreによる通知・状態管理
  - Google Cloudのサーバーレスアーキテクチャで実現
  - Cloud Run + Cloud Tasks + Firestoreの組み合わせ
  - 詳細は @references/04_gcp_serverless.md を参照してください

### 実現手法の比較

| 観点 | Rails (Solid Queue) | Rails (Sidekiq) | BullMQ | AWS Serverless | GCP Serverless |
|------|---------------------|-----------------|--------|----------------|----------------|
| 追加インフラ | なし | Redis | Redis | SQS, DynamoDB等 | Cloud Tasks, Firestore |
| スケーラビリティ | 中 | 高 | 高 | 非常に高 | 非常に高 |
| 運用負荷 | 低 | 中 | 中 | 低 | 低 |
| コスト（低負荷時） | 低 | 中 | 中 | 非常に低 | 非常に低 |
| リアルタイム通知 | ActionCable | ActionCable | 独自実装 | AppSync Events | Firestore |
| 最大処理時間 | 無制限 | 無制限 | 無制限 | 15分(Lambda) | 60分(Cloud Run) |
| 適したユースケース | 小〜中規模Rails | 中〜大規模Rails | Node.js全般 | AWS中心のサーバーレス | GCP中心のサーバーレス | 

### 非同期処理のバックエンド実装

バックエンド実装時には、以下の観点について各実現手法ごとのベストプラクティスを参照してください。

#### 共通の実装観点

- **パラメータの受け取り方**
  - シリアライズ可能なデータのみを渡す
  - パラメータサイズの制限を考慮（大きなデータは外部ストレージを使用）
  - IDベースの参照を推奨
  - バリデーションの実装

- **エラー発生時の処理と通知**
  - リトライ可能なエラーと不可能なエラーの分類
  - リトライ設定（回数、バックオフ戦略）
  - Dead Letter Queue（DLQ）の処理
  - エラー通知（構造化ログ、外部サービス連携）

- **進捗の状態管理**
  - 状態管理用データモデルの設計
  - 進捗率の計算と更新
  - リアルタイム通知（WebSocket、SSE、ポーリング）
  - キャンセル処理

- **その他**
  - 冪等性の確保
  - タイムアウト対策
  - ジョブの分割とチェーン
  - テスト戦略

#### 実現手法別リファレンス

| 実現手法 | リファレンス |
|---------|------------|
| Ruby on Rails (ActiveJob) | @references/05_backend_rails.md |
| TypeScript BullMQ | @references/06_backend_bullmq.md |
| AWS Serverless (Lambda + SQS) | @references/07_backend_aws.md |
| GCP Serverless (Cloud Run + Cloud Tasks) | @references/08_backend_gcp.md |

### 非同期処理のUIを実現するフロントエンド実装

フロントエンド実装時には、以下の観点について各フレームワークごとのベストプラクティスを参照してください。

#### 共通の実装観点

- **非同期処理の呼び出し方**
  - フォーム送信による非同期タスクの開始
  - カスタムフックやComposableによる呼び出し管理
  - 二重送信の防止

- **状態管理と表示**
  - 進捗状況のリアルタイム表示
  - ポーリングによる状態更新
  - WebSocket/SSEによるプッシュ通知
  - Optimistic Updates（楽観的更新）

- **接続復帰処理**
  - WebSocket/SSE接続の自動再接続
  - ページ非表示時の接続管理
  - Visibility APIを使用した状態同期
  - オフライン/オンライン状態の監視

- **エラーハンドリング**
  - Error Boundaryによるエラー捕捉
  - グローバルエラーハンドリング
  - リトライ機能（Exponential Backoff）
  - ユーザーへのエラー通知

#### フレームワーク別リファレンス

| フレームワーク | リファレンス |
|--------------|------------|
| Rails Hotwire (Turbo + Stimulus + ActionCable) | @references/09_frontend_hotwire.md |
| Next.js (React / App Router) | @references/10_frontend_nextjs.md |
| Vue.js 3 (Composition API) | @references/11_frontend_vuejs.md |