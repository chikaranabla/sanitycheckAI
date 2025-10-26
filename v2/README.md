# SanityCheck AI V2 - Chat Interface

## 概要

V2では、AIとのチャットベースのインターフェースを通じて、Opentrons実験セットアップの検証とプロトコル実行を行います。

## 主な変更点

### 1. チャットベースのUI
- ファイルアップロード（protocol.pyのみ）
- リアルタイムチャット機能
- AI誘導による段階的なセットアップ検証

### 2. MCP統合
- **カメラ撮影**: AIが判断して自動的にセットアップ画像を撮影
- **ロボット実行**: 検証成功後、AIが自動的にプロトコルを実行

### 3. ワークフロー

```
1. ユーザーがprotocol.pyをアップロード
   ↓
2. AIがプロトコルを分析し、必要なセットアップを説明
   ↓
3. ユーザーが物理的なセットアップを実行
   ↓
4. ユーザーが「セットアップ完了」と伝える
   ↓
5. AIがカメラで撮影（MCP: take_photo）
   ↓
6. AIがセットアップを検証（チェックポイント照合）
   ↓
7a. 検証成功 → AIがプロトコルを実行（MCP: upload_and_run）
7b. 検証失敗 → AIが修正を指示 → ステップ3に戻る
```

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成して以下を設定：

```bash
# Gemini API Key（必須）
GOOGLE_API_KEY=your_gemini_api_key_here

# Opentrons Robot IP（オプション、デフォルト: 192.168.68.119:31950）
OPENTRONS_HOST=192.168.68.119:31950

# Camera Settings（オプション）
CAMERA_DEVICE_INDEX=0
CAMERA_WIDTH=1920
CAMERA_HEIGHT=1080
```

### 3. MCPサーバーの起動

#### ターミナル1: カメラサーバー
```bash
cd v2
python camera_server.py
```

#### ターミナル2: Opentrons サーバー
```bash
cd v2
python opentrons_server.py
```

### 4. Webアプリケーションの起動

#### ターミナル3: バックエンド
```bash
python -m backend.main
```

ブラウザで `http://localhost:8000` にアクセス

## 使用方法

### 1. プロトコルのアップロード
- 「Protocol File (.py)」からOpentrons プロトコルファイルを選択
- 「Start Chat」をクリック

### 2. チャット開始
- AIが挨拶し、必要なセットアップを説明します
- メッセージをよく読んで、指示に従ってください

### 3. セットアップ実行
- 物理的にLabwareを配置
- Tip rackにチップを充填
- その他プロトコルに必要な準備を完了

### 4. セットアップ完了の通知
チャット欄に以下のようなメッセージを送信：
- 「セットアップ完了しました」
- 「Setup done」
- 「Ready」
- 「Finished」

### 5. 自動検証
- AIが自動的にカメラで撮影
- 撮影した画像を表示
- チェックポイントに基づいて検証

### 6. 結果確認
- **✅ 全てパス**: AIがプロトコル実行を開始
- **❌ 失敗**: AIが具体的な修正点を指示
  - 修正後、再度「セットアップ完了」と送信

## APIエンドポイント

### チャット関連

#### POST `/api/chat/start`
新しいチャットセッションを開始
- **Body**: `protocol_file` (multipart/form-data)
- **Response**: `{ session_id, message, protocol_name }`

#### POST `/api/chat/message`
メッセージを送信
- **Body**: `session_id`, `message` (form-data)
- **Response**: `{ message, image_url, checkpoints, action, protocol_executed }`

#### GET `/api/chat/history/{session_id}`
チャット履歴を取得
- **Response**: `{ session_id, messages[] }`

#### GET `/api/chat/image/{session_id}/{image_index}`
撮影された画像を取得
- **Response**: PNG画像

## アーキテクチャ

```
Frontend (HTML/CSS/JS)
    ↓ HTTP
Backend (FastAPI)
    ↓
ChatService (Gemini + Session Management)
    ↓
MCPClient
    ↓
[camera_server.py]  [opentrons_server.py]
       ↓                    ↓
    Camera            Opentrons Robot
```

## トラブルシューティング

### カメラが見つからない
- カメラが接続されているか確認
- `CAMERA_DEVICE_INDEX` を変更してみる（0, 1, 2...）

### Opentrons接続エラー
- ロボットのIPアドレスが正しいか確認
- ロボットが起動しているか確認
- `OPENTRONS_HOST` 環境変数を確認

### MCPサーバーが起動しない
- `mcp` と `fastmcp` がインストールされているか確認
- Python 3.8以上を使用しているか確認

### AIが画像を撮影しない
- ユーザーメッセージに「完了」「done」「ready」などのキーワードが含まれているか確認
- MCPサーバー（camera_server.py）が起動しているか確認

## 開発者向け情報

### 新しいファイル
- `backend/mcp_client.py` - MCPクライアント
- `backend/chat_service.py` - チャットロジック
- `v2/config.py` - 設定管理

### 主な変更
- `backend/prompts.py` - チャット用プロンプト追加
- `backend/main.py` - チャットエンドポイント追加
- `frontend/*` - チャットUI実装

### システムプロンプト
AIの動作は `backend/prompts.py` の `CHAT_SYSTEM_INSTRUCTION` で定義されています。
必要に応じてカスタマイズできます。

## ライセンス

© 2024 SanityCheck AI

