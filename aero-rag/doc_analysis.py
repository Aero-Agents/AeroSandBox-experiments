import os
from pathlib import Path
from google import genai
import matplotlib.pyplot as plt

# Initialize the Gemini client
client = genai.Client()

# Path to the clean_docs directory
clean_docs_dir = Path(__file__).parent / "clean_docs"

# Lists to store results
document_names = []
token_counts = []

print("Counting tokens for each document...\n")

# Iterate through all .txt files in clean_docs
for txt_file in sorted(clean_docs_dir.glob("*.txt")):
    try:
        # Read the file content
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count tokens using the Gemini API
        total_tokens = client.models.count_tokens(
            model="gemini-2.0-flash",
            contents=content
        )
        
        # Extract the token count
        token_count = total_tokens.total_tokens
        
        # Store results
        document_names.append(txt_file.name)
        token_counts.append(token_count)
        
        print(f"{txt_file.name}: {token_count} tokens")
        
    except Exception as e:
        print(f"Error processing {txt_file.name}: {e}")

print(f"\n{'='*60}")
print(f"Total documents processed: {len(token_counts)}")
print(f"Total tokens across all documents: {sum(token_counts)}")
print(f"Average tokens per document: {sum(token_counts) / len(token_counts):.2f}")
print(f"Min tokens: {min(token_counts)}")
print(f"Max tokens: {max(token_counts)}")
print(f"{'='*60}\n")

# Create histogram
plt.figure(figsize=(12, 6))
plt.hist(token_counts, bins=30, edgecolor='black', alpha=0.7)
plt.xlabel('Token Count', fontsize=12)
plt.ylabel('Number of Documents', fontsize=12)
plt.title('Distribution of Document Token Lengths', fontsize=14, fontweight='bold')
plt.grid(axis='y', alpha=0.3)

# Add statistics to the plot
stats_text = f'Total Docs: {len(token_counts)}\n'
stats_text += f'Total Tokens: {sum(token_counts):,}\n'
stats_text += f'Mean: {sum(token_counts) / len(token_counts):.1f}\n'
stats_text += f'Min: {min(token_counts)}\n'
stats_text += f'Max: {max(token_counts)}'
plt.text(0.98, 0.97, stats_text,
         transform=plt.gca().transAxes,
         verticalalignment='top',
         horizontalalignment='right',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
         fontsize=10)

plt.tight_layout()

# Save the plot
output_path = Path(__file__).parent / "token_distribution.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Histogram saved to: {output_path}")

# Show the plot
plt.show()
