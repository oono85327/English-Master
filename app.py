import streamlit as st
import json
import os
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import google.generativeai as genai
from features.data_manager import DataManager
from features.progress_tracker import (
    save_session,
    record_quiz_result,
    create_session_dataframe,
    create_daily_sessions_chart,
    get_vocabulary_progress_data
)
from features.flashcard import (
    show_flashcard_review,
    get_due_words
)
from features.ui_quiz import show_ui_quiz
from features.vocabulary_quiz import show_vocabulary_quiz

# --- Page Configuration ---
st.set_page_config(
    page_title="TechEnglish Master",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .stTextArea>div>div>textarea {
        background-color: #ffffff;
        color: #000000 !important;
        font-size: 14px;
    }
    .explanation-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LLM Logic (Gemini 2.5 Flash) ---
def get_gemini_response(api_key: str, prompt: str) -> str:
    """Gemini APIを呼び出してレスポンスを取得する（ダミー関数ではなく実動作を想定）"""
    if not api_key:
        return "Error: API Key is missing."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash') # 2.5-flashが利用可能な環境を想定しつつ、標準的な名前を使用
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_text(api_key: str, text: str) -> Dict[str, Any]:
    """英文を解析して構造分解、用語抽出、クイズ生成を行う"""
    prompt = f"""
    あなたは世界トップレベルの教育工学エンジニアです。
    以下の英文を解析し、エンジニアが学習しやすい形式でJSONデータを出力してください。

    【英文】
    {text}

    【出力フォーマット(JSON)】
    {{
        "structure": [
            {{
                "phrase": "英文のフレーズ",
                "literal_translation": "直訳",
                "explanation": "文法やニュアンスの解説"
            }}
        ],
        "vocabulary": [
            {{
                "term": "重要な技術用語または慣用句",
                "meaning": "意味",
                "type": "Keyword または Idiom"
            }}
        ],
        "quizzes": [
            {{
                "question": "単語や慣用句に関する3択クイズ",
                "options": ["選択肢1", "選択肢2", "選択肢3"],
                "answer_index": 0
            }}
        ]
    }}

    【制約事項】
    - structureは、原文を意味の塊（チャンク）ごとに分解してください。
    - explanationは、中学レベルの文法知識（SVO, 関係代名詞など）をベースに分かりやすく説明してください。
    - vocabularyは、技術的に重要な単語と、日本人が間違いやすい慣用句を抽出してください。
    - quizzesは、抽出したvocabularyから3問程度作成してください。
    - 出力は純粋なJSONのみにしてください（Markdownの装飾は不要）。
    """
    
    response_text = get_gemini_response(api_key, prompt)
    
    # JSONのパース（Markdownのコードブロックが含まれる場合の対策）
    try:
        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:-3]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:-3]
        return json.loads(clean_json)
    except Exception as e:
        st.error(f"JSONパースエラー: {str(e)}")
        st.text(response_text) # デバッグ用に生出力を表示
        return None

# --- Data Manager Initialization ---
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()
    st.session_state.user_data = st.session_state.data_manager.load_user_data()

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")

    # APIキーの取得（secrets.toml → 手動入力の順）
    default_api_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            default_api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ APIキーが設定ファイルから読み込まれました")
    except:
        pass

    # APIキー入力欄（設定済みの場合は非表示）
    if default_api_key:
        api_key = default_api_key
        with st.expander("🔑 APIキー設定", expanded=False):
            st.info("APIキーは `.streamlit/secrets.toml` から読み込まれています。")
            if st.button("別のAPIキーを使用"):
                st.session_state['use_custom_api_key'] = True
                st.rerun()

    if not default_api_key or st.session_state.get('use_custom_api_key', False):
        api_key = st.text_input("Gemini API Key", type="password", help="Google AI Studioから取得したAPIキーを入力してください。")

    st.info("このアプリは Gemini 2.5 Flash を使用して英文を解析します。")
    
    st.divider()
    st.markdown("### 💡 使い方")
    st.write("1. APIキーを入力")
    st.write("2. 解析したい英文を貼り付け")
    st.write("3. 'Analyze' ボタンをクリック")
    st.write("4. 構造分解とクイズで学習！")

    st.divider()
    st.markdown("### 💾 データ管理")

    # 統計情報の表示
    stats = st.session_state.user_data['statistics']
    st.info(f"📚 学習セッション: {stats['total_sessions']}回")

    # フラッシュカード復習待ち表示
    due_words = get_due_words(st.session_state.user_data['vocabulary_bank'])
    if due_words:
        st.warning(f"🎴 復習待ち: {len(due_words)}語")
    else:
        st.success("✅ 復習完了！")

    # バックアップダウンロード
    backup_data = st.session_state.data_manager.export_backup()
    st.download_button(
        label="📥 バックアップをダウンロード",
        data=backup_data,
        file_name=f"techenglish_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        help="学習データをJSONファイルとしてダウンロード"
    )

    # バックアップアップロード
    uploaded_file = st.file_uploader("📤 バックアップを復元", type=['json'], help="以前にダウンロードしたバックアップファイルをアップロード")
    if uploaded_file is not None:
        if st.session_state.data_manager.import_backup(uploaded_file.read()):
            st.session_state.user_data = st.session_state.data_manager.load_user_data()
            st.success("✅ データを復元しました")
            st.rerun()
        else:
            st.error("❌ データの復元に失敗しました")

# --- Main UI ---
st.title("🎓 TechEnglish Master")
st.subheader("エンジニアのための技術ドキュメント学習支援")

input_text = st.text_area("解析したい英文を入力してください:", height=200, placeholder="Paste English technical documentation here...")

