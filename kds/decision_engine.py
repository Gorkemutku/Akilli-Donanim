"""
KDS (Decision Support Systems) Decision Engine:
- Multi-Criteria Decision Making (MCDM / WSM - Weighted Sum Model)
- Hard constraint filtering with explicit elimination reasons
- Dynamic weight synthesis for multi-purpose selections
- Academic rationale generation and Google Search link formatting
"""
import urllib.parse
from typing import List, Dict, Any, Tuple, Optional


# Purpose profiles for Laptop criteria weights (Hardware priorities)
PURPOSE_PROFILES = {
    "oyun": {
        "name": "Oyun",
        "weights": {
            "gpu": 0.35,
            "cpu": 0.20,
            "display": 0.18,
            "ram": 0.15,
            "battery": 0.06,
            "portability": 0.06
        },
        "min_ram": 16,
        "min_gpu": 65,
        "min_storage": 512
    },
    "yazilim": {
        "name": "Yazılım Geliştirme",
        "weights": {
            "cpu": 0.35,
            "ram": 0.24,
            "battery": 0.16,
            "display": 0.13,
            "portability": 0.07,
            "gpu": 0.05
        },
        "min_ram": 16,
        "min_cpu": 70,
        "min_storage": 512
    },
    "grafik": {
        "name": "Grafik Tasarım",
        "weights": {
            "display": 0.32,
            "gpu": 0.24,
            "cpu": 0.20,
            "ram": 0.14,
            "battery": 0.05,
            "portability": 0.05
        },
        "min_ram": 16,
        "min_display": 75,
        "min_storage": 512
    },
    "gunluk": {
        "name": "Günlük Kullanım",
        "weights": {
            "battery": 0.28,
            "portability": 0.24,
            "display": 0.20,
            "cpu": 0.16,
            "ram": 0.08,
            "gpu": 0.04
        },
        "min_ram": 8,
        "min_storage": 256
    }
}

PHONE_DEFAULT_WEIGHTS = {
    "cpu": 0.25,
    "camera": 0.25,
    "battery": 0.20,
    "display": 0.15,
    "price": 0.15
}

TABLET_DEFAULT_WEIGHTS = {
    "display": 0.30,
    "stylus_or_cam": 0.25,
    "cpu": 0.20,
    "battery": 0.15,
    "price": 0.10
}


def normalize_weights(weight_dict: Dict[str, float]) -> Dict[str, float]:
    """Ensures sum of weights equals 1.0."""
    total = sum(weight_dict.values())
    if total <= 0:
        count = len(weight_dict)
        return {k: 1.0 / count for k in weight_dict}
    return {k: round(v / total, 4) for k, v in weight_dict.items()}


def synthesize_laptop_weights(purposes: List[str], price_weight: float = 0.15) -> Dict[str, float]:
    """
    Dynamically combines criteria weights when user selects multiple purposes
    (e.g., both Gaming and Software Development).
    """
    if not purposes:
        purposes = ["gunluk"]

    # Normalize purpose keys
    valid_purposes = [p.lower() for p in purposes if p.lower() in PURPOSE_PROFILES]
    if not valid_purposes:
        valid_purposes = ["gunluk"]

    aggregated_hw: Dict[str, float] = {
        "cpu": 0.0,
        "gpu": 0.0,
        "ram": 0.0,
        "display": 0.0,
        "battery": 0.0,
        "portability": 0.0
    }

    for p in valid_purposes:
        p_weights = PURPOSE_PROFILES[p]["weights"]
        for criterion, w in p_weights.items():
            aggregated_hw[criterion] += w

    # Hardware subtotal normalized to (1.0 - price_weight)
    total_hw_raw = sum(aggregated_hw.values())
    target_hw_share = 1.0 - price_weight

    synthesized = {}
    for crit, val in aggregated_hw.items():
        synthesized[crit] = round((val / total_hw_raw) * target_hw_share, 4)

    synthesized["price"] = price_weight
    return normalize_weights(synthesized)


def calculate_price_utility(price: float, budget: float, max_budget_tolerance: float = 0.10) -> float:
    """
    Calculates 0-100 price utility score.
    - If price <= budget: Higher utility when price is within budget, with bonus for economic value.
    - If price > budget but <= budget*(1+tolerance): Soft penalty applied.
    - If price > budget*(1+tolerance): 0.
    """
    if budget <= 0:
        return 50.0

    if price <= budget:
        # Scale between 70 and 100: paying less than budget gives economic surplus
        ratio = price / budget
        return round(100.0 - (ratio * 25.0), 2)
    elif price <= budget * (1.0 + max_budget_tolerance):
        # In tolerance zone: linearly decay from 65 to 40
        overshoot = (price - budget) / (budget * max_budget_tolerance)
        return round(65.0 - (overshoot * 25.0), 2)
    else:
        return 0.0


