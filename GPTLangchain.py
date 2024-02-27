import os

from langchain.schema import HumanMessage
from langchain_openai import AzureChatOpenAI
from langchain import PromptTemplate
from langchain.chains import LLMChain



AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPEN_API_KEY =  os.environ["AZURE_OPENAI_API_KEY"]

model = AzureChatOpenAI(
    openai_api_version="2023-05-15",
    azure_deployment="gpt-35-turbo-16k",
)

Template = """
        You are a world class assistant.
        Make good answers.
        professionalism is your key value
        Help answering the following questions:
        {question}

        this is the context of the discussion, use it if needed.
        {chathistory}
"""


prompt = PromptTemplate(  
    input_variables=["question","chathistory"],  
    template=Template  
)  

chain = LLMChain(llm=model, prompt=prompt)

history = []  
history_limit = 20


def generate_response(message,history):
    response = chain.run(question = message,chathistory = history)
    return response

while True:
    message = input("Enter your message: ")
    response = generate_response(message,history)
    history.append(message)  
    history.append(response)

    while len(history) > history_limit:  
        history.pop(0) 

    #print(f"history : {history}")
    print(response)
    