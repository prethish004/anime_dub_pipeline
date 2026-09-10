"""
style_eval.py
=============
Hand-labeled accuracy check for dialogue style detection
(step3_translation.detect_dialogue_style), so its accuracy is a measured
number instead of a guess.

Runs the same ~26 labeled Japanese lines through both methods:
  - keyword_only : the original substring matching (STYLE_PATTERNS)
  - hybrid       : keyword matching first, zero-shot classifier as a
                   fallback when keywords find nothing (the current
                   production behavior in detect_dialogue_style)

Each line is also tagged "keyword_pattern" (contains one of the literal
words the keyword matcher looks for) or "novel_phrasing" (conveys the
same style without any of those words) — that split is the whole point:
keyword_only should score ~100% on keyword_pattern lines and ~0% on
novel_phrasing ones, and the interesting question is how much the
classifier actually recovers on the novel_phrasing lines it's meant to help with.

Reports a confusion matrix (expected style -> predicted style counts)
for each method so it's clear not just *how often* it's wrong but
*what it confuses with what*.
"""

import os
import json
from datetime import datetime

from web_app.backend.step3_translation import (
    _detect_dialogue_style_keywords,
    detect_dialogue_style,
    make_style_classifier,
)

STYLE_CATEGORIES = ["tsundere", "aggressive", "formal_cool", "cute", "reflective", "neutral"]

EVAL_SET = [
    # tsundere
    {"text": "べつに、あんたのことなんか、好きじゃないんだから！", "expected": "tsundere", "category": "keyword_pattern"},
    {"text": "う、うるさいわね！何よそれ！", "expected": "tsundere", "category": "keyword_pattern"},
    {"text": "あんたなんかと一緒にいたくないもん！でも…雨の日は迎えに来てくれてもいいけど", "expected": "tsundere", "category": "novel_phrasing"},
    {"text": "勘違いしないでよね、心配してるわけじゃないんだから", "expected": "tsundere", "category": "novel_phrasing"},

    # aggressive
    {"text": "てめぇ、ぶっ殺すぞ！", "expected": "aggressive", "category": "keyword_pattern"},
    {"text": "この野郎、ぶっ殺してやる！", "expected": "aggressive", "category": "keyword_pattern"},
    {"text": "お前を八つ裂きにしてやる、覚悟しろ！", "expected": "aggressive", "category": "novel_phrasing"},
    {"text": "二度とその口が利けないようにしてやろうか", "expected": "aggressive", "category": "novel_phrasing"},

    # formal_cool
    {"text": "かしこまりました。承知いたしました。", "expected": "formal_cool", "category": "keyword_pattern"},
    {"text": "なるほど、そういうことでしたか", "expected": "formal_cool", "category": "keyword_pattern"},
    {"text": "恐れ入りますが、こちらにご記入をお願いいたします", "expected": "formal_cool", "category": "novel_phrasing"},
    {"text": "本日はお忙しい中お時間をいただき、誠にありがとうございます", "expected": "formal_cool", "category": "novel_phrasing"},

    # cute
    {"text": "先輩、おねがいします！えへへ", "expected": "cute", "category": "keyword_pattern"},
    {"text": "お兄ちゃん大好き！ぎゅーってして！", "expected": "cute", "category": "novel_phrasing"},
    {"text": "わーい！今日はいっぱい遊べて嬉しいな！", "expected": "cute", "category": "novel_phrasing"},
    {"text": "ねぇねぇ、いっしょにおやつ食べよう！", "expected": "cute", "category": "novel_phrasing"},

    # reflective
    {"text": "ふむ、かなあ…そうかもしれない", "expected": "reflective", "category": "keyword_pattern"},
    {"text": "変わってしまったのかな、この気持ちも", "expected": "reflective", "category": "keyword_pattern"},
    {"text": "この道を選んで、本当によかったのだろうか", "expected": "reflective", "category": "novel_phrasing"},
    {"text": "誰にも言えない想いを、そっと胸にしまった", "expected": "reflective", "category": "novel_phrasing"},

    # neutral
    {"text": "今日は学校に行って、それから帰ってきた", "expected": "neutral", "category": "novel_phrasing"},
    {"text": "明日の会議は10時からです", "expected": "neutral", "category": "novel_phrasing"},
    {"text": "これはテーブルの上に置いてあります", "expected": "neutral", "category": "novel_phrasing"},
    {"text": "駅まで歩いて15分くらいです", "expected": "neutral", "category": "novel_phrasing"},
    {"text": "彼はその部屋に入っていった", "expected": "neutral", "category": "novel_phrasing"},
    {"text": "荷物はこちらの箱に入れておきました", "expected": "neutral", "category": "novel_phrasing"},
]

REPORT_CACHE_PATH = os.path.join(os.path.dirname(__file__), "style_eval_report_cache.json")


def _blank_matrix():
    return {expected: {predicted: 0 for predicted in STYLE_CATEGORIES} for expected in STYLE_CATEGORIES}


def _score(guesses):
    """guesses: list of (expected, predicted, category, text) -> accuracy stats."""
    matrix = _blank_matrix()
    correct = 0
    by_category = {}
    mistakes = []

    for expected, predicted, category, text in guesses:
        matrix[expected][predicted] += 1
        is_correct = expected == predicted
        correct += int(is_correct)

        cat_stats = by_category.setdefault(category, {"correct": 0, "total": 0})
        cat_stats["total"] += 1
        cat_stats["correct"] += int(is_correct)

        if not is_correct:
            mistakes.append({"text": text, "expected": expected, "got": predicted, "category": category})

    total = len(guesses)
    return {
        "accuracy": round(correct / total, 3) if total else 0.0,
        "correct": correct,
        "total": total,
        "confusion_matrix": matrix,
        "by_category": {
            cat: {
                "accuracy": round(v["correct"] / v["total"], 3) if v["total"] else 0.0,
                "correct": v["correct"],
                "total": v["total"],
            }
            for cat, v in by_category.items()
        },
        "mistakes": mistakes,
    }


def run_evaluation() -> dict:
    style_pipe = make_style_classifier(-1)  # CPU: this eval never fights a real pipeline run for GPU

    keyword_guesses = []
    hybrid_guesses = []
    for item in EVAL_SET:
        text, expected, category = item["text"], item["expected"], item["category"]
        keyword_guesses.append((expected, _detect_dialogue_style_keywords(text), category, text))
        hybrid_guesses.append((expected, detect_dialogue_style(text, style_pipe), category, text))

    return {
        "classifier_loaded": style_pipe is not None,
        "eval_set_size": len(EVAL_SET),
        "keyword_only": _score(keyword_guesses),
        "hybrid": _score(hybrid_guesses),
    }


def get_report(force_refresh: bool = False) -> dict:
    if not force_refresh and os.path.exists(REPORT_CACHE_PATH):
        with open(REPORT_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    report = run_evaluation()
    report["generated_at"] = datetime.now().isoformat()
    with open(REPORT_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report
