import PyPDF2  
import os
import streamlit as st  
from langchain_community.document_loaders import UnstructuredPDFLoader      
import shutil  
from pinecone import Pinecone
from langchain.embeddings import AzureOpenAIEmbeddings
from time import sleep
from pinecone import Pinecone, PodSpec
from tqdm import tqdm 
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv('.env')

# Get the API keys from environment variables
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

 
  
def PagePDFExtracter(pdf_file_path):  
    from PyPDF2 import PdfReader  
  
    reader = PdfReader(pdf_file_path)  
    number_of_pages = len(reader.pages)  
  
    doc = {}  

    progress_bar = st.sidebar.progress(0)  
    progress_text = st.sidebar.empty()
      
    for i in range(number_of_pages):  
        page = reader.pages[i]  
        text = page.extract_text()  
        doc[f'doc{page}'] = {'text': text, 'page': i+1}    
        progress_bar.progress((i+1)/number_of_pages)  # update progress bar  
        progress_text.text(f"Reading doc: {((i+1)/number_of_pages)*100:.2f}%") 

    progress_bar.empty()  
    progress_text.empty()
          
    return doc  



def PagePDExtracter(pdf_file_path):  
    # Initialize PDF file reader object  
    pdf = PyPDF2.PdfFileReader(pdf_file_path)  
  
    # Get the base file name (without extension)  
    base_file_name = os.path.splitext(os.path.basename(pdf_file_path))[0]  
  
    # Create a directory with the base file name  
    os.makedirs(base_file_name, exist_ok=True)  
  
    # Initialize the dictionary to hold the results  
    doc = {}  
  
    # Split the PDF into individual pages and extract text  
    for page in range(pdf.getNumPages()):  
        # Create a writer object and add the page to it  
        pdf_writer = PyPDF2.PdfFileWriter()  
        pdf_writer.addPage(pdf.getPage(page))  
  
        # Create the output file path for the page  
        output_filename = os.path.join(base_file_name, f'{base_file_name}_page{page+1}.pdf')  
  
        # Write the page to a new PDF file  
        with open(output_filename, 'wb') as out:  
            pdf_writer.write(out)  
  
        try:  
            # Load the page content using UnstructuredPDFLoader  
            loader = UnstructuredPDFLoader(output_filename)  
            data = loader.load()  
            data[0].page_content = data[0].page_content.replace("\n", " ")  
  
            # Add the page content and page number to the dictionary  
            doc[f'doc{page}'] = {'text': data[0].page_content, 'page': page+1}  
        except:  
            print(f"Couldn't extract from this page: {output_filename}")  
  
    # Delete the directory with all the individual page PDF files  
    shutil.rmtree(base_file_name)  
  
    return doc  




def extract_page(pdf_file_path, page_number):  
    # Initialize PDF file reader object  
    pdf = PyPDF2.PdfFileReader(pdf_file_path)  
  
    # Create a writer object and add the page to it  
    pdf_writer = PyPDF2.PdfFileWriter()  
    pdf_writer.addPage(pdf.getPage(page_number - 1))  
  
    # Get the base file name (without extension)  
    base_file_name = os.path.splitext(os.path.basename(pdf_file_path))[0]  
  
    # Create the output file path for the page  
    output_filename = f'{base_file_name}_page{page_number}.pdf'  
  
    # Write the page to a new PDF file  
    with open(output_filename, 'wb') as out:  
        pdf_writer.write(out)  
  
    return output_filename  



def SearchInPineconeIndex(APIKey,OpenAIKey,IndexName,Query,User,k=3):


            
            
    embeddings =  AzureOpenAIEmbeddings(openai_api_key = OpenAIKey)  # Generating embeddings


    pc = Pinecone(api_key = APIKey )
    index = pc.Index(IndexName )

    Vector = embeddings.embed_documents([Query])

    #Result = index.query(
    #vector=Vector[0],
    #top_k=k,
    #include_values=True,
    #include_metadata=True,
    #filter={"user": {"$eq": "Test2"}}
    #)
    #print(Result)
    Result = index.query( namespace=User,vector=Vector[0],top_k=k, include_values=True,include_metadata=True)
    
    TextRes  = [Text['metadata']['text'] + f" [Found in page {Text['metadata']['page']}] " for Text in Result['matches']]
    #print(TextRes)
    return TextRes

def FillPod(PineconeAPIKey,OpenAIKey,IndexName,PDFDoc,User):
        from langchain.embeddings import AzureOpenAIEmbeddings
        from langchain_community.document_loaders import UnstructuredPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        pc = Pinecone(api_key=PineconeAPIKey)

        
        Doc = PagePDFExtracter(PDFDoc)
        
        embeddings =  AzureOpenAIEmbeddings(openai_api_key = OpenAIKey)  # Generating embeddings
        
        index = pc.Index(IndexName)    
        
        DocumentVector = embeddings.embed_documents([Doc[doc]["text"] for doc in (Doc)])
    
        k=0
        progress_bar = st.sidebar.progress(0)  
        progress_text = st.sidebar.empty() 
        for doc in Doc:
            index.upsert(vectors=[{"id": str(k)+str(PDFDoc),"values": DocumentVector[k],"metadata":{"text":(Doc[doc]["text"]),"page":int(Doc[doc]["page"]), "user":User,"document":PDFDoc}}],namespace= User)
            k+=1
            progress_bar.progress((k)/len(Doc))  # update progress bar  
            progress_text.text(f"Vectorizing Data: {((k)/len(Doc))*100:.2f}%")  

        progress_bar.empty()  
        progress_text.empty() 

        #for i in range(len(DocumentVector)):
        #    index.upsert(vectors=[{"id": str(i),"values": DocumentVector[i],"metadata":{"text":(Doc[i].page_content),"page":(Doc[i].page)}}])




def CreatePod(PineconeAPIKey,IndexName,Metric="cosine"):
    
    def CreatePod():
    
        
        pc.create_index(
        	name=IndexName,
        	dimension=1536,
        	metric=Metric,
        	spec=PodSpec(
        		environment='eastus-azure',
        		pod_type='p1.x1',
        		pods=1,
        		metadata_config={ 
        			'indexed': ['propertyName']
        		}
        	)
        )
    


   

    pc = Pinecone(api_key=PineconeAPIKey)
    Indexes = pc.list_indexes()
    IndexNames = [index["name"] for index in Indexes]

    if IndexName not in IndexNames:
        CreatePod()
    else:
        print("Pod already exists")
        return False


    print("Pod created successfully")   
    
    #sleep(10)
    #FillPod()


#CreateAndFillPod(PINECONE_API_KEY, OPENAI_KEY,"docusearch","PDFs/project topics.pdf","admin")  # Replace the empty strings with your Pinecone API Key, OpenAI API Key, Index Name and PDF Document Path
#FillPod(PINECONE_API_KEY,OPENAI_KEY,"docsearch","PDFs/project topics.pdf","admin")
#matches = SearchInPineconeIndex(PINECONE_API_KEY, OPENAI_KEY,"docsearch","admission","default")  # Replace the empty strings with your Pinecone API Key, OpenAI API Key, Index Name and Query
#print(matches)

#for i in range(len(matches)):
   # print(matches[i])  # Replace the empty string with your Pinecone API Key
