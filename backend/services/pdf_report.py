"""PDF 检测报告生成（迁移自 app.py:generate_pdf_report，英文版避免中文字体问题）。

新签名：generate_pdf_report(result: dict) -> bytes。结果需含 s11_data/s21_data/dtf_data/
thresholds/device_info/analysis_detail 等字段。
"""
import io

import matplotlib

matplotlib.use("Agg")  # 无界面后端，服务器环境必需
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

_CABLE_EN = {
    "RG316": "RG316",
    "RG58": "RG58",
    "半刚电缆": "Semi-rigid",
    "RG174": "RG174",
    "LMR-200": "LMR-200",
    "RG6": "RG6",
}


def _plot_series(freqs, mags, thr_freqs, thr_mags, title, ylabel, color) -> io.BytesIO:
    """绘制一条曲线 + 随频率变化的阈值虚线，返回 PNG 字节流。"""
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(np.array(freqs) / 1e9, mags, color=color, linewidth=1.5, label=title.split()[0])
    if thr_freqs and thr_mags and freqs:
        thr_interp = np.interp(freqs, thr_freqs, thr_mags)
        ax.plot(np.array(freqs) / 1e9, thr_interp, "r--", linewidth=1.2, label="Threshold")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    return buf


def _plot_dtf(dist, amp) -> io.BytesIO:
    """绘制 DTF 距离-反射曲线，返回 PNG 字节流。"""
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(dist, amp, color="#8c564b", linewidth=1.5)
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Reflection (dB)")
    ax.set_title("DTF - Fault Location")
    ax.grid(True, alpha=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pdf_report(result: dict) -> bytes:
    """根据检测结果生成英文 PDF 报告，返回字节流。"""
    cable_display = _CABLE_EN.get(result["cable_type"], result["cable_type"])
    detail = result["analysis_detail"]
    s11_mean = detail.get("s11_mean", 0)
    s21_mean = detail.get("s21_mean", 0)
    message = (
        f"{cable_display} {'PASS' if result['qualified'] else 'FAIL'} "
        f"(S11 mean {s11_mean:.1f} dB, S21 mean {s21_mean:.1f} dB)"
    )

    freq, s11 = result["s11_data"]
    _, s21 = result["s21_data"]
    th = result.get("thresholds") or {}
    thr_freqs = th.get("freqs") or []
    thr_s11 = th.get("S11") or []
    thr_s21 = th.get("S21") or []

    png_s11 = _plot_series(freq, s11, thr_freqs, thr_s11, "S11 Parameter", "S11 (dB)", "#5470c6")
    png_s21 = _plot_series(freq, s21, thr_freqs, thr_s21, "S21 Parameter", "S21 (dB)", "#91cc75")

    buf_pdf = io.BytesIO()
    c = canvas.Canvas(buf_pdf, pagesize=A4)
    width, height = A4
    y = height - 30

    c.setFont("Helvetica-Bold", 20)
    c.drawString(30, y, "Cable Test Report")
    y -= 36

    c.setFont("Helvetica", 11)
    dev = result.get("device_info") or {}
    for text in (
        f"Instrument: {dev.get('model', 'N/A')}",
        f"Test Time: {dev.get('test_time', 'N/A')}",
        f"Cable Type: {cable_display}",
        f"Cable Length: {result['length']} m",
    ):
        c.drawString(30, y, text)
        y -= 16
    y -= 10

    c.setFont("Helvetica-Bold", 13)
    c.drawString(30, y, "Test Result")
    y -= 20
    c.setFont("Helvetica", 11)
    for text in (
        f"Overall: {'PASS' if result['qualified'] else 'FAIL'}",
        f"Message: {message}",
        f"S11: {'PASS' if result['s11_qualified'] else 'FAIL'}  (mean {s11_mean:.1f} dB)",
        f"S21: {'PASS' if result['s21_qualified'] else 'FAIL'}  (mean {s21_mean:.1f} dB)",
    ):
        c.drawString(30, y, text)
        y -= 16
    y -= 14

    for title, png in (("S11 Curve", png_s11), ("S21 Curve", png_s21)):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, title)
        y -= 18
        c.drawImage(ImageReader(png), 30, y - 110, width=width - 60, height=110, preserveAspectRatio=True)
        y -= 130

    # DTF 曲线（数据存在且空间不足时换页）
    dtf_dist, dtf_amp = result.get("dtf_data") or ([], [])
    if len(dtf_dist) > 1:
        if y < 160:
            c.showPage()
            y = height - 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "DTF - Fault Location")
        y -= 18
        c.drawImage(ImageReader(_plot_dtf(dtf_dist, dtf_amp)), 30, y - 110,
                    width=width - 60, height=110, preserveAspectRatio=True)

    c.save()
    buf_pdf.seek(0)
    return buf_pdf.getvalue()
