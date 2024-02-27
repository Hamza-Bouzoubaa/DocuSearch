from langchain.vectorstores import FAISS
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

from PyPDF2 import PdfReader
from docx import Document

import os



AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPEN_API_KEY =  os.environ["AZURE_OPENAI_API_KEY"]




def ReadFile(FilePath):
    # Get the file extension
    file_extension = FilePath.split('.')[-1].lower()

    if file_extension == 'pdf':
        doc_reader = PdfReader(FilePath)
        raw_text = ''
        for i, page in enumerate(doc_reader.pages):
            text = page.extract_text()
            if text:
                raw_text += text

    elif file_extension == 'docx':
        doc = Document(FilePath)
        raw_text = ''
        for paragraph in doc.paragraphs:
            raw_text += paragraph.text + '\n'

    elif file_extension == 'txt':
        with open(FilePath, 'r', encoding='utf-8') as file:
            raw_text = file.read()

    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

    return raw_text


def SplitText(Text,chunk_size=1500,chunk_overlap = 300):

    rec_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size= chunk_size,
    chunk_overlap = chunk_overlap,
    length_function=len

    )

    chunks = rec_text_splitter.split_text(Text)

    return chunks

def GenerateEmbeddings(FilePath):  #Works with PDF DOCX and TXT

    FileText = ReadFile(FilePath)  #Extracting raw text from file
    
    FileSections = SplitText(FileText)  # splitting the raw text into sections

    embeddings =  AzureOpenAIEmbeddings(model = "text-embedding-ada-002")  # Generating embeddings
    db = FAISS.from_texts(FileSections,embeddings)      #storing embeddings 

    return db

def QuerySimilaritySearch(Query,db,k=3):
    similar = db.similarity_search(Query,k)
    page_content_array = [doc.page_content for doc in similar]
    return page_content_array