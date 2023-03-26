import json
import os

import httpx
import streamlit as st
from annotated_text import annotated_text

st.title("Oracle of Ammon")
base_url: str = f'{os.environ.get("API_URL", "http://127.0.0.1")}:{os.environ.get("API_PORT", "8000")}'


search_tab, upload_tab = st.tabs(["Search", "Upload"])

with search_tab:
    with st.form(key="search"):
        col1, col2 = st.columns(2)
        query_type: str = col1.selectbox(
            label="Query Type",
            options=[
                "FAQ",
                "Extractive",
                "Document Search",
                "Search Summarization",
                "Search Span Summarization",
            ],
        )
        index: str = col2.text_input(label="Index", value="document")
        query: str = st.text_input(label="Query")

        with st.expander(label="Advanced"):
            init_params: dict = {"Retriever": {"top_k": 3, "index": index}}
            params = st.text_area(
                label="Engine Parameters",
                value=json.dumps(init_params, indent=4),
                height=200,
            )

        submitted: bool = st.form_submit_button(label="Search")

        if submitted:
            query_map: dict = {
                "FAQ": "/faq-search",
                "Extractive": "/extractive-search",
                "Document Search": "/document-search",
                "Search Summarization": "/search-summarization",
                "Search Span Summarization": "/search-span-summarization",
            }
            payload: dict = {"query": query, "params": json.loads(params)}
            try:
                r: httpx.Response = httpx.request(
                    method="POST",
                    url=base_url + query_map[query_type],
                    json=payload,
                    timeout=300,
                )
            except Exception:
                st.error("Unable to process request. Make sure API is available.")
                st.stop()

            if r.status_code >= 200 and r.status_code < 300 and hasattr(r, "json"):
                r_json: dict = r.json()

                if "answers" in r_json:
                    if len(r_json.get("answers")) < 1:
                        st.write("No answers returned.")
                        st.stop()
                    elif "Extractive" in query_type:
                        context = r_json["answers"][0]["context"]
                        offsets = r_json["answers"][0]["offsets_in_context"][0]

                        st.write(f'Answer: {r_json["answers"][0]["answer"]}')

                        annotated_text(
                            (context[0 : offsets["start"]]),
                            (
                                context[offsets["start"] : offsets["end"]],
                                "answer",
                                "rgba(140,20,200,0.4)",
                            ),
                            (context[offsets["end"] :]),
                        )
                    elif "FAQ" in query_type:
                        st.write(f'Answer: {r_json["answers"][0]["answer"]}')
                elif "documents" in r_json:
                    if len(r_json.get("documents")) < 1:
                        st.write("No documents returned.")
                        st.stop()
                    elif (
                        "Document Search" in query_type
                    ):  # returns list of entire documents
                        st.write(
                            [
                                {
                                    "content": dict(x).get("content"),
                                    "id": dict(x).get("id"),
                                }
                                for x in r_json.get("documents")
                            ]
                        )
                    elif (
                        "Search Summarization" in query_type
                        or "Search Span Summarization" in query_type
                    ):  # returns list of entire documents + summary
                        st.write(
                            [
                                {
                                    "summary": dict(x).get("meta").get("summary"),
                                    "content": dict(x).get("content"),
                                    "id": dict(x).get("id"),
                                }
                                for x in r_json.get("documents")
                            ]
                        )
            else:
                st.warning(
                    f"Unable to retrieve response from API. Status Code: {r.status_code}"
                )


with upload_tab:
    with st.form(key="upload-documents"):
        index: str = st.text_input(
            label="Index", value=os.environ.get("INDEX", "document")
        )
        sheet_name: str = st.text_input(
            label="Sheet Name",
            help="If xlsx is used, define which sheet(s) to index. If none selected, all sheets will be indexed.",
            placeholder="Only use with XLSX",
        )
        is_faq: bool = st.checkbox(label="FAQ")
        files = st.file_uploader(
            label="Upload Documents",
            accept_multiple_files=True,
            type=["xlsx", "pdf", "csv", "tsv", "json", "txt"],
        )

        json_payload: dict = {"index": index, "is_faq": is_faq}
        file_payload: dict = [("files", file) for file in files]

        submitted: bool = st.form_submit_button(label="Upload")

        if submitted:
            if not files:
                st.warning("No files selected.")
            else:
                try:
                    r: httpx.Response = httpx.request(
                        method="POST",
                        url=base_url + "/upload-documents",
                        files=file_payload,
                        json=json_payload,
                    )
                except Exception:
                    st.error("Unable to process request. Make sure API is available.")
                    st.stop()

                if r.status_code >= 200 and r.status_code < 300 and hasattr(r, "json"):
                    r_json: dict = r.json()
                    st.info(r_json.get("message"))

                else:
                    st.warning(
                        f"Unable to retrieve response from API. Status Code: {r.status_code}"
                    )
