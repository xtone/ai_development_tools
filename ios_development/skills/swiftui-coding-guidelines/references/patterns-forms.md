# SwiftUI フォーム・入力パターン

## 3-1. 検索機能（デバウンス付き）

### iOS 15+ searchableモディファイア

```swift
struct SearchableListView: View {
    @StateObject private var viewModel = SearchViewModel()
    @State private var searchText = ""

    var body: some View {
        NavigationStack {
            List(viewModel.results) { item in
                ItemRow(item: item)
            }
            .navigationTitle("検索")
            .searchable(text: $searchText, prompt: "キーワードを入力")
            .onChange(of: searchText) { _, newValue in
                viewModel.searchTextChanged(newValue)
            }
        }
    }
}

@MainActor
class SearchViewModel: ObservableObject {
    @Published var results: [Item] = []

    private var searchTask: Task<Void, Never>?

    func searchTextChanged(_ text: String) {
        // 前の検索をキャンセル
        searchTask?.cancel()

        guard !text.isEmpty else {
            results = []
            return
        }

        // デバウンス: 300ms後に検索実行
        searchTask = Task {
            try? await Task.sleep(nanoseconds: 300_000_000)

            guard !Task.isCancelled else { return }

            do {
                results = try await searchService.search(query: text)
            } catch {
                // エラーハンドリング
            }
        }
    }
}
```

---

## 3-2. フォーム入力（バリデーション付き）

```swift
struct RegistrationForm: View {
    @StateObject private var viewModel = RegistrationViewModel()

    var body: some View {
        Form {
            Section("アカウント情報") {
                TextField("メールアドレス", text: $viewModel.email)
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
                    .textInputAutocapitalization(.never)

                if let error = viewModel.emailError {
                    Text(error)
                        .foregroundColor(.red)
                        .font(.caption)
                }

                SecureField("パスワード", text: $viewModel.password)
                    .textContentType(.newPassword)

                if let error = viewModel.passwordError {
                    Text(error)
                        .foregroundColor(.red)
                        .font(.caption)
                }
            }

            Section {
                Button("登録") {
                    Task {
                        await viewModel.register()
                    }
                }
                .disabled(!viewModel.isValid)
            }
        }
    }
}

@MainActor
class RegistrationViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""

    var emailError: String? {
        guard !email.isEmpty else { return nil }
        let emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/
        return email.uppercased().wholeMatch(of: emailRegex) == nil
            ? "有効なメールアドレスを入力してください"
            : nil
    }

    var passwordError: String? {
        guard !password.isEmpty else { return nil }
        return password.count < 8
            ? "パスワードは8文字以上必要です"
            : nil
    }

    var isValid: Bool {
        !email.isEmpty &&
        !password.isEmpty &&
        emailError == nil &&
        passwordError == nil
    }

    func register() async {
        // 登録処理
    }
}
```

---

## 3-3. 認証画面（ログインフォーム）

### 完全な実装例

FocusState、textContentType、キーボード設定を組み合わせた認証画面の推奨パターン。

```swift
struct LoginView: View {
    enum Field: Hashable {
        case email
        case password
    }

    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?

    @FocusState private var focusedField: Field?

    var body: some View {
        Form {
            Section {
                // メールアドレス入力欄
                TextField("メールアドレス", text: $email)
                    .focused($focusedField, equals: .email)
                    .textContentType(.username)           // パスワードマネージャー対応
                    .keyboardType(.emailAddress)          // メール用キーボード
                    .textInputAutocapitalization(.never)  // 自動大文字化を無効
                    .autocorrectionDisabled()             // 自動修正を無効
                    .submitLabel(.next)                   // Returnキーを「次へ」に
                    .onSubmit {
                        focusedField = .password          // パスワード欄にフォーカス移動
                    }

                // パスワード入力欄
                SecureField("パスワード", text: $password)
                    .focused($focusedField, equals: .password)
                    .textContentType(.password)           // パスワードマネージャー対応
                    .submitLabel(.go)                     // Returnキーを「Go」に
                    .onSubmit {
                        login()                           // ログイン実行
                    }
            } header: {
                Text("アカウント情報")
            } footer: {
                if let errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red)
                }
            }

            Section {
                Button {
                    login()
                } label: {
                    if isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("ログイン")
                            .frame(maxWidth: .infinity)
                    }
                }
                .disabled(!isFormValid || isLoading)
            }
        }
        .onAppear {
            // 画面表示時に最初のフィールドにフォーカス
            focusedField = .email
        }
    }

    private var isFormValid: Bool {
        !email.isEmpty && !password.isEmpty
    }

    private func login() {
        // 未入力フィールドがあればフォーカス移動
        if email.isEmpty {
            focusedField = .email
            return
        }
        if password.isEmpty {
            focusedField = .password
            return
        }

        // キーボードを閉じる
        focusedField = nil

        isLoading = true
        errorMessage = nil

        Task {
            // ログイン処理...
        }
    }
}
```