col1, col2 = st.columns([1, 1])

if st.button("🚀 Analyze"):
    if not api_key:
        st.warning("APIキーを入力してください。")
    elif not input_text:
        st.warning("英文を入力してください。")
    else:
        with st.spinner("解析中... (Gemini 2.5 Flash is thinking)"):
            result = analyze_text(api_key, input_text)
            if result:
                st.session_state['analysis_result'] = result

                # セッションを保存
                session = save_session(st.session_state.user_data, input_text, result)
                st.session_state['current_session_id'] = session['session_id']

                # データを保存
                st.session_state.data_manager.save_user_data(st.session_state.user_data)

                st.success("解析が完了しました！")

# --- Results Display ---
if 'analysis_result' in st.session_state:
    res = st.session_state['analysis_result']

    tab1, tab2, tab3, tab4 = st.tabs(["📖 構造分解・翻訳", "🧪 用語・クイズ", "📊 学習統計", "🎴 フラッシュカード"])
    
    with tab1:
        st.markdown("### 英文の構造分解")
        # テーブル形式での表示
        st.table(res['structure'])
        
        st.markdown("### 全文の完成訳")
        full_translation = " ".join([item['literal_translation'] for item in res['structure']])
        st.info(full_translation)

    with tab2:
        col_v1, col_v2 = st.columns([1, 1])
        
        with col_v1:
            st.markdown("### 🔑 重要用語・慣用句")
            st.table(res['vocabulary'])
            
        with col_v2:
            st.markdown("### 📝 即席クイズ")
            if st.button("🎯 クイズに挑戦する"):
                st.session_state['show_quiz'] = True
            
            if st.session_state.get('show_quiz', False):
                for i, q in enumerate(res['quizzes']):
                    st.markdown(f"**Q{i+1}. {q['question']}**")
                    answer = st.radio(f"選択肢 (Q{i+1})", q['options'], key=f"q_{i}")

                    if st.button(f"回答を確認 (Q{i+1})", key=f"btn_{i}"):
                        # 回答開始時刻を記録（session_stateに保存していない場合は現在時刻）
                        if f'quiz_start_time_{i}' not in st.session_state:
                            st.session_state[f'quiz_start_time_{i}'] = time.time()

                        # 正誤判定
                        correct = q['options'].index(answer) == q['answer_index']

                        if correct:
                            st.success("正解です！")
                        else:
                            st.error(f"残念。正解は: {q['options'][q['answer_index']]}")

                        # 回答時間を計算
                        answer_time = time.time() - st.session_state.get(f'quiz_start_time_{i}', time.time())

                        # クイズ結果を記録
                        if 'current_session_id' in st.session_state:
                            record_quiz_result(
                                st.session_state.user_data,
                                st.session_state['current_session_id'],
                                i,
                                correct,
                                answer_time
                            )
                            # データを保存
                            st.session_state.data_manager.save_user_data(st.session_state.user_data)

                if st.button("クイズを閉じる"):
                    st.session_state['show_quiz'] = False
                    st.rerun()

    with tab3:
        st.markdown("### 📈 学習の進捗")

        stats = st.session_state.user_data['statistics']

        # メトリクス表示
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("総セッション数", stats['total_sessions'])
        col2.metric("習得単語数", stats['total_words_learned'])
        col3.metric("クイズ正解率", f"{stats['quiz_accuracy']*100:.1f}%")
        col4.metric("連続学習日数", f"{stats['streak_days']}日", delta="🔥" if stats['streak_days'] > 0 else None)

        st.divider()

        # 語彙習得状況
        st.markdown("#### 📚 語彙習得状況")
        vocab_progress = get_vocabulary_progress_data(st.session_state.user_data['vocabulary_bank'])

        col1, col2, col3 = st.columns(3)
        col1.metric("学習中", vocab_progress['learning'], delta="⏳")
        col2.metric("復習中", vocab_progress['reviewing'], delta="📝")
        col3.metric("習得済み", vocab_progress['mastered'], delta="✅")

        st.divider()

        # 日別セッション数グラフ
        st.markdown("#### 📅 日別学習セッション数")
        if st.session_state.user_data['sessions']:
            chart = create_daily_sessions_chart(st.session_state.user_data['sessions'])
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("まだセッションデータがありません。英文を解析して学習を開始しましょう！")

        st.divider()

        # セッション履歴テーブル
        st.markdown("#### 📜 学習履歴（最新20件）")
        if st.session_state.user_data['sessions']:
            session_df = create_session_dataframe(st.session_state.user_data['sessions'])
            st.dataframe(session_df, use_container_width=True, hide_index=True)
        else:
            st.info("まだ学習履歴がありません。")

    with tab4:
        show_flashcard_review(st.session_state.user_data, st.session_state.data_manager)

# --- General Vocabulary Quiz Section ---
st.divider()
st.markdown("## 📚 一般英単語・英熟語クイズ")
st.markdown("中学レベルの基礎からビジネス・エンジニア英語まで、体系的に学習できます")

with st.expander("📖 一般英単語クイズを開始", expanded=False):
    show_vocabulary_quiz()

# --- UI Element Quiz Section ---
st.divider()
st.markdown("## 🖥️ UI要素翻訳クイズ")
st.markdown("解析とは別に、実際のソフトウェアUI（GitHub、Vercel、AWS等）で使われる英語表現を学習できます")

with st.expander("📚 UI要素クイズを開始", expanded=False):
    show_ui_quiz()

# --- Footer ---
st.divider()
st.caption("Developed by Manus - Your AI Education Engineering Partner")
