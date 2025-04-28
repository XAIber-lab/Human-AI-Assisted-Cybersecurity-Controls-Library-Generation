# Save this as pdf_highlighter.py
import fitz
import pandas as pd
import re
import unicodedata
from difflib import SequenceMatcher

class PDFHighlighter:
    def __init__(self, default_color=(1, 1, 0), default_alpha=0.5, similarity_threshold=0.75):
        self.default_color = default_color
        self.default_alpha = default_alpha
        self.similarity_threshold = similarity_threshold
        self.color_map = {
            'red': (1, 0, 0),
            'blue': (0, 0, 1),
            'yellow': (1, 1, 0),
            'green': (0, 1, 0)
        }

    def _clean_text(self, text: str) -> str:
        """
        Basic text cleaning:
        1. Remove superscript/subscript numbers
        2. Remove extra whitespace
        3. Remove punctuation except commas and periods
        """
        # Convert to string if not already
        text = str(text)
        
        # Remove superscript/subscript numbers
        text = re.sub(r'[⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]', '', text)
        
        # Remove regular numbers that appear as superscripts
        text = re.sub(r'(?<=\w)[\d]+(?!\w)', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two strings
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def _get_text_instances(self, page, block_rect: fitz.Rect, text: str) -> list:
        """
        Get precise text locations within a block
        """
        instances = page.search_for(text)
        # Only return instances that are within our block
        return [inst for inst in instances if block_rect.intersects(inst)]

    def _find_text_in_page(self, page, search_text: str) -> list:
        """
        Find text in page using similarity matching and precise coordinates
        """
        cleaned_search_text = self._clean_text(search_text)
        matches = []
        
        # Get all text blocks from the page
        blocks = page.get_text("blocks")
        
        for block in blocks:
            block_text = block[4]  # The text content is at index 4
            cleaned_block_text = self._clean_text(block_text)
            
            # Calculate similarity
            similarity = self._calculate_similarity(cleaned_search_text, cleaned_block_text)
            
            # If we have a potential match
            if similarity >= self.similarity_threshold or cleaned_search_text in cleaned_block_text:
                # Try to get precise coordinates using search_for
                block_rect = fitz.Rect(block[:4])
                instances = self._get_text_instances(page, block_rect, search_text)
                
                if instances:
                    # Use the precise coordinates
                    matches.extend(instances)
                else:
                    # Fallback: search with cleaned text
                    instances = self._get_text_instances(page, block_rect, cleaned_search_text)
                    if instances:
                        matches.extend(instances)
                    else:
                        # Last resort: use block coordinates
                        matches.append(block_rect)
        
        return matches

    def _find_cross_page_text(self, doc, search_text: str, color, page_num: int) -> bool:
        """
        Find text across pages by looking for significant parts 
        of the text at page boundaries
        """
        if page_num >= len(doc) - 1:
            return False

        current_page = doc[page_num]
        next_page = doc[page_num + 1]
        
        # Get text from both pages
        current_page_text = current_page.get_text("text")
        next_page_text = next_page.get_text("text")
        
        # Clean the search text
        cleaned_search = self._clean_text(search_text)
        words = cleaned_search.split()
        
        # Generate all possible subsequences of words (minimum 4 words)
        subsequences = []
        for i in range(len(words)):
            for j in range(i + 4, len(words) + 1):
                subsequences.append(' '.join(words[i:j]))
        
        # Sort subsequences by length, longest first
        subsequences.sort(key=len, reverse=True)
        
        # Look for subsequences in both pages
        found_in_current = None
        found_in_next = None
        
        # Find matches in current page
        current_blocks = current_page.get_text("blocks")
        for block in current_blocks:
            block_text = self._clean_text(block[4])
            for subseq in subsequences:
                if self._calculate_similarity(subseq, block_text) > 0.9 or subseq in block_text:
                    found_in_current = (subseq, block[:4])
                    break
            if found_in_current:
                break
        
        # Find matches in next page
        next_blocks = next_page.get_text("blocks")
        for block in next_blocks:
            block_text = self._clean_text(block[4])
            for subseq in subsequences:
                if self._calculate_similarity(subseq, block_text) > 0.9 or subseq in block_text:
                    found_in_next = (subseq, block[:4])
                    break
            if found_in_next:
                break
        
        # If we found matches in both pages
        if found_in_current and found_in_next:
            # Highlight the matches
            highlight = current_page.add_highlight_annot(fitz.Rect(found_in_current[1]))
            highlight.set_colors(stroke=color)
            highlight.update(opacity=self.default_alpha)
            
            highlight = next_page.add_highlight_annot(fitz.Rect(found_in_next[1]))
            highlight.set_colors(stroke=color)
            highlight.update(opacity=self.default_alpha)
            
            return True
            
        return False

    def _parse_color(self, color_str):
        if not color_str or pd.isna(color_str):
            return self.default_color

        color_str = str(color_str).lower().strip()
        if color_str in self.color_map:
            return self.color_map[color_str]
        
        try:
            rgb = [float(x.strip())/255 for x in color_str.split(',')]
            if len(rgb) == 3:
                return tuple(rgb)
        except:
            pass
        
        return self.default_color

    def process_csv_highlights(self, csv_path: str, pdf_path: str, output_path: str = None,
                             text_column: str = 'text_extract',
                             color_column: str = 'highlight_color',
                             delimiter: str = ';') -> bool:
        try:
            # Read CSV file
            df = pd.read_csv(csv_path, delimiter=delimiter, encoding='utf-8')
            
            if output_path is None:
                output_path = pdf_path.replace('.pdf', '_highlighted.pdf')
            
            # Open the PDF
            doc = fitz.open(pdf_path)
            results = []
            
            # Process each text extract
            for index, row in df.iterrows():
                # Get the text to highlight
                text_to_highlight = str(row[text_column]).strip().strip('"\'')
                
                # Get color
                color = self._parse_color(row[color_column] if color_column in df.columns else None)
                
                success = False
                
                # First try normal search
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    instances = self._find_text_in_page(page, text_to_highlight)
                    
                    if instances:
                        for inst in instances:
                            highlight = page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=color)
                            highlight.update(opacity=self.default_alpha)
                        success = True
                        break
                
                # If not found and text is long enough, try cross-page search
                if not success and len(text_to_highlight.split()) >= 10:
                    for page_num in range(len(doc) - 1):
                        if self._find_cross_page_text(doc, text_to_highlight, color, page_num):
                            success = True
                            break
                
                results.append({
                    'text': text_to_highlight,
                    'found': success,
                    'index': index + 1
                })
                
                # Print progress
                print(f"Processing extract {index + 1}/{len(df)}: {'Success' if success else 'Not found'}")
            
            # Save the modified PDF
            doc.save(output_path)
            doc.close()
            
            # Print final report
            print("\nProcessing Report:")
            print("-" * 50)
            print(f"Total extracts in CSV: {len(df)}")
            
            successful = [r for r in results if r['found']]
            failed = [r for r in results if not r['found']]
            
            print(f"Successfully highlighted: {len(successful)}")
            print(f"Failed to highlight: {len(failed)}")
            
            if failed:
                print("\nExtracts that were not found:")
                for result in failed:
                    print(f"\nExtract #{result['index']}:")
                    print(f"Text: '{result['text']}'")
            
            return True
            
        except Exception as e:
            print(f"Error processing highlights: {str(e)}")
            return False
