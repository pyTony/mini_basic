import fitz  # PyMuPDF
import io
import ollama

import fitz  # PyMuPDF
import io
import ollama

# --- ASETUKSET ---
# --- ASETUKSET ---
PDF_POLKU = "BBC BASIC Reference Manual-opt.pdf"       # Muuta tähän oman PDF-tiedostosi nimi
MALLI = "qwen3.5:9b-q4_K_M"               # Käytettävä Ollama-malli (esim. qwen2.5-vl tai moondream)
TALLENNUS_POLKU = "clean_text.txt"  # Tiedosto, johon valmis teksti tallennetaan

# Täydellinen ja tiukka ohjeistus mallille layoutin ja tekstin korjaamiseen:
PROMPT = """Analyze this document page image and perform high-quality OCR. 
Strictly follow these rules:
1. Fix all typos, broken words, and OCR errors (e.g., replace 'beløre' with 'before').
2. Maintain the correct and natural reading order of columns, headers, and paragraphs.
3. If there are tables, format them cleanly using Markdown syntax.
4. Output ONLY the clean, extracted text. Do not add any conversational text, explanations, or greetings."""

def tee_pdf_ocr(pdf_path, output_path, model_name, prompt_text):
    print(f"Avataan tiedosto: {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Virhe: PDF-tiedostoa ei voitu avata. Tarkista polku. ({e})")
        return

    # Avataan tiedosto kirjoittamista varten (korvaa vanhan tiedoston)
    with open(output_path, "w", encoding="utf-8") as f:
        for page_num in range(len(doc)):
            print(f"\n--- Prosessoidaan sivu {page_num + 1} / {len(doc)} ---")
            
            # 1. Muunnetaan PDF-sivu kuvaksi
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            image_bytes = pix.tobytes("png")
            
            # 2. Lähetetään kuva Ollamalle
            try:
                response = ollama.generate(
                    model=model_name,
                    prompt=prompt_text,
                    images=[image_bytes]
                )
                sivun_teksti = response['response']
                
                # Tulostetaan näytölle seurantaa varten
                print(sivun_teksti)
                
                # Kirjoitetaan tiedostoon
                f.write(f"\n--- SIVU {page_num + 1} ---\n")
                f.write(sivun_teksti)
                f.write("\n")
                
            except Exception as e:
                print(f"Virhe Ollama-kutsussa sivulla {page_num + 1}: {e}")
                print("Varmista, että Ollama-palvelin on käynnissä ja malli ladattu.")

    print(f"\nValmis! Puhdistettu teksti tallennettu tiedostoon: {output_path}")

if __name__ == "__main__":
    tee_pdf_ocr(PDF_POLKU, TALLENNUS_POLKU, MALLI, PROMPT)
