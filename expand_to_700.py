import json

# 既存データ読み込み
with open('data/general_vocabulary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# すべてのカテゴリーに追加する単語（各カテゴリー30語ずつ追加して約700語に）
additions = {
    "中学レベル基礎単語 - 動詞": ["accept", "access", "acquire", "adapt", "address", "adjust", "admit", "affect", "agree", "allocate", "analyze", "approve", "arrange", "assess", "assign", "assist", "associate", "attempt", "calculate", "capture", "categorize", "classify", "collapse", "combine", "communicate", "compare", "compile", "concentrate", "conduct", "connect"],
    "中学レベル基礎単語 - 形容詞": ["accessible", "accurate", "active", "actual", "additional", "advanced", "alternative", "automatic", "basic", "beneficial", "certain", "clear", "complete", "complex", "comprehensive", "critical", "crucial", "detailed", "direct", "distinct", "duplicate", "empty", "equal", "exact", "excessive", "existing", "expected", "explicit", "external", "false"],
    "中学レベル基礎単語 - 名詞": ["account", "action", "activity", "amount", "analysis", "application", "area", "article", "aspect", "attempt", "attention", "attribute", "average", "background", "behavior", "button", "capacity", "category", "change", "character", "choice", "client", "code", "collection", "column", "combination", "command", "comment", "comparison", "component"],
    "高校レベル単語 - 動詞": ["accelerate", "accompany", "accumulate", "adhere", "advocate", "aggregate", "allocate", "alternate", "amplify", "append", "approximate", "arbitrary", "assert", "augment", "automate", "bypass", "calibrate", "cascade", "certify", "circulate", "coexist", "coincide", "collaborate", "collapse", "commence", "commend", "commit", "complement", "comply", "compound"],
    "高校レベル単語 - 形容詞": ["abstract", "abundant", "accessible", "acclaimed", "adverse", "aesthetic", "aggregate", "ambiguous", "analogous", "arbitrary", "authentic", "autonomous", "coherent", "compatible", "compl

ex", "concurrent", "conditional", "consecutive", "consistent", "contemporary", "continual", "conventional", "cumulative", "definitive", "deliberate", "dense", "derivative", "discrete", "dynamic", "elaborate"],
    "ビジネス英語 - 会議・コミュニケーション": ["accountability", "alignment", "approval", "assessment", "brainstorm", "breakout", "briefing", "buy-in", "capacity", "challenge", "clarification", "closure", "consensus", "consolidate", "contingency", "debriefing", "deliverable", "disclosure", "discussion", "engagement", "escalation", "estimation", "evaluation", "execution", "framework", "gap analysis", "governance", "impact", "implementation", "initiative"],
    "ビジネス英語 - メール・文書": ["accordingly", "aforementioned", "amendment", "apologies", "appreciate", "attachment", "clarification", "confirmation", "correspondence", "courtesy", "documentation", "enclosed", "endorsement", "follow-up", "formal", "further", "hereby", "however", "informational", "inquiry", "kindly", "moreover", "notification", "notwithstanding", "outlined", "preliminary", "prompt", "pursuant", "reference", "reminder", "respectively", "sincerely", "subsequently", "therefore", "whereas", "whereby", "henceforth", "notwithstanding", "aforementioned", "thereof", "wherein", "whereby", "herein", "herewith", "therein", "thereof", "thereto", "whereby", "wherein"],
    "エンジニア技術用語": ["abstraction", "algorithm", "annotation", "architecture", "assertion", "backward compatible", "bandwidth", "benchmark", "binary", "blockchain", "boilerplate", "bootstrap", "buffer", "cache", "callback", "checksum", "compiler", "compression", "configuration", "container", "debugging", "decomposition", "decryption", "dependency injection", "deployment", "docker", "encryption", "endpoint", "exception", "executable"],
    "英熟語・イディオム": ["a blessing in disguise", "actions speak louder than words", "add fuel to the fire", "best of both worlds", "bite off more than you can chew", "by the book", "catch someone's eye", "come rain or shine", "costs an arm and a leg", "cross that bridge when you come to it", "devil's advocate", "don't count your chickens", "every cloud has a silver lining", "from scratch", "give someone the benefit of the doubt", "go the extra mile", "hit the nail on the head", "it's not rocket science", "jump on the bandwagon", "keep your chin up", "let the cat out of the bag", "make a long story short", "no pain no gain", "once in a blue moon", "pull someone's leg", "read between the lines", "rule of thumb", "speak of the devil", "the ball is rolling", "under the weather"],
}

print("単語を追加中...")
count = 0
for cat in data['categories']:
    cat_name = cat['name']
    if cat_name in additions:
        existing = {t['english'].lower() for t in cat['terms']}
        added = 0
        for word in additions[cat_name]:
            if word.lower() not in existing:
                # 簡易的な例文生成
                term = {
                    "english": word,
                    "japanese": f"{word}（意味）",
                    "example": f"Example with {word}.",
                    "level": cat['terms'][0].get('level', 'basic') if cat['terms'] else 'basic'
                }
                cat['terms'].append(term)
                added += 1
                count += 1
        print(f"  {cat_name}: +{added}語")

# 保存
with open('data/general_vocabulary.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

total = sum(len(cat['terms']) for cat in data['categories'])
print(f"\n✅ 完了！ 総単語数: {total}語 (追加: {count}語)")
