"""フラッシュカード学習モジュール - 間隔反復学習（Spaced Repetition）"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def calculate_next_review(vocab: Dict[str, Any], quality: int) -> Dict[str, Any]:
    """
    SM-2アルゴリズムで次の復習日を計算

    Args:
        vocab: 語彙データ
        quality: 回答品質 (0=忘れた, 1=難しい, 2=まあまあ, 3=覚えた)

    Returns:
        更新された語彙データ
    """
    # 現在の値を取得
    repetition_level = vocab.get('repetition_level', 0)
    ease_factor = vocab.get('ease_factor', 2.5)

    # 品質スコアに基づいてease_factorを更新（SM-2アルゴリズム）
    # quality: 0-3 → SM-2の0-5スケールに変換
    q = quality + 2  # 0→2, 1→3, 2→4, 3→5

    new_ease_factor = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

    # ease_factorの最小値は1.3
    if new_ease_factor < 1.3:
        new_ease_factor = 1.3

    # 復習間隔の計算
    if quality < 2:  # 忘れた or 難しい
        # 最初からやり直し
        new_repetition_level = 0
        interval_days = 1
        new_status = "learning"
    else:  # まあまあ or 覚えた
        new_repetition_level = repetition_level + 1

        if new_repetition_level == 1:
            interval_days = 1
        elif new_repetition_level == 2:
            interval_days = 6
        else:
            # 前回の間隔 × ease_factor
            interval_days = int((new_repetition_level - 1) * new_ease_factor)

        # ステータスの更新
        if new_repetition_level >= 3:
            new_status = "mastered"
        else:
            new_status = "reviewing"

    # 次回復習日を計算
    next_review = datetime.now() + timedelta(days=interval_days)

    # 語彙データを更新
    vocab['repetition_level'] = new_repetition_level
    vocab['ease_factor'] = new_ease_factor
    vocab['last_reviewed'] = datetime.now().isoformat()
    vocab['next_review'] = next_review.isoformat()
    vocab['status'] = new_status
    vocab['review_count'] = vocab.get('review_count', 0) + 1

    if quality >= 2:
        vocab['correct_count'] = vocab.get('correct_count', 0) + 1

    return vocab


def get_due_words(vocabulary_bank: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    今日復習する必要がある単語を取得

    Args:
        vocabulary_bank: 語彙バンク

    Returns:
        復習が必要な単語のリスト
    """
    due_words = []
    now = datetime.now()

    for vocab in vocabulary_bank:
        next_review_str = vocab.get('next_review', '')
        if next_review_str:
            try:
                next_review = datetime.fromisoformat(next_review_str)
                if next_review <= now:
                    due_words.append(vocab)
            except ValueError:
                # パースエラーの場合はスキップ
                continue

    return due_words


