"""進捗トラッキングモジュール - 学習履歴と統計の管理"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import altair as alt


def save_session(user_data: Dict[str, Any], input_text: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析結果をセッションとして保存

    Args:
        user_data: ユーザーデータ
        input_text: 入力テキスト
        analysis_result: 解析結果

    Returns:
        保存したセッション
    """
    session = {
        "session_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "input_text": input_text[:200],  # 最初の200文字のみ保存
        "analysis_result": analysis_result,
        "quiz_results": []
    }

    user_data['sessions'].append(session)

    # 語彙バンクに用語を追加
    for vocab in analysis_result.get('vocabulary', []):
        add_to_vocabulary_bank(user_data, vocab)

    # 統計を更新
    update_statistics(user_data)

    return session


def add_to_vocabulary_bank(user_data: Dict[str, Any], vocab: Dict[str, Any]):
    """
    用語を語彙バンクに追加（重複チェック付き）

    Args:
        user_data: ユーザーデータ
        vocab: 用語情報
    """
    term = vocab.get('term', '')

    # 既に存在するか確認
    existing = next((v for v in user_data['vocabulary_bank'] if v['term'] == term), None)

    if existing:
        # 既存の単語の場合、復習回数を増やす
        existing['review_count'] = existing.get('review_count', 0) + 1
    else:
        # 新しい単語の場合、語彙バンクに追加
        vocab_entry = {
            "term": term,
            "meaning": vocab.get('meaning', ''),
            "type": vocab.get('type', 'Keyword'),
            "category": "General",
            "status": "learning",
            "added_at": datetime.now().isoformat(),
            "last_reviewed": datetime.now().isoformat(),
            "next_review": datetime.now().isoformat(),
            "repetition_level": 0,
            "ease_factor": 2.5,
            "review_count": 1,
            "correct_count": 0
        }
        user_data['vocabulary_bank'].append(vocab_entry)


def record_quiz_result(user_data: Dict[str, Any], session_id: str, quiz_index: int,
                       correct: bool, answer_time: float):
    """
    クイズ結果を記録

    Args:
        user_data: ユーザーデータ
        session_id: セッションID
        quiz_index: クイズのインデックス
        correct: 正解かどうか
        answer_time: 回答時間（秒）
    """
    # セッションを検索
    session = next((s for s in user_data['sessions'] if s['session_id'] == session_id), None)

    if session:
        session['quiz_results'].append({
            "quiz_index": quiz_index,
            "correct": correct,
            "answer_time_seconds": answer_time
        })

    # 統計を更新
    update_statistics(user_data)


def update_statistics(user_data: Dict[str, Any]):
    """
    統計データを更新

    Args:
        user_data: ユーザーデータ
    """
    stats = user_data['statistics']

    # 総セッション数
    stats['total_sessions'] = len(user_data['sessions'])

    # 習得単語数（learning以外の単語）
    stats['total_words_learned'] = len([
        v for v in user_data['vocabulary_bank']
        if v['status'] in ['reviewing', 'mastered']
    ])

    # クイズ正解率の計算
    all_quiz_results = []
    for session in user_data['sessions']:
        all_quiz_results.extend(session.get('quiz_results', []))

    if all_quiz_results:
        correct_count = sum(1 for r in all_quiz_results if r['correct'])
        stats['quiz_accuracy'] = correct_count / len(all_quiz_results)
    else:
        stats['quiz_accuracy'] = 0.0

    # 連続学習日数を計算
    stats['streak_days'] = calculate_streak(user_data['sessions'])

    # 最終学習日を更新
    stats['last_study_date'] = datetime.now().date().isoformat()


def calculate_streak(sessions: List[Dict[str, Any]]) -> int:
    """
    連続学習日数を計算

    Args:
        sessions: セッションのリスト

    Returns:
        連続学習日数
    """
    if not sessions:
        return 0

    # セッションの日付を取得（重複除去）
    dates = set()
    for session in sessions:
        timestamp = session.get('timestamp', '')
        if timestamp:
            date = datetime.fromisoformat(timestamp).date()
            dates.add(date)

    if not dates:
        return 0

    # 日付をソート
    sorted_dates = sorted(dates, reverse=True)

    # 今日から連続している日数をカウント
    today = datetime.now().date()
    streak = 0

    for i, date in enumerate(sorted_dates):
        expected_date = today - timedelta(days=i)
        if date == expected_date:
            streak += 1
        else:
            break

    return streak


def create_session_dataframe(sessions: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    セッションデータをDataFrameに変換

    Args:
        sessions: セッションのリスト

    Returns:
        DataFrame
    """
    data = []
    for session in sessions[-20:]:  # 最新20件のみ表示
        timestamp = session.get('timestamp', '')
        date = timestamp[:10] if len(timestamp) >= 10 else ''
        time = timestamp[11:16] if len(timestamp) >= 16 else ''

        vocab_count = len(session.get('analysis_result', {}).get('vocabulary', []))
        quiz_results = session.get('quiz_results', [])
        correct_count = sum(1 for r in quiz_results if r.get('correct', False))
        total_count = len(quiz_results)

        data.append({
            "日付": date,
            "時刻": time,
            "解析テキスト": session.get('input_text', '')[:50] + "...",
            "単語数": vocab_count,
            "クイズ正解": f"{correct_count}/{total_count}" if total_count > 0 else "未実施"
        })

    return pd.DataFrame(data)


def create_daily_sessions_chart(sessions: List[Dict[str, Any]]):
    """
    日別セッション数のグラフを作成

    Args:
        sessions: セッションのリスト

    Returns:
        Altairチャート
    """
    if not sessions:
        # データがない場合は空のチャートを返す
        return alt.Chart(pd.DataFrame({'日付': [], 'セッション数': []})).mark_bar()

    # セッションの日付を集計
    session_dates = []
    for session in sessions:
        timestamp = session.get('timestamp', '')
        if timestamp:
            date = timestamp[:10]
            session_dates.append(date)

    if not session_dates:
        return alt.Chart(pd.DataFrame({'日付': [], 'セッション数': []})).mark_bar()

    # 日付ごとにカウント
    date_counts = pd.DataFrame({'日付': session_dates})
    date_counts = date_counts['日付'].value_counts().reset_index()
    date_counts.columns = ['日付', 'セッション数']
    date_counts = date_counts.sort_values('日付')

    # グラフを作成
    chart = alt.Chart(date_counts).mark_bar(color='#007bff').encode(
        x=alt.X('日付:T', title='日付', axis=alt.Axis(format='%m/%d')),
        y=alt.Y('セッション数:Q', title='セッション数'),
        tooltip=[
            alt.Tooltip('日付:T', title='日付', format='%Y-%m-%d'),
            alt.Tooltip('セッション数:Q', title='セッション数')
        ]
    ).properties(
        height=300,
        title='日別学習セッション数'
    )

    return chart


def get_vocabulary_progress_data(vocabulary_bank: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    語彙習得状況のデータを取得

    Args:
        vocabulary_bank: 語彙バンク

    Returns:
        ステータスごとの単語数
    """
    status_counts = {
        'learning': 0,
        'reviewing': 0,
        'mastered': 0
    }

    for vocab in vocabulary_bank:
        status = vocab.get('status', 'learning')
        if status in status_counts:
            status_counts[status] += 1

    return status_counts
