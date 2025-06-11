#!/bin/bash

# 統一環境管理システム 起動スクリプト

case "$1" in
    "dev"|"development")
        echo "==========================================="
        echo "DEVELOPMENT環境を起動しています..."
        echo "==========================================="
        export FLASK_ENV=development
        export FLASK_DEBUG=false  # バックグラウンド実行のためデバッグ無効
        nohup python app_unified.py > dev.log 2>&1 &
        echo "開発環境を起動しました (PID: $!)"
        echo "アクセス: http://192.168.212.112:5002"
        ;;
    "staging")
        echo "==========================================="
        echo "STAGING環境を起動しています..."
        echo "==========================================="
        export FLASK_ENV=staging
        export FLASK_DEBUG=false
        nohup python app_unified.py > staging.log 2>&1 &
        echo "ステージング環境を起動しました (PID: $!)"
        echo "アクセス: http://192.168.212.112:5003"
        ;;
    "both")
        echo "==========================================="
        echo "両環境を起動しています..."
        echo "==========================================="
        
        # 開発環境
        export FLASK_ENV=development
        export FLASK_DEBUG=false
        nohup python app_unified.py > dev.log 2>&1 &
        DEV_PID=$!
        
        sleep 2
        
        # ステージング環境
        export FLASK_ENV=staging
        export FLASK_DEBUG=false
        nohup python app_unified.py > staging.log 2>&1 &
        STAGING_PID=$!
        
        echo "開発環境を起動しました (PID: $DEV_PID)"
        echo "ステージング環境を起動しました (PID: $STAGING_PID)"
        echo "開発環境: http://192.168.212.112:5002"
        echo "ステージング環境: http://192.168.212.112:5003"
        ;;
    "stop")
        echo "統一環境を停止しています..."
        pkill -f app_unified.py
        echo "停止完了"
        ;;
    "status")
        echo "===== プロセス状況 ====="
        ps aux | grep app_unified.py | grep -v grep
        echo ""
        echo "===== ポート使用状況 ====="
        lsof -i :5002 -i :5003 2>/dev/null || echo "ポート使用なし"
        ;;
    *)
        echo "使用方法: $0 {dev|staging|both|stop|status}"
        echo ""
        echo "  dev      - 開発環境のみ起動"
        echo "  staging  - ステージング環境のみ起動" 
        echo "  both     - 両環境を起動"
        echo "  stop     - 全環境を停止"
        echo "  status   - 状況確認"
        exit 1
        ;;
esac 