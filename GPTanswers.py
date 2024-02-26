import os
from langchain.schema import HumanMessage
from langchain_openai import AzureChatOpenAI
from langchain import PromptTemplate
from langchain.chains import LLMChain

from PineconeRAG import SearchInPineconeIndex


from EnbeddingsCreator import GenerateEmbeddings, QuerySimilaritySearch

from dotenv import load_dotenv


# Load API keys from .env file
load_dotenv('.env')

# Get the API keys from environment variables
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')


model = AzureChatOpenAI(
    openai_api_version="2023-05-15",
    azure_deployment="HamzaGPT4",
)

Template = """  
    You are a world-class AI assistant. Your role is to provide precise and concise answers to queries using the sources provided. Your answers should be based on the information available in the sources, and you should avoid making unsupported assumptions. You should strive to present your answers in an easy-to-understand format, using bullet points when appropriate. When a direct answer is not available in the sources, you may infer the best possible response using the methodology or logic evident in the sources. Always remember to cite the page number where you found the information in APA format.   
    
    Question: {question}    
    
    Please use the following sources to answer the question:    
    {DataInfo}    
    
    Here is the context of the discussion, use it if needed:    
    {chathistory}  
    
    Based on these sources, how would you formulate a detailed, clear, and concise response to the query? If the exact information isn't found in the sources, how would you extrapolate or infer the best possible answer using the methodology or logic inherent in the sources?  
    
    Please provide the response in a user-friendly format that may include bullet points for clarity. At the end of your response, please cite the sources used, including the page numbers, in APA format.  
    """  



prompt = PromptTemplate(  
    input_variables=["question","chathistory","DataInfo"],  
    template=Template  
)  

chain = LLMChain(llm=model, prompt=prompt)

history = []  
history_limit = 20


def generate_response(message,history,DataInfo):
    response = chain.run(question = message,chathistory = history,DataInfo=DataInfo)
    return response

#documentEmbeddings
def AskRAGQuestion():

    while True:
        message = input("Enter your message: ")
        res = SearchInPineconeIndex(PINECONE_API_KEY,OPENAI_KEY,"uottawaprospectus",message)
        
        
        #Data = QuerySimilaritySearch(message,documentEmbeddings)
        response = generate_response(message,history,res)
        history.append(message)  
        history.append(response)
    
        while len(history) > history_limit:  
            history.pop(0) 
    
        #print(f"history : {history}")
        print(response)
    
    
    

