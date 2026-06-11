DocBuddy Pro – Q&A Over Multiple PDFs with Source Citations

Project Overview

DocBuddy Pro is a Retrieval-Augmented Generation (RAG) application that allows users to upload multiple PDF documents and ask questions about their contents. The application retrieves relevant information from the uploaded documents and uses a Large Language Model to generate grounded answers along with source citations.

What is RAG?

Retrieval-Augmented Generation (RAG) combines document retrieval with large language models to produce accurate and grounded responses. Instead of relying only on the model’s built-in knowledge, it first retrieves relevant information from external documents and then generates answers using that context. This reduces hallucinations and improves transparency through citations.

Features

* Upload and index multiple PDF documents
* Semantic search using vector embeddings
* ChromaDB persistent vector database
* HuggingFace sentence-transformer embeddings
* Question answering using Groq LLM
* Source citations with page numbers
* Retrieved context viewer
* Hallucination prevention using grounded prompting
* Gradio-based user interface

Installation

1. Clone the repository.
2. Navigate to the project directory.

pip install -r requirements.txt

3. Create a .env file and add:

GROQ_API_KEY=your_groq_api_key

4. Run the application:

python app.py

Screenshots

* Successful document indexing
* A correct answer with visible citations
![correct ans](<answer_with_citations.png>)

* Hallucination prevention (“I don’t have that information in the provided documents.”)
![Haluucination prevention](<hallucination_test.png>)


What Worked Well

The retrieval pipeline using ChromaDB and HuggingFace embeddings worked effectively and produced grounded answers with citations. Gradio provided a simple interface, and Groq generated responses quickly.

What I Would Improve

If given more time, I would implement streaming responses, conversation memory for follow-up questions, document-level filtering, and chunk analytics to further enhance the user experience.

Learning Reflection

Through this project, I learned how Retrieval-Augmented Generation systems work end-to-end, including PDF processing, chunking strategies, vector databases, embeddings, retrieval, prompt grounding, and integrating large language models into an interactive application.