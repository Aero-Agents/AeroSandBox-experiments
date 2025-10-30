import os
import re
import chromadb
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.storage import LocalFileStore
import time
from collections import deque

import getpass
import os

if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key: ")

# --- 1. DEFINE PATHS ---
# Directory where ChromaDB will store its persistent data
CHROMA_PATH = "./chroma_db"
# Directory where parent documents will be stored
DOCSTORE_PATH = "./chroma_db/docstore"
# Directory containing the cleaned documentation files
CLEAN_DOCS_DIR = "./clean_docs"
# Names for the collections (like tables in a SQL DB)
VECTOR_COLLECTION_NAME = "child_chunks"
DOCSTORE_COLLECTION_NAME = "parent_docs"

# --- 2. SETUP STORES (Persistent Client) ---
print("Setting up ChromaDB client and stores...")
# Initialize the persistent Chroma client
# This will create the ./chroma_db directory if it doesn't exist
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Initialize the Gemini embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", task_type="RETRIEVAL_DOCUMENT")

# 1. The vector store (for child docs)
vectorstore = Chroma(
    client=client,
    collection_name=VECTOR_COLLECTION_NAME,
    embedding_function=embeddings,
)

# 2. The document store (for parent docs)
# Use LocalFileStore to persist parent documents to disk
docstore = LocalFileStore(DOCSTORE_PATH)

# 3. The splitter for the "child" documents
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)

# 4. Initialize the retriever
# This import now comes from langchain_community.retrievers
retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    child_splitter=child_splitter,
)

# --- 3. LOAD, CHUNK, AND ADD DOCUMENTS ---
print(f"Loading documentation files from {CLEAN_DOCS_DIR}...")

# Get all .txt files from clean_docs directory
clean_docs_path = Path(CLEAN_DOCS_DIR)
txt_files = list(clean_docs_path.glob("*.txt"))

print(f"Found {len(txt_files)} .txt files.")

# --- 4. PARSE FILENAMES AND CREATE DOCUMENTS ---
print("Creating parent documents from files...")

def parse_filename(filename):
    """
    Parse filename to extract metadata.
    Examples:
        - Airplane.txt -> {name: "Airplane", type: "class", parent: None}
        - Airplane.draw.txt -> {name: "draw", type: "method", parent: "Airplane"}
        - AeroBuildup.run.txt -> {name: "run", type: "method", parent: "AeroBuildup"}
    """
    # Remove .txt extension
    name_parts = filename.stem.split('.')
    
    metadata = {
        'filename': filename.name,
        'full_name': filename.stem
    }
    
    if len(name_parts) == 1:
        # Single part: likely a class or function
        metadata['name'] = name_parts[0]
        metadata['type'] = 'class'  # Assume class for single-part names
        metadata['parent'] = None
    else:
        # Multiple parts: parent.method or parent.subclass.method
        metadata['name'] = name_parts[-1]  # Last part is the method/attribute name
        metadata['parent'] = '.'.join(name_parts[:-1])  # Everything before is the parent
        metadata['type'] = 'method'  # Assume method for multi-part names
    
    return metadata

parent_docs = []
for txt_file in txt_files:
    # Read the file content
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Skip empty files
    if not content:
        print(f"  Skipping empty file: {txt_file.name}")
        continue
    
    # Parse metadata from filename
    metadata = parse_filename(txt_file)
    metadata['source'] = str(txt_file)
    
    # Create Document
    doc = Document(
        page_content=content,
        metadata=metadata
    )
    parent_docs.append(doc)

print(f"Created {len(parent_docs)} parent documents.")

# Preview the first few documents
print("\nPreviewing first 5 documents...")
for i, doc in enumerate(parent_docs[:5]):
    print(f"\n--- Document {i+1} ---")
    print("Metadata:", doc.metadata)
    print(f"Content length: {len(doc.page_content)} characters")
    print("Content preview:", doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)


# --- 5. ADD DOCUMENTS TO RETRIEVER ---
# This one command does all the work:
# 1. Splits parent docs into child docs (400 chars) where needed
# 2. Embeds all child docs (using Gemini)
# 3. Adds child docs to the 'vectorstore' collection
# 4. Adds parent docs to the 'docstore' collection
# ** All data is automatically saved to disk by the PersistentClient **
print("\nAdding documents to retriever (this will take a while)...")
print("  - Short docs will be embedded as-is")
print("  - Long docs will be split into 400-char child chunks for search")
retriever.add_documents(parent_docs, ids=None)

print(f"\n--- 💡 Index built and saved to {CHROMA_PATH}! ---")
print(f"Total parent documents: {len(parent_docs)}")
print(f"Vector collection: {VECTOR_COLLECTION_NAME}")
print(f"Docstore collection: {DOCSTORE_COLLECTION_NAME}")
