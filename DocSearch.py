import streamlit as st  
from GPTanswers import generate_response  
from PineconeRAG import PagePDFExtracter,CreatePod,FillPod,SearchInPineconeIndex  
from AzureSQL import ConnectToAzureSQL,AuthenticateUser,AddaUser
from AzureBlobStorage import save_file_in_blob_azure
import os   
  
# Get the API keys from environment variables  
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')  
OPENAI_KEY = os.getenv('OPENAI_API_KEY')  
MicrosoftEntraPass = os.getenv('MICROSOFT_ENTRA_PASSWORD')
AZURE_BLOB_KEY = os.getenv('AZURE_BLOB_KEY')
AZURE_BLOB_URL = "https://docusearchstorage.blob.core.windows.net/docusearchfolder"



  
def save_uploaded_file(directory: str, file):    
    """Save uploaded file to the specified directory and return the path."""    
    if not os.path.exists(directory):    
        os.makedirs(directory)    
    
    filepath = os.path.join(directory, file.name)    
    with open(filepath, 'wb') as f:    
        f.write(file.getbuffer())    
    
    return filepath  
  

  

  

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
# Variable to hold login status  

def main():   
    
     
    print(st.session_state["user"])
    cursor,conn = ConnectToAzureSQL(MicrosoftEntraPass)    
  
    st.title('Welcome to Docu Search')        
        
    if st.session_state["logged_in"] == False:
        st.sidebar.title("User Authentication")      

        menu = ["Login","SignUp"]  
        choice = st.sidebar.selectbox("Menu",menu)      
 
    else:
        #menu = ["Home"]   
        choice = "Home"   

    if choice == "Home":      
        if st.session_state["logged_in"] == True:    
            pass    
        else:    
            st.sidebar.warning("Please log in to access the home page.")      
    
    elif choice == "Login":      
        st.sidebar.subheader("Login Section")      
    
        username = st.sidebar.text_input("User Name")      
        password = st.sidebar.text_input("Password",type='password')      
        if st.sidebar.button("Login"):      
            result = AuthenticateUser(username, password, cursor, conn)    
            if result:      
                st.sidebar.success("Logged In as {}".format(username))      
                st.session_state["logged_in"] = True   
                st.session_state["user"] = username 
                st.rerun()
            else:      
                st.sidebar.warning("Incorrect Username/Password")

    elif choice == "SignUp":      
        st.sidebar.subheader("Create New Account")      
        new_user = st.sidebar.text_input("Username")      
        new_password = st.sidebar.text_input("Password",type='password')      
    
        if st.sidebar.button("Signup"):      
            SignUp = AddaUser(new_user, new_password, cursor, conn)
            if SignUp[0]:   
                st.sidebar.success("You have successfully created an account and have been logged in.")      
                st.session_state["logged_in"] = True
                st.session_state["user"] = new_user    
                st.rerun()
            else:      
                st.sidebar.warning(SignUp[1])

    
    if st.session_state["logged_in"] == True:    

        GPTVersion = st.toggle('Activate GPT-4')          
        
        st.sidebar.title("Upload your PDF")        
        file = st.sidebar.file_uploader("Drop your file here", type=['pdf'])        
  
        if file is not None and st.sidebar.button('Submit File'):        
                   
            CreatePod(PINECONE_API_KEY,"docusearch")
            FillPod(PINECONE_API_KEY,OPENAI_KEY,"docusearch",file,str(st.session_state["user"]))
            save_file_in_blob_azure(AZURE_BLOB_KEY , AZURE_BLOB_URL, "docusearchstorage", file)
            st.sidebar.success('File uploaded and processed successfully.')      
        st.header('Ask your document')        
        user_input = st.text_input('Type your question here...')      
                
        if st.button('Search'):        
            result = SearchInPineconeIndex(PINECONE_API_KEY,OPENAI_KEY,"docusearch",user_input,st.session_state["user"],7)    
            print(result)  
            answer = generate_response(user_input," ",result,GPTVersion)      
            st.write(answer)        
        
if __name__ == "__main__":        
    main()    