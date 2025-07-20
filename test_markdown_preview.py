import streamlit as st

# 创建两列布局
col1, col2 = st.columns(2)

# 左边框：Markdown 输入
with col1:
    st.header("Markdown 输入")
    markdown_input = st.text_area("输入你的 Markdown 文本：", "")

# 右边框：Markdown 预览
with col2:
    st.header("Markdown 预览")
    st.markdown(markdown_input) 