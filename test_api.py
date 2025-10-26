"""
API動作確認用の簡易テストスクリプト
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from backend.gemini_service import GeminiService


def test_checkpoint_generation():
    """チェックポイント生成のテスト"""
    print("=" * 60)
    print("チェックポイント生成のテスト")
    print("=" * 60)
    
    # サンプルプロトコルを読み込み
    protocol_path = Path(__file__).parent / "96-ch_partial_test.py"
    
    if not protocol_path.exists():
        print("❌ エラー: サンプルプロトコルファイルが見つかりません")
        return False
    
    with open(protocol_path, "r", encoding="utf-8") as f:
        protocol_content = f.read()
    
    print(f"✅ プロトコルファイルを読み込みました: {protocol_path.name}")
    print(f"   内容: {len(protocol_content)} 文字\n")
    
    # Geminiサービスを初期化
    try:
        service = GeminiService()
        print("✅ Geminiサービスを初期化しました\n")
    except ValueError as e:
        print(f"❌ エラー: {e}")
        print("\n💡 解決方法:")
        print("   1. .envファイルを作成してください")
        print("   2. GOOGLE_API_KEY=your_api_key_here を追加してください")
        print("   3. https://makersuite.google.com/app/apikey でAPIキーを取得できます\n")
        return False
    
    # チェックポイントを生成
    print("🔄 チェックポイントを生成中...\n")
    try:
        checkpoints_data = service.generate_checkpoints(protocol_content)
        
        if "checkpoints" in checkpoints_data:
            checkpoints = checkpoints_data["checkpoints"]
            print(f"✅ チェックポイントを生成しました: {len(checkpoints)}個\n")
            
            for i, checkpoint in enumerate(checkpoints, 1):
                print(f"チェックポイント #{i}:")
                print(f"  説明: {checkpoint.get('description', 'N/A')}")
                print(f"  カテゴリ: {checkpoint.get('category', 'N/A')}")
                print(f"  期待値: {checkpoint.get('expected', 'N/A')[:100]}...")
                print()
            
            return True
        else:
            print("❌ チェックポイントの生成に失敗しました")
            print(f"   レスポンス: {checkpoints_data}")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_validation():
    """完全な検証プロセスのテスト"""
    print("\n" + "=" * 60)
    print("完全な検証プロセスのテスト")
    print("=" * 60)
    
    # サンプルプロトコルを読み込み
    protocol_path = Path(__file__).parent / "96-ch_partial_test.py"
    image_path = Path(__file__).parent / "good_photo_1.jpg"
    
    if not protocol_path.exists():
        print("❌ エラー: サンプルプロトコルファイルが見つかりません")
        return False
    
    if not image_path.exists():
        print("❌ エラー: サンプル画像が見つかりません")
        return False
    
    with open(protocol_path, "r", encoding="utf-8") as f:
        protocol_content = f.read()
    
    print(f"✅ プロトコルファイル: {protocol_path.name}")
    print(f"✅ 画像ファイル: {image_path.name}\n")
    
    # Geminiサービスを初期化
    try:
        service = GeminiService()
        print("✅ Geminiサービスを初期化しました\n")
    except ValueError as e:
        print(f"❌ エラー: {e}")
        return False
    
    # 完全な検証を実行
    print("🔄 検証を実行中...\n")
    try:
        result = service.full_validation(
            protocol_content=protocol_content,
            image_path=str(image_path)
        )
        
        print(f"✅ 検証が完了しました\n")
        print(f"総合判定: {'✅ 合格' if result['overall_result'] == 'pass' else '❌ 不合格'}\n")
        
        print("チェックポイント詳細:")
        for checkpoint in result.get("checkpoints", []):
            status = "✅" if checkpoint["result"] == "pass" else "❌"
            print(f"{status} #{checkpoint['id']}: {checkpoint['description']}")
            if checkpoint.get("details"):
                print(f"   詳細: {checkpoint['details']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_environment():
    """環境確認"""
    print("=" * 60)
    print("環境確認")
    print("=" * 60)
    
    # .envファイルの確認
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print("✅ .envファイルが存在します")
    else:
        print("❌ .envファイルが見つかりません")
        return False
    
    # API Keyの確認
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ GOOGLE_API_KEYが設定されています（長さ: {len(api_key)}文字）")
    else:
        print("❌ GOOGLE_API_KEYが設定されていません")
        return False
    
    # サンプルファイルの確認
    protocol_path = Path(__file__).parent / "96-ch_partial_test.py"
    if protocol_path.exists():
        print(f"✅ サンプルプロトコルが存在します: {protocol_path.name}")
    else:
        print("❌ サンプルプロトコルが見つかりません")
        return False
    
    image_path = Path(__file__).parent / "good_photo_1.jpg"
    if image_path.exists():
        print(f"✅ サンプル画像が存在します: {image_path.name}")
    else:
        print("❌ サンプル画像が見つかりません")
        return False
    
    print()
    return True


def main():
    """メイン関数"""
    from dotenv import load_dotenv
    
    # .envファイルを読み込み
    load_dotenv()
    
    print("\n🔬 Opentrons Protocol Sanity Check - API動作確認\n")
    
    # 環境確認
    if not check_environment():
        print("\n❌ 環境設定に問題があります。上記のメッセージを確認してください。")
        return
    
    # テストを実行
    print("\n実行するテストを選択してください:")
    print("1. チェックポイント生成のみ")
    print("2. 完全な検証プロセス（チェックポイント生成 + 画像検証）")
    print("3. 両方を実行")
    
    choice = input("\n選択 (1/2/3): ").strip()
    
    if choice == "1":
        test_checkpoint_generation()
    elif choice == "2":
        test_full_validation()
    elif choice == "3":
        success1 = test_checkpoint_generation()
        if success1:
            success2 = test_full_validation()
            if success1 and success2:
                print("\n✅ すべてのテストが正常に完了しました！")
        else:
            print("\n❌ テストが失敗しました")
    else:
        print("\n❌ 無効な選択です")


if __name__ == "__main__":
    main()

