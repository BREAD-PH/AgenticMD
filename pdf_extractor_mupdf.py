import fitz  # PyMuPDF
import os
from typing import Dict, List, Tuple
import json
from pathlib import Path

class PDFExtractor:
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF extractor with a PDF file path
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def extract_text_by_page(self) -> Dict[int, str]:
        """
        Extract text from each page of the PDF
        
        Returns:
            Dict[int, str]: Dictionary mapping page numbers to extracted text
        """
        text_by_page = {}
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text_by_page[page_num] = page.get_text()
        return text_by_page

    def extract_text_with_formatting(self) -> Dict[int, List[Dict]]:
        """
        Extract text with formatting information (font, size, color)
        
        Returns:
            Dict[int, List[Dict]]: Dictionary mapping page numbers to lists of text blocks with formatting
        """
        formatted_text = {}
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            blocks = []
            for block in page.get_text("dict")["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            blocks.append({
                                "text": span["text"],
                                "font": span["font"],
                                "size": span["size"],
                                "color": span["color"]
                            })
            formatted_text[page_num] = blocks
        return formatted_text

    def extract_tables(self) -> Dict[int, List[List[str]]]:
        """
        Extract tables from the PDF
        
        Returns:
            Dict[int, List[List[str]]]: Dictionary mapping page numbers to lists of tables
        """
        tables_by_page = {}
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            tables = []
            for table in page.find_tables():
                tables.append(table.extract())
            if tables:
                tables_by_page[page_num] = tables
        return tables_by_page

    def extract_images(self, output_dir: str) -> List[Tuple[int, str]]:
        """
        Extract images from the PDF and save them to a directory
        
        Args:
            output_dir (str): Directory to save extracted images
            
        Returns:
            List[Tuple[int, str]]: List of tuples containing page number and image path
        """
        os.makedirs(output_dir, exist_ok=True)
        image_list = []
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            image_list.extend(self._extract_images_from_page(page, page_num, output_dir))
            
        return image_list

    def _extract_images_from_page(self, page, page_num: int, output_dir: str) -> List[Tuple[int, str]]:
        """
        Helper method to extract images from a single page
        """
        image_list = []
        image_count = 0
        
        for image_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = self.doc.extract_image(xref)
            
            if base_image:
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"page{page_num + 1}_image{image_count + 1}.{image_ext}"
                image_path = os.path.join(output_dir, image_filename)
                
                with open(image_path, "wb") as image_file:
                    image_file.write(image_bytes)
                    
                image_list.append((page_num, image_path))
                image_count += 1
                
        return image_list

    def save_extracted_text(self, output_path: str, include_formatting: bool = False):
        """
        Save extracted text to a JSON file
        
        Args:
            output_path (str): Path to save the JSON file
            include_formatting (bool): Whether to include formatting information
        """
        if include_formatting:
            content = self.extract_text_with_formatting()
        else:
            content = self.extract_text_by_page()
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

    def close(self):
        """Close the PDF document"""
        self.doc.close()

def main():
    # Example usage
    pdf_path = "example.pdf"  # Replace with your PDF path
    output_dir = "extracted_content"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize extractor
        extractor = PDFExtractor(pdf_path)
        
        # Extract and save plain text
        text_output = os.path.join(output_dir, "extracted_text.json")
        extractor.save_extracted_text(text_output)
        print(f"Text extracted and saved to: {text_output}")
        
        # Extract and save formatted text
        formatted_output = os.path.join(output_dir, "formatted_text.json")
        extractor.save_extracted_text(formatted_output, include_formatting=True)
        print(f"Formatted text extracted and saved to: {formatted_output}")
        
        # Extract tables
        tables = extractor.extract_tables()
        if tables:
            tables_output = os.path.join(output_dir, "tables.json")
            with open(tables_output, 'w') as f:
                json.dump(tables, f, indent=2)
            print(f"Tables extracted and saved to: {tables_output}")
        
        # Extract images
        images_dir = os.path.join(output_dir, "images")
        images = extractor.extract_images(images_dir)
        if images:
            print(f"Images extracted to: {images_dir}")
            print(f"Number of images extracted: {len(images)}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        extractor.close()

if __name__ == "__main__":
    main()
