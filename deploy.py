#!/usr/bin/env python3
"""
釣り糸製造BOM管理システム デプロイメントスクリプト
開発環境からステージング、本番への自動昇格を支援
"""

import os
import sys
import shutil
import sqlite3
import subprocess
import json
from datetime import datetime
from pathlib import Path


class BOMDeploymentManager:
    """BOMシステムのデプロイメント管理クラス"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.environments = ['development', 'staging', 'production']
        self.required_files = [
            'app_unified.py',
            'config.py',
            'bom_manager.py',
            'schema_enhanced.sql',
            'requirements.txt'
        ]
    
    def validate_environment(self, env):
        """環境名の検証"""
        if env not in self.environments:
            raise ValueError(f"無効な環境名: {env}. 有効な環境: {', '.join(self.environments)}")
    
    def check_prerequisites(self):
        """前提条件の確認"""
        print("🔍 前提条件を確認しています...")
        
        missing_files = []
        for file in self.required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ 必要なファイルが見つかりません: {', '.join(missing_files)}")
            return False
        
        print("✅ すべての必要ファイルが存在します")
        return True
    
    def backup_database(self, source_env):
        """データベースのバックアップ"""
        from config import get_config
        
        config_class = get_config(source_env)
        source_db = config_class.DATABASE_PATH
        
        if not os.path.exists(source_db):
            print(f"⚠️  ソースデータベースが見つかりません: {source_db}")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup_{source_env}_{timestamp}.db"
        
        shutil.copy2(source_db, backup_path)
        print(f"💾 データベースをバックアップしました: {backup_path}")
        
        return backup_path
    
    def migrate_database(self, source_env, target_env):
        """データベースの移行"""
        from config import get_config
        
        source_config = get_config(source_env)
        target_config = get_config(target_env)
        
        source_db = source_config.DATABASE_PATH
        target_db = target_config.DATABASE_PATH
        
        if not os.path.exists(source_db):
            print(f"❌ ソースデータベースが見つかりません: {source_db}")
            return False
        
        # バックアップ作成
        backup_path = self.backup_database(source_env)
        
        # データベースのコピー
        try:
            shutil.copy2(source_db, target_db)
            print(f"📋 データベースを移行しました: {source_db} → {target_db}")
            
            # 環境固有の調整
            self.adjust_database_for_environment(target_db, target_env)
            
            return True
            
        except Exception as e:
            print(f"❌ データベース移行エラー: {e}")
            return False
    
    def adjust_database_for_environment(self, db_path, env):
        """環境固有のデータベース調整"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            if env == 'production':
                # 本番環境用の調整
                print("🔧 本番環境用にデータベースを調整しています...")
                
                # テストデータの削除
                cursor.execute("DELETE FROM items WHERE item_id LIKE 'TEST_%' OR item_id LIKE 'SAMPLE_%'")
                cursor.execute("DELETE FROM bom_components WHERE parent_item_id LIKE 'TEST_%' OR component_item_id LIKE 'TEST_%'")
                
                # 本番用メタデータの追加
                cursor.execute("UPDATE items SET updated_at = CURRENT_TIMESTAMP")
                
                print("✅ 本番環境用調整完了")
                
            elif env == 'staging':
                # ステージング環境用の調整
                print("🔧 ステージング環境用にデータベースを調整しています...")
                
                # ステージング用メタデータの追加
                cursor.execute("UPDATE items SET updated_at = CURRENT_TIMESTAMP")
                
                print("✅ ステージング環境用調整完了")
            
            conn.commit()
            
        except Exception as e:
            print(f"⚠️  データベース調整中にエラー: {e}")
            conn.rollback()
        
        finally:
            conn.close()
    
    def create_environment_script(self, env):
        """環境固有の起動スクリプト作成"""
        script_content = f"""#!/bin/bash
# {env.upper()}環境起動スクリプト
# 自動生成 - {datetime.now().isoformat()}

export FLASK_ENV={env}
export FLASK_APP=app_unified.py

echo "========================================="
echo "{env.upper()}環境を起動しています..."
echo "========================================="

python app_unified.py
"""
        
        script_path = f"start_{env}.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 実行権限の付与
        os.chmod(script_path, 0o755)
        print(f"📝 起動スクリプトを作成しました: {script_path}")
        
        return script_path
    
    def create_deployment_manifest(self, source_env, target_env):
        """デプロイメントマニフェストの作成"""
        manifest = {
            'deployment_info': {
                'timestamp': datetime.now().isoformat(),
                'source_environment': source_env,
                'target_environment': target_env,
                'deployed_by': os.environ.get('USER', 'unknown'),
                'git_commit': self.get_git_commit(),
                'version': 'v1.0'
            },
            'files_deployed': self.required_files,
            'database_migrated': True,
            'environment_config': {
                'host': '0.0.0.0' if target_env != 'development' else '127.0.0.1',
                'debug': target_env == 'development'
            }
        }
        
        manifest_path = f"deployment_manifest_{target_env}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"📋 デプロイメントマニフェストを作成しました: {manifest_path}")
        return manifest_path
    
    def get_git_commit(self):
        """現在のGitコミットハッシュを取得"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                 capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                return result.stdout.strip()[:7]  # 短縮形
        except:
            pass
        return 'unknown'
    
    def deploy(self, source_env, target_env, skip_database=False):
        """環境の昇格デプロイメント"""
        print(f"🚀 {source_env} → {target_env} への昇格を開始します")
        
        # 前提条件の確認
        if not self.check_prerequisites():
            return False
        
        # 環境の検証
        try:
            self.validate_environment(source_env)
            self.validate_environment(target_env)
        except ValueError as e:
            print(f"❌ {e}")
            return False
        
        # データベース移行
        if not skip_database:
            if not self.migrate_database(source_env, target_env):
                print("❌ データベース移行に失敗しました")
                return False
        else:
            print("⏭️  データベース移行をスキップしました")
        
        # 起動スクリプト作成
        script_path = self.create_environment_script(target_env)
        
        # デプロイメントマニフェスト作成
        manifest_path = self.create_deployment_manifest(source_env, target_env)
        
        print(f"✅ {target_env}環境への昇格が完了しました！")
        print(f"   起動方法: ./{script_path}")
        print(f"   または: FLASK_ENV={target_env} python app_unified.py")
        
        return True
    
    def rollback(self, env, backup_path):
        """ロールバック"""
        from config import get_config
        
        config_class = get_config(env)
        target_db = config_class.DATABASE_PATH
        
        if not os.path.exists(backup_path):
            print(f"❌ バックアップファイルが見つかりません: {backup_path}")
            return False
        
        try:
            shutil.copy2(backup_path, target_db)
            print(f"🔄 {env}環境をロールバックしました: {backup_path} → {target_db}")
            return True
        except Exception as e:
            print(f"❌ ロールバックエラー: {e}")
            return False
    
    def list_available_backups(self):
        """利用可能なバックアップの一覧表示"""
        backup_files = list(self.project_root.glob("backup_*.db"))
        
        if not backup_files:
            print("📂 利用可能なバックアップはありません")
            return []
        
        print("📂 利用可能なバックアップ:")
        for backup in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            size = backup.stat().st_size / 1024  # KB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"   {backup.name} ({size:.1f}KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        
        return [str(f) for f in backup_files]


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("""
🚀 BOM管理システム デプロイメントツール

