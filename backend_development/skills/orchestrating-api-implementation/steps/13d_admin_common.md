# ステップ13d: 管理画面の共通設定

## 目次

- [データ型と入力フォームのマッピング](#データ型と入力フォームのマッピング)
- [動作確認チェックリスト](#動作確認チェックリスト)
- [トラブルシューティング](#トラブルシューティング)
- [リッチテキストエディタの実装](#リッチテキストエディタの実装)
- [デザインガイドライン](#デザインガイドライン)
- [displayNameの活用](#displaynameの活用)
- [Playwrightテスト例](#playwrightテスト例)

---

## データ型と入力フォームのマッピング

JSON仕様のデータ型に応じて、適切な入力フォームを選択します。

### ActiveAdmin / Formtastic

| JSON仕様の型 | ActiveAdmin入力タイプ | 説明 |
|-------------|---------------------|------|
| `string` | `as: :string` | 一行テキスト入力 |
| `text` | `as: :text` | 複数行テキストエリア |
| `richText` | `as: :trix_editor` | リッチテキストエディタ |
| `number` | `as: :number, step: 0.01` | 小数入力 |
| `integer` | `as: :number, step: 1` | 整数入力 |
| `boolean` | `as: :boolean` | チェックボックス |
| `date` | `as: :datetime_picker` | 日付ピッカー |
| `uuid` | `as: :string` (読み取り専用) | UUID表示 |
| `image` | `as: :file` | ファイルアップロード |
| `enum` | `as: :select` | セレクトボックス |
| `relation` | `as: :select` | 関連モデル選択 |

### Administrate

| JSON仕様の型 | Administrate Field | 説明 |
|-------------|-------------------|------|
| `string` | `Field::String` | 一行テキスト |
| `text` | `Field::Text` | 複数行テキスト |
| `richText` | `Field::RichText` | Action Textエディタ |
| `number` | `Field::Number` | 数値入力 |
| `boolean` | `Field::Boolean` | チェックボックス |
| `date` | `Field::DateTime` | 日時ピッカー |
| `enum` | `Field::Select` | セレクトボックス |
| `relation` | `Field::BelongsTo` / `Field::HasMany` | リレーション |

### Hotwire (Rails View)

| JSON仕様の型 | Railsヘルパー | 説明 |
|-------------|--------------|------|
| `string` | `f.text_field` | 一行テキスト |
| `text` | `f.text_area` | 複数行テキスト |
| `richText` | `f.rich_text_area` | Trixエディタ |
| `number` | `f.number_field step: 0.01` | 小数入力 |
| `integer` | `f.number_field step: 1` | 整数入力 |
| `boolean` | `f.check_box` | チェックボックス |
| `date` | `f.datetime_field` | 日時入力 |
| `image` | `f.file_field` + Active Storage | ファイルアップロード |
| `enum` | `f.select` | セレクトボックス |
| `relation` | `f.collection_select` | 関連モデル選択 |

---

## 動作確認チェックリスト

| 機能 | 確認内容 |
|------|----------|
| 一覧 | データが表示される |
| ページネーション | ページ切り替えができる |
| 検索・フィルタ | 条件で絞り込める |
| 詳細 | データが正しく表示される |
| 作成 | 新規データを作成できる |
| 編集 | データを更新できる |
| 削除 | データを削除できる |
| バリデーション | エラーメッセージが表示される |

---

## トラブルシューティング

### 1. ActiveAdmin::Commentとの名前衝突

**エラー**: アプリケーションに`Comment`モデルがあると、ActiveAdminの内部モデルと衝突する

**解決方法**: `as`オプションで別名を指定
```ruby
ActiveAdmin.register Comment, as: "AppComment" do
  menu label: "コメント"
end
```

### 2. richText（Action Text）の表示エラー

**エラー**: `undefined method 'body' for nil:NilClass`

**解決方法**:

1. Action Textがインストールされているか確認
```bash
docker compose exec web bundle exec rails action_text:install
docker compose exec web bundle exec rails db:migrate
```

2. モデルに `has_rich_text` を追加
```ruby
class Article < ApplicationRecord
  has_rich_text :contents
end
```

3. ActiveAdminでの表示を修正
```ruby
row(:contents) { |article| article.contents.body&.to_s&.html_safe }
```

### 3. 関連モデルの表示エラー

**エラー**: `undefined method 'name' for #<Account:...>`

**解決方法**: 関連モデルに `to_s` を定義
```ruby
class Account < ApplicationRecord
  def to_s
    name || email || id
  end
end
```

### 4. 日本語が文字化けする

**解決方法**: エンコーディングを確認

```ruby
# config/database.yml
default: &default
  adapter: postgresql
  encoding: unicode
```

```ruby
# config/application.rb
config.encoding = "utf-8"
config.i18n.default_locale = :ja
```

### 5. CSSが適用されない（ActiveAdmin）

**解決方法**:

1. dartsass-railsがインストールされているか確認
```ruby
gem 'dartsass-rails'
```

2. アセットを再コンパイル
```bash
docker compose exec web bundle exec rails assets:precompile
docker compose restart web
```

### 6. マイグレーションエラー「relation already exists」

**原因**: `t.references` と `add_index` の重複

**解決方法**: `t.references` は自動的にインデックスを作成するため、別途 `add_index` は不要
```ruby
# OK
t.references :account, foreign_key: true, type: :uuid

# NG（重複）
t.references :account, foreign_key: true, type: :uuid
add_index :articles, :account_id  # これは不要
```

### 7. シードデータのバリデーションエラー

**エラー**: `Validation failed: Xxx is not included in the list`

**解決方法**: enumの値とバリデーションの整合性を確認
```ruby
# enumの場合
Article.create!(publish_status: 'draft')  # enumのキー

# inclusion validationの場合
Article.create!(publish_status: 'ドラフト')  # 定義された値
```

### 8. Docker環境でのファイル権限エラー

**エラー**: `Permission denied @ dir_s_mkdir`

**解決方法**:
```bash
sudo chown -R $(id -u):$(id -g) .
```

---

## リッチテキストエディタの実装

### Action Text (Trix) - Rails標準

```bash
docker compose exec web rails action_text:install
docker compose exec web rails db:migrate
```

```ruby
class Article < ApplicationRecord
  has_rich_text :contents
end
```

```erb
<%= f.rich_text_area :contents, class: 'mt-1 block w-full' %>
```

### Quill Editor - 高機能エディタ

```bash
bin/importmap pin quill
```

`app/javascript/controllers/quill_controller.js`:

```javascript
import { Controller } from "@hotwired/stimulus"
import Quill from "quill"

export default class extends Controller {
  static targets = ["editor", "input"]
  static values = { placeholder: String }

  connect() {
    this.quill = new Quill(this.editorTarget, {
      theme: 'snow',
      placeholder: this.placeholderValue || '内容を入力...',
      modules: {
        toolbar: [
          [{ 'header': [1, 2, 3, false] }],
          ['bold', 'italic', 'underline', 'strike'],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          ['link', 'image'],
          ['clean']
        ]
      }
    })

    if (this.inputTarget.value) {
      this.quill.root.innerHTML = this.inputTarget.value
    }

    this.quill.on('text-change', () => {
      this.inputTarget.value = this.quill.root.innerHTML
    })
  }
}
```

---

## デザインガイドライン

### デザイン原則

| 原則 | 説明 |
|------|------|
| 一貫性 | 全画面で同じパターンを使用 |
| 可読性 | 適切な余白とコントラスト |
| 効率性 | 最小限のクリックで操作完了 |
| フィードバック | 操作結果を明確に伝える |

### カラーパレット

```css
:root {
  --color-primary: #3B82F6;      /* Blue-500 */
  --color-primary-hover: #2563EB; /* Blue-600 */
  --color-success: #10B981;      /* Green-500 */
  --color-warning: #F59E0B;      /* Amber-500 */
  --color-danger: #EF4444;       /* Red-500 */
  --color-bg: #F9FAFB;           /* Gray-50 */
  --color-card: #FFFFFF;
  --color-border: #E5E7EB;       /* Gray-200 */
  --color-text: #111827;         /* Gray-900 */
  --color-text-muted: #6B7280;   /* Gray-500 */
}
```

### フラッシュメッセージ

```erb
<% flash.each do |type, message| %>
  <%
    colors = {
      'notice' => 'bg-green-50 text-green-800 border-green-200',
      'alert' => 'bg-red-50 text-red-800 border-red-200',
      'warning' => 'bg-yellow-50 text-yellow-800 border-yellow-200'
    }
    color_class = colors[type] || 'bg-blue-50 text-blue-800 border-blue-200'
  %>
  <div class="<%= color_class %> border rounded-md p-4 mb-4">
    <%= message %>
  </div>
<% end %>
```

---

## displayNameの活用

JSON仕様の`displayName`を管理画面で自動的に使用します。

### i18nファイルの自動生成

`lib/tasks/generate_i18n.rake`:

```ruby
namespace :i18n do
  desc 'Generate i18n file from JSON specification'
  task generate_from_spec: :environment do
    spec_file = Rails.root.join('app_def', 'app.json')
    spec = JSON.parse(File.read(spec_file))

    translations = {
      'ja' => {
        'activerecord' => {
          'models' => {},
          'attributes' => {}
        }
      }
    }

    spec['models'].each do |model|
      model_name = model['name'].underscore
      display_name = model['displayName'] || model['name']

      translations['ja']['activerecord']['models'][model_name] = display_name
      translations['ja']['activerecord']['attributes'][model_name] = {}

      model['fields'].each do |field|
        field_name = field['name'].underscore
        field_display = field['displayName'] || field['name'].titleize
        translations['ja']['activerecord']['attributes'][model_name][field_name] = field_display
      end
    end

    output_path = Rails.root.join('config', 'locales', 'models.ja.yml')
    File.write(output_path, translations.to_yaml)

    puts "Generated: #{output_path}"
  end
end
```

実行:

```bash
docker compose exec web rails i18n:generate_from_spec
```

---

## Playwrightテスト例

```typescript
import { test, expect } from '@playwright/test';

test.describe('記事管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/login');
    await page.fill('[data-testid="input-email"]', 'admin@example.com');
    await page.fill('[data-testid="input-password"]', 'password');
    await page.click('[data-testid="submit-button"]');
    await expect(page).toHaveURL('/admin');
  });

  test('記事一覧を表示', async ({ page }) => {
    await page.click('[data-testid="nav-articles"]');
    await expect(page.locator('[data-testid="articles-table"]')).toBeVisible();
  });

  test('記事を作成', async ({ page }) => {
    await page.click('[data-testid="nav-articles"]');
    await page.click('[data-testid="new-article-button"]');

    await page.fill('[data-testid="input-title"]', 'テスト記事');
    await page.fill('[data-testid="input-contents"]', 'テスト本文');
    await page.click('[data-testid="submit-button"]');

    await expect(page.locator('[data-testid="flash-notice"]')).toContainText('作成しました');
  });

  test('記事を編集', async ({ page }) => {
    await page.click('[data-testid="nav-articles"]');
    const firstEditLink = page.locator('[data-testid^="article-edit-"]').first();
    await firstEditLink.click();

    await page.fill('[data-testid="input-title"]', '更新後のタイトル');
    await page.click('[data-testid="submit-button"]');

    await expect(page.locator('[data-testid="flash-notice"]')).toContainText('更新しました');
  });

  test('記事を削除', async ({ page }) => {
    await page.click('[data-testid="nav-articles"]');
    const firstDeleteLink = page.locator('[data-testid^="article-delete-"]').first();

    page.on('dialog', dialog => dialog.accept());
    await firstDeleteLink.click();

    await expect(page.locator('[data-testid="flash-notice"]')).toContainText('削除しました');
  });
});
```
