import streamlit as st
import pandas as pd
import requests
import openai
import os
import numpy as np
from streamlit.errors import StreamlitSecretNotFoundError
from cable_thresholds import FREQ_THRESHOLDS, MEAN_THRESHOLDS, SUPPORTED_LENGTHS,DEFAULT_FREQ_THRESHOLD,DEFAULT_MEAN
from copy import deepcopy
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import io
import tempfile

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

if "selected_batch_idx" not in st.session_state:
    st.session_state.selected_batch_idx = None

if "batch_mode" not in st.session_state:
    st.session_state.batch_mode = False
if "batch_index" not in st.session_state:
    st.session_state.batch_index = 0
if "batch_results" not in st.session_state:
    st.session_state.batch_results = []
if "batch_total" not in st.session_state:
    st.session_state.batch_total = 0
if "batch_cable" not in st.session_state:
    st.session_state.batch_cable = ""
if "batch_length" not in st.session_state:
    st.session_state.batch_length = 1.0

# token限制（目前2400，可长对话）
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
            max_tokens=2400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI 分析暂时不可用：{str(e)}"

def call_deepseek_with_history(messages: list, system_prompt: str = "你是射频测试专家。") -> str:
    """
    messages: 对话历史，格式为 [{"role": "user/assistant", "content": "..."}, ...]
    system_prompt: 系统提示（可包含阈值标准）
    """
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.7,
            max_tokens=2400   # 已放开
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI 分析暂时不可用：{str(e)}"

def get_threshold_comparison(cable_type, length, result):
    """生成当前线缆的阈值标准与实际测量值的对比文本"""
    # 获取频率点阈值（若没有精确匹配长度，使用最接近长度的阈值）
    supported_lengths = SUPPORTED_LENGTHS
    if supported_lengths:
        closest_len = min(supported_lengths, key=lambda L: abs(L - length))
    else:
        closest_len = None
    
    if cable_type in FREQ_THRESHOLDS and closest_len in FREQ_THRESHOLDS[cable_type]:
        ft = FREQ_THRESHOLDS[cable_type][closest_len]
        freq_th = ft["freqs"]
        s11_th_table = ft["S11"]
        s21_th_table = ft["S21"]
    else:
        ft = DEFAULT_FREQ_THRESHOLD
        freq_th = ft["freqs"]
        s11_th_table = ft["S11"]
        s21_th_table = ft["S21"]
    
    # 获取均值阈值
    mean_th = MEAN_THRESHOLDS.get(cable_type, DEFAULT_MEAN)
    s11_mean_good = mean_th["s11_mean_good"]
    s21_mean_good = mean_th["s21_mean_good"]
    
    # 提取实际测量数据
    freq_meas, s11_meas = result['s11_data']
    _, s21_meas = result['s21_data']
    
    # 构建逐点对比字符串（限制展示前10个点避免过长）
    s11_points = []
    s21_points = []
    for i, f in enumerate(freq_meas):
        # 找到对应的阈值（插值）
        s11_th = np.interp(f, freq_th, s11_th_table)
        s21_th = np.interp(f, freq_th, s21_th_table)
        s11_ok = s11_meas[i] < s11_th
        s21_ok = s21_meas[i] > s21_th
        s11_points.append(f"频率 {f/1e9:.1f}GHz: 实测 {s11_meas[i]:.1f}dB, 阈值 {s11_th:.1f}dB, {'合格' if s11_ok else '不合格'}")
        s21_points.append(f"频率 {f/1e9:.1f}GHz: 实测 {s21_meas[i]:.1f}dB, 阈值 {s21_th:.1f}dB, {'合格' if s21_ok else '不合格'}")
    
    # 只展示前5个点和后5个点（如果点很多）
    if len(s11_points) > 10:
        s11_display = s11_points[:5] + ["..."] + s11_points[-5:]
        s21_display = s21_points[:5] + ["..."] + s21_points[-5:]
    else:
        s11_display = s11_points
        s21_display = s21_points
    
    comparison_text = f"""
### 阈值标准（线缆类型：{cable_type}，长度：{length}m，实际使用阈值长度：{closest_len}m）

**S11 反射损耗阈值（越低越好）**：频率点 {freq_th[0]/1e9:.1f}GHz~{freq_th[-1]/1e9:.1f}GHz 范围内，阈值从 {s11_th_table[0]}dB 到 {s11_th_table[-1]}dB 线性变化。
**S21 插入损耗阈值（越高越好）**：频率点 {freq_th[0]/1e9:.1f}GHz~{freq_th[-1]/1e9:.1f}GHz 范围内，阈值从 {s21_th_table[0]}dB 到 {s21_th_table[-1]}dB 线性变化。
**均值良好标准**：S11 均值 < {s11_mean_good}dB 且 S21 均值 > {s21_mean_good}dB 时，判定为“性能良好”；否则仅算“合格”。

### 实际测量与阈值逐点对比

**S11 对比：**
{chr(10).join(s11_display)}

**S21 对比：**
{chr(10).join(s21_display)}

**整体结果**：S11 整体{'合格' if result['s11_qualified'] else '不合格'}，S21 整体{'合格' if result['s21_qualified'] else '不合格'}。
**测量均值**：S11 均值 {result['analysis_detail']['s11_mean']}dB，S21 均值 {result['analysis_detail']['s21_mean']}dB。
    """
    return comparison_text


