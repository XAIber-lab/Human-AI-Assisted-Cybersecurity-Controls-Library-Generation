# Save this as runner.py
from pdf_highlighter import PDFHighlighter
import sys

def main():
    # Check if correct number of arguments are provided
    if len(sys.argv) < 3:
        print("Usage: python runner.py input.pdf input.csv [output.pdf]")
        print("Example: python runner.py document.pdf extracts.csv")
        return

    # Get input files from command line arguments
    pdf_file = sys.argv[1]
    csv_file = sys.argv[2]
    
    # If output file is provided as third argument, use it
    # Otherwise, create output filename by adding '_highlighted' to the input PDF name
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    else:
        output_file = pdf_file.replace('.pdf', '_highlighted.pdf')

    # Create highlighter instance
    highlighter = PDFHighlighter()
    
    # Process the highlights
    print("\nProcessing highlights...")
    print(f"Input PDF: {pdf_file}")
    print(f"CSV file: {csv_file}")
    print(f"Output will be saved as: {output_file}")
    
    result = highlighter.process_csv_highlights(
        csv_path=csv_file,
        pdf_path=pdf_file,
        output_path=output_file
    )

if __name__ == "__main__":
    main()
