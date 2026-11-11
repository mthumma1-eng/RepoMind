import streamlit as st
from core.github_loader import clone_repository, validate_github_url
from core.indexer import build_index
from core.analysis import scan_bugs, build_architecture, make_overview
from core.rag import answer_question
from core.config import APP_NAME

st.set_page_config(page_title=APP_NAME, page_icon="🧠", layout="wide")
st.title("🧠 Codebase Intelligence")
st.caption("Understand a GitHub repository. Ask questions. Explore architecture. Find potential bugs.")

if "repo" not in st.session_state:
    st.session_state.repo = None
if "index" not in st.session_state:
    st.session_state.index = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None

with st.sidebar:
    st.header("Connect repository")
    github_url = st.text_input("Public GitHub URL", placeholder="https://github.com/owner/repository")
    analyze = st.button("Analyze repository", type="primary", use_container_width=True)
    st.divider()
    st.caption("The first analysis may take a few minutes while the repository is cloned and indexed.")
    st.caption("For AI-generated answers, add GROQ_API_KEY to your .env file.")

if analyze:
    try:
        owner, name = validate_github_url(github_url)
        with st.spinner("Cloning repository..."):
            repo_info = clone_repository(github_url)
        with st.spinner("Parsing files and building the searchable knowledge base..."):
            index_info = build_index(repo_info["path"])
        with st.spinner("Analyzing project structure..."):
            analysis = {
                "bugs": scan_bugs(repo_info["path"]),
                "architecture": build_architecture(repo_info["path"]),
                "overview": make_overview(repo_info["path"], index_info),
            }
        st.session_state.repo = repo_info
        st.session_state.index = index_info
        st.session_state.analysis = analysis
        st.success("Repository analysis completed.")
    except Exception as exc:
        st.error(f"Could not analyze repository: {exc}")

if not st.session_state.repo:
    st.info("Paste a public GitHub repository URL in the sidebar to get started.")
    c1, c2, c3 = st.columns(3)
    c1.markdown("**💬 Ask questions**\n\nAsk how functions, APIs, and modules work.")
    c2.markdown("**🐛 Find potential bugs**\n\nReview suspicious patterns and security issues.")
    c3.markdown("**🧩 Explore architecture**\n\nSee imports, modules, and project structure.")
    st.stop()

repo = st.session_state.repo
index_info = st.session_state.index
analysis = st.session_state.analysis

st.subheader(f"📁 {repo['owner']} / {repo['name']}")
st.caption(repo["path"])
m1, m2, m3, m4 = st.columns(4)
m1.metric("Indexed chunks", index_info["chunk_count"])
m2.metric("Files indexed", index_info["file_count"])
m3.metric("Languages", len(index_info["languages"]))
m4.metric("Potential findings", len(analysis["bugs"]))

chat_tab, bug_tab, architecture_tab, overview_tab = st.tabs(
    ["💬 Chat with codebase", "🐛 Bug finder", "🧩 Architecture", "📄 Project overview"]
)

with chat_tab:
    st.subheader("Ask your codebase")
    st.write("Ask questions about the repository. Answers include retrieved file references.")
    question = st.text_area("Your question", placeholder="How does user authentication work?", height=90)
    if st.button("Ask AI", type="primary", key="ask"):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Searching code and preparing an answer..."):
                result = answer_question(question, index_info)
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("Retrieved source code"):
                    for source in result["sources"]:
                        st.markdown(f"**{source['path']}** · lines {source['start_line']}-{source['end_line']}")
                        st.code(source["content"], language=source.get("language", "text"))

with bug_tab:
    st.subheader("Potential bug and security review")
    st.caption("This first version uses lightweight static checks. Findings are suggestions to verify, not proof of exploitable bugs.")
    if st.button("Run scan", key="rescan"):
        with st.spinner("Scanning supported source files..."):
            analysis["bugs"] = scan_bugs(repo["path"])
        st.session_state.analysis = analysis
    bugs = analysis["bugs"]
    if not bugs:
        st.success("No issues were detected by the current checks.")
    else:
        for item in bugs:
            with st.expander(f"{item['severity']} · {item['title']} · {item['path']}:{item['line']}"):
                st.write(item["description"])
                st.caption(f"Suggested review: {item['recommendation']}")
                if item.get("snippet"):
                    st.code(item["snippet"], language=item.get("language", "text"))

with architecture_tab:
    st.subheader("Repository architecture")
    arch = analysis["architecture"]
    st.write(arch["summary"])
    if arch["dot"]:
        st.graphviz_chart(arch["dot"], use_container_width=True)
    st.markdown("**Detected Python modules and imports**")
    if arch["edges"]:
        st.dataframe(arch["edges"], use_container_width=True, hide_index=True)
    else:
        st.info("No Python import relationships were detected. The first version's graph focuses on Python imports.")

with overview_tab:
    st.subheader("Repository onboarding report")
    st.markdown(analysis["overview"]["report"])
    st.download_button(
        "Download onboarding report",
        data=analysis["overview"]["report"],
        file_name="repository_onboarding_report.md",
        mime="text/markdown",
    )
    st.subheader("File inventory")
    st.dataframe(analysis["overview"]["files"], use_container_width=True, hide_index=True)
