import random
import pandas as pd  # type: ignore[import-unresolved]

INPUT_FILE = "laptop.csv"
OUTPUT_FILE = "laptops_with_weight.csv"

df = pd.read_csv(INPUT_FILE)
random.seed(42)


def estimate_pc_weight(row):
    brand = str(row.get("brand", "")).strip().lower()
    model = str(row.get("model_name", "")).strip().lower()
    gpu = str(row.get("graphics", "")).strip().lower()

    raw_inches = pd.to_numeric(row.get("screen_size(inches)"), errors="coerce")
    inches = float(raw_inches) if pd.notna(raw_inches) else 15.6

    # Masaüstü / kasa ibaresi varsa ağırlık gerekmez
    if any(k in model for k in ["desktop", "tower", "all-in-one", "aio"]):
        return None

    # Apple modelleri için bilinen ağırlıklar
    if brand == "apple" or "macbook" in model:
        if "air" in model and inches <= 13.6:
            return 1.24
        if "air" in model and inches <= 15.5:
            return 1.51
        if inches <= 13.6:
            return 1.24
        if inches <= 14.5:
            return 1.55
        return 2.14

    # Harici ekran kartı (gaming / iş istasyonu) kontrolü
    has_dedicated_gpu = any(
        k in gpu for k in ["rtx", "gtx", "quadro", "radeon rx", "arc"]
    )
    is_gaming_model = any(
        k in model for k in ["gaming", "nitro", "predator", "legion", "rog", "tuf", "victus", "omen"]
    )

    if has_dedicated_gpu or is_gaming_model:
        if inches >= 17.0:
            return round(float(random.uniform(2.70, 3.20)), 2)
        return round(float(random.uniform(2.20, 2.75)), 2)

    # İnce / taşınabilir cihazlar
    if inches <= 14.5 or any(k in model for k in ["ultrabook", "zenbook", "thinkpad x", "swift", "vivobook"]):
        return round(float(random.uniform(1.15, 1.48)), 2)

    # Standart 15.6" - 16" cihazlar
    return round(float(random.uniform(1.65, 1.98)), 2)


df["Weight_kg"] = df.apply(estimate_pc_weight, axis=1)
df.to_csv(OUTPUT_FILE, index=False)

print("Tamamlandı! Kaydedilen dosya:", OUTPUT_FILE)
print(df[["brand", "model_name", "screen_size(inches)", "graphics", "Weight_kg"]].head(10))