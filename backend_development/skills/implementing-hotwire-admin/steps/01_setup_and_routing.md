# ステップ1: セットアップとルーティング

## 目次

- [概要](#概要)
- [名前空間の決定](#名前空間の決定)
- [ベースコントローラの作成](#ベースコントローラの作成)
- [ルーティングの設定](#ルーティングの設定)
- [認証・認可の設定](#認証認可の設定)

---

## 概要

管理画面の基盤となる名前空間、ベースコントローラ、ルーティングを設定します。

## 名前空間の決定

管理画面のパスを決定します。一般的な選択肢：

| パス | 用途 |
|------|------|
| `/admin` | 一般的な管理画面 |
| `/system_admin` | システム管理者向け |
| `/staff` | スタッフ向け |
| `/dashboard` | ダッシュボード |

```bash
# コントローラ生成コマンド
rails generate controller Admin::Dashboard index
# または
rails generate controller SystemAdmin::Dashboard index
```

## ベースコントローラの作成

`app/controllers/admin/base_controller.rb`:

```ruby
class Admin::BaseController < ApplicationController
  # 管理画面専用レイアウトを使用
  layout 'admin'

  # 認証を必須に
  before_action :authenticate_user!
  before_action :authorize_admin!

  private

  def authorize_admin!
    unless current_user&.admin?
      flash[:alert] = '管理者権限が必要です'
      redirect_to root_path
    end
  end
end
```

### 各リソースコントローラの基本構造

`app/controllers/admin/users_controller.rb`:

```ruby
class Admin::UsersController < Admin::BaseController
  before_action :set_user, only: [:show, :edit, :update, :destroy]

  def index
    @users = User.order(created_at: :desc).page(params[:page])
  end

  def show
  end

  def new
    @user = User.new
  end

  def create
    @user = User.new(user_params)
    if @user.save
      redirect_to admin_user_path(@user), notice: 'ユーザーを作成しました'
    else
      render :new, status: :unprocessable_entity
    end
  end

  def edit
  end

  def update
    if @user.update(user_params)
      redirect_to admin_user_path(@user), notice: 'ユーザーを更新しました'
    else
      render :edit, status: :unprocessable_entity
    end
  end

  def destroy
    @user.destroy
    redirect_to admin_users_path, notice: 'ユーザーを削除しました'
  end

  private

  def set_user
    @user = User.find(params[:id])
  end

  def user_params
    params.require(:user).permit(:name, :email, :role)
  end
end
```

## ルーティングの設定

`config/routes.rb`:

```ruby
Rails.application.routes.draw do
  # 管理画面
  namespace :admin do
    root to: 'dashboard#index'

    # リソース
    resources :users do
      member do
        post :toggle_role    # 権限切替
        post :soft_delete    # 論理削除
        post :revive         # 復活
      end
    end

    resources :projects do
      resources :members, controller: 'projects/members', only: [:index, :create, :destroy]
    end

    resources :reports, only: [:index, :show, :edit, :update, :destroy] do
      collection do
        get :summary       # 集計
        get :unsubmitted   # 未提出一覧
      end
    end

    resources :estimates
    resources :bills
    resources :user_roles, only: [:index, :show]

    # CSV出力
    resources :csvs, only: [:index] do
      collection do
        get :users
        get :projects
        get :reports
      end
    end
  end
end
```

## 認証・認可の設定

### Deviseを使用する場合

```ruby
# config/routes.rb
namespace :admin do
  # 管理者専用のscopeを追加
end

# app/controllers/admin/base_controller.rb
class Admin::BaseController < ApplicationController
  before_action :authenticate_user!
  before_action :require_admin!

  private

  def require_admin!
    redirect_to root_path, alert: '権限がありません' unless current_user.admin?
  end
end
```

### 自作認証を使用する場合

```ruby
# app/controllers/admin/base_controller.rb
class Admin::BaseController < ApplicationController
  before_action :require_admin_login!

  private

  def require_admin_login!
    unless session[:admin_user_id]
      redirect_to admin_login_path, alert: 'ログインが必要です'
    end
  end

  def current_admin_user
    @current_admin_user ||= AdminUser.find_by(id: session[:admin_user_id])
  end
  helper_method :current_admin_user
end
```

### ロールベースの認可

```ruby
# app/models/user.rb
class User < ApplicationRecord
  has_many :user_roles
  has_many :roles, through: :user_roles

  def admin?
    roles.exists?(name: 'admin')
  end

  def has_role?(role_name)
    roles.exists?(name: role_name)
  end
end

# app/controllers/admin/base_controller.rb
class Admin::BaseController < ApplicationController
  before_action :authorize_admin!

  private

  def authorize_admin!
    unless current_user&.admin?
      respond_to do |format|
        format.html { redirect_to root_path, alert: '管理者権限が必要です' }
        format.turbo_stream { head :forbidden }
      end
    end
  end
end
```

## 次のステップ

レイアウトとナビゲーションの作成に進みます → @steps/02_layout_and_navigation.md
