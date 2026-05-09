import os
import json
from utils import logger, get_data_path, get_docs_path, load_json, write_text, save_json

def build_markdown(latest):
    md = f"# 🎰 Daily Pachinko Report (Osaka Namba)\n\n"
    md += f"**생성 시각:** {latest.get('generated_at', 'Unknown')}\n"
    md += f"**수동 메모 반영 여부:** {'예' if latest.get('manual_notes_used') else '아니오'}\n"
    md += f"**1엔 에바 우선 여부:** {latest.get('primary_target', '')}\n"
    md += f"**에바 외 대체 기종 기준:** {latest.get('fallback_target', '')}\n\n"
    
    md += "## 🏆 오늘의 후보 매장 순위\n\n"
    
    ranking = latest.get("ranking", [])
    for r in ranking:
        md += f"### {r['rank']}위: {r['store_name']} (점수: {r['score']})\n"
        md += f"- **수집 상태:** {r['source_status']} ({r['data_freshness']})\n"
        md += f"- **추천 이유:** {r['reason']}\n"
        md += f"- **행동 지침:** {r['action']}\n\n"
        
    md += "## 🚦 현장 1,000엔 회전수 판단 기준\n"
    guide = latest.get("field_decision_guide", {})
    md += f"- 70회전 이상: {guide.get('>=70', '')}\n"
    md += f"- 60~70회전: {guide.get('60-69', '')}\n"
    md += f"- 55~60회전: {guide.get('55-59', '')}\n"
    md += f"- 55회전 미만: {guide.get('<55', '')}\n\n"
    
    return md

def build_html(latest, md_content):
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pachinko Osaka Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; color: #333; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .card {{ background: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
        .rank-1 {{ border-left: 5px solid #ffd700; }}
        .rank-2 {{ border-left: 5px solid #c0c0c0; }}
        .rank-3 {{ border-left: 5px solid #cd7f32; }}
        ul {{ padding-left: 20px; }}
        .meta {{ background: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>🎰 오늘의 파친코 후보 매장 리포트</h1>
    
    <div class="meta">
        <p><strong>생성 시각:</strong> {latest.get('generated_at', 'Unknown')}</p>
        <p><strong>수동 메모 반영 여부:</strong> {'예' if latest.get('manual_notes_used') else '아니오'}</p>
        <p><strong>1엔 에바 우선 여부:</strong> {latest.get('primary_target', '')}</p>
        <p><strong>에바 외 대체 기종 기준:</strong> {latest.get('fallback_target', '')}</p>
    </div>
    
    <h2>🚦 현장 1,000엔 회전수 판단 기준</h2>
    <ul>
"""
    guide = latest.get("field_decision_guide", {})
    html += f"""        <li><strong>70회전 이상:</strong> {guide.get('>=70', '')}</li>
        <li><strong>60~70회전:</strong> {guide.get('60-69', '')}</li>
        <li><strong>55~60회전:</strong> {guide.get('55-59', '')}</li>
        <li><strong>55회전 미만:</strong> {guide.get('<55', '')}</li>
    </ul>

    <h2>🏆 오늘의 후보 매장 순위</h2>
"""
    ranking = latest.get("ranking", [])
    for r in ranking:
        rank_class = f"rank-{r['rank']}" if r['rank'] <= 3 else ""
        html += f"""
    <div class="card {rank_class}">
        <h3>{r['rank']}위: {r['store_name']} (점수: {r['score']})</h3>
        <p><strong>📡 수집 상태:</strong> {r['source_status']} ({r['data_freshness']})</p>
        <p><strong>✅ 이유:</strong> {r['reason']}</p>
        <p><strong>🏃 지침:</strong> {r['action']}</p>
    </div>
"""
        
    html += f"""
</body>
</html>
"""
    return html

def main():
    latest = load_json(get_data_path('latest.json'), {})
    if not latest:
        logger.error("latest.json is empty. Aborting report build.")
        return
        
    md_content = build_markdown(latest)
    html_content = build_html(latest, md_content)
    
    # Save files
    write_text(md_content, get_data_path('latest-report.md'))
    write_text(md_content, get_docs_path('latest-report.md'))
    write_text(html_content, get_docs_path('index.html'))
    save_json(latest, get_docs_path('latest.json'))
    
    logger.info("Reports successfully built in data/ and docs/")

if __name__ == "__main__":
    main()
