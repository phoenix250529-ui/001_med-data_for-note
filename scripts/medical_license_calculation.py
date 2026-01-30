#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医療系国家資格の「本当の合格率」計算スクリプト

計算方法:
1. 各資格の養成機関への入学に必要な偏差値から、人口上位何%に該当するかを算出
2. 養成課程でのドロップアウト率(留年率・退学率)を算出
3. 国家試験合格率を掛け合わせて、「本当の合格率」を算出
"""

import math
from scipy.stats import norm
import pandas as pd

def hensachi_to_percentile(hensachi):
    """
    偏差値から上位何%かを計算
    偏差値 = 50 + 10 × (個人の得点 - 平均点) / 標準偏差
    → Z = (hensachi - 50) / 10
    """
    z_score = (hensachi - 50) / 10
    # 上位何%か(累積確率の補数)
    percentile = (1 - norm.cdf(z_score)) * 100
    return percentile

def percentile_to_probability(percentile):
    """
    上位何%かから、その偏差値帯に入れる確率を計算
    """
    return percentile / 100

# 各医療職のデータ
medical_licenses_data = {
    "医師": {
        "国家試験合格率": 0.924,  # 92.4%
        "新卒合格率": 0.95,
        "既卒合格率": 0.60,
        "入学偏差値_最低": 67,  # 最も入りやすい医学部
        "入学偏差値_平均": 70,  # 平均的な医学部
        "入学偏差値_上位": 77,  # 東大理三
        "ストレート卒業率": 0.849,  # 84.9% (全国平均、2024年度)
        "6年間で医師になる確率": 0.813,  # 81.3% (ストレート卒業率×新卒合格率)
        "養成期間": 6,
    },
    "歯科医師": {
        "国家試験合格率": 0.703,  # 70.3%
        "入学偏差値_最低": 50,
        "入学偏差値_平均": 55,
        "入学偏差値_上位": 65,
        "ストレート卒業率": 0.75,  # 推定75% (医師より低い)
        "養成期間": 6,
    },
    "薬剤師": {
        "国家試験合格率": 0.6885,  # 68.85%
        "新卒合格率": 0.8496,  # 84.96%
        "既卒合格率": 0.4394,  # 43.94%
        "入学偏差値_最低": 44,  # 私立最低レベル
        "入学偏差値_平均": 57,  # 中堅私立・国公立下位
        "入学偏差値_上位": 65,  # 国公立上位
        "ストレート卒業率": 0.673,  # 67.3% (6年間で32.7%留年)
        "6年間でストレート薬剤師になる確率": 0.571,  # 57.1% (留年率32.7%考慮後×新卒合格率)
        "養成期間": 6,
    },
    "看護師": {
        "国家試験合格率": 0.901,  # 90.1%
        "新卒合格率": 0.959,  # 95.9%
        "既卒合格率": 0.449,  # 44.9%
        "入学偏差値_最低": 40,  # 専門学校・私立大学下位
        "入学偏差値_平均": 48,  # 専門学校・私立大学平均
        "入学偏差値_上位": 60,  # 国公立大学・難関私立
        "ストレート卒業率": 0.85,  # 推定85% (医学部より高い)
        "養成期間_専門": 3,
        "養成期間_大学": 4,
    },
    "保健師": {
        "国家試験合格率": 0.957,  # 95.7%
        "前提資格": "看護師",
        "入学偏差値_追加": 5,  # 看護師よりやや高い
    },
    "助産師": {
        "国家試験合格率": 0.988,  # 98.8%
        "前提資格": "看護師",
        "入学偏差値_追加": 5,  # 看護師よりやや高い
    },
    "理学療法士": {
        "国家試験合格率": 0.896,  # 89.6%
        "新卒合格率": 0.925,  # 92.5%
        "入学偏差値_最低": 35,  # 専門学校下位
        "入学偏差値_平均": 48,  # 専門学校・私立大学平均
        "入学偏差値_上位": 65,  # 京都大学
        "ストレート卒業率": 0.88,  # 推定88% (国試合格率高いため)
        "養成期間_専門": 3,
        "養成期間_大学": 4,
    },
    "作業療法士": {
        "国家試験合格率": 0.858,  # 85.8%
        "入学偏差値_最低": 35,
        "入学偏差値_平均": 47,
        "入学偏差値_上位": 65,
        "ストレート卒業率": 0.86,  # 推定86%
        "養成期間_専門": 3,
        "養成期間_大学": 4,
    },
    "診療放射線技師": {
        "国家試験合格率": 0.847,  # 84.7%
        "入学偏差値_最低": 38,
        "入学偏差値_平均": 50,
        "入学偏差値_上位": 60,
        "ストレート卒業率": 0.85,  # 推定85%
        "養成期間_専門": 3,
        "養成期間_大学": 4,
    },
    "臨床検査技師": {
        "国家試験合格率": 0.846,  # 84.6%
        "新卒合格率": 0.940,  # 94.0%
        "入学偏差値_最低": 38,
        "入学偏差値_平均": 50,
        "入学偏差値_上位": 60,
        "ストレート卒業率": 0.85,  # 推定85%
        "養成期間_専門": 3,
        "養成期間_大学": 4,
    },
}

def calculate_true_pass_rate(license_name, data, use_hensachi="平均"):
    """
    「本当の合格率」を計算
    """
    print(f"\n{'='*60}")
    print(f"【{license_name}】の本当の合格率計算")
    print(f"{'='*60}")
    
    # 1. 入学難易度の選抜倍率
    if use_hensachi == "最低":
        hensachi_key = "入学偏差値_最低"
    elif use_hensachi == "上位":
        hensachi_key = "入学偏差値_上位"
    else:
        hensachi_key = "入学偏差値_平均"
    
    hensachi = data.get(hensachi_key, 50)
    upper_percentile = hensachi_to_percentile(hensachi)
    selection_probability = percentile_to_probability(upper_percentile)
    
    print(f"\n1. 入学選抜での絞り込み")
    print(f"   - 使用偏差値: {hensachi} ({use_hensachi})")
    print(f"   - 人口上位: {upper_percentile:.2f}%")
    print(f"   - 入学できる確率: {selection_probability:.4f} ({selection_probability*100:.2f}%)")
    
    # 2. 養成課程でのドロップアウト率
    straight_graduation_rate = data.get("ストレート卒業率", 0.85)
    print(f"\n2. 養成課程でのドロップアウト")
    print(f"   - ストレート卒業率: {straight_graduation_rate:.3f} ({straight_graduation_rate*100:.1f}%)")
    print(f"   - 留年・退学率: {1-straight_graduation_rate:.3f} ({(1-straight_graduation_rate)*100:.1f}%)")
    
    # 3. 国家試験合格率
    national_exam_pass_rate = data.get("国家試験合格率", 0.90)
    new_grad_pass_rate = data.get("新卒合格率", national_exam_pass_rate)
    
    print(f"\n3. 国家試験")
    print(f"   - 全体合格率: {national_exam_pass_rate:.3f} ({national_exam_pass_rate*100:.1f}%)")
    if "新卒合格率" in data:
        print(f"   - 新卒合格率: {new_grad_pass_rate:.3f} ({new_grad_pass_rate*100:.1f}%)")
    
    # 4. 本当の合格率
    true_pass_rate = selection_probability * straight_graduation_rate * new_grad_pass_rate
    
    print(f"\n{'='*60}")
    print(f"【最終結果】")
    print(f"{'='*60}")
    print(f"本当の合格率 = 入学確率 × ストレート卒業率 × 新卒国試合格率")
    print(f"            = {selection_probability:.4f} × {straight_graduation_rate:.3f} × {new_grad_pass_rate:.3f}")
    print(f"            = {true_pass_rate:.6f}")
    print(f"            = {true_pass_rate*100:.3f}%")
    print(f"\n→ つまり、一般人口から見て {1/true_pass_rate:.1f}人に1人 が{license_name}になれる")
    print(f"{'='*60}\n")
    
    return {
        "資格名": license_name,
        "使用偏差値": hensachi,
        "人口上位%": upper_percentile,
        "入学確率": selection_probability,
        "ストレート卒業率": straight_graduation_rate,
        "新卒国試合格率": new_grad_pass_rate,
        "本当の合格率": true_pass_rate,
        "本当の合格率%": true_pass_rate * 100,
        "難易度(何人に1人)": 1 / true_pass_rate
    }

# 全資格の計算結果を格納
results = []

# 各資格について、最低・平均・上位の3パターンで計算
for license_name, data in medical_licenses_data.items():
    if "前提資格" in data:
        # 保健師・助産師は看護師が前提なのでスキップ(別途計算)
        continue
    
    # 平均偏差値で計算
    result = calculate_true_pass_rate(license_name, data, use_hensachi="平均")
    results.append(result)

# 結果をDataFrameにまとめる
df = pd.DataFrame(results)
df = df.sort_values("本当の合格率%", ascending=False)

print("\n\n")
print("="*100)
print("【全資格比較表】本当の合格率ランキング(平均偏差値ベース)")
print("="*100)
print(df.to_string(index=False))
print("="*100)

# CSV出力
df.to_csv("/home/claude/medical_license_true_pass_rates.csv", index=False, encoding="utf-8-sig")
print("\n結果をCSVファイルに出力しました: /home/claude/medical_license_true_pass_rates.csv")
