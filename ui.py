import requests, streamlit as st

API = "http://127.0.0.1:8000"
st.title("📄 Ask your PDFs")

up = st.sidebar.file_uploader("Upload a PDF", type="pdf")
if up and st.sidebar.button("Process"):
    r = requests.post(f"{API}/upload", files={"file": (up.name, up.getvalue())})
    st.sidebar.success(r.json())

q = st.text_input("Your question")
if q:
    with st.spinner("Thinking..."):
        r = requests.post(f"{API}/ask", json={"question": q}).json()
    st.write(r["answer"])
    if "latency" in r:
        st.caption(f"Latency: {r['latency']}")
    for c in r["citations"]:
        with st.expander(f"[{c['id']}] {c['doc']}, page {c['page']}"):
            st.write(c["snippet"])