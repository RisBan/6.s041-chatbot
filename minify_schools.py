import json

INPUT_PATH = "en.data.json"     # Replace with your full file name
OUTPUT_PATH = "all_schools_minified.json"

def extract_minimal_school_data(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print("❌ Failed to parse JSON:", e)
            return

    # Only keep selected fields
    minified = [
        {
            "id": s.get("id", ""),
            "name": s.get("school", ""),
            "address": s.get("address", "")
        }
        for s in data if isinstance(s, dict)
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(minified, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(minified)} entries to {output_path}")

if __name__ == "__main__":
    extract_minimal_school_data(INPUT_PATH, OUTPUT_PATH)