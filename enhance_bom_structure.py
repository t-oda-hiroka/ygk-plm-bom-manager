#!/usr/bin/env python3
"""
BOM構造大幅拡張スクリプト
Oracleデータに基づく現実的で詳細なBOM構造を作成
"""

import sqlite3
from bom_manager import BOMManager
import os
import sys

def create_enhanced_bom_structure():
    """Oracle風の詳細なBOM構造を作成"""
    
    print("🔧 BOM構造を大幅拡張中...")
    
    bom_manager = BOMManager('bom_database_dev.db')
    
    # まず、現在のリアルデータ作成スクリプトを実行
    try:
        exec(open('create_realistic_data.py').read())
        print("✅ リアルデータ作成完了")
    except Exception as e:
        print(f"⚠️ リアルデータ作成でエラー: {e}")
        # 既存データを使用して続行
    
    # Oracle風の詳細なBOM構成を追加
    oracle_bom_structure = [
        # ============= 完成品レベル =============
        
        # モノフィラメント製品のBOM
        {
            'parent': 'MONO-NY6-10',
            'components': [
                ('NY6-DYE-BLU-020', 1.0, 'Main Material'),  # 染色糸を直接使用
                ('PKG-SPOOL-150', 1.0, 'Container'),        # スプール
                ('PKG-LABEL-MONO', 1.0, 'Packaging'),       # ラベル
            ]
        },
        {
            'parent': 'MONO-NY6-15',
            'components': [
                ('NY6-DYE-GRN-025', 1.0, 'Main Material'),
                ('PKG-SPOOL-150', 1.0, 'Container'),
                ('PKG-LABEL-MONO', 1.0, 'Packaging'),
            ]
        },
        {
            'parent': 'MONO-FC-20',
            'components': [
                ('FC-CLR-030', 1.0, 'Main Material'),       # フロロカーボン糸
                ('PKG-SPOOL-200', 1.0, 'Container'),
                ('PKG-LABEL-MONO', 1.0, 'Packaging'),
            ]
        },
        
        # PEブレイデッド製品のBOM
        {
            'parent': 'BRAID-PE-10',
            'components': [
                ('PE-X8-150', 1.0, 'Main Material'),        # PE編み糸
                ('PKG-SPOOL-150', 1.0, 'Container'),
                ('PKG-LABEL-BRAID', 1.0, 'Packaging'),
            ]
        },
        {
            'parent': 'BRAID-PE-15',
            'components': [
                ('PE-X8-150', 1.0, 'Main Material'),
                ('PKG-SPOOL-200', 1.0, 'Container'),
                ('PKG-LABEL-BRAID', 1.0, 'Packaging'),
            ]
        },
        {
            'parent': 'BRAID-PE-20',
            'components': [
                ('PE-X4-200', 1.0, 'Main Material'),        # 4本編み糸
                ('PKG-SPOOL-200', 1.0, 'Container'),
                ('PKG-LABEL-BRAID', 1.0, 'Packaging'),
            ]
        },
        
        # スプール製品のBOM（既存製品＋スプール＋包装）
        {
            'parent': 'SPOOL-MONO-NY6-10-150',
            'components': [
                ('MONO-NY6-10', 150.0, 'Main Material'),    # 完成品糸を150m分
                ('PKG-SPOOL-150', 1.0, 'Container'),
                ('PKG-BOX-SINGLE', 1.0, 'Packaging'),
                ('PKG-LABEL-MONO', 2.0, 'Packaging'),       # 製品ラベル＋スプールラベル
            ]
        },
    ]

    # データベースにBOM構造を追加
    for item in oracle_bom_structure:
        bom_manager.add_bom_item(item['parent'], item['components'])

    print("✅ BOM構造の拡張が完了しました") 