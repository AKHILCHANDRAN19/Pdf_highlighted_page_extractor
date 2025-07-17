import fitz  # PyMuPDF
import os

# --- CONFIGURATION ---

# 1. The path to your folder.
PDF_FOLDER_PATH = '/storage/emulated/0/TEXT'

# 2. This is the list of colors we will search for.
#    These are standard (R, G, B) values for the colors you mentioned.
#    R, G, and B values are between 0.0 and 1.0.
TARGET_COLORS = [
    (1.0, 1.0, 0.0),    # Yellow
    (0.0, 1.0, 0.0),    # Green
    (0.0, 0.749, 1.0)   # A common Sky Blue
]

# 3. How "close" a color needs to be to match.
#    This helps catch slight variations from your PDF app.
#    You probably won't need to change this.
COLOR_TOLERANCE = 0.05

# 4. The suffix for the new, created PDF file.
OUTPUT_SUFFIX = '_my_highlights.pdf'

# --- HELPER FUNCTION TO CHECK COLORS ---

def is_color_close_enough(color_to_check, target_colors, tolerance):
    """
    Checks if a color is close to any of the colors in our target list.
    """
    if not color_to_check:
        return False  # No color to check

    # Unpack the R, G, B values of the color we're checking
    r1, g1, b1 = color_to_check

    # Loop through our list of target colors (Yellow, Green, Sky Blue)
    for target_color in target_colors:
        r2, g2, b2 = target_color
        # Check if the difference for each component (R, G, B) is within our tolerance
        if (abs(r1 - r2) < tolerance and
            abs(g1 - g2) < tolerance and
            abs(b1 - b2) < tolerance):
            return True  # It's a match!

    return False # No match was found

# --- MAIN FUNCTION ---

def create_pdf_from_specific_highlights(folder_path, suffix):
    """
    Scans PDFs, finds pages with highlights matching specific colors, and
    creates a new PDF from those pages.
    """
    print(f"Searching for PDF files in: {folder_path}\n")

    try:
        all_files = os.listdir(folder_path)
    except Exception as e:
        print(f"❌ ERROR accessing folder: {e}")
        print("Please check the folder path and grant storage permissions to the app.")
        return

    pdf_files = [f for f in all_files if f.lower().endswith('.pdf') and not f.lower().endswith(suffix)]

    if not pdf_files:
        print("No source PDF files were found to process.")
        return

    print(f"Found {len(pdf_files)} PDF file(s). Starting scan...\n")
    total_new_files = 0

    for filename in pdf_files:
        pdf_path = os.path.join(folder_path, filename)
        print(f"--- 📖 Processing: {filename} ---")

        pages_to_keep = [] # A list to store the page numbers we want

        try:
            with fitz.open(pdf_path) as doc:
                # Loop through every page in the PDF
                for page_index, page in enumerate(doc):
                    # Get all highlight annotations on the current page
                    annots = page.annots(types=[fitz.PDF_ANNOT_HIGHLIGHT])

                    if not annots:
                        continue # Skip page if it has no highlights at all

                    # Now, check the color of EACH highlight on the page
                    for annot in annots:
                        # The highlight color is stored in 'stroke'
                        annot_color = annot.colors['stroke']

                        # Check if this highlight's color matches one of our targets
                        if is_color_close_enough(annot_color, TARGET_COLORS, COLOR_TOLERANCE):
                            print(f"  > Match found on Page {page_index + 1}! (Your highlight)")
                            pages_to_keep.append(page_index)
                            # Once we find one of YOUR highlights, we don't need to check
                            # the rest on this page. We know we want to keep it.
                            break # Go to the next page

                # After checking all pages, see if we found any of your highlights
                if pages_to_keep:
                    print(f"\n  ✅ Found {len(pages_to_keep)} pages with your highlights. Creating new PDF...")

                    # Remove duplicate page numbers (just in case)
                    unique_pages = sorted(list(set(pages_to_keep)))

                    new_doc = fitz.open() # Create a new empty PDF
                    new_doc.insert_pdf(doc, from_page=unique_pages[0], to_page=unique_pages[0]) # Start with the first page
                    
                    # Insert the rest of the pages one by one
                    for page_index in unique_pages[1:]:
                        new_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)

                    output_filename = f"{os.path.splitext(filename)[0]}{suffix}"
                    output_filepath = os.path.join(folder_path, output_filename)

                    new_doc.save(output_filepath, garbage=4, deflate=True, clean=True)
                    new_doc.close()

                    print(f"  👍 Successfully saved: {output_filename}\n")
                    total_new_files += 1
                else:
                    print("  - No highlights matching your specific colors were found in this file.\n")

        except Exception as e:
            print(f"  ❌ An error occurred while processing '{filename}': {e}\n")

    print("--- 🏁 Processing Complete! ---")
    if total_new_files > 0:
        print(f"Created {total_new_files} new PDF file(s) in your TEXT folder.")
    else:
        print("No new PDFs were created. If you are sure you have yellow, green, or blue highlights,")
        print("the color codes in the PDF might be slightly different. Let me know if this happens.")

# --- RUN THE SCRIPT ---
if __name__ == '__main__':
    create_pdf_from_specific_highlights(PDF_FOLDER_PATH, OUTPUT_SUFFIX)
