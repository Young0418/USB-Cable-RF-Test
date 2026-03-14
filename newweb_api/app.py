import json
import logging
import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request

try:
    from controller import run as controller_run
    controller_available = True
except Exception as exc:
    controller_available = False
    logging.warning("controller.py 导入失败，使用模拟数据: %s", exc)

    def controller_run(cable_type: str):
        import random
        return {
            "qualified": random.choice([True, True, False]),
            "message": f"{cable_type} 自动模拟检测完成",
            "s11_qualified": random.choice([True, True, False]),
            "s21_qualified": True,
            "cable_type": cable_type,
            "analysis_detail": {
                "s11_mean": round(random.uniform(-30, -15), 1),
                "s21_mean": round(random.uniform(-3, -0.5), 1),
            },
            "device_info": {
                "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": "Virtual-VNA",
            },
        }

try:
    from deepseek_client import DeepSeekClient
except ImportError as exc:
    raise RuntimeError("deepseek_client.py 导入失败") from exc

app = Flask(__name__, static_folder="static", template_folder="templates")
app.json.ensure_ascii = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log", encoding="utf-8")],
)
logger = logging.getLogger(__name__)

DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
os.makedirs(DATA_DIR, exist_ok=True)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
deepseek_client = DeepSeekClient(DEEPSEEK_API_KEY) if DEEPSEEK_API_KEY else None
if not DEEPSEEK_API_KEY:
    logger.warning("未检测到 DEEPSEEK_API_KEY，AI功能不可用")


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("读取历史记录失败: %s", exc)
        return []


def save_history(record):
    history = load_history()
    record["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.insert(0, record)
    history = history[:50]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error("写入历史记录失败: %s", exc)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/test", methods=["POST"])
def api_test():
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"success": False, "error": "请求数据为空"}), 400

    cable_type = payload.get("cable_type") or "RG316"
    logger.info("开始检测线缆: %s", cable_type)
    try:
        result = controller_run(cable_type)
        save_history(
            {
                "cable_type": cable_type,
                "qualified": result.get("qualified"),
                "message": result.get("message", ""),
                "s11_mean": result.get("analysis_detail", {}).get("s11_mean"),
                "s21_mean": result.get("analysis_detail", {}).get("s21_mean"),
                "s11_qualified": result.get("s11_qualified", True),
                "s21_qualified": result.get("s21_qualified", True),
            }
        )
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        logger.exception("检测失败: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    try:
        return jsonify({"success": True, "data": load_history()})
    except Exception as exc:
        logger.exception("获取历史记录失败")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/ai-analysis", methods=["POST"])
def api_ai_analysis():
    if not deepseek_client:
        return jsonify({"success": False, "analysis": "AI服务暂不可用"})
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"success": False, "analysis": "请求数据为空"}), 400

    result = payload.get("result") or {}
    question = payload.get("question", "").strip()
    try:
        analysis = deepseek_client.analyze_cable_data(result, question)
        return jsonify({"success": True, "analysis": analysis})
    except Exception as exc:
        logger.exception("AI分析失败: %s", exc)
        return jsonify({"success": False, "analysis": f"AI分析失败：{exc}"}), 500


@app.route("/api/test-ai", methods=["GET"])
def api_test_ai():
    if not deepseek_client:
        return jsonify({"success": False, "message": "DeepSeek 未配置"})
    try:
        success, message = deepseek_client.test_connection()
        return jsonify({"success": success, "message": message})
    except Exception as exc:
        logger.exception("AI连接测试异常")
        return jsonify({"success": False, "message": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "controller": controller_available,
            "ai_service": bool(deepseek_client),
        }
    )


if __name__ == "__main__":
    logger.info("线缆检测系统启动 http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)