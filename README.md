# 水星家纺 · 异常交易实时监测（Hackathon Demo）

TGD 2026 GC Customer AI Use Case —— 场景 5 异常交易实时检测。  
Fiori 风格交互界面，展示 AI 告警卡：异常原因（三层联动）+ 相似历史案例 + 建议动作。

## 运行

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --port 8000
# 浏览器打开 http://127.0.0.1:8000/
```

## 演示脚本

1. 首页点「▶ 触发实时检测」——展示三层检测流水动画（5 步），发现 3 条异常
2. 点开 **供应商银行账户变更后首笔大额付款**（风险 91）——讲 BEC 欺诈 + 画像层间隔风险
3. 点开 **重复付款**（风险 82）——讲多系统孤岛跨渠道关联，同发票号 12 天内两次支付
4. 点开 **临界值聚集拆单**（风险 87）——讲统计层 Z-Score=3.8 + 画像集中度偏差
5. 强调每张卡的 ④ 建议动作（立即/24h内/可选）= 决策支持，而非"异常"标签

## 架构接缝（接真实环境只需替换）

| 当前实现 | 生产替换目标 |
|---------|------------|
| `backend/data/alerts.json` 预制数据 | 鼎捷 ERP / BTP 集成层实时取数 |
| 结构化模板生成告警卡 | SAP AI Core + Qwen / Generative AI Hub |
| 静态历史案例 | HANA Cloud 向量引擎 RAG 检索 |

## 测试

```bash
python -m pytest tests/ -v
```

## 项目结构

```
backend/
  main.py              # FastAPI：告警 API + A2A 协议 + 静态托管
  data/alerts.json     # 3 张完整告警卡
frontend/
  index.html / app.js / styles.css   # Fiori 风单页应用
tests/
  test_api.py          # API 契约冒烟测试（4 项）
```
