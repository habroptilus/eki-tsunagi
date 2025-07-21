#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全エリアのクイズを一括生成するスクリプト

Usage:
    python generate_all_quizzes.py --iterations 10
    python generate_all_quizzes.py --areas central,osaka,nagoya --iterations 5
    python generate_all_quizzes.py --output output/quizzes --iterations 20
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from generate_quiz import generate_multiple_quizzes


def get_available_areas():
    """
    area.jsonから利用可能なエリアのリストを取得
    
    Returns:
        エリア名のリスト
    """
    try:
        with open('area.json', 'r', encoding='utf-8') as f:
            area_data = json.load(f)
        return list(area_data.keys())
    except FileNotFoundError:
        print("❌ area.json が見つかりません")
        return []
    except json.JSONDecodeError:
        print("❌ area.json の形式が無効です")
        return []


def generate_all_area_quizzes(areas=None, iterations=10, output_dir=".", verbose=True, min_max_components=4):
    """
    指定されたエリアのクイズを全て生成
    
    Args:
        areas: 生成するエリアのリスト (None の場合は全エリア)
        iterations: 各エリアのクイズ数
        output_dir: 出力ディレクトリ
        verbose: 詳細出力の有無
        min_max_components: 最大連結成分数の下限
        
    Returns:
        生成結果の辞書 {area_name: {"success": bool, "count": int, "filename": str}}
    """
    available_areas = get_available_areas()
    if not available_areas:
        return {}
    
    if areas is None:
        areas = available_areas
    else:
        # 指定されたエリアが存在するかチェック
        invalid_areas = [area for area in areas if area not in available_areas]
        if invalid_areas:
            print(f"⚠️ 無効なエリア: {invalid_areas}")
            print(f"✅ 利用可能なエリア: {available_areas}")
            areas = [area for area in areas if area in available_areas]
    
    if not areas:
        print("❌ 生成可能なエリアがありません")
        return {}
    
    # 出力ディレクトリを作成
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    results = {}
    total_quizzes = 0
    
    print(f"🎯 {len(areas)}エリアで各{iterations}個のクイズを生成開始")
    print("=" * 60)
    
    for i, area in enumerate(areas, 1):
        if verbose:
            print(f"\n📍 エリア {i}/{len(areas)}: {area}")
            print("-" * 40)
        
        try:
            # クイズ生成
            quizzes = generate_multiple_quizzes(area, iterations, min_max_components)
            
            if quizzes and len(quizzes) > 0:
                # ファイル名生成
                filename = f"quizzes_{area}.json"
                filepath = Path(output_dir) / filename
                
                # JSONファイルに保存
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(quizzes, f, ensure_ascii=False, indent=2)
                
                results[area] = {
                    "success": True,
                    "count": len(quizzes),
                    "filename": str(filepath),
                    "max_components_range": {
                        "min": min(q["max_connected_components"] for q in quizzes),
                        "max": max(q["max_connected_components"] for q in quizzes),
                        "avg": sum(q["max_connected_components"] for q in quizzes) / len(quizzes)
                    }
                }
                
                total_quizzes += len(quizzes)
                
                if verbose:
                    print(f"✅ {area}: {len(quizzes)}個のクイズを生成")
                    print(f"   ファイル: {filepath}")
                    range_info = results[area]["max_components_range"]
                    print(f"   連結成分数: {range_info['min']}-{range_info['max']} (平均{range_info['avg']:.1f})")
            else:
                results[area] = {
                    "success": False,
                    "count": 0,
                    "filename": None,
                    "error": "クイズ生成失敗"
                }
                if verbose:
                    print(f"❌ {area}: クイズ生成失敗")
        
        except Exception as e:
            results[area] = {
                "success": False,
                "count": 0,
                "filename": None,
                "error": str(e)
            }
            if verbose:
                print(f"❌ {area}: エラー - {e}")
    
    # 生成結果のサマリー
    if verbose:
        print("\n" + "=" * 60)
        print("🎉 全エリア生成完了!")
        print("-" * 30)
        
        successful_areas = [area for area, result in results.items() if result["success"]]
        failed_areas = [area for area, result in results.items() if not result["success"]]
        
        print(f"✅ 成功: {len(successful_areas)}エリア")
        print(f"❌ 失敗: {len(failed_areas)}エリア")
        print(f"📊 総クイズ数: {total_quizzes}個")
        
        if successful_areas:
            print("\n📝 生成されたファイル:")
            for area in successful_areas:
                result = results[area]
                print(f"  {area}: {result['filename']} ({result['count']}個)")
        
        if failed_areas:
            print(f"\n⚠️ 失敗したエリア: {failed_areas}")
    
    return results


def create_summary_report(results, output_dir=".", timestamp=None):
    """
    生成結果のサマリーレポートを作成
    
    Args:
        results: generate_all_area_quizzes()の結果
        output_dir: 出力ディレクトリ
        timestamp: タイムスタンプ (None の場合は現在時刻)
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "timestamp": timestamp,
        "summary": {
            "total_areas": len(results),
            "successful_areas": len([r for r in results.values() if r["success"]]),
            "failed_areas": len([r for r in results.values() if not r["success"]]),
            "total_quizzes": sum(r.get("count", 0) for r in results.values())
        },
        "areas": results
    }
    
    # サマリーファイル保存
    summary_file = Path(output_dir) / f"quiz_generation_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 サマリーレポート: {summary_file}")
    return str(summary_file)


def main():
    parser = argparse.ArgumentParser(
        description="全エリアのクイズを一括生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  %(prog)s --iterations 10                    # 全エリアで各10個
  %(prog)s --areas central,osaka --iterations 5   # 指定エリアで各5個
  %(prog)s --output quizzes --iterations 20       # 出力先指定
        """
    )
    
    parser.add_argument(
        "--areas",
        type=str,
        help="生成するエリア（カンマ区切り、未指定の場合は全エリア）"
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="各エリアのクイズ数 (デフォルト: 10)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="出力ディレクトリ (デフォルト: カレントディレクトリ)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="詳細出力を抑制"
    )
    
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="サマリーレポートを生成しない"
    )
    
    parser.add_argument(
        "--list-areas",
        action="store_true",
        help="利用可能なエリアを表示して終了"
    )
    
    parser.add_argument(
        "--min-components",
        type=int,
        default=4,
        help="最大連結成分数の下限 (デフォルト: 4)"
    )
    
    args = parser.parse_args()
    
    # エリア一覧表示
    if args.list_areas:
        areas = get_available_areas()
        print("利用可能なエリア:")
        for area in areas:
            print(f"  {area}")
        return
    
    # エリア解析
    areas = None
    if args.areas:
        areas = [area.strip() for area in args.areas.split(",")]
    
    # クイズ生成実行
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = generate_all_area_quizzes(
        areas=areas,
        iterations=args.iterations,
        output_dir=args.output,
        verbose=not args.quiet,
        min_max_components=args.min_components
    )
    
    # サマリーレポート作成
    if not args.no_summary and results:
        create_summary_report(results, args.output, timestamp)
    
    # 終了コード
    failed_count = len([r for r in results.values() if not r["success"]])
    if failed_count > 0:
        exit(1)


if __name__ == "__main__":
    main()