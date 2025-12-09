"""
Download translation model
Run this once before starting the server
"""

from transformers import MarianMTModel, MarianTokenizer

print("=" * 60)
print("📥 Downloading Translation Model")
print("=" * 60)
print("Model: Helsinki-NLP/opus-mt-en-fr")
print("Size: ~300 MB")
print("This will take 2-3 minutes...\n")

model_name = 'Helsinki-NLP/opus-mt-en-fr'

try:
    print("Step 1/2: Downloading tokenizer...")
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    print("✓ Tokenizer downloaded")
    
    print("\nStep 2/2: Downloading model (this is the big one)...")
    model = MarianMTModel.from_pretrained(model_name)
    print("✓ Model downloaded")
    
    print("\nSaving to local folder...")
    tokenizer.save_pretrained('./models/opus-mt-en-fr')
    model.save_pretrained('./models/opus-mt-en-fr')
    print("✓ Saved to ./models/opus-mt-en-fr")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Model is ready to use")
    print("=" * 60)
    print("\nNext step: Run the server with:")
    print("  uvicorn app.main:app --reload")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check your internet connection")
    print("2. Make sure you have enough disk space (~1 GB free)")
    print("3. Try running again")