def calculate_portability_score(weight_kg: Optional[float]) -> float:
    """
    Converts physical weight into a 0-100 portability benchmark score.
    < 1.3 kg -> 95-100
    1.3 - 1.8 kg -> 80-95
    1.8 - 2.0 kg -> 70-80 (< 2.0 kg is lightweight)
    2.0 - 2.5 kg -> 50-70 (Medium)
    > 2.5 kg -> 25-50 (Heavy / Performance)
    """
    if weight_kg is None:
        return 50.0
    if weight_kg <= 1.2:
        return 98.0
    elif weight_kg < 2.0:
        # 1.2 to 2.0 kg: 98 down to 72
        factor = (weight_kg - 1.2) / 0.8
        return round(98.0 - (factor * 26.0), 2)
    elif weight_kg <= 2.5:
        # 2.0 to 2.5 kg: 70 down to 50
        factor = (weight_kg - 2.0) / 0.5
        return round(70.0 - (factor * 20.0), 2)
    else:
        # > 2.5 kg: 48 down to 25
        factor = min(1.0, (weight_kg - 2.5) / 1.0)
        return round(48.0 - (factor * 23.0), 2)


def calculate_ram_score(ram_gb: Optional[int]) -> float:
    """Converts RAM capacity into 0-100 score."""
    if not ram_gb:
        return 50.0
    if ram_gb >= 64:
        return 100.0
    elif ram_gb >= 32:
        return 95.0
    elif ram_gb >= 18:
        return 88.0
    elif ram_gb >= 16:
        return 80.0
    elif ram_gb >= 12:
        return 65.0
    elif ram_gb >= 8:
        return 45.0
    else:
        return 25.0


def build_google_search_link(brand: str, model: str) -> str:
    """Creates a secure Google search link for the device price."""
    query = f"{brand} {model} fiyat"
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"


def generate_recommendation_rationale(
    device: Dict[str, Any],
    category: str,
    purposes: List[str],
    suitability_score: float,
    budget: float
) -> str:
    """Generates an academic, detailed Turkish rationale for why the device is recommended."""
    reasons = []

    price = device["price_try"]
    price_diff = budget - price
    if price_diff >= 0:
        savings_pct = (price_diff / budget) * 100
        reasons.append(f"Belirttiğiniz {budget:,.0f} TL bütçeye tam uyum sağlamakta olup %{savings_pct:.1f} bütçe tasarrufu sunmaktadır.")
    else:
        overshoot_pct = (abs(price_diff) / budget) * 100
        reasons.append(f"Bütçe sınırınızı yalnızca %{overshoot_pct:.1f} aşmasına karşın sağladığı yüksek donanım avantajıyla tolerans bandında yer almıştır.")

    if category == "laptop":
        purpose_names = [PURPOSE_PROFILES[p]["name"] for p in purposes if p in PURPOSE_PROFILES]
        p_str = " ve ".join(purpose_names) if purpose_names else "Genel Kullanım"

        if "oyun" in purposes and "yazilim" in purposes:
            reasons.append(
                f"Hem Oyun hem Yazılım Geliştirme kesişim kümesinde yer alan 16 GB+ RAM ({device.get('ram_gb', 0)} GB) "
                f"ve güçlü işlemci barajını ({device['cpu_score']}/100) fazlasıyla sağlamaktadır."
            )
        elif "oyun" in purposes:
            reasons.append(
                f"Oyun için kritik olan GPU performansı ({device['gpu_score']}/100) ve {device.get('ram_gb', 0)} GB RAM kapasitesi "
                "ile modern oyun motorları için güçlü bir zemin teşkil eder."
            )
        elif "yazilim" in purposes:
            reasons.append(
                f"Yazılım derleme ve emülatör iş yüklerinde öne çıkan yüksek CPU gücü ({device['cpu_score']}/100) "
                f"ve {device.get('ram_gb', 0)} GB RAM ile çoklu görev kapasitesi sunar."
            )
        elif "grafik" in purposes:
            reasons.append(
                f"Görsel üretim ve tasarım için elzem olan yüksek ekran kalitesi ({device['display_score']}/100) "
                f"ve renk/panel yetkinliği ön plandadır."
            )

        weight = device.get("weight_kg")
        if weight:
            if weight < 2.0:
                reasons.append(f"{weight:.2f} kg hafif gövdesiyle yüksek mobilite ve taşıma ergonomisi sağlar.")
            else:
                reasons.append(f"{weight:.2f} kg ağırlığı güçlü soğutma bloğu ve kalıcı performans stabilitesi sunar.")

    elif category == "phone":
        reasons.append(
            f"Kamera yetkinliği ({device['camera_or_stylus_score']}/100), işlemci akıcılığı ({device['cpu_score']}/100) "
            f"ve {device['battery_score']}/100 batarya dayanımıyla dengeli bir mobil deneyim vadeder."
        )
    elif category == "tablet":
        reasons.append(
            f"Ekran panel kalitesi ({device['display_score']}/100) ve kalem/üretkenlik desteği ({device['camera_or_stylus_score']}/100) "
            f"ile akademik not alma, çizim ve medya tüketiminde optimum fayda/maliyet oranı sunar."
        )

    full_rationale = (
        f"KDS Uygunluk İndeksi: %{suitability_score:.1f}. " + " ".join(reasons)
    )
    return full_rationale


