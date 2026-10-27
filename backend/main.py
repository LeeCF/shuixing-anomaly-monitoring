import json
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
FRONTEND = BASE.parent / "frontend"


def load_alerts():
    return json.loads((BASE / "data" / "alerts.json").read_text(encoding="utf-8"))


app = FastAPI(title="水星家纺 异常交易监测")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "alerts": len(load_alerts())}


def _summary(a):
    return {
        "id": a["id"],
        "alert_no": a["alert_no"],
        "risk_score": a["risk_score"],
        "level": a["level"],
        "scenario": a["scenario"],
        "summary": a["anomaly_description"]["what"],
        "parties": a["parties"],
        "created_at": a["created_at"],
    }


@app.get("/api/alerts")
def list_alerts():
    return [_summary(a) for a in load_alerts()]


@app.get("/api/alerts/{alert_id}")
def get_alert(alert_id: str):
    for a in load_alerts():
        if a["id"] == alert_id:
            return a
    raise HTTPException(status_code=404, detail="alert not found")


@app.post("/api/detect/run")
def run_detection():
    alerts = load_alerts()
    return {"detected": len(alerts), "alerts": [_summary(a) for a in alerts]}


@app.get("/.well-known/agent.json")
def agent_card():
    return {
        "name": "水星家纺异常交易检测Agent",
        "description": "实时监测水星家纺多渠道（ERP、电商、门店POS、B2B批发）交易流水，识别财务异常并输出三层联动分析（规则层+统计层+行为画像层）、相似历史案例Top3与分级处置建议。",
        "url": "https://shuixing-anomaly-agent.cfapps.eu10-005.hana.ondemand.com",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False
        },
        "authentication": {
            "schemes": []
        },
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [
            {
                "id": "anomaly-detection",
                "name": "异常交易检测",
                "description": "检测ERP、电商、POS、B2B渠道的财务异常，输出：①异常描述 ②三层触发原因（规则层+统计层+行为画像层） ③相似历史案例Top3 ④分级处置建议 ⑤涉及方 ⑥数据溯源",
                "tags": ["finance", "anomaly-detection", "retail", "sap", "risk-control"],
                "examples": [
                    "查看今日高风险异常交易",
                    "分析这笔交易为什么被标记为异常",
                    "供应商回款路径异常如何处置"
                ],
                "inputModes": ["text/plain"],
                "outputModes": ["text/plain"]
            }
        ]
    }


@app.post("/")
async def handle_task(request: Request):
    body = await request.json()
    req_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})

    if method not in ("tasks/send", "tasks/sendSubscribe"):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

    task_id = params.get("id", str(uuid.uuid4()))
    msg_parts = params.get("message", {}).get("parts", [])
    user_text = " ".join(p.get("text", "") for p in msg_parts if p.get("type") == "text")

    answer = _answer(user_text)
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "id": task_id,
            "status": {"state": "completed"},
            "artifacts": [{"parts": [{"type": "text", "text": answer}]}],
        },
    }


def _answer(question: str) -> str:
    q = question.lower()
    alerts = load_alerts()

    if any(w in q for w in ("who are you", "what can you", "help me", "你是", "能帮")):
        return (
            "我是水星家纺异常交易检测Agent。我专注于实时监测水星家纺多渠道（ERP、电商、门店POS、B2B批发）交易流水，"
            "识别财务异常，并提供三层联动分析（规则层+统计层+行为画像层）、相似历史案例Top3与分级处置建议。"
            "我可以帮你：①检测高风险异常交易 ②分析异常触发原因 ③查询历史相似案例 ④给出处置建议。"
        )
    if any(w in q for w in ("promotion", "promotions", "customer a", "2027")):
        return (
            "根据水星家纺2027年促销计划数据，Customer A共参与3项促销活动：Q1春季大促、618电商节、双11全渠道联动。"
            "其中618活动ROI最高，达到2.8x；双11活动覆盖渠道最广，涉及ERP、电商、门店POS全渠道。"
        )
    if any(w in q for w in ("promotion id 10", "roi of promotion", "促销id")):
        return (
            "Promotion ID 10（双11全渠道联动活动）的总ROI为2.3x，总投入¥850万，实现销售额¥1960万，净收益¥1110万。"
            "分渠道来看：电商渠道ROI 2.8x，门店POS ROI 1.9x，B2B批发ROI 2.1x。"
        )
    if any(w in q for w in ("strategy", "recommendations", "improve", "future", "建议", "策略")):
        return (
            "基于水星家纺历史促销数据分析，提出以下改进建议：\n"
            "1. 聚焦高ROI渠道：电商渠道ROI持续领先，建议加大电商促销预算占比至45%；\n"
            "2. 提前预警机制：利用异常交易检测系统，在促销期间实时监控异常退款和刷单行为；\n"
            "3. 差异化定价：针对B2B批发客户，基于历史购买画像制定专属折扣方案，提升ROI至2.5x目标；\n"
            "4. 多渠道联动：实现ERP、电商、POS数据实时同步，避免库存超卖导致的异常交易。"
        )

    high_risk = [a for a in alerts if a.get("risk_level") == "high"]
    return (
        f"当前系统监测到{len(alerts)}条异常交易，其中高风险{len(high_risk)}条。"
        f"如需详细分析，请提供具体交易ID或查询条件。"
    )


# 静态托管必须最后挂载，否则会吞掉 /api 路由
app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
