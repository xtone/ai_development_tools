# 本画面遷移時のイベントセクション

## 基本構造

```markdown
## 本画面遷移時のイベント

| 番号 | イベント概要 | 内容 | API | 備考 |
|------|------------|------|-----|------|
| 1    |            |      |     |      |
```

## 列の説明

### イベント概要
- イベントの概要を簡潔に記載
- 例: 「ログイン状態の確認」「データの初期取得」「画面表示の記録」

### 内容
- イベントの詳細な内容を記載
- どのような処理が行われるかを具体的に説明
- 非エンジニア向けに分かりやすく記載
- 例: 「ログインしているユーザー情報を取得。未ログインの場合はログイン誘導画面を表示。同時に画面アクセスをAnalyticsに記録」

### API
- 呼び出すAPIメソッド名を記載
- API名はPascalCase形式
- APIを呼ばない場合: 「-」または空欄
- ローカルストレージからのデータ取得の場合も「-」

### 備考
- 補足情報を記載
- ローカルデータ取得の場合は「ローカルデータ取得」などと明記

## 対象となるイベント

画面表示時に**自動的**に発火するイベントを記載します。ユーザー操作によるイベントは「イベント項目」に記載してください。

### 典型的なパターン

1. **initState() / useEffect()**
   ```dart
   @override
   void initState() {
     super.initState();
     _loadData();
   }
   ```

2. **ref.listen() / ref.watch()**
   ```dart
   ref.listen(authStateProvider, (previous, next) {
     // 認証状態の監視
   });
   ```

3. **Analytics画面表示イベント**
   ```dart
   useAnalyticsScreen(ref);  // screenName: 'MyPagePage'
   ```

4. **FutureBuilder / StreamBuilder**
   ```dart
   FutureBuilder(
     future: fetchData(),
     builder: ...
   )
   ```

## オプション列

### analytics@property_value列
```markdown
| 番号 | イベント概要 | 内容 | API | analytics@property_value | 備考 |
```
- 画面表示イベントの場合、通常は画面名を記載
- 例: 「MyPagePage」「ReservationDetailPage」
