# RAG Augmenting LLM with specialized and mutable knowledge

# In general : 
    # Prompt -> LLM -> Response

# RAG
    # User query -> RAG module (Knowledge Base) -> Prompt -> LLM -> Response

    # Retirever and Knowledge base
    # Knowledge base is a collection of Text embeddings (db records)
    # user query is converted to a text embedding and compared with the db records to find the most similar record (retriever)

# Working

    # 1. Load the documents 
    # 2. Chunk the documents (realtive information)
    # 3. Embed the chunks
    # 4. Create a Vector database (for easy retrieval)


# loading the pdf
import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
# from get_embedding_function import get_embedding_function
from langchain_community.vectorstores import Chroma


DATA_PATH = '/home/snakkill/Projects/LLM/RAG/data/'
from langchain_community.document_loaders import PyPDFDirectoryLoader
# we can use any document loader, here we are using PyPDFDirectoryLoader for loading pdfs

def load_docs():
    doc_loader = PyPDFDirectoryLoader(DATA_PATH)
    return doc_loader.load()


# print(docs[0])

# Splitting the documents

# we using RecursiveCharacterTextSplitter for splitting the documents, a built in splitter in langchain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document

def split_documents(docs: list[Document]):
    txt_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    return txt_splitter.split_documents(docs)


docs = load_docs()
chunks = split_documents(docs)
# print(chunks[0])

# Embedding the chunks

from langchain_community.embeddings.bedrock import BedrockEmbeddings

def get_embedding_function():
    embeddings = BedrockEmbeddings(
        credentials_profile_name='default', region_name="us-west-2"
    )
    return embeddings

# Building the vector database

from get_embedding_funcition import get_embedding_function
from langchain.vectorstores.chroma import Chroma

def add_to_chroma(chunks: list[Document]):
    db = Chroma(
        persist_directory=CHROMA+PATH,embedding_function=get_embedding_function()
    )
    db.add_documents(new_chunks,ids=new_chunk_ids)

    db.persist()

# indexing the chunks
last_page_id =None
current_chunk_index = 0

for chunk in chunks:
    source = chunk.metadata.get('source')
    page = chunk.metadata.get('page')
    current_page_id = f'{source}_{page}'
    if current_page_id == last_page_id:
        current_chunk_index += 1
    else:
        current_chunk_index = 0
    chunk.metadata['id'] = chunk_id