def generate_pdf_report(result, cable_length, selected_cable, s11_th, s21_th):
    """生成包含曲线和检测结果的 PDF 报告（英文版，避免中文乱码）"""
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 线缆类型英文映射
    cable_type_map = {
        "RG316": "RG316",
        "RG58": "RG58",
        "半刚电缆": "Semi-rigid"
    }
    cable_type_display = cable_type_map.get(selected_cable, selected_cable)

    # 构建英文消息
    s11_mean = result['analysis_detail'].get('s11_mean', 0)
    s21_mean = result['analysis_detail'].get('s21_mean', 0)
    message = f"{cable_type_display} {'PASS' if result['qualified'] else 'FAIL'} (S11 mean {s11_mean:.1f} dB, S21 mean {s21_mean:.1f} dB)"

    # 创建临时文件保存曲线图
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_s11, \
         tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_s21:
        # 绘制 S11 曲线
        fig, ax = plt.subplots(figsize=(8, 4))
        freq_s11 = result['s11_data'][0] if result['s11_data'] else []
        mag_s11 = result['s11_data'][1] if result['s11_data'] else []
        if freq_s11 and mag_s11:
            ax.plot(freq_s11, mag_s11, 'b-', label='S11')
            ax.axhline(y=s11_th, color='r', linestyle='--', label=f'Threshold {s11_th} dB')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('S11 (dB)')
            ax.set_title('S11 Parameter Curve')
            ax.legend()
            ax.grid(True)
            plt.savefig(tmp_s11.name, dpi=150, bbox_inches='tight', pad_inches=0.2)
            plt.close()

        # 绘制 S21 曲线
        fig, ax = plt.subplots(figsize=(8, 4))
        freq_s21 = result['s21_data'][0] if result['s21_data'] else []
        mag_s21 = result['s21_data'][1] if result['s21_data'] else []
        if freq_s21 and mag_s21:
            ax.plot(freq_s21, mag_s21, 'g-', label='S21')
            ax.axhline(y=s21_th, color='r', linestyle='--', label=f'Threshold {s21_th} dB')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('S21 (dB)')
            ax.set_title('S21 Parameter Curve')
            ax.legend()
            ax.grid(True)
            plt.savefig(tmp_s21.name, dpi=150, bbox_inches='tight', pad_inches=0.2)
            plt.close()

    # 生成 PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 30

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(30, y, "Cable Test Report")
    y -= 40

    # Device Information
    c.setFont("Helvetica", 12)
    dev_info = result['device_info']
    c.drawString(30, y, f"Instrument: {dev_info.get('model', 'N/A')}")
    y -= 20
    c.drawString(30, y, f"Test Time: {dev_info.get('test_time', 'N/A')}")
    y -= 20
    c.drawString(30, y, f"Cable Type: {cable_type_display}")
    y -= 20
    c.drawString(30, y, f"Cable Length: {cable_length} m")
    y -= 30

    # Test Result
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "Test Result")
    y -= 25
    c.setFont("Helvetica", 12)
    c.drawString(30, y, f"Overall: {'PASS' if result['qualified'] else 'FAIL'}")
    y -= 20
    c.drawString(30, y, f"Message: {message}")
    y -= 30

    c.drawString(30, y, f"S11: {'PASS' if result['s11_qualified'] else 'FAIL'} (Threshold {s11_th} dB)")
    y -= 20
    c.drawString(30, y, f"S21: {'PASS' if result['s21_qualified'] else 'FAIL'} (Threshold {s21_th} dB)")
    y -= 40

    # Embed curves
    if freq_s11 and mag_s11:
        c.drawString(30, y, "S11 Curve")
        y -= 20
        img_s11 = ImageReader(tmp_s11.name)
        c.drawImage(img_s11, 30, y-150, width=width-60, height=150, preserveAspectRatio=True)
        y -= 170

    if freq_s21 and mag_s21:
        c.drawString(30, y, "S21 Curve")
        y -= 20
        img_s21 = ImageReader(tmp_s21.name)
        c.drawImage(img_s21, 30, y-150, width=width-60, height=150, preserveAspectRatio=True)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ========== 生成 e‑label 图片（二维码 + 文字标签）==========
