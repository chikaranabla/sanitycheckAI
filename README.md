# Opentrons Protocol Sanity Check System

Opentrons実験プロトコルファイル(.py)を解析し、物理セッティングのチェックポイントを自動生成。人間が行ったセッティングの画像をAI（Gemini 2.5 Pro）で検証し、ミスがないかを判定するWebアプリケーション。

## 🎯 主な機能

- **チェックポイント自動生成**: プロトコルファイルから物理セッティングの確認項目を自動生成
- **画像検証**: セッティング画像をAIが解析し、各チェックポイントを検証
- **直感的なUI**: シンプルなWebインターフェースでファイルアップロードと結果表示
- **詳細レポート**: 各チェック項目の合否と詳細な説明を表示

## 📋 システム要件

- Python 3.10 以上
- Google AI API Key (Gemini API)
- インターネット接続

## 🚀 セットアップ手順

### 1. リポジトリのクローンまたはダウンロード

```bash
cd sanitycheckAI
```

### 2. 仮想環境の作成（推奨）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、Google AI API Keyを設定してください：

```env
# .env
GOOGLE_API_KEY=your_api_key_here
PORT=8000
```

**Google AI API Keyの取得方法:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. "Create API Key" をクリック
4. 生成されたAPIキーをコピーして `.env` ファイルに貼り付け

### 5. サーバーの起動

```bash
# 方法1: Pythonモジュールとして起動
python -m backend.main

# 方法2: Uvicornで直接起動
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

サーバーが起動したら、ブラウザで以下のURLにアクセス：

```
http://localhost:8000
```

## 📖 使用方法

### 基本的な使い方

1. **ファイルの準備**
   - Opentrons プロトコルファイル（.py）
   - 実験セッティングの写真（.jpg または .png）

2. **検証の実行**
   - ブラウザで http://localhost:8000 にアクセス
   - プロトコルファイルをアップロード
   - セッティング画像をアップロード
   - 「検証開始」ボタンをクリック

3. **結果の確認**
   - 総合判定（合格/不合格）を確認
   - 各チェックポイントの詳細を確認
   - 不合格の場合は問題箇所を確認

### サンプルファイル

プロジェクトには以下のサンプルファイルが含まれています：

- `96-ch_partial_test.py`: テスト用プロトコルファイル
- `good_photo_1.jpg`: 正しいセッティング例
- `bad_photo_1.jpg`, `bad_photo_2.jpg`, `bad_photo_3.jpg`: 不正なセッティング例

これらを使用して動作確認ができます。

## 🏗️ プロジェクト構造

```
sanitycheckAI/
├── README.md                  # このファイル
├── requirements.txt           # Python依存関係
├── .env                       # 環境変数（自分で作成）
├── 96-ch_partial_test.py      # サンプルプロトコル
├── good_photo_1.jpg           # サンプル画像（正しい例）
├── bad_photo_*.jpg            # サンプル画像（誤った例）
├── backend/
│   ├── main.py               # FastAPIアプリケーション
│   ├── gemini_service.py     # Gemini API連携
│   └── prompts.py            # System Instruction定義
├── frontend/
│   ├── index.html            # メインUI
│   ├── style.css             # スタイル
│   └── script.js             # フロントエンドロジック
└── docs/
    └── requirements.md       # 要件定義書
```

## 🔍 チェックポイントの例

システムは以下のような項目を自動的にチェックします：

1. ✅ 指定位置にピペットチップラックが配置されているか（例: C2）
2. ✅ チップラック内のすべてのピペットチップが埋まっているか
3. ✅ ゴミ箱が指定位置に配置されているか（例: A3）
4. ✅ 不要な場所にラボウェアが置かれていないか
5. ✅ その他プロトコル固有の要件

## 🛠️ トラブルシューティング

### よくある問題

**Q: "Google API Key is required" というエラーが出る**
- `.env` ファイルが正しく作成されているか確認
- `GOOGLE_API_KEY` が正しく設定されているか確認
- APIキーが有効か確認

**Q: 画像がアップロードできない**
- ファイル形式が .jpg, .jpeg, .png のいずれかか確認
- ファイルサイズが大きすぎないか確認（推奨: 10MB以下）

**Q: チェックポイントが正しく生成されない**
- プロトコルファイルがOpentrons API 2.x形式か確認
- プロトコルファイルの構文エラーがないか確認

**Q: localhost:8000 にアクセスできない**
- サーバーが正しく起動しているか確認
- ポート8000が他のアプリケーションで使用されていないか確認
- 環境変数 `PORT` を変更して別のポートを試す

## 🔒 セキュリティに関する注意

- **APIキーの管理**: `.env` ファイルは絶対にGitにコミットしないでください
- **本番環境での使用**: 本番環境で使用する場合は、適切な認証機能を追加してください
- **CORS設定**: 必要に応じて `backend/main.py` のCORS設定を適切に制限してください

## 📝 API仕様

### エンドポイント

#### POST /api/validate
プロトコルと画像を検証

**リクエスト:**
- `protocol_file`: プロトコルファイル (.py)
- `image_file`: セッティング画像 (.jpg, .png)

**レスポンス:**
```json
{
  "success": true,
  "checkpoints": [
    {
      "id": 1,
      "description": "C2にピペットチップラックが配置されているか",
      "result": "pass",
      "details": ""
    }
  ],
  "overall_result": "pass"
}
```

#### POST /api/checkpoints
チェックポイントのみを生成

**リクエスト:**
- `protocol_file`: プロトコルファイル (.py)

**レスポンス:**
```json
{
  "checkpoints": [
    {
      "id": 1,
      "category": "labware_position",
      "description": "チェック項目の説明",
      "expected": "期待される状態"
    }
  ]
}
```

## 🔮 将来的な拡張可能性

- 複数画像の同時検証
- カスタムチェックポイントの追加UI
- 検証履歴の保存
- 画像アノテーション（問題箇所のハイライト）
- 他のロボットプラットフォームへの対応
- ユーザー認証機能
- データベース連携

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

バグ報告、機能リクエスト、プルリクエストを歓迎します。

## 📧 サポート

問題が発生した場合は、GitHubのIssueセクションで報告してください。

---

**注意**: このシステムはAI（Gemini）による検証を使用しているため、100%の精度を保証するものではありません。重要な実験の前には、必ず人間による最終確認を行ってください。