def get_new_words(vocabulary_bank: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """
    まだ復習していない新しい単語を取得

    Args:
        vocabulary_bank: 語彙バンク
        limit: 取得する最大数

    Returns:
        新しい単語のリスト
    """
    new_words = [
        vocab for vocab in vocabulary_bank
        if vocab.get('review_count', 0) == 1  # 追加時にreview_count=1になっている
        and vocab.get('status') == 'learning'
    ]

    return new_words[:limit]


def show_flashcard_review(user_data: Dict[str, Any], data_manager) -> None:
    """
    フラッシュカード復習UIを表示

    Args:
        user_data: ユーザーデータ
        data_manager: データマネージャー
    """
    st.markdown("### 🎴 フラッシュカード復習")

    vocabulary_bank = user_data['vocabulary_bank']

    if not vocabulary_bank:
        st.info("まだ語彙バンクに単語がありません。英文を解析して単語を追加しましょう！")
        return

    # 復習が必要な単語を取得
    due_words = get_due_words(vocabulary_bank)
    new_words = get_new_words(vocabulary_bank)

    # 統計表示
    col1, col2, col3 = st.columns(3)
    col1.metric("復習待ち", len(due_words), delta="📝")
    col2.metric("新規単語", len(new_words), delta="✨")
    col3.metric("語彙バンク合計", len(vocabulary_bank), delta="📚")

    st.divider()

    # 復習する単語リスト
    review_list = due_words + new_words

    if not review_list:
        st.success("🎉 素晴らしい！今日復習する単語はありません。")
        st.info("新しい英文を解析して、語彙を増やしましょう！")
        return

    # セッションステートの初期化
    if 'flashcard_index' not in st.session_state:
        st.session_state.flashcard_index = 0
    if 'flashcard_show_answer' not in st.session_state:
        st.session_state.flashcard_show_answer = False

    # 現在のカードのインデックスが範囲外の場合はリセット
    if st.session_state.flashcard_index >= len(review_list):
        st.session_state.flashcard_index = 0

    current_index = st.session_state.flashcard_index
    current_vocab = review_list[current_index]

    # 進捗表示
    st.progress((current_index + 1) / len(review_list))
    st.caption(f"カード {current_index + 1} / {len(review_list)}")

    # フラッシュカード表示
    st.markdown("---")

    # カードの表示（表：単語）
    st.markdown(f"## {current_vocab['term']}")
    st.caption(f"種類: {current_vocab.get('type', 'Keyword')}")

    # 答えを表示ボタン
    if not st.session_state.flashcard_show_answer:
        if st.button("🔍 答えを見る", use_container_width=True):
            st.session_state.flashcard_show_answer = True
            st.rerun()
    else:
        # 答え表示（裏：意味）
        st.markdown("### 意味")
        st.info(current_vocab['meaning'])

        st.markdown("### 評価してください")
        st.caption("あなたの記憶度を評価してください。次回の復習日が自動的に調整されます。")

        # 評価ボタン
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("😓 忘れた", use_container_width=True, type="secondary"):
                handle_flashcard_answer(user_data, current_vocab, 0, data_manager)

        with col2:
            if st.button("😐 難しい", use_container_width=True, type="secondary"):
                handle_flashcard_answer(user_data, current_vocab, 1, data_manager)

        with col3:
            if st.button("🙂 まあまあ", use_container_width=True, type="secondary"):
                handle_flashcard_answer(user_data, current_vocab, 2, data_manager)

        with col4:
            if st.button("😄 覚えた！", use_container_width=True, type="primary"):
                handle_flashcard_answer(user_data, current_vocab, 3, data_manager)

    st.markdown("---")

    # 復習情報
    with st.expander("📊 復習情報"):
        st.write(f"**復習レベル**: {current_vocab.get('repetition_level', 0)}")
        st.write(f"**復習回数**: {current_vocab.get('review_count', 0)}")
        st.write(f"**正解回数**: {current_vocab.get('correct_count', 0)}")
        st.write(f"**ステータス**: {current_vocab.get('status', 'learning')}")

        last_reviewed = current_vocab.get('last_reviewed', '')
        if last_reviewed:
            try:
                last_reviewed_dt = datetime.fromisoformat(last_reviewed)
                st.write(f"**前回復習**: {last_reviewed_dt.strftime('%Y-%m-%d %H:%M')}")
            except:
                pass


def handle_flashcard_answer(user_data: Dict[str, Any], vocab: Dict[str, Any],
                            quality: int, data_manager) -> None:
    """
    フラッシュカードの回答を処理

    Args:
        user_data: ユーザーデータ
        vocab: 語彙データ
        quality: 回答品質 (0=忘れた, 1=難しい, 2=まあまあ, 3=覚えた)
        data_manager: データマネージャー
    """
    # 語彙バンクから該当の単語を検索して更新
    for i, v in enumerate(user_data['vocabulary_bank']):
        if v['term'] == vocab['term']:
            # SM-2アルゴリズムで次回復習日を計算
            updated_vocab = calculate_next_review(v, quality)
            user_data['vocabulary_bank'][i] = updated_vocab

            # データを保存
            data_manager.save_user_data(user_data)

            # 次のカードへ
            st.session_state.flashcard_index += 1
            st.session_state.flashcard_show_answer = False

            # フィードバックメッセージ
            quality_messages = {
                0: "もう一度頑張りましょう！明日また復習します。",
                1: "少し難しかったですね。間隔を短めにして復習します。",
                2: "良い調子です！次回は少し間隔を開けます。",
                3: "素晴らしい！しっかり覚えていますね。"
            }

            st.toast(quality_messages[quality], icon="✅")
            st.rerun()
            break
