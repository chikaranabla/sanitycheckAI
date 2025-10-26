"""
Gemini API Service for Protocol Validation
"""

import os
import json
import google.generativeai as genai
from typing import Dict, Any, List
from .prompts import SYSTEM_INSTRUCTION, PHASE1_PROMPT_TEMPLATE, PHASE2_PROMPT


class GeminiService:
    """Gemini APIを使用してプロトコル検証を行うサービス"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini Service
        
        Args:
            api_key: Google AI API Key (if not provided, uses GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API Key is required")
        
        genai.configure(api_key=self.api_key)
        
        # Gemini モデルの初期化
        # 注: system_instructionはチャットの最初のメッセージとして送信します
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro"
        )
        
        self.chat = None
        self.system_instruction = SYSTEM_INSTRUCTION
    
    def generate_checkpoints(self, protocol_content: str) -> Dict[str, Any]:
        """
        フェーズ1: プロトコルファイルからチェックポイントを生成
        
        Args:
            protocol_content: プロトコルファイルの内容
            
        Returns:
            チェックポイントのリスト
        """
        # 新しいチャットセッションを開始
        self.chat = self.model.start_chat(history=[])
        
        # System Instructionとプロンプトを結合
        full_prompt = f"{self.system_instruction}\n\n{PHASE1_PROMPT_TEMPLATE.format(protocol_content=protocol_content)}"
        
        # Gemini APIを呼び出し
        response = self.chat.send_message(full_prompt)
        
        # レスポンスからJSONを抽出
        try:
            # レスポンステキストからJSON部分を抽出
            response_text = response.text
            
            # マークダウンのコードブロックを削除
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            checkpoints_data = json.loads(response_text)
            return checkpoints_data
        except json.JSONDecodeError as e:
            # JSONパースに失敗した場合
            print(f"JSON parse error: {e}")
            print(f"Response text: {response_text}")
            # フォールバック: テキストから手動でチェックポイントを抽出
            return {
                "checkpoints": [
                    {
                        "id": 1,
                        "category": "error",
                        "description": "チェックポイントの生成に失敗しました",
                        "expected": response.text
                    }
                ]
            }
    
    def validate_image(self, image_path: str) -> Dict[str, Any]:
        """
        フェーズ2: 画像を検証
        
        Args:
            image_path: 検証する画像のパス
            
        Returns:
            検証結果
        """
        if not self.chat:
            raise ValueError("チェックポイントを先に生成してください")
        
        # 画像をアップロード
        uploaded_file = genai.upload_file(image_path)
        
        # 画像と共にプロンプトを送信
        response = self.chat.send_message([PHASE2_PROMPT, uploaded_file])
        
        # レスポンスからJSONを抽出
        try:
            response_text = response.text
            
            # マークダウンのコードブロックを削除
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            validation_result = json.loads(response_text)
            
            # ファイルをクリーンアップ
            genai.delete_file(uploaded_file.name)
            
            return validation_result
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response text: {response_text}")
            
            # クリーンアップ
            genai.delete_file(uploaded_file.name)
            
            return {
                "results": [
                    {
                        "id": 1,
                        "result": "fail",
                        "details": f"検証結果のパースに失敗しました: {response.text}"
                    }
                ]
            }
    
    def full_validation(self, protocol_content: str, image_path: str) -> Dict[str, Any]:
        """
        完全な検証プロセスを実行（チェックポイント生成 + 画像検証）
        
        Args:
            protocol_content: プロトコルファイルの内容
            image_path: 検証する画像のパス
            
        Returns:
            完全な検証結果
        """
        # フェーズ1: チェックポイント生成
        checkpoints_data = self.generate_checkpoints(protocol_content)
        
        # フェーズ2: 画像検証
        validation_data = self.validate_image(image_path)
        
        # 結果を統合
        checkpoints = checkpoints_data.get("checkpoints", [])
        results = validation_data.get("results", [])
        
        # チェックポイントと結果をマージ
        merged_results = []
        for checkpoint in checkpoints:
            checkpoint_id = checkpoint.get("id")
            # 対応する結果を検索
            result = next(
                (r for r in results if r.get("id") == checkpoint_id),
                {"result": "unknown", "details": "検証結果が見つかりません"}
            )
            
            merged_results.append({
                "id": checkpoint_id,
                "description": checkpoint.get("description", ""),
                "result": result.get("result", "unknown"),
                "details": result.get("details", "")
            })
        
        # 全体の結果を判定
        overall_result = "pass" if all(
            r.get("result") == "pass" for r in merged_results
        ) else "fail"
        
        return {
            "success": True,
            "checkpoints": merged_results,
            "overall_result": overall_result
        }

