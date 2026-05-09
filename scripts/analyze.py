import os
import json
from utils import logger, get_data_path, load_json, read_text, save_json, get_kst_now

def analyze_rule_based(stores, rules, collected_data, manual_notes):
    logger.info("Performing rule-based analysis.")
    ranking = []
    
    for idx, store in enumerate(stores):
        store_id = store['id']
        c_data = collected_data.get(store_id, {})
        
        # Base score based on priority
        score = 80 - (store['priority'] * 5)
        reason = "기본 매장 우선순위 반영"
        action = "현장 1000엔 테스트 진행"
        
        # Adjust score based on collected data keywords and rules
        found_keywords = []
        links_data = c_data.get("links_data", {})
        for k, v in links_data.items():
            if v.get("status") == "success":
                found_keywords.extend(v.get("keywords_found", []))
        
        found_keywords = list(set(found_keywords))
        
        # Rule-based scoring
        primary_targets = rules.get("primary_targets", [])
        if any(pt in found_keywords for pt in primary_targets) or "에바" in store['target']:
            score += 10
            reason = "1엔 에바15/에바 계열 확인됨"
            action = "에바 현장 1000엔 회전수 테스트"
        elif "甘デジ" in found_keywords:
            score += 5
            reason = "에바 외 대체 기종(甘デジ) 확인"
        elif "ライト" in found_keywords or "ライトミドル" in found_keywords:
            score += 3
            reason = "에바 외 대체 기종(ライト급) 확인"
        elif "ミドル" in found_keywords:
            score += 1
            reason = "미들급 확인됨 (에바 외)"
            
        # Adjust based on manual notes
        if store['name'] in manual_notes:
            if "좋" in manual_notes or "추천" in manual_notes:
                score += 15
                reason = "수동 메모 긍정적 내용 반영"
            elif "별로" in manual_notes or "비추" in manual_notes or "나쁘" in manual_notes:
                score -= 20
                reason = "수동 메모 부정적 내용 반영"

        # Check collection failure
        source_status = "OK"
        if all(v.get("status") != "success" for k, v in links_data.items() if v.get("status") != "skipped"):
            score -= 5
            source_status = "Failed (Used previous/fallback data)"
            
        ranking.append({
            "rank": 0,
            "store_id": store_id,
            "store_name": store['name'],
            "score": score,
            "confidence": "Medium",
            "reason": reason,
            "action": f"{action} (현장 1,000엔 회전수 확인 필수)",
            "data_freshness": c_data.get("checked_at", "Unknown"),
            "source_status": source_status
        })
    
    ranking = sorted(ranking, key=lambda x: x['score'], reverse=True)
    for i, r in enumerate(ranking):
        r['rank'] = i + 1
        
    return ranking

def main():
    stores_data = load_json(get_data_path('stores.json'), {})
    stores = stores_data.get('stores', []) if isinstance(stores_data, dict) else stores_data
    rules = stores_data.get('machine_priority_rules', {}) if isinstance(stores_data, dict) else {}
    
    collected_data = load_json(get_data_path('collected.json'), {})
    manual_notes = read_text(get_data_path('manual-notes.md'))
    
    ranking = analyze_rule_based(stores, rules, collected_data, manual_notes)
        
    latest_data = {
        "generated_at": get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "target": "1엔 파친코",
        "primary_target": "에바15 / 에바 계열 우선",
        "fallback_target": "에바 외 대체 (1/99, 1/129, 1/199 전후 가벼운 기종 우선)",
        "manual_notes_used": len(manual_notes) > 10,
        "ranking": ranking,
        "field_decision_guide": {
            ">=70": "계속 칠 만함",
            "60-69": "연출 목적이면 가능",
            "55-59": "오래 앉기 비추천",
            "<55": "이동 권장"
        }
    }
    
    save_json(latest_data, get_data_path('latest.json'))
    logger.info("Analysis finished.")

if __name__ == "__main__":
    main()
