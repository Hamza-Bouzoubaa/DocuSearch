from azure.cosmos import exceptions, CosmosClient, PartitionKey
from langchain.embeddings import AzureOpenAIEmbeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity  
import streamlit as st  
from io import BytesIO  
import random
import os 
import re  






# Get the API keys from environment variables
cosmosdb_endpoint = os.environ['COSMODB_ENDPOINT']
cosmosdb_key = os.environ['COSMODB_KEY']
cosmosdb_connection_str = os.environ['COSMODB_CONNECTION_STR']


AZURE_OPENAI_KEY = os.environ['AZURE_OPENAI_API_KEY']
embeddings =  AzureOpenAIEmbeddings(openai_api_key = AZURE_OPENAI_KEY)  # Generating embeddings

client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)



  
def clean_text(text):  
    # remove multiple spaces, newline characters, and tabs  
    text = re.sub('\s+', ' ', text)  
    # convert all text to lower case  
    text = text.lower()  
    return text  



def CreateDBandContainer(DatabaseName,ContainerName,Partition_Key,offer_throughput=1000):
    # Create a database in Azure Cosmos DB.
    try:
        database = client.create_database_if_not_exists(id=DatabaseName)
        print(f"Database created: {database.id}")

    except exceptions.CosmosResourceExistsError:
        print("Database already exists.")



    # Create a container in Azure Cosmos DB.  
    try:  
        partition_key_path = PartitionKey(path=Partition_Key)  
        container = database.create_container_if_not_exists(  
            id=ContainerName,  
            partition_key=partition_key_path,  
            offer_throughput= offer_throughput,  
        )  
        print(f"Container created: {container.id}")  
    except exceptions.CosmosResourceExistsError:  
        print("Container already exists.")  

    return container


def InsertDocument(container,UserID, group_id,DocumentID, DocumentText, embedding):  
    random_id = random.randint(1, 1000000)  # Generates a random integer between 1 and 1000000  
  
    item_body = {    
        'id': str(UserID) + str(DocumentID) + str(random_id),  # assuming 'user_id' and 'DocumentID' can form a unique 'id' for each item  
        'UserID': str(UserID),   
        'DocumentID': DocumentID,  
        'partitionKey': str(UserID),    
        'group_id': group_id,    
        'DocumentText': DocumentText,    
        'embedding': embedding  # Convert numpy array to list to save in JSON format    
    }    
    container.upsert_item(body=item_body)    


def fetch_documents_from_user(container,user_id):  
    query = f"SELECT * FROM my_container"  
    query_iterable = container.query_items(  
        query=query,  
        partition_key=user_id  # use user_id as partition key  
    )  
    results = list(query_iterable)  
  
    return results  

def VectorSimilaritySearch(Query,Vectors,Top_n=3):
    #print(Query)


    similarity_scores = cosine_similarity(Query, Vectors)
    print(similarity_scores[0])
    most_similar_indices = np.argsort(similarity_scores)[0][-Top_n:]

    return most_similar_indices


def PagePDFExtracter(pdf_file_path):  
    from PyPDF2 import PdfReader  
  
    reader = PdfReader(BytesIO(pdf_file_path.read()))  
    number_of_pages = len(reader.pages)  
  
    doc = {}  

    progress_bar = st.sidebar.progress(0)  
    progress_text = st.sidebar.empty()
      
    for i in range(number_of_pages):  
        page = reader.pages[i]  
        text = page.extract_text()  
        doc[f'doc{page}'] = {'text': clean_text(text), 'page': i+1}    
        progress_bar.progress((i+1)/number_of_pages)  # update progress bar  
        progress_text.text(f"Reading doc: {((i+1)/number_of_pages)*100:.2f}%") 

    progress_bar.empty()  
    progress_text.empty()


          
    return doc  


def FillContainer(container,AZURE_OPENAI_KEY,PDFDoc,UserID):
        from langchain.embeddings import AzureOpenAIEmbeddings
        from langchain_community.document_loaders import UnstructuredPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        Doc = PagePDFExtracter(PDFDoc)
        
        embeddings =  AzureOpenAIEmbeddings(openai_api_key = AZURE_OPENAI_KEY)  # Generating embeddings
        
        for doc in Doc:
            print(Doc[doc]["text"])
        
        DocumentVector = embeddings.embed_documents([Doc[doc]["text"] for doc in (Doc)])
    
        k=0
        progress_bar = st.sidebar.progress(0)  
        progress_text = st.sidebar.empty() 
        for doc in Doc:
            InsertDocument(container,UserID,PDFDoc.name,PDFDoc.name,Doc[doc]["text"],DocumentVector[k])
            k+=1
            progress_bar.progress((k)/len(Doc))  # update progress bar  
            progress_text.text(f"Vectorizing Data: {((k)/len(Doc))*100:.2f}%") 
            print(str(k)+"inserted") 

        progress_bar.empty()  
        progress_text.empty() 

        return "Data Inserted"

    

def SearchUserContainer(container,UserID,Query,Top_n=3):
    print(Query)
    query_vector = embeddings.embed_documents([Query])
    print(len(query_vector[0]))
    
    results = fetch_documents_from_user(container,UserID)
    Vectors = [result['embedding'] for result in results]
    print(len(Vectors[0]))
    most_similar_indices = VectorSimilaritySearch(query_vector,Vectors,Top_n)
    print(most_similar_indices)
    TextRes  = [result['DocumentText'] for result in results]
    return [TextRes[i] for i in most_similar_indices]