def generate_elabel(result, cable_length, selected_cable):
    """
    生成一个简单的 e‑label 图片（PNG），包含线缆信息、检测结果、测试时间。
    返回图片的字节流，可直接用于 st.download_button。
    """
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    import io
    import numpy as np

    # 准备要编码到二维码中的信息（简洁版）
    qr_data = (
        f"Cable: {selected_cable}\n"
        f"Length: {cable_length}m\n"
        f"Pass: {'YES' if result['qualified'] else 'NO'}\n"
        f"S11: {result['analysis_detail'].get('s11_mean',0):.1f}dB\n"
        f"S21: {result['analysis_detail'].get('s21_mean',0):.1f}dB\n"
        f"Time: {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    # 生成二维码
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 创建画布（尺寸 500x300，白色背景）
    label_img = Image.new('RGB', (500, 300), 'white')
    draw = ImageDraw.Draw(label_img)

    # 尝试使用系统字体（Windows 下用 simhei.ttf，若没有则用默认）
    try:
        font_title = ImageFont.truetype("simhei.ttf", 20)
        font_text = ImageFont.truetype("simhei.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # 绘制文字区域（左侧）
    text_lines = [
        f"线缆类型: {selected_cable}",
        f"长度: {cable_length} m",
        f"合格状态: {'合格' if result['qualified'] else '不合格'}",
        f"S11均值: {result['analysis_detail'].get('s11_mean',0):.1f} dB",
        f"S21均值: {result['analysis_detail'].get('s21_mean',0):.1f} dB",
        f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    y = 20
    for line in text_lines:
        draw.text((20, y), line, fill='black', font=font_text)
        y += 25

    # 将二维码粘贴到右侧（位置 x=330, y=30）
    qr_img = qr_img.resize((150, 150))
    label_img.paste(qr_img, (330, 30))

    # 保存到字节流
    img_bytes = io.BytesIO()
    label_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()
# ========== 新增结束 ==========
#批量检测界面
if st.session_state.batch_mode:
    st.sidebar.info(f"批量模式: {st.session_state.batch_index}/{st.session_state.batch_total}")
    st.subheader("📦 批量检测模式")

    # 显示当前使用的参数，并提供修改按钮
    col_params, col_edit = st.columns([3, 1])
    with col_params:
        st.info(f"当前检测参数：线缆类型 **{st.session_state.batch_cable}**，长度 **{st.session_state.batch_length}** 米")
    with col_edit:
        if st.button("✏️ 修改参数", key="edit_params_btn"):
            st.session_state.show_param_edit = True  # 触发表单显示

    # 如果用户点击修改，显示一个表单
    if st.session_state.get("show_param_edit", False):
        with st.form(key="param_edit_form"):
            new_cable = st.selectbox("新线缆类型", cable_options,
                                     index=cable_options.index(st.session_state.batch_cable))
            new_length = st.number_input("新长度 (m)", min_value=0.1, max_value=100.0,
                                         value=st.session_state.batch_length, step=0.1)
            col_sub, col_cancel = st.columns(2)
            with col_sub:
                submitted = st.form_submit_button("确认修改")
            with col_cancel:
                canceled = st.form_submit_button("取消")
            if submitted:
                # 更新批量参数，但已测数据保持不变（只影响后续测量）
                st.session_state.batch_cable = new_cable
                st.session_state.batch_length = new_length
                st.session_state.show_param_edit = False
                st.rerun()
            if canceled:
                st.session_state.show_param_edit = False
                st.rerun()
    if st.session_state.batch_index < st.session_state.batch_total:
        st.info(f"请连接第 {st.session_state.batch_index + 1} 根线缆，然后点击下方按钮开始测量")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("📡 开始测量当前线缆", key="batch_measure_btn"):
                with st.spinner(f"正在测量第 {st.session_state.batch_index + 1} 根线缆..."):
                    try:
                        resp = requests.post(
                            API_URL,
                            json={"cable_type": st.session_state.batch_cable,
                                  "length": st.session_state.batch_length
                                  },
                            timeout=30
                        )
                        resp.raise_for_status()
                        result = resp.json()
                        # 保存结果
                        st.session_state.batch_results.append(result)
                        st.session_state.batch_index += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"测量失败: {e}")
                        st.session_state.batch_mode = False
                        st.rerun()
        with col_b2:
            if st.button("❌ 取消批量检测", key="cancel_batch"):
                st.session_state.batch_mode = False
                st.rerun()
    else:
        st.success("🎉 批量检测完成！")
        if st.session_state.batch_results:
            # 构建汇总 DataFrame（用于导出 CSV）
            batch_df = pd.DataFrame([
                {
                    "序号": i + 1,
                    "合格": r.get("qualified", False),
                    "S11合格": r.get("s11_qualified", False),
                    "S21合格": r.get("s21_qualified", False),
                    "消息": r.get("message", "")
                } for i, r in enumerate(st.session_state.batch_results)
            ])

            st.subheader("📊 批量检测结果汇总")
            # 手动展示每一条结果，方便加入按钮
            for idx, r in enumerate(st.session_state.batch_results):
                cols = st.columns([1, 2, 3, 1])
                with cols[0]:
                    st.write(f"**{idx + 1}**")
                with cols[1]:
                    qualified = r.get("qualified", False)
                    st.write("✅ 合格" if qualified else "❌ 不合格")
                with cols[2]:
                    st.write(r.get("message", "")[:50])
                with cols[3]:
                    if st.button("📈 查看曲线", key=f"view_curve_{idx}"):
                        st.session_state.selected_batch_idx = idx
                        st.rerun()
                st.divider()

            # 如果选中了某条记录，显示其曲线
            if st.session_state.selected_batch_idx is not None:
                idx = st.session_state.selected_batch_idx
                r = st.session_state.batch_results[idx]
                st.subheader(f"线缆 #{idx + 1} 的 S 参数曲线")
                # S11 曲线
                freq_s11 = r['s11_data'][0] if r['s11_data'] else []
                mag_s11 = r['s11_data'][1] if r['s11_data'] else []
                if freq_s11 and mag_s11:
                    freq_mhz = [f/1e6 for f in freq_s11]
                    df_s11 = pd.DataFrame({'频率 (MHz)': freq_mhz, 'S11 (dB)': mag_s11})
                    st.line_chart(df_s11.set_index('频率 (MHz)'))
                else:
                    st.write("无 S11 数据")
                # S21 曲线
                freq_s21 = r['s21_data'][0] if r['s21_data'] else []
                mag_s21 = r['s21_data'][1] if r['s21_data'] else []
                if freq_s21 and mag_s21:
                    freq_mhz = [f/1e6 for f in freq_s21]
                    df_s21 = pd.DataFrame({'频率 (MHz)': freq_mhz, 'S21 (dB)': mag_s21})
                    st.line_chart(df_s21.set_index('频率 (MHz)'))
                else:
                    st.write("无 S21 数据")
                # 关闭按钮
                if st.button("❌ 关闭曲线", key="close_curve"):
                    st.session_state.selected_batch_idx = None
                    st.rerun()

            # 导出 CSV 按钮
            csv = batch_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ 导出结果 (CSV)",
                csv,
                "batch_results.csv",
                "text/csv",
                key="batch_export"
            )

    st.stop()  # 批量模式下不显示单次检测内容

#批量检测按钮
st.sidebar.subheader("批量检测")
batch_count = st.sidebar.number_input(
    "线缆数量",
    min_value=1,
    max_value=20,
    value=3,
    step=1,
    key="batch_count_input",
    help="输入本次要测量的线缆数量"
)
if st.sidebar.button("开始批量测量", key="start_batch"):
    st.session_state.batch_mode = True
    st.session_state.batch_index = 0
    st.session_state.batch_results = []
    st.session_state.batch_total = batch_count
    st.session_state.selected_batch_idx = None  # 添加重置
    # 保存当前参数
    st.session_state.batch_cable = selected_cable
    st.session_state.batch_length = cable_length
    st.rerun()

st.sidebar.markdown("---")

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

# ---------- 显示检测结果 ----------
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

    # ---------- PDF 报告生成按钮 ----------
    col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 2])   # 改为三列，容纳两个按钮
    with col_pdf1:
        if st.button("📄 生成 PDF 报告", key="pdf_btn"):
            with st.spinner("正在生成报告，请稍候..."):
                pdf_bytes = generate_pdf_report(
                    result, cable_length, selected_cable, s11_th, s21_th
                )
                st.download_button(
                    label="⬇️ 下载报告",
                    data=pdf_bytes,
                    file_name=f"cable_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="pdf_download"
                )

    # ========== 新增：e‑label 生成按钮 ==========
    with col_pdf3:   # 放在第三列
        if st.button("🏷️ 生成 e‑label", key="elabel_btn"):
            with st.spinner("正在生成 e‑label..."):
                elabel_bytes = generate_elabel(result, cable_length, selected_cable)
                st.download_button(
                    label="⬇️ 下载 e‑label 图片",
                    data=elabel_bytes,
                    file_name=f"elabel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    key="elabel_download"
                )
    # ========== 新增结束 ==========

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
        st.dataframe(history_df, width='stretch', hide_index=True)
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
                # 生成阈值对比文本
                comparison = get_threshold_comparison(selected_cable, cable_length, result)
                init_prompt = f"""
你是一位资深的射频线缆检测专家。请根据以下线缆检测结果和阈值标准，给出专业的分析。
{comparison}

输出内容大致为：
1. 分析结论：线缆是否合格？如果合格，是否达到“性能良好”级别？
2. 问题定位：如果不合格，具体是哪个参数（S11或S21）在哪个频率点超出阈值？超出多少？
3. 原因推测：可能的物理原因（例如接触不良、介质损耗过大、阻抗不匹配等）。
4. 建议：针对当前情况给出可操作的建议（如更换线缆、检查连接器、缩短长度等）。

- 线缆类型：{result.get('cable_type')}
- 整体合格：{'是' if result.get('qualified') else '否'}
- S11 合格：{'是' if result.get('s11_qualified') else '否'}
- S21 合格：{'是' if result.get('s21_qualified') else '否'}
- S11 均值：{result['analysis_detail'].get('s11_mean')} dB
- S21 均值：{result['analysis_detail'].get('s21_mean')} dB
- 线缆长度：{cable_length} 米
- 系统消息：{result.get('message')}

尽量给出一个易懂的分析或结论，语气专业但道理易懂，可以为普通用户讲解，总字数控制在500字内。
                """
                initial_analysis = call_deepseek(init_prompt,system_prompt="你是射频测试专家，熟悉S参数和线缆阈值标准。")
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
                    with st.spinner("AI 正在回答..."):
                        answer = call_deepseek_with_history(
                            messages=st.session_state.conversation,   # 包含历史对话
                            system_prompt="你是射频测试专家，请基于之前的检测数据和对话回答。"
                        )
                        st.session_state.conversation.append({"role": "assistant", "content": answer})
                    st.session_state.remaining_questions -= 1
                    st.rerun()
        else:
            st.info("你已用完 3 次提问机会。如需继续咨询，请重新开始检测。")
else:
    st.info("点击左侧“开始检测”按钮，先获取线缆检测结果。")

st.sidebar.markdown("---")
st.sidebar.caption("项目：USB线缆检测大创")
