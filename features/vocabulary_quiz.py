"""一般英単語・英熟語クイズモジュール - 基礎からビジネス英語まで学習"""

import streamlit as st
import json
import os
import random
from typing import Dict, List, Any


@st.cache_data
def load_general_vocabulary() -> Dict[str, Any]:
    """
    一般英単語・英熟語をJSONファイルから読み込む

    Returns:
        一般英単語・英熟語データ
    """
    vocabulary_path = os.path.join("data", "general_vocabulary.json")

    if not os.path.exists(vocabulary_path):
        st.error(f"一般英単語ファイルが見つかりません: {vocabulary_path}")
        return {"categories": []}

    try:
        with open(vocabulary_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        st.error(f"一般英単語の読み込みエラー: {e}")
        return {"categories": []}


def generate_wrong_answers(all_terms: List[Dict[str, Any]], correct_term: Dict[str, Any],
                           mode: str, count: int = 2) -> List[str]:
    """
    誤答選択肢を生成

    Args:
        all_terms: カテゴリー内の全用語
        correct_term: 正解の用語
        mode: クイズモード（"en_to_ja" or "ja_to_en"）
        count: 誤答の数（デフォルト2つ）

    Returns:
        誤答のリスト
    """
    # 正解を除外
    other_terms = [t for t in all_terms if t['english'] != correct_term['english']]

    # ランダムに選択
    if len(other_terms) < count:
        count = len(other_terms)

    selected = random.sample(other_terms, count)

    # モードに応じて誤答を生成
    if mode == "en_to_ja":
        return [t['japanese'] for t in selected]
    else:  # ja_to_en
        return [t['english'] for t in selected]


def show_vocabulary_quiz() -> None:
    """
    一般英単語・英熟語クイズのメイン画面を表示
    """
    st.markdown("### 📚 一般英単語・英熟語クイズ")
    st.caption("中学レベルからビジネス・エンジニア英語まで、幅広く学習しましょう")

    # 一般英単語を読み込み
    vocab_data = load_general_vocabulary()
    categories = vocab_data.get('categories', [])

    if not categories:
        st.warning("一般英単語データが見つかりません。")
        return

    # カテゴリー選択
    st.markdown("#### 📖 カテゴリー選択")

    category_options = [f"{cat['icon']} {cat['name']}" for cat in categories]
    selected_category_display = st.selectbox(
        "学習したいカテゴリーを選択してください",
        category_options,
        key="vocab_quiz_category"
    )

    # 選択されたカテゴリーを取得
    selected_index = category_options.index(selected_category_display)
    selected_category = categories[selected_index]

    # カテゴリー情報表示
    st.info(f"📝 このカテゴリーには {len(selected_category['terms'])} 個の単語・熟語があります")

    st.divider()

    # モード選択
    st.markdown("#### 🎯 クイズモード選択")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🇬🇧 英語 → 日本語", use_container_width=True, type="primary", key="vocab_quiz_en_to_ja_btn"):
            # 古いクイズの選択肢キャッシュをクリア
            keys_to_delete = [k for k in st.session_state.keys() if k.startswith('vocab_quiz_options_')]
            for k in keys_to_delete:
                del st.session_state[k]

            st.session_state['vocab_quiz_mode'] = 'en_to_ja'
            st.session_state['vocab_quiz_active'] = True
            st.session_state['vocab_quiz_current_index'] = 0
            st.session_state['vocab_quiz_score'] = 0
            st.session_state['vocab_quiz_answered'] = False
            # 用語をシャッフル
            st.session_state['vocab_quiz_terms'] = random.sample(
                selected_category['terms'],
                len(selected_category['terms'])
            )
            st.rerun()

    with col2:
        if st.button("🇯🇵 日本語 → 英語", use_container_width=True, type="primary", key="vocab_quiz_ja_to_en_btn"):
            # 古いクイズの選択肢キャッシュをクリア
            keys_to_delete = [k for k in st.session_state.keys() if k.startswith('vocab_quiz_options_')]
            for k in keys_to_delete:
                del st.session_state[k]

            st.session_state['vocab_quiz_mode'] = 'ja_to_en'
            st.session_state['vocab_quiz_active'] = True
            st.session_state['vocab_quiz_current_index'] = 0
            st.session_state['vocab_quiz_score'] = 0
            st.session_state['vocab_quiz_answered'] = False
            # 用語をシャッフル
            st.session_state['vocab_quiz_terms'] = random.sample(
                selected_category['terms'],
                len(selected_category['terms'])
            )
            st.rerun()

    st.divider()

    # クイズ実行
    if st.session_state.get('vocab_quiz_active', False):
        run_vocabulary_quiz(selected_category)


def run_vocabulary_quiz(category: Dict[str, Any]) -> None:
    """
    一般英単語・英熟語クイズを実行

    Args:
        category: 選択されたカテゴリーデータ
    """
    mode = st.session_state.get('vocab_quiz_mode', 'en_to_ja')
    terms = st.session_state.get('vocab_quiz_terms', category['terms'])
    current_index = st.session_state.get('vocab_quiz_current_index', 0)
    score = st.session_state.get('vocab_quiz_score', 0)

    # クイズ終了チェック
    if current_index >= len(terms):
        st.success(f"🎉 クイズ完了！ スコア: {score}/{len(terms)} ({score/len(terms)*100:.1f}%)")

        # 結果の評価
        accuracy = score / len(terms)
        if accuracy >= 0.9:
            st.balloons()
            st.success("🏆 素晴らしい！ほぼ完璧です！")
        elif accuracy >= 0.7:
            st.success("👍 よくできました！")
        elif accuracy >= 0.5:
            st.info("📝 もう少し復習が必要かもしれません")
        else:
            st.warning("💪 頑張りましょう！何度も挑戦することが大切です")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("もう一度挑戦", type="primary", use_container_width=True, key="vocab_quiz_retry_btn"):
                st.session_state['vocab_quiz_active'] = False
                st.rerun()

        with col2:
            if st.button("別のカテゴリーを選択", use_container_width=True, key="vocab_quiz_change_category_btn"):
                st.session_state['vocab_quiz_active'] = False
                st.rerun()

        return

    # 進捗表示
    st.progress((current_index + 1) / len(terms))
    st.caption(f"問題 {current_index + 1} / {len(terms)} | 現在のスコア: {score}")

    # 現在の問題
    current_term = terms[current_index]

    # 問題文を表示
    st.markdown("---")

    if mode == "en_to_ja":
        st.markdown(f"## {current_term['english']}")
        st.markdown("#### この英語の意味は？")
        correct_answer = current_term['japanese']
    else:  # ja_to_en
        st.markdown(f"## {current_term['japanese']}")
        st.markdown("#### この日本語に対応する英語は？")
        correct_answer = current_term['english']

    # 例文表示
    if current_term.get('example'):
        st.caption(f"📝 例文: {current_term['example']}")

    st.markdown("")

    # 選択肢を生成（初回のみ、セッションステートに保存）
    options_key = f'vocab_quiz_options_{current_index}'
    if options_key not in st.session_state:
        wrong_answers = generate_wrong_answers(category['terms'], current_term, mode, count=2)
        options = wrong_answers + [correct_answer]
        random.shuffle(options)
        st.session_state[options_key] = options
    else:
        options = st.session_state[options_key]

    # 回答
    if not st.session_state.get('vocab_quiz_answered', False):
        selected_answer = st.radio(
            "選択肢",
            options,
            key=f"vocab_quiz_answer_{current_index}"
        )

        if st.button("回答する", type="primary", use_container_width=True, key=f"vocab_quiz_submit_{current_index}"):
            st.session_state['vocab_quiz_answered'] = True
            st.session_state['vocab_quiz_selected_answer'] = selected_answer
            st.rerun()
    else:
        # 回答結果表示
        selected_answer = st.session_state.get('vocab_quiz_selected_answer', '')

        if selected_answer == correct_answer:
            st.success("✅ 正解です！")
            st.session_state['vocab_quiz_score'] += 1
        else:
            st.error(f"❌ 不正解。正解は: {correct_answer}")

        # 詳細情報
        with st.expander("📖 詳細情報", expanded=True):
            st.write(f"**英語**: {current_term['english']}")
            st.write(f"**日本語**: {current_term['japanese']}")
            st.write(f"**例文**: {current_term.get('example', 'なし')}")
            if current_term.get('level'):
                level_labels = {
                    'basic': '基礎',
                    'business': 'ビジネス',
                    'technical': '技術',
                    'idiom': 'イディオム'
                }
                st.write(f"**レベル**: {level_labels.get(current_term['level'], current_term['level'])}")

        # 次へボタン
        if st.button("次の問題へ", type="primary", use_container_width=True, key=f"vocab_quiz_next_{current_index}"):
            # 現在の問題の選択肢をクリア
            options_key = f'vocab_quiz_options_{current_index}'
            if options_key in st.session_state:
                del st.session_state[options_key]

            st.session_state['vocab_quiz_current_index'] += 1
            st.session_state['vocab_quiz_answered'] = False
            st.rerun()

    st.markdown("---")

    # クイズ終了ボタン
    if st.button("クイズを終了", type="secondary", key=f"vocab_quiz_exit_{current_index}"):
        st.session_state['vocab_quiz_active'] = False
        st.rerun()
