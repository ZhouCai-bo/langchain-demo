import streamlit as st
import numpy as np
import pandas as pd

#title
st.markdown("# Roles Dashbaord")

st.code('''
def main(a, b):
    return a * b
''', language="python")


msg = ""
if "name" in st.session_state:
    msg = {"name": st.session_state.name, "passwd": st.session_state.passwd}

print(111, st.session_state)
st.write(f"输入的内容是：{msg}")

#defining side bar
st.sidebar.header("Filters:")

name = st.sidebar.text_input(label='用户名：')
passwd = st.sidebar.text_input(label='密码：')
submit = st.button("确定")

if submit:
    print(name, passwd)
    st.session_state["name"] = name
    st.session_state["passwd"] = passwd
    print(222, st.session_state)

#placing filters in the sidebar using unique values.
location = st.sidebar.multiselect(
    "Select Location:",
    options=['abc', 'bcd'],
    default=['abc']
)

df = pd.DataFrame(
    np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
    columns=['lat', 'lon'])

st.map(df)