# クイックスタートガイド

このガイドでは、最速で Opentrons Protocol Sanity Check System を起動し、動作確認する手順を説明します。

## ⏱️ 5分で始める

### ステップ1: Google AI API Keyの取得（2分）

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. **"Create API Key"** をクリック
4. 生成されたAPIキーをコピー（後で使用します）

### ステップ2: 環境のセットアップ（2分）

```bash
# 1. プロジェクトディレクトリに移動
cd sanitycheckAI

# 2. 仮想環境の作成（Windows）
python -m venv venv
venv\Scripts\activate

# 仮想環境の作成（macOS/Linux）
python3 -m venv venv
source venv/bin/activate

# 3. 依存関係のインストール
pip install -r requirements.txt

# 4. 環境変数ファイルの作成
# Windowsの場合
echo GOOGLE_API_KEY=ここに先ほどコピーしたAPIキーを貼り付け > .env
echo PORT=8000 >> .env

# macOS/Linuxの場合
echo "GOOGLE_API_KEY=ここに先ほどコピーしたAPIキーを貼り付け" > .env
echo "PORT=8000" >> .env
```

**重要**: `.env` ファイルの `GOOGLE_API_KEY=` の後に、ステップ1でコピーしたAPIキーを貼り付けてください。

### ステップ3: サーバーの起動（1分）

```bash
# サーバーを起動
python -m backend.main
```

以下のようなメッセージが表示されれば成功です：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### ステップ4: ブラウザでアクセス

ブラウザで以下のURLを開きます：

```
http://localhost:8000
```

## 🧪 サンプルファイルで動作確認

プロジェクトに含まれるサンプルファイルを使用して、システムの動作を確認できます。

### 正しいセッティングのテスト

1. **プロトコルファイル**: `96-ch_partial_test.py` を選択
2. **画像ファイル**: `good_photo_1.jpg` を選択
3. **検証開始** ボタンをクリック

結果: ✅ すべてのチェックポイントが合格するはずです

### 誤ったセッティングのテスト

1. **プロトコルファイル**: `96-ch_partial_test.py` を選択
2. **画像ファイル**: `bad_photo_1.jpg` または `bad_photo_2.jpg` を選択
3. **検証開始** ボタンをクリック

結果: ❌ 一部のチェックポイントで問題が検出されるはずです

## 📊 結果の見方

### 総合判定

- **✅ 検証成功**: すべてのチェックポイントをクリア
- **❌ 検証失敗**: 1つ以上のチェックポイントで問題を検出

### チェックポイント詳細

各チェックポイントには以下の情報が表示されます：

- **番号**: チェック項目の識別番号
- **説明**: 何を確認しているか
- **結果**: ✅（合格）または ❌（不合格）
- **詳細**: 判定の理由や追加情報

## 🎯 期待される動作

### プロトコル: `96-ch_partial_test.py`

このプロトコルでは以下の配置が期待されます：

1. **C2**: 96 Filter Tiprack 1000µL（すべてのチップが埋まっている）
2. **A3**: ゴミ箱（trash bin）
3. **その他の位置**: 何も配置されていない

### good_photo_1.jpg の場合

- C2にチップラックが正しく配置されている
- すべてのチップが揃っている
- A3にゴミ箱がある
- 不要な場所に何も置かれていない

→ **結果**: ✅ すべて合格

### bad_photo_*.jpg の場合

様々な問題が含まれています：

- チップが不足している
- 位置が間違っている
- 不要なものが配置されている

→ **結果**: ❌ 問題が検出される

## 🔧 トラブルシューティング

### サーバーが起動しない

```bash
# エラーメッセージを確認
python -m backend.main
```

**よくある原因:**
- `.env` ファイルが作成されていない
- APIキーが設定されていない
- ポート8000が使用中

**解決方法:**
```bash
# .env ファイルの確認
cat .env  # macOS/Linux
type .env  # Windows

# 別のポートで起動
# .env ファイルで PORT=8001 に変更
```

### "Google API Key is required" エラー

`.env` ファイルを確認してください：

```env
GOOGLE_API_KEY=実際のAPIキー
PORT=8000
```

APIキーが正しく設定されているか、スペースや改行が余分に入っていないか確認してください。

### ブラウザでページが表示されない

1. サーバーが起動しているか確認
2. URLが正しいか確認: `http://localhost:8000`
3. 別のブラウザで試す
4. キャッシュをクリアする

### 検証が遅い

Gemini APIの呼び出しには時間がかかる場合があります（10-30秒程度）。
ネットワーク接続が安定していることを確認してください。

## 🎓 次のステップ

システムが正常に動作したら、以下を試してみましょう：

1. **独自のプロトコルファイルでテスト**
   - あなたのOpentrons実験プロトコルをアップロード
   - 実際のセッティング写真で検証

2. **APIを直接使用**
   - `/api/validate` エンドポイントをcURLやPythonから呼び出し
   - 自動化スクリプトに組み込む

3. **コードをカスタマイズ**
   - `backend/prompts.py` でチェック項目を調整
   - `frontend/` でUIをカスタマイズ

## 📚 詳細情報

より詳しい情報は、以下のドキュメントを参照してください：

- [README.md](../README.md): 完全なドキュメント
- [requirements.md](requirements.md): 要件定義書
- [FastAPI ドキュメント](http://localhost:8000/docs): APIの詳細仕様（サーバー起動後にアクセス）

## 💡 ヒント

- **画像の撮り方**: デッキ全体が見えるように真上から撮影すると、AIの判定精度が上がります
- **プロトコルの作成**: load_labware()とload_trash_bin()の位置指定を明確に記述してください
- **結果の解釈**: AIの判定は参考情報です。最終的な確認は人間が行ってください

---

**問題が解決しない場合は、GitHubのIssueで質問してください。**

