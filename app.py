# app.py
# Streamlit 前端页面

import streamlit as st
import pandas as pd
from mainfunction import run

# 页面配置
st.set_page_config(page_title="USB线缆检测系统", layout="wide")
st.title("🔌 USB 线缆 S 参数检测")
st.sidebar.header("操作面板")

# 按钮触发检测
if st.sidebar.button("开始检测"):
    with st.spinner("正在读取数据并分析..."):
        try:
            result = run()  # 调用主流程函数
        except Exception as e:
            st.error(f"检测失败：{e}")
            st.stop()

        # 显示设备信息
        st.subheader("📋 设备信息")
        dev_info = result['device_info']
        col1, col2, col3 = st.columns(3)
        col1.metric("仪器型号", dev_info.get('model', 'N/A'))
        col2.metric("线缆类型", dev_info.get('cable_type', 'N/A'))
        col3.metric("测试时间", dev_info.get('test_time', 'N/A'))
        # 显示合格状态
        st.subheader("✅ 检测结果")
        if result['qualified']:
            st.success(f"线缆合格：{result['message']}")
        else:
            st.error(f"线缆不合格：{result['message']}")

        # 详细参数分析
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**S11 参数**")
            if result['s11_qualified']:
                st.info("S11 合格 (所有点 < -20 dB)")
            else:
                st.warning("S11 不合格 (存在 ≥ -20 dB 的点)")

            # 绘制 S11 曲线
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
                st.info("S21 合格 (所有点 > -3 dB)")
            else:
                st.warning("S21 不合格 (存在 ≤ -3 dB 的点)")

            freq_s21 = result['s21_data'][0] if result['s21_data'] else []
            mag_s21 = result['s21_data'][1] if result['s21_data'] else []
            if freq_s21 and mag_s21:
                df_s21 = pd.DataFrame({'测试点': freq_s21, 'S21 (dB)': mag_s21})
                st.line_chart(df_s21.set_index('测试点'))
            else:
                st.write("无 S21 数据")

        # 显示原始数据（可折叠）
        with st.expander("查看原始数据"):
            st.json(result)

else:
    st.info("点击左侧“开始检测”按钮，读取仪器数据并分析。")

# 底部信息
st.sidebar.markdown("---")
st.sidebar.caption("项目：USB线缆检测大创")