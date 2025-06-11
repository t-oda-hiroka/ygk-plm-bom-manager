"""
釣り糸製造BOM管理システム 設定管理
環境別設定とデプロイメント管理
"""

import os
from datetime import datetime

class Config:
    """基本設定クラス"""
    # 共通設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bom_management_secret_key_2024'
    
    # データベース設定
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # アプリケーション設定
    APP_NAME = "釣り糸製造BOM管理システム"
    VERSION = "v1.0"
    
    # アイテムタイプ定数（製造工程の逆順：完成品→原糸）
    ITEM_TYPES = [
        '完成品', '巻き取り糸', '後PS糸', '染色糸', '製紐糸', 
        'PS糸', '原糸', '成形品', '梱包資材', '芯糸'
    ]
    
    # 用途タイプ定数
    USAGE_TYPES = [
        'Main Material', 'Main Braid Thread', 'Core Thread',
        'Packaging', 'Container', 'Process Material'
    ]
    
    # 単位定数
    UNITS = ['KG', 'M', '個', '枚', 'セット', '本']
    MATERIAL_TYPES = ['EN', 'SK', 'AL', 'PE', 'ナイロン', 'その他']
    TWIST_TYPES = ['S', 'Z']
    KNIT_TYPES = ['X8', 'X4', 'X9', 'X5', 'X16', 'X6丸', 'その他']
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    ENVIRONMENT = "DEVELOPMENT"
    DATABASE_PATH = "bom_database_dev.db"
    SCHEMA_FILE = "schema_enhanced.sql"
    HOST = '0.0.0.0'  # 社内LAN対応
    PORT = 5002
    
    # 開発用機能
    ENABLE_DEBUG_TOOLBAR = True
    ENABLE_PROFILER = True
    ENABLE_SAMPLE_DATA = True  # サンプルデータを有効化
    
    # Oracle接続（開発用）
    ORACLE_ENABLED = True
    ORACLE_CONNECTION_STRING = os.environ.get('ORACLE_DEV_CONNECTION')


class StagingConfig(Config):
    """ステージング環境設定"""
    DEBUG = False
    ENVIRONMENT = "STAGING"
    DATABASE_PATH = "bom_database_staging.db"
    SCHEMA_FILE = "schema_enhanced.sql"
    HOST = '0.0.0.0'
    PORT = 5003
    
    # ステージング用機能
    ENABLE_RESET_FUNCTION = True
    ENABLE_SAMPLE_DATA = True
    SHOW_ENVIRONMENT_BANNER = True
    
    # Oracle接続（ステージング用）
    ORACLE_ENABLED = False  # サンプルデータを使用
    MOCK_ORACLE_DATA = True


class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    ENVIRONMENT = "PRODUCTION"
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or "bom_database_prod.db"
    SCHEMA_FILE = "schema_enhanced.sql"
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5001))
    
    # 本番用セキュリティ
    ENABLE_RESET_FUNCTION = False
    ENABLE_SAMPLE_DATA = False
    SHOW_ENVIRONMENT_BANNER = False
    
    # Oracle接続（本番用）
    ORACLE_ENABLED = True
    ORACLE_CONNECTION_STRING = os.environ.get('ORACLE_PROD_CONNECTION')
    
    # ログ設定
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'bom_manager_prod.log'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # 本番用ログ設定
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                ProductionConfig.LOG_FILE, maxBytes=10240000, backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('BOM Manager startup')


class TestingConfig(Config):
    """テスト環境設定"""
    TESTING = True
    ENVIRONMENT = "TESTING"
    DATABASE_PATH = ":memory:"  # インメモリデータベース
    SCHEMA_FILE = "schema_enhanced.sql"
    HOST = '127.0.0.1'
    PORT = 5999
    
    # テスト用設定
    WTF_CSRF_ENABLED = False
    ORACLE_ENABLED = False


# 環境設定マッピング
config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(environment=None):
    """環境に応じた設定を取得"""
    if environment is None:
        environment = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(environment, config['default'])


def create_deployment_info():
    """デプロイメント情報を生成"""
    return {
        'deployed_at': datetime.now().isoformat(),
        'version': Config.VERSION,
        'git_commit': os.environ.get('GIT_COMMIT', 'unknown'),
        'build_number': os.environ.get('BUILD_NUMBER', 'manual')
    } 