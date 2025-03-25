import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI

# Load environment variables
load_dotenv()

class PDFSwarmExtractor:
    def __init__(self, max_workers: int = 4):
        """
        Initialize the PDF Swarm Extractor
        
        Args:
            max_workers (int): Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self.llm = OpenAI(temperature=0)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )

    def process_single_pdf(self, pdf_path: str) -> List[str]:
        """
        Process a single PDF file and extract its text
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            List[str]: List of extracted text chunks
        """
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            # Split the document into chunks
            chunks = self.text_splitter.split_documents(pages)
            
            # Extract raw text from chunks
            texts = [chunk.page_content for chunk in chunks]
            
            print(f"Successfully processed {pdf_path}")
            return texts
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            return []

    def process_pdf_directory(self, directory_path: str) -> dict:
        """
        Process all PDFs in a directory using parallel processing
        
        Args:
            directory_path (str): Path to directory containing PDFs
            
        Returns:
            dict: Dictionary mapping PDF filenames to their extracted text
        """
        pdf_files = [str(f) for f in Path(directory_path).glob("**/*.pdf")]
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pdf = {executor.submit(self.process_single_pdf, pdf): pdf 
                           for pdf in pdf_files}
            
            for future in future_to_pdf:
                pdf_path = future_to_pdf[future]
                try:
                    texts = future.result()
                    results[pdf_path] = texts
                except Exception as e:
                    print(f"Error processing {pdf_path}: {str(e)}")
                    results[pdf_path] = []
        
        return results

def main():
    # Make sure you have set your OpenAI API key in .env file
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY in the .env file")
        return

    # Initialize the extractor
    extractor = PDFSwarmExtractor(max_workers=4)
    
    # Example usage
    pdf_directory = "pdfs"  # Change this to your PDF directory
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)
        print(f"Created directory: {pdf_directory}")
        print("Please place your PDF files in this directory")
        return
    
    # Process all PDFs in the directory
    results = extractor.process_pdf_directory(pdf_directory)
    
    # Print results
    for pdf_path, texts in results.items():
        print(f"\nProcessed {pdf_path}:")
        print(f"Extracted {len(texts)} text chunks")
        if texts:
            print("First chunk preview:", texts[0][:200] + "...")

if __name__ == "__main__":
    main()
