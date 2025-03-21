import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI , GoogleGenerativeAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from PyPDF2 import PdfReader

from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

def get_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def chunker(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 10000,chunk_overlap = 1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model ="models/embedding-001")
    vector_Store = FAISS.from_texts(text_chunks,embedding=embeddings)
    vector_Store.save_local("Faiis_Index")


def conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model = "gemini-1.5-flash",embeddings = 0.7)
    prompt = PromptTemplate(template=prompt_template,input_variables=["context","question"])
    chain = load_qa_chain(model,chain_type = "stuff",prompt = prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    new_db = FAISS.load_local("Faiis_Index",embeddings=embeddings,allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    chain = conversational_chain()
    response = chain(
        {"input_documents":docs, "question": user_question}
        , return_only_outputs=True)
    print(response)
    st.write("Response",response["output_text"])


def main():
    st.set_page_config("RAG")
    user_question = st.text_input("Ask Question from The PDF")
    if user_question:
        user_input(user_question)
    
    with st.sidebar:
        user_docs = st.file_uploader("Upload your document",accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing"):
                raw_text = get_text(user_docs)
                text_chunks = chunker(raw_text)
                get_vector_store(text_chunks)
                st.success("File Is Stored in Vector Database")
if __name__ =="__main__":
    main()




        