def evaluate_devices(
    devices: List[Dict[str, Any]],
    category: str,
    budget: float,
    purposes: Optional[List[str]] = None,
    weight_bands: Optional[List[str]] = None,
    budget_tolerance: float = 0.05,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Main KDS Decision Support evaluation function.
    Returns:
    {
        "category": category,
        "total_evaluated": int,
        "qualified_count": int,
        "eliminated_count": int,
        "weights_used": dict,
        "hard_constraints_applied": list,
        "recommended": [ { ...device, "suitability_score": float, "rationale": str, "google_link": str } ],
        "eliminated": [ { ...device, "reason": str, "type": "hard_constraint" | "score_below_threshold" } ]
    }
    """
    if purposes is None:
        purposes = ["gunluk"]
    if weight_bands is None:
        weight_bands = ["hafif", "orta", "agir"]

    category = category.lower().strip()
    filtered_by_cat = [d for d in devices if d.get("category") == category]

    recommended = []
    eliminated = []
    hard_constraints_log = []

    # Prepare Weights
    if category == "laptop":
        weights = custom_weights or synthesize_laptop_weights(purposes, price_weight=0.15)
        # Log constraints applied
        if "oyun" in purposes and "yazilim" in purposes:
            hard_constraints_log.append("Oyun + Yazılım Kesişimi: RAM ≥ 16 GB, Depolama ≥ 512 GB, CPU Puanı ≥ 70, GPU Puanı ≥ 65")
        elif "oyun" in purposes:
            hard_constraints_log.append("Oyun Kısıtları: RAM ≥ 16 GB, GPU Puanı ≥ 65, Depolama ≥ 512 GB")
        elif "yazilim" in purposes:
            hard_constraints_log.append("Yazılım Kısıtları: RAM ≥ 16 GB, CPU Puanı ≥ 70, Depolama ≥ 512 GB")
        if "grafik" in purposes:
            hard_constraints_log.append("Grafik Tasarım Kısıtları: Ekran Puanı ≥ 75, RAM ≥ 16 GB")

        # Weight band constraint log
        if weight_bands == ["hafif"]:
            hard_constraints_log.append("Taşınabilirlik Kısıtı: Sadece Hafif (< 2.0 kg) seçildi; ≥ 2.0 kg cihazlar elenir")
        elif len(weight_bands) < 3:
            hard_constraints_log.append(f"Seçili Ağırlık Bantları: {', '.join(weight_bands)}")

    elif category == "phone":
        weights = custom_weights or normalize_weights(PHONE_DEFAULT_WEIGHTS)
        hard_constraints_log.append("Standart Telefon KDS Profili: İşlemci, Kamera, Batarya, Ekran ve Fiyat dengesi")
    elif category == "tablet":
        weights = custom_weights or normalize_weights(TABLET_DEFAULT_WEIGHTS)
        hard_constraints_log.append("Standart Tablet KDS Profili: Ekran, Kalem/Üretkenlik, İşlemci, Batarya ve Fiyat dengesi")
    else:
        weights = {"price": 1.0}

    # Bounded budget check
    effective_max_price = budget * (1.0 + budget_tolerance) if budget > 0 else float('inf')
    hard_constraints_log.append(f"Bütçe Limiti: Maksimum {budget:,.0f} TL (+%{int(budget_tolerance*100)} tolerans: {effective_max_price:,.0f} TL)")

    for device in filtered_by_cat:
        brand = device.get("brand", "Bilinmeyen")
        model = device.get("model", "Cihaz")
        price = device.get("price_try")
        cpu_score = device.get("cpu_score")
        gpu_score = device.get("gpu_score")
        battery_score = device.get("battery_score")
        display_score = device.get("display_score")
        cam_or_stylus = device.get("camera_or_stylus_score")
        ram_gb = device.get("ram_gb")
        storage_gb = device.get("storage_gb")
        weight_kg = device.get("weight_kg")

        elimination_reason = None

        # 1. Missing Critical Data Check
        if price is None or price <= 0:
            elimination_reason = "Eksik kritik veri: Fiyat bilgisi (price_try) veritabanında tanımsız veya geçersiz."
        elif cpu_score is None:
            elimination_reason = "Eksik kritik veri: İşlemci KDS puanı (cpu_score) eksik."
        elif gpu_score is None:
            elimination_reason = "Eksik kritik veri: Grafik işlemci KDS puanı (gpu_score) eksik."

        # 2. Budget Hard Constraint
        if not elimination_reason and budget > 0:
            if price > effective_max_price:
                diff = price - budget
                elimination_reason = (
                    f"Bütçe aşımı: Cihaz fiyatı {price:,.0f} TL; belirtilen {budget:,.0f} TL bütçeyi "
                    f"ve %{int(budget_tolerance*100)} toleransı aşmaktadır (+{diff:,.0f} TL)."
                )

        # 3. Category Specific Hard Constraints
        if not elimination_reason and category == "laptop":
            # Weight constraints
            if weight_bands:
                # Under 2.0 kg is lightweight
                if "hafif" in weight_bands and len(weight_bands) == 1:
                    if weight_kg is None or weight_kg >= 2.0:
                        elimination_reason = (
                            f"Taşınabilirlik kısıtı: Cihaz ağırlığı {weight_kg if weight_kg else '?'} kg; "
                            "sadece hafif (< 2.0 kg) tercihi nedeniyle elenmiştir."
                        )
                else:
                    # Check whether weight fits any chosen band
                    in_selected_band = False
                    if weight_kg is not None:
                        if "hafif" in weight_bands and weight_kg < 2.0:
                            in_selected_band = True
                        elif "orta" in weight_bands and 2.0 <= weight_kg <= 2.5:
                            in_selected_band = True
                        elif "agir" in weight_bands and weight_kg > 2.5:
                            in_selected_band = True
                    if not in_selected_band and len(weight_bands) < 3:
                        elimination_reason = (
                            f"Ağırlık kısıtı: Cihaz ağırlığı {weight_kg if weight_kg else '?'} kg; "
                            f"seçilen ağırlık aralıklarına ({', '.join(weight_bands)}) uymamaktadır."
                        )

            # Purpose constraints
            if not elimination_reason:
                # Both Gaming + Software Dev Intersection Check
                if "oyun" in purposes and "yazilim" in purposes:
                    if (ram_gb or 0) < 16:
                        elimination_reason = f"RAM {ram_gb or 0} GB; Oyun ve Yazılım Geliştirme kesişimi için en az 16 GB RAM zorunludur."
                    elif (storage_gb or 0) < 512:
                        elimination_reason = f"Depolama {storage_gb or 0} GB; Oyun ve geliştirme ortamları için en az 512 GB gereklidir."
                    elif cpu_score < 70:
                        elimination_reason = f"CPU puanı {cpu_score}/100; Oyun ve yazılım derleme gereksinimini karşılamıyor (En az 70 CPU puanı gerekir)."
                    elif gpu_score < 65:
                        elimination_reason = f"GPU puanı {gpu_score}/100; Oyun donanım barajını karşılamıyor (En az 65 GPU puanı gerekir)."

                # Gaming standalone constraints
                elif "oyun" in purposes:
                    if (ram_gb or 0) < 16:
                        elimination_reason = f"RAM {ram_gb or 0} GB; Oyun kriterini karşılamadığı için sert kısıtla elendi (En az 16 GB RAM gerekli)."
                    elif gpu_score < 65:
                        elimination_reason = f"GPU puanı {gpu_score}/100; Oyun için yetersiz grafik gücü (En az 65 GPU puanı gerekli)."
                    elif (storage_gb or 0) < 512:
                        elimination_reason = f"Depolama {storage_gb or 0} GB; Modern oyun kurulumları için en az 512 GB depolama gerekli."

                # Software Dev standalone constraints
                elif "yazilim" in purposes:
                    if (ram_gb or 0) < 16:
                        elimination_reason = f"RAM {ram_gb or 0} GB; Yazılım geliştirme ve emülasyon için en az 16 GB RAM önerilir/zorunludur."
                    elif cpu_score < 70:
                        elimination_reason = f"CPU puanı {cpu_score}/100; Yazılım derleme ve çoklu iş parçacığı için en az 70 CPU puanı gereklidir."
                    elif (storage_gb or 0) < 512:
                        elimination_reason = f"Depolama {storage_gb or 0} GB; SDK ve konteyner ortamları için en az 512 GB depolama gerekli."

                # Graphic Design constraints
                elif "grafik" in purposes:
                    if display_score < 75:
                        elimination_reason = f"Ekran puanı {display_score}/100; Grafik tasarım için yüksek renk doğruluğu ve panel kalitesi (≥75) gereklidir."
                    elif (ram_gb or 0) < 16:
                        elimination_reason = f"RAM {ram_gb or 0} GB; Grafik ve görsel düzenleme için en az 16 GB RAM gereklidir."

        if elimination_reason:
            eliminated_record = dict(device)
            eliminated_record["reason"] = elimination_reason
            eliminated_record["elimination_type"] = "hard_constraint"
            eliminated_record["google_link"] = build_google_search_link(brand, model)
            eliminated.append(eliminated_record)
            continue

        # 4. Multi-Criteria Scoring (WSM - Weighted Sum Model)
        price_utility = calculate_price_utility(price, budget, budget_tolerance)

        if category == "laptop":
            portability_val = calculate_portability_score(weight_kg)
            ram_val = calculate_ram_score(ram_gb)
            w_score = (
                weights.get("cpu", 0.0) * cpu_score +
                weights.get("gpu", 0.0) * gpu_score +
                weights.get("ram", 0.0) * ram_val +
                weights.get("display", 0.0) * display_score +
                weights.get("battery", 0.0) * battery_score +
                weights.get("portability", 0.0) * portability_val +
                weights.get("price", 0.0) * price_utility
            )
        elif category == "phone":
            w_score = (
                weights.get("cpu", 0.0) * cpu_score +
                weights.get("camera", 0.0) * (cam_or_stylus or 50) +
                weights.get("battery", 0.0) * battery_score +
                weights.get("display", 0.0) * display_score +
                weights.get("price", 0.0) * price_utility
            )
        elif category == "tablet":
            w_score = (
                weights.get("display", 0.0) * display_score +
                weights.get("stylus_or_cam", 0.0) * (cam_or_stylus or 50) +
                weights.get("cpu", 0.0) * cpu_score +
                weights.get("battery", 0.0) * battery_score +
                weights.get("price", 0.0) * price_utility
            )
        else:
            w_score = price_utility

        suitability_score = round(max(0.0, min(100.0, w_score)), 1)

        # 5. 60% Threshold Check (Baraj)
        if suitability_score < 60.0:
            eliminated_record = dict(device)
            eliminated_record["suitability_score"] = suitability_score
            eliminated_record["reason"] = f"Uygunluk puanı %{suitability_score:.1f}; %60 barajının altında kaldı."
            eliminated_record["elimination_type"] = "score_below_threshold"
            eliminated_record["google_link"] = build_google_search_link(brand, model)
            eliminated.append(eliminated_record)
        else:
            qualified_record = dict(device)
            qualified_record["suitability_score"] = suitability_score
            qualified_record["price_utility"] = price_utility
            qualified_record["rationale"] = generate_recommendation_rationale(
                device, category, purposes, suitability_score, budget
            )
            qualified_record["google_link"] = build_google_search_link(brand, model)
            recommended.append(qualified_record)

    # Sort recommended descending by suitability_score
    recommended.sort(key=lambda x: x["suitability_score"], reverse=True)

    return {
        "category": category,
        "budget": budget,
        "purposes": purposes,
        "weight_bands": weight_bands,
        "total_evaluated": len(filtered_by_cat),
        "qualified_count": len(recommended),
        "eliminated_count": len(eliminated),
        "weights_used": weights,
        "hard_constraints_applied": hard_constraints_log,
        "recommended": recommended,
        "eliminated": eliminated
    }
