#!/bin/bash
# STAGING環境起動スクリプト
# 自動生成 - 2025-06-11T15:04:33.039503

export FLASK_ENV=staging
export FLASK_APP=app_unified.py

echo "========================================="
echo "STAGING環境を起動しています..."
echo "========================================="

python app_unified.py