使用方法:
  python deploy.py deploy <source_env> <target_env>    # 環境昇格
  python deploy.py rollback <env> <backup_path>        # ロールバック
  python deploy.py list-backups                        # バックアップ一覧
  python deploy.py check                               # 前提条件確認

環境名: development, staging, production

例:
  python deploy.py deploy development staging    # 開発→ステージング
  python deploy.py deploy staging production     # ステージング→本番
  python deploy.py check                         # 前提条件確認
        """)
        return
    
    manager = BOMDeploymentManager()
    command = sys.argv[1]
    
    if command == 'deploy':
        if len(sys.argv) < 4:
            print("❌ 使用方法: python deploy.py deploy <source_env> <target_env>")
            return
        
        source_env = sys.argv[2]
        target_env = sys.argv[3]
        skip_db = '--skip-database' in sys.argv
        
        manager.deploy(source_env, target_env, skip_database=skip_db)
    
    elif command == 'rollback':
        if len(sys.argv) < 4:
            print("❌ 使用方法: python deploy.py rollback <env> <backup_path>")
            return
        
        env = sys.argv[2]
        backup_path = sys.argv[3]
        manager.rollback(env, backup_path)
    
    elif command == 'list-backups':
        manager.list_available_backups()
    
    elif command == 'check':
        if manager.check_prerequisites():
            print("✅ デプロイメント準備完了")
        else:
            print("❌ 前提条件を満たしていません")
    
    else:
        print(f"❌ 不明なコマンド: {command}")


if __name__ == '__main__':
    main() 