"""データ管理モジュール - ユーザーデータの永続化とバックアップ"""

import json
import os
from datetime import datetime
from typing import Dict, Any


class DataManager:
    """ユーザーデータの保存・読み込み・バックアップを管理"""

    def __init__(self, data_dir: str = "./data"):
        """
        Args:
            data_dir: データディレクトリのパス
        """
        self.data_dir = data_dir
        self.user_data_path = os.path.join(data_dir, "user_data.json")
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """データディレクトリが存在しない場合は作成"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load_user_data(self) -> Dict[str, Any]:
        """
        ユーザーデータを読み込む

        Returns:
            ユーザーデータの辞書
        """
        if os.path.exists(self.user_data_path):
            try:
                with open(self.user_data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"データ読み込みエラー: {e}")
                return self._create_empty_user_data()
        return self._create_empty_user_data()

    def save_user_data(self, data: Dict[str, Any]) -> bool:
        """
        ユーザーデータを保存

        Args:
            data: 保存するユーザーデータ

        Returns:
            保存成功時True、失敗時False
        """
        try:
            # メタデータの更新
            data['meta']['last_updated'] = datetime.now().isoformat()

            # JSONファイルに保存
            with open(self.user_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, TypeError) as e:
            print(f"データ保存エラー: {e}")
            return False

    def export_backup(self) -> bytes:
        """
        バックアップデータを生成

        Returns:
            JSON形式のバックアップデータ（bytes）
        """
        data = self.load_user_data()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return json_str.encode('utf-8')

    def import_backup(self, file_bytes: bytes) -> bool:
        """
        バックアップデータをインポート

        Args:
            file_bytes: インポートするJSONデータ（bytes）

        Returns:
            インポート成功時True、失敗時False
        """
        try:
            json_str = file_bytes.decode('utf-8')
            data = json.loads(json_str)

            # データ構造の基本検証
            if not self._validate_user_data(data):
                print("バックアップデータの構造が不正です")
                return False

            return self.save_user_data(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"バックアップインポートエラー: {e}")
            return False

    def _create_empty_user_data(self) -> Dict[str, Any]:
        """
        空のユーザーデータ構造を作成

        Returns:
            初期化されたユーザーデータ
        """
        return {
            "meta": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "sessions": [],
            "vocabulary_bank": [],
            "statistics": {
                "total_sessions": 0,
                "total_words_learned": 0,
                "quiz_accuracy": 0.0,
                "streak_days": 0,
                "last_study_date": None
            }
        }

    def _validate_user_data(self, data: Dict[str, Any]) -> bool:
        """
        ユーザーデータの構造を検証

        Args:
            data: 検証するデータ

        Returns:
            有効な構造の場合True
        """
        required_keys = {'meta', 'sessions', 'vocabulary_bank', 'statistics'}
        return all(key in data for key in required_keys)
