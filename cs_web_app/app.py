#!/usr/bin/env python3
"""
出張買取プラス CSサポートツール - Webアプリ版
"""

from flask import Flask, render_template, request, jsonify
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

app = Flask(__name__)

class CallLog:
    def __init__(self, call_id: int, date_time: str, overview: str, summary: str, transcript: str):
        self.call_id = call_id
        self.date_time = date_time
        self.overview = overview
        self.summary = summary
        self.transcript = transcript
        self.keywords = self._extract_keywords()
    
    def _extract_keywords(self) -> set:
        text = f"{self.summary} {self.transcript}"
        text = text.lower()
        text = unicodedata.normalize('NFKC', text)
        return set(re.findall(r'[\w]+', text))


class CSKnowledgeBase:
    def __init__(self):
        self.call_logs: List[CallLog] = []
        self.faq_patterns: Dict[str, Dict] = {}
        self._build_faq_patterns()
    
    def _build_faq_patterns(self):
        self.faq_patterns = {
            "他社で断られた": {
                "keywords": ["他", "断られ", "引き取って", "くれなかった", "ダメ", "無理", "他社", "別のところ"],
                "line_reply": """お問い合わせありがとうございます。

他社様でお断りされたお品物でも、パーツ取り等でお値段がつく場合もございます。

まずは無料の訪問査定にて、当日担当者へご相談いただけますと幸いです。

ご希望の日時がございましたらお知らせください🙇"""
            },
            "予約変更": {
                "keywords": ["変更", "日程変更", "ずらし", "別日", "時間変更", "予約変更"],
                "line_reply": """ご連絡ありがとうございます。

ご予約の変更を承ります。

お手数ですが、以下をお知らせいただけますでしょうか。
・現在のご予約日時
・ご変更希望の日時

確認でき次第、空き状況をご案内いたします🙇"""
            },
            "キャンセル": {
                "keywords": ["キャンセル", "取消", "やめ", "取りやめ"],
                "line_reply": """ご連絡ありがとうございます。

ご予約のキャンセルを承ります。

お手数ですが、ご予約日時をお知らせいただけますでしょうか。

確認でき次第、キャンセル処理をさせていただきます🙇"""
            },
            "新規予約・査定依頼": {
                "keywords": ["予約したい", "お願い", "来てほしい", "見に来て", "申し込み", "査定してほしい"],
                "line_reply": """お問い合わせありがとうございます。

無料の訪問査定を承ります。

お手数ですが、以下をお知らせいただけますでしょうか。

①査定ご希望のお品物
②お伺い先のご住所
③ご希望の日時
④ご対応者様のお名前
⑤ご連絡先のお電話番号

よろしくお願いいたします🙇"""
            },
            "対応エリア確認": {
                "keywords": ["エリア", "地域", "来れ", "対応", "範囲", "行ける", "出張"],
                "line_reply": """お問い合わせありがとうございます。

お伺い先の市区町村をお知らせいただけますでしょうか。

対応可能エリアか確認させていただきます🙇"""
            },
            "エリア外": {
                "keywords": ["福岡", "大阪", "北海道", "名古屋", "京都", "広島", "沖縄", "九州", "関西"],
                "line_reply": """お問い合わせありがとうございます。

大変申し訳ございませんが、現在のサービス対応エリアは東京都・神奈川県・埼玉県・千葉県となっております。

ご期待に沿えず申し訳ございません。

またの機会がございましたら、よろしくお願いいたします🙇"""
            },
            "査定対象確認": {
                "keywords": ["買取", "見て", "冷蔵庫", "洗濯機", "テレビ", "エアコン", 
                            "ベッド", "家具", "家電", "できますか", "大丈夫"],
                "line_reply": """お問い合わせありがとうございます。

はい、査定の対象でございます。

家具・家電を中心に幅広く査定しておりますので、ぜひ無料の訪問査定をご利用ください。

ご希望の日時がございましたらお知らせください🙇"""
            },
            "料金・費用": {
                "keywords": ["料金", "費用", "かかる", "有料", "処分費", "整理代", "無料", "お金"],
                "line_reply": """お問い合わせありがとうございます。

訪問査定は完全無料でございます。

査定の結果、お値段がつく場合はその場で買取金額をお支払いいたします。

お値段がつかないお品物については、状態により無料でお引き取りできる場合と、整理代をいただいてお引き取りする場合がございます。

詳しくは当日、査定員よりご案内させていただきます🙇"""
            },
            "当日の流れ": {
                "keywords": ["当日", "流れ", "どのくらい", "時間", "何分"],
                "line_reply": """お問い合わせありがとうございます。

当日の流れをご案内いたします。

①ご予約時間の10〜30分前に、査定員よりお電話でご連絡いたします
②査定員がお伺いし、お品物を確認いたします（約30分程度）
③その場で査定結果をご案内いたします
④ご納得いただければ、そのままお引き取りも可能です

ご不明点がございましたらお気軽にお申し付けください🙇"""
            },
            "品物の状態・古い": {
                "keywords": ["汚れ", "古い", "壊れ", "状態", "傷", "動かない", "使用感", "年数", "何年"],
                "line_reply": """お問い合わせありがとうございます。

汚れや使用感があるお品物でも査定は可能でございます。

実際のお値段については、当日査定員が現物を確認させていただいた上でのご案内となります。

お気軽にご相談ください🙇"""
            },
            "搬出・引っ越し": {
                "keywords": ["搬出", "持っていく", "引っ越し", "いつまで", "2週間", "運び出し"],
                "line_reply": """お問い合わせありがとうございます。

査定当日、その場でお引き取りすることも可能でございます。

お品物の大きさや搬出経路によっては、後日のお引き取りとなる場合もございます。

なお、査定日から2週間以内のお引き取りをお願いしております。

詳しくは当日、査定員にご相談ください🙇"""
            },
            "最短・急ぎ": {
                "keywords": ["明日", "今日", "最短", "すぐ", "急ぎ", "早く"],
                "line_reply": """お問い合わせありがとうございます。

最短の日程を確認いたします。

お伺い先の市区町村をお知らせいただけますでしょうか。

空き状況を確認の上、ご案内させていただきます🙇"""
            },
            "到着時間": {
                "keywords": ["何時", "時間", "到着", "来る", "いつ頃"],
                "line_reply": """お問い合わせありがとうございます。

ご予約いただいた時間枠内（例：10時〜11時）に査定員が到着いたします。

当日、到着の10〜30分前に査定員よりお電話でご連絡させていただきますので、ご対応をお願いいたします🙇"""
            },
            "お礼・ありがとう": {
                "keywords": ["ありがとう", "助かり", "よかった", "お世話に"],
                "line_reply": """こちらこそありがとうございます。

またご不明点などございましたら、お気軽にご連絡ください。

どうぞよろしくお願いいたします🙇"""
            },
            "了解・わかりました": {
                "keywords": ["わかりました", "了解", "承知", "大丈夫", "オッケー", "ok"],
                "line_reply": """ありがとうございます。

ご不明点などございましたら、お気軽にお申し付けください。

当日はどうぞよろしくお願いいたします🙇"""
            }
        }
    
    def load_from_markdown(self, filepath: str):
        print(f"読み込み中: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        call_pattern = re.compile(
            r'## Call (\d+)\s*\n'
            r'.*?- \*\*date_time\*\*:\s*(.+?)\n'
            r'.*?- \*\*overview\*\*:\s*(.+?)\n'
            r'.*?- \*\*summary\*\*:\s*\n(.*?)'
            r'- \*\*transcript\*\*:\s*\n(.*?)(?=---|\Z)',
            re.DOTALL
        )
        
        matches = call_pattern.findall(content)
        for match in matches:
            call_id = int(match[0])
            date_time = match[1].strip()
            overview = match[2].strip()
            summary = match[3].strip()
            transcript = match[4].strip()
            
            if summary and transcript:
                self.call_logs.append(CallLog(call_id, date_time, overview, summary, transcript))
        
        print(f"読み込み完了: {len(self.call_logs)}件の通話ログ")
    
    def search_similar_calls(self, query: str, top_n: int = 5) -> List[Tuple[CallLog, float]]:
        query = query.lower()
        query = unicodedata.normalize('NFKC', query)
        query_keywords = set(re.findall(r'[\w]+', query))
        
        results = []
        for log in self.call_logs:
            common = query_keywords & log.keywords
            if common:
                score = len(common) / len(query_keywords) if query_keywords else 0
                summary_match = sum(1 for kw in query_keywords if kw in log.summary.lower())
                score += summary_match * 0.5
                results.append((log, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]
    
    def get_faq_response(self, query: str) -> Tuple[str, str]:
        query_lower = query.lower()
        query_normalized = unicodedata.normalize('NFKC', query_lower)
        
        best_match = None
        best_category = None
        best_score = 0
        
        for category, pattern in self.faq_patterns.items():
            score = 0
            for kw in pattern["keywords"]:
                if kw in query_normalized:
                    score += len(kw)
            if score > best_score:
                best_score = score
                best_match = pattern["line_reply"]
                best_category = category
        
        if best_score >= 2:
            return (best_category, best_match)
        return (None, None)
    
    def generate_response(self, question: str) -> Dict:
        result = {
            "question": question,
            "suggested_response": "",
            "similar_cases": [],
            "faq_match": None,
            "faq_category": None
        }
        
        faq_category, faq_response = self.get_faq_response(question)
        if faq_response:
            result["faq_match"] = faq_response
            result["faq_category"] = faq_category
        
        similar = self.search_similar_calls(question, top_n=3)
        for log, score in similar:
            if score > 0.2:
                result["similar_cases"].append({
                    "call_id": log.call_id,
                    "summary": log.summary[:500] + "..." if len(log.summary) > 500 else log.summary,
                    "relevance_score": round(score, 2)
                })
        
        if faq_response:
            result["suggested_response"] = faq_response
        elif similar and similar[0][1] > 0.3:
            best_log = similar[0][0]
            result["suggested_response"] = f"【過去の類似事例 Call {best_log.call_id} を参考】\n\n{best_log.summary}"
        else:
            result["suggested_response"] = "該当する過去事例が見つかりませんでした。\nお手数ですが、詳細をお聞きして対応をご案内ください。"
        
        return result


# グローバルな知識ベースインスタンス
kb = CSKnowledgeBase()

@app.route('/')
def index():
    return render_template('index.html', log_count=len(kb.call_logs))

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    question = data.get('question', '')
    
    if not question.strip():
        return jsonify({"error": "質問を入力してください"})
    
    result = kb.generate_response(question)
    return jsonify(result)

@app.route('/faq')
def faq_list():
    faqs = []
    for category, pattern in kb.faq_patterns.items():
        faqs.append({
            "category": category,
            "keywords": pattern["keywords"][:5],
            "response": pattern["response_template"]
        })
    return jsonify(faqs)


def init_app():
    log_file = Path(__file__).parent / "出張買取プラス_IVRy通話ログ.md"
    if log_file.exists():
        kb.load_from_markdown(str(log_file))
    else:
        print(f"警告: ログファイルが見つかりません: {log_file}")
        print("FAQパターンのみで動作します")


init_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
