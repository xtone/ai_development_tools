# Common Development Skills

プラットフォーム非依存の汎用開発スキル集。Android, iOS, Web, バックエンドなど、あらゆるプロジェクトで使える共通ツールです。

## インストール

```bash
# マーケットプレイスを追加
/plugin marketplace add xtone/ai_development_tools

# プラグインをインストール
/plugin install common-development@xtone-ai-development-tools
```

## スキル一覧

| スキル | 説明 |
|--------|------|
| **video-keyframe-analyzer** | 動画からキーフレームを抽出してコスト効率的に分析（API コスト93%削減） |
| **lessons-md-manager** | CLAUDE.mdの「Lessons Learned」セクションを管理。セッション中の学びを自動抽出・蓄積 |
| **review-feedback-learner** | PRレビューで受けた指摘をCLAUDE.mdのルールとして蓄積。レビュアーの暗黙知をチーム資産に |

## スキル詳細

### video-keyframe-analyzer

動画を全フレーム読み込むと高コストになるため、差分検出により重要なフレームのみを抽出。

**使い方:**
```
/video-keyframe-analyzer

画面遷移の動画を分析したい。
動画: ~/Downloads/screen_recording.mp4
```

**コスト削減効果:**
| 方法 | フレーム数 | コスト |
|-----|-----------|--------|
| 全フレーム（30fps、5秒） | 150枚 | 約450円 |
| キーフレーム抽出 | 8-10枚 | 約24-30円 |

詳細: [skills/video-keyframe-analyzer/README.md](./skills/video-keyframe-analyzer/README.md)

### lessons-md-manager

Boris Cherny氏のTip #3「CLAUDE.mdへの投資」を仕組み化したスキル。

**使い方:**
```
/lessons          # セッション中の学びをCLAUDE.mdに追記
/lessons review   # 既存ルールのレビュー・整理
```

**特徴:**
- セッション中の修正・失敗・発見を自動抽出
- カテゴリ分類・重複チェック付きで蓄積
- チーム全員が即座に恩恵を受けられる知見共有

詳細: [skills/lessons-md-manager/README.md](./skills/lessons-md-manager/README.md)

### review-feedback-learner

PRレビューで受けた指摘をCLAUDE.mdのルールとして蓄積するスキル。lessons-md-managerと補完関係にあり、「自分の気づき」＋「他者の指摘」の両方を蓄積できます。

**使い方:**
```
/review-learn          # 直近のマージ済みPRから学ぶ
/review-learn #123     # 指定PRのレビューから学ぶ
```

**lessons-md-managerとの補完関係:**
| スキル | 学びの源泉 | タイミング |
|--------|-----------|-----------|
| `/lessons` | 自分で気づいた失敗・修正 | セッション終了時 |
| `/review-learn` | 他者からの指摘 | PRマージ後 |

詳細: [skills/review-feedback-learner/README.md](./skills/review-feedback-learner/README.md)

## ディレクトリ構造

```
common_development/
├── .claude-plugin/
│   ├── marketplace.json    # マーケットプレイス設定
│   └── plugin.json         # プラグイン基本情報
├── skills/
│   ├── video-keyframe-analyzer/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   ├── extract_keyframes.py
│   │   └── requirements.txt
│   ├── lessons-md-manager/
│   │   ├── SKILL.md
│   │   └── README.md
│   └── review-feedback-learner/
│       ├── SKILL.md
│       └── README.md
└── README.md
```

## 関連リンク

- [Claude Code Plugins - 公式ドキュメント](https://docs.claude.com/en/docs/claude-code/plugins)
- [ai_development_tools リポジトリ](https://github.com/xtone/ai_development_tools)
