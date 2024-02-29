
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import streamlit as st
import os

    
def save_file_in_blob_azure(credential , account_url, container_name, file):    
    """Save uploaded file to the specified Azure Blob Storage container and return the blob URL."""    
    
  
    # get the container client    
    blob_service_client = BlobServiceClient(account_url, credential=credential)  
  
    blob_client = blob_service_client.get_container_client(container=container_name)    
  
    
    # Convert the file object to bytes  
    data = file.getvalue()  
    blob_client.upload_blob(name=file.name, data=data, overwrite=True)
  
    
        
    # return the blob URL    
    return blob_client.url   

