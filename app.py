import streamlit as st
import pandas as pd
import requests
import openai
import os
from streamlit.errors import StreamlitSecretNotFoundError
from cable_thresholds import FREQ_THRESHOLDS, MEAN_THRESHOLDS, SUPPORTED_LENGTHS
from copy import deepcopy
from datetime import datetime


def get_closest_length(target_length, supported_lengths):
    if not supported_lengths:
        return None
    return min(supported_lengths, key=lambda L: abs(L - target_length))


# ---------- 安全获取 DeepSeek API 密钥 ----------
try:
    _ = st.secrets
    DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
except StreamlitSecretNotFoundError:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    st.error("未找到 DeepSeek API 密钥，请在环境变量或 ..streamlit/secrets.toml 中设置 DEEPSEEK_API_KEY")
    st.stop()

client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

# ---------- Streamlit 页面配置 ----------
st.set_page_config(page_title="USB线缆检测系统 (AI 增强版)", layout="wide")
st.title("USB 线缆 S 参数检测 + DeepSeek 智能分析")
st.sidebar.header("操作面板")

cable_options = list(MEAN_THRESHOLDS.keys())
selected_cable = st.sidebar.selectbox("选择线缆类型", cable_options)

cable_length = st.sidebar.number_input(
    "线缆长度 (m)",
    min_value=0.1,
    max_value=100.0,
    value=1.0,
    step=0.1,
    help="输入被测线缆的实际长度，用于S21阈值计算（损耗与长度成正比）"
)

# 自动匹配最接近的长度
use_len = get_closest_length(cable_length, SUPPORTED_LENGTHS)
if selected_cable in FREQ_THRESHOLDS and use_len in FREQ_THRESHOLDS[selected_cable]:
    freq_config = FREQ_THRESHOLDS[selected_cable][use_len]
else:
    freq_config = DEFAULT_FREQ_THRESHOLD

s11_th = freq_config["S11"][0]
s21_th = freq_config["S21"][0]

API_URL = "http://localhost:8000/analyze"

# ---------- 初始化会话状态 ----------
if "detection_result" not in st.session_state:
    st.session_state.detection_result = None
if "ai_analysis_triggered" not in st.session_state:
    st.session_state.ai_analysis_triggered = False
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "remaining_questions" not in st.session_state:
    st.session_state.remaining_questions = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "history_selected" not in st.session_state:
    st.session_state.history_selected = None