### 新規登録画面

新規パスワード作成時は `.newPassword` を使用。

```swift
struct SignUpView: View {
    enum Field: Hashable {
        case email
        case password
        case confirmPassword
    }

    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""

    @FocusState private var focusedField: Field?

    var body: some View {
        Form {
            TextField("メールアドレス", text: $email)
                .focused($focusedField, equals: .email)
                .textContentType(.username)
                .keyboardType(.emailAddress)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .submitLabel(.next)
                .onSubmit { focusedField = .password }

            SecureField("パスワード", text: $password)
                .focused($focusedField, equals: .password)
                .textContentType(.newPassword)  // ✅ 新規パスワード
                .submitLabel(.next)
                .onSubmit { focusedField = .confirmPassword }

            SecureField("パスワード（確認）", text: $confirmPassword)
                .focused($focusedField, equals: .confirmPassword)
                .textContentType(.newPassword)  // ✅ 新規パスワード
                .submitLabel(.done)
                .onSubmit { signUp() }
        }
    }

    private func signUp() {
        // 登録処理
    }
}
```

### ワンタイムパスワード（OTP）入力

SMSやメールで送信されたコードの入力。

```swift
struct OTPInputView: View {
    @State private var code = ""
    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(spacing: 24) {
            Text("認証コードを入力")
                .font(.headline)

            TextField("000000", text: $code)
                .focused($isFocused)
                .textContentType(.oneTimeCode)    // ✅ OTP自動入力対応
                .keyboardType(.numberPad)         // 数字キーボード
                .multilineTextAlignment(.center)
                .font(.title.monospaced())
                .frame(maxWidth: 200)
                .onChange(of: code) { _, newValue in
                    // 6桁入力で自動送信
                    if newValue.count == 6 {
                        verifyCode()
                    }
                }

            Text("SMSで送信されたコードを入力してください")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .onAppear {
            isFocused = true
        }
    }

    private func verifyCode() {
        // 検証処理
    }
}
```

### textContentType 一覧

| 用途 | textContentType | 説明 |
|------|-----------------|------|
| ユーザー名/メール | `.username` | ログイン時のID入力 |
| 既存パスワード | `.password` | ログイン時のパスワード |
| 新規パスワード | `.newPassword` | 登録・変更時のパスワード |
| ワンタイムコード | `.oneTimeCode` | SMS/メール認証コード |
| メールアドレス | `.emailAddress` | メール専用入力 |
| 電話番号 | `.telephoneNumber` | 電話番号入力 |
| 名前 | `.name` | フルネーム |
| 姓 | `.familyName` | 姓のみ |
| 名 | `.givenName` | 名のみ |

### FocusStateのベストプラクティス

```swift
// ✅ 推奨: enumでフォーカス状態を管理
enum Field: Hashable {
    case username
    case password
}
@FocusState private var focusedField: Field?

// フォーカス移動
focusedField = .password

// キーボードを閉じる
focusedField = nil

// ❌ 避けるべき: 複数のBool FocusState
@FocusState private var isUsernameFocused: Bool
@FocusState private var isPasswordFocused: Bool
// → 状態管理が複雑になり、同時に複数がtrueになる可能性
```

### キーボードのReturnキー設定

| submitLabel | 表示 | 用途 |
|-------------|------|------|
| `.next` | 次へ | 次のフィールドへ移動 |
| `.done` | 完了 | 入力完了 |
| `.go` | Go | アクション実行 |
| `.send` | 送信 | メッセージ送信 |
| `.search` | 検索 | 検索実行 |
| `.continue` | 続ける | 次のステップへ |
| `.join` | 参加 | 参加アクション |
| `.return` | 改行 | デフォルト |

### アクセシビリティ対応

```swift
TextField("メールアドレス", text: $email)
    .textContentType(.username)
    .accessibilityLabel("メールアドレス入力欄")
    .accessibilityHint("ログインに使用するメールアドレスを入力してください")

SecureField("パスワード", text: $password)
    .textContentType(.password)
    .accessibilityLabel("パスワード入力欄")
    // パスワードの内容は読み上げられない（セキュリティ）
```
