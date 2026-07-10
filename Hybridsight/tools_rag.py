from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from  langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.tools import tool
import os

vectorstore=None
embeddings=HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

def index_documents(pdf_paths:list)->str:
    global vectorstore

    all_docs=[]

    for pdf_path in pdf_paths:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        filename = os.path.basename(pdf_path)
        for doc in docs:
            doc.metadata = {
                "source": filename,
                "page": doc.metadata.get("page", 0) + 1
            }
        all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(all_docs)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_store"
    )

    return f"Indexed {len(chunks)} chunks successfully."


@tool
def search_documents(query:str)->str:
    """
    Search the user's uploaded PDF documents for information relevant to the query.

    Use this tool when the user asks about content from an uploaded PDF, such as
    "the document", "my notes", "the PDF", "the file", or asks questions that can
    only be answered from the uploaded documents.

    Do NOT use this tool for general knowledge, current events, web searches, or
    questions about uploaded images.
    """
    if vectorstore is None:
        return "No documents uploaded yet"
    
    if vectorstore._collection.count()==0:
        return "No documents uploaded yet!"
    
    retriever=vectorstore.as_retriever(search_kwargs={"k":5})
    chunks=retriever.invoke(query)

    if not chunks:
        return "No relevant content found in the uploaded documents"

    return "\n\n".join([
        f"[p.{c.metadata.get('page','?')}] {c.page_content}"
        for c in chunks
    ])