def call_deepseek(prompt: str, system_prompt: str = "你是一位线缆检测专家，回复简洁易懂。") -> str:
    """调用 DeepSeek API 生成回答"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI 分析暂时不可用：{str(e)}"

# ---------- 开始检测按钮 ----------
if st.sidebar.button("开始检测"):
    with st.spinner("正在调用后端 API 进行分析..."):
        try:
            resp = requests.post(
                API_URL,
                json={"cable_type":selected_cable, "length":cable_length},
                timeout=30
            )
            resp.raise_for_status()
            result = resp.json()
            st.session_state.detection_result = result

            history_entry = {
                "record_id": len(st.session_state.history) + 1,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cable_type": selected_cable,
                "length": float(cable_length),
                "qualified": result.get("qualified"),
                "message": result.get("message"),
                "result": deepcopy(result)
            }
            st.session_state.history.insert(0, history_entry)
            st.session_state.history_selected = history_entry["record_id"]

            # 重置 AI 相关状态
            st.session_state.ai_analysis_triggered = False
            st.session_state.conversation = []
            st.session_state.remaining_questions = 0
        except Exception as e:
            st.error(f"后端调用失败：{e}")
            st.stop()

# ---------- 显示检测结果（如果有） ----------
if st.session_state.detection_result:
    result = st.session_state.detection_result

    st.subheader("设备信息")
    dev_info = result['device_info']
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("仪器型号", dev_info.get('model', 'N/A'))
    col2.metric("硬件线缆类型", dev_info.get('cable_type', 'N/A'))
    col3.metric("测试时间", dev_info.get('test_time', 'N/A'))
    col4.metric("用户选择", selected_cable)
    st.caption(f"线缆长度：{cable_length} 米 → 匹配阈值长度：{use_len} 米")

    st.subheader("检测结果")
    if result['qualified']:
        st.success(f"线缆合格：{result['message']}")
    else:
        st.error(f"线缆不合格：{result['message']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**S11 参数**")
        if result['s11_qualified']:
            st.info(f"S11 合格 (所有点 < {s11_th} dB)")
        else:
            st.warning(f"S11 不合格 (存在 ≥ {s11_th} dB 的点)")
        freq_s11 = result['s11_data'][0] if result['s11_data'] else []
        mag_s11 = result['s11_data'][1] if result['s11_data'] else []
        if freq_s11 and mag_s11:
            df_s11 = pd.DataFrame({'测试点': freq_s11, 'S11 (dB)': mag_s11})
            st.line_chart(df_s11.set_index('测试点'))
        else:
            st.write("无 S11 数据")

    with col2:
        st.markdown("**S21 参数**")
        if result['s21_qualified']:
            st.info(f"S21 合格 (所有点 > {s21_th} dB)")
        else:
            st.warning(f"S21 不合格 (存在 ≤ {s21_th} dB 的点)")
        freq_s21 = result['s21_data'][0] if result['s21_data'] else []
        mag_s21 = result['s21_data'][1] if result['s21_data'] else []
        if freq_s21 and mag_s21:
            df_s21 = pd.DataFrame({'测试点': freq_s21, 'S21 (dB)': mag_s21})
            st.line_chart(df_s21.set_index('测试点'))
        else:
            st.write("无 S21 数据")

    with st.expander("查看原始数据"):
        st.json(result)

    # ---------- AI 分析部分 ----------
    st.markdown("---")

    st.subheader("历史检测记录")
    history = st.session_state.history
    if history:
        history_df = pd.DataFrame([
            {
                "记录ID": rec["record_id"],
                "检测时间": rec["time"],
                "线缆": rec["cable_type"],
                "长度(m)": rec["length"],
                "整体验收": "合格" if rec["qualified"] else "不合格",
                "备注": rec["message"]
            }
            for rec in history
        ])
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        options = {f'#{rec["record_id"]} | {rec["time"]} | {rec["cable_type"]}':
                   rec["record_id"] for rec in history}
        selected_label = st.selectbox(
            "选择一条历史记录进行回放：",
            options=list(options.keys()),
            key="history_select",
        )
        col_hist1, col_hist2 = st.columns([1, 1])
        if col_hist1.button("加载该记录", use_container_width=True):
            selected_id = options[selected_label]
            selected_record = next((rec for rec in history if rec["record_id"] == selected_id), None)
            if selected_record:
                st.session_state.detection_result = deepcopy(selected_record["result"])
                st.session_state.ai_analysis_triggered = False
                st.session_state.conversation = []
                st.session_state.remaining_questions = 0
                st.session_state.history_selected = selected_id
                st.rerun()
        if col_hist2.button("清空历史记录", use_container_width=True):
            st.session_state.history.clear()
            st.session_state.history_selected = None
            st.rerun()
    else:
        st.info("暂无历史数据，点击“开始检测”后会自动保存每一次结果。")

    st.subheader("AI 智能分析")

    if not st.session_state.ai_analysis_triggered:
        if st.button("进行AI分析"):
            with st.spinner("AI 正在思考中..."):
                init_prompt = f"""
你是一个射频线缆检测专家。以下是某次 USB 线缆 S 参数检测的结果：

- 线缆类型：{result.get('cable_type')}
- 整体合格：{'是' if result.get('qualified') else '否'}
- S11 合格：{'是' if result.get('s11_qualified') else '否'}
- S21 合格：{'是' if result.get('s21_qualified') else '否'}
- S11 均值：{result['analysis_detail'].get('s11_mean')} dB
- S21 均值：{result['analysis_detail'].get('s21_mean')} dB
- 线缆长度：{cable_length} 米
- 系统消息：{result.get('message')}

请用 50 字以内给出一个简短、易懂的结论，并可以提一句建议（比如是否需要更换线缆、调整测试环境等）。语气要友好，适合展示给普通用户。
                """
                initial_analysis = call_deepseek(init_prompt)
                st.session_state.conversation.append({"role": "assistant", "content": initial_analysis})
                st.session_state.remaining_questions = 3
                st.session_state.ai_analysis_triggered = True
                st.rerun()
    else:
        for msg in st.session_state.conversation:
            if msg["role"] == "assistant":
                st.info(f"🧠 AI：{msg['content']}")
            else:
                st.markdown(f"👤 你：{msg['content']}")

        if st.session_state.remaining_questions > 0:
            with st.form(key="question_form"):
                user_question = st.text_input(f"你有什么问题想问AI？（剩余 {st.session_state.remaining_questions} 次）")
                submitted = st.form_submit_button("发送")
                if submitted and user_question.strip():
                    st.session_state.conversation.append({"role": "user", "content": user_question})
                    st.session_state.remaining_questions -= 1
                    with st.spinner("AI 正在回答..."):
                        answer = call_deepseek(user_question)
                        st.session_state.conversation.append({"role": "assistant", "content": answer})
                    st.rerun()
        else:
            st.info("你已用完 3 次提问机会。如需继续咨询，请重新开始检测。")
else:
    st.info("点击左侧“开始检测”按钮，先获取线缆检测结果。")

st.sidebar.markdown("---")
st.sidebar.caption("项目：USB线缆检测大创")
