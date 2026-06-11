from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from  langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os 
import gradio as gr
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client= Groq(api_key=os.getenv("GROQ_API_KEY"))
vectorstore=None
embeddings=HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

def index_documents(pdf_paths:list)->int:
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

def ask(question:str)->tuple[str,str]:
    global vectorstore

    if vectorstore is None:
        return "Please index some documents first"
    
    retriever=vectorstore.as_retriever(search_kwargs={"k":5})

    docs=retriever.invoke(question)
    
    context="\n\n".join(
        doc.page_content 
        for doc in docs)
    
    prompt=f""" You are a helpful document assistant.
    you are eager to help ans the query of the user with that fun but intuitive vibe.
    Answer ONLY using the provided context. 
    If the answer is not present in the context say "Sorry, I don't know the answer to that question based on the provided documents."
    dont use your training data to answer the question, only use the provided context.

    Context: {context}
    Question: {question}
    """

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]

    )
    
    ans=response.choices[0].message.content

    citation=[]

    for doc in docs:
        source=doc.metadata.get("source","unknown")
        page=doc.metadata.get("page","?")
        citation.append(f"{source}|page {page}")
    
    citation_text="\n".join(
        sorted(set(citation))
    )

    final_ans=(
        f"{ans}\n\n"
        f"sources:\n{citation_text}"
    )

    retrieved_context=""

    for i,doc in enumerate(docs,1):
        retrieved_context+=(
            f"Chunk {i}:\n"
            f"Source: {doc.metadata.get('source','unknown')} \n"
            f"Page: {doc.metadata.get('page','?')}\n\n"
            f"{doc.page_content}\n\n"

        )
    return final_ans,retrieved_context

with gr.Blocks(title="DocBuddy Pro") as demo:

    gr.Markdown("# DocBuddy Pro")
    gr.Markdown("Your personal document assistant. Upload your PDFs and ask questions about them!")

    pdf_input=gr.File(
        file_count="multiple",
        file_types=[".pdf"],
        label="Upload PDFs",
        type="filepath"
    )

    index_btn=gr.Button("Index Documents")

    status= gr.Textbox(
        label="Status"
    )

    index_btn.click(
        fn=index_documents,
        inputs=pdf_input,
        outputs=status
    )

    question = gr.Textbox(
        label="Ask a Question"
    )

    ask_btn = gr.Button("Ask")
    
    answer = gr.Textbox(
        label="Answer",
        lines=8
    )

    with gr.Accordion("Retrieved Context", open=False):
        context = gr.Textbox(
            lines=20,
            label="Context"
        )

    ask_btn.click(
        fn=ask,
        inputs=question,
        outputs=[answer, context]
    )

    demo.launch()