"""Customer Segment Intelligence Service for Udyam360.

Encapsulates segment profiles, priority features, category weights, and suitability
scoring for Micro Retail and Professional Offices without rigid name hardcoding.
"""

from typing import Dict, List, Optional, Any
from app.schemas.catalogue import Product
from app.schemas.business_profile import BusinessProfile, TargetSegmentEnum


SEGMENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    TargetSegmentEnum.MICRO_RETAIL.value: {
        "code": "micro",
        "display_name": "Micro Retail & Services",
        "description": "Kirana stores, neighbourhood pharmacies, salons, hardware, and small retail stores.",
        "archetypes": ["Kirana Store", "Pharmacy", "Salon", "Hardware Store", "Retail Shop", "Bakery"],
        "is_primary_target": True,
        "priority_features": [
            "Affordable internet (Fibre / 5G AirFiber)",
            "Business mobile connectivity for delivery/orders",
            "GST-ready POS & UPI digital billing",
            "Customer engagement via WhatsApp Business / SMS",
            "Shop surveillance & theft prevention via Cloud CCTV",
            "Customer Guest Wi-Fi",
        ],
        "category_priority": {
            "Connectivity": 0.35,
            "Cloud & Productivity": 0.25,
            "Communication": 0.20,
            "Security": 0.10,
            "IoT & Physical": 0.10,
        },
        "feature_keywords": ["airfiber", "pos", "billing", "cctv", "camera", "whatsapp", "sms", "fibre 100", "wi-fi", "postpaid 299"],
        "essential_min_products": ["P04", "P01"],  # Preferred broadband base
        "growth_boost_products": ["P19", "P15", "P23", "P07"],
        "premium_boost_products": ["P18", "P22", "P14"],
    },
    TargetSegmentEnum.PROFESSIONAL_OFFICE.value: {
        "code": "prof",
        "display_name": "Professional Offices",
        "description": "Medical clinics, CA firms, coaching institutes, law practices, and consultancies.",
        "archetypes": ["Clinic", "CA Firm", "Coaching Centre", "Legal Consultancy", "Architecture Firm", "Diagnostic Lab"],
        "is_primary_target": True,
        "priority_features": [
            "High-uptime fibre broadband with optional static IP",
            "Business email & office collaboration suite",
            "Encrypted cloud backup for sensitive client records",
            "Endpoint security & ransomware protection",
            "Cloud telephony / SIP / Toll-free lines",
            "Automatic 4G/5G failover for uninterrupted operations",
        ],
        "category_priority": {
            "Connectivity": 0.30,
            "Cloud & Productivity": 0.25,
            "Security": 0.20,
            "Communication": 0.15,
            "IoT & Physical": 0.10,
        },
        "feature_keywords": ["email", "office", "backup", "endpoint", "security", "firewall", "sip", "telephony", "static ip", "failover", "fibre 300", "fibre 100"],
        "essential_min_products": ["P01", "P02"],
        "growth_boost_products": ["P16", "P17", "P20", "P11", "P09"],
        "premium_boost_products": ["P12", "P13", "P21", "P18"],
    },
    TargetSegmentEnum.MULTI_SITE.value: {
        "code": "multi",
        "display_name": "Small Multi-site Businesses",
        "description": "Retail chains, distributed clinics, and multi-branch operations.",
        "is_primary_target": False,
        "priority_features": ["Managed SD-WAN", "Inter-site VPN", "Central billing", "Fleet tracking"],
    },
    TargetSegmentEnum.MANUFACTURING.value: {
        "code": "mfg",
        "display_name": "Small Manufacturers",
        "description": "Workshops, fabrication units, and small factories.",
        "is_primary_target": False,
        "priority_features": ["Internet Leased Line", "Machine IoT monitoring", "Managed firewall"],
    },
}


class SegmentService:
    """Provides segment intelligence, suitability scoring, and configuration."""

    def get_supported_segments(self) -> List[Dict[str, Any]]:
        """Return list of supported customer segments with preference profiles."""
        return list(SEGMENT_DEFINITIONS.values())

    def get_segment_info(self, segment_code: str) -> Optional[Dict[str, Any]]:
        """Retrieve segment specification by code."""
        return SEGMENT_DEFINITIONS.get(segment_code.lower())

    def identify_segment(self, profile: BusinessProfile) -> Dict[str, Any]:
        """Classify customer into a segment and report whether it fits the primary hackathon scope."""
        seg_code = profile.get_normalized_segment()
        info = SEGMENT_DEFINITIONS.get(seg_code)

        if not info:
            return {
                "segment_code": seg_code,
                "display_name": "Other / Unclassified SMB",
                "is_primary_target": False,
                "explanation": "Customer profile does not match primary target segments (Micro Retail or Professional Offices).",
            }

        return {
            "segment_code": seg_code,
            "display_name": info["display_name"],
            "is_primary_target": info.get("is_primary_target", False),
            "explanation": f"Classified under {info['display_name']} based on business type / segment profile.",
            "priority_features": info.get("priority_features", []),
        }

    def score_product_suitability(self, product: Product, segment_code: str) -> float:
        """Calculate a segment suitability multiplier from 0.0 to 1.0 for a given product."""
        seg_info = SEGMENT_DEFINITIONS.get(segment_code)
        if not seg_info:
            return 0.5  # Neutral baseline for general/unclassified SMBs

        score = 0.0

        # 1. Native Catalogue Target Segments mapping (0.50 max)
        if segment_code in product.target_segments:
            score += 0.50
        elif "all" in product.target_segments or len(product.target_segments) >= 3:
            score += 0.25

        # 2. Category Priority Weight (0.25 max)
        cat_priorities = seg_info.get("category_priority", {})
        cat_weight = cat_priorities.get(product.category, 0.15)
        score += cat_weight * 0.25

        # 3. Priority Feature / Keyword Alignment (0.25 max)
        keywords = seg_info.get("feature_keywords", [])
        combined_text = f"{product.product_name} {product.description} {product.category}".lower()
        matched_kw = sum(1 for kw in keywords if kw in combined_text)
        if matched_kw > 0:
            score += min(0.25, matched_kw * 0.10)

        return min(1.0, round(score, 3))

    def explain_suitability(self, product: Product, segment_code: str) -> str:
        """Generate human-readable explanation of why this product fits the segment."""
        seg_info = SEGMENT_DEFINITIONS.get(segment_code)
        seg_name = seg_info["display_name"] if seg_info else "general businesses"

        if segment_code == TargetSegmentEnum.MICRO_RETAIL.value:
            if "pos" in product.product_name.lower():
                return f"Essential for {seg_name} to automate counter sales, UPI payments, and GST invoicing."
            if "cctv" in product.product_name.lower():
                return f"Provides 24/7 store surveillance and theft protection for {seg_name} premises."
            if "airfiber" in product.product_name.lower() or "fibre 100" in product.product_name.lower():
                return f"Provides affordable high-speed connectivity to power billing terminals and customer Wi-Fi in {seg_name}."
            if "whatsapp" in product.product_name.lower() or "sms" in product.product_name.lower():
                return f"Enables direct promotional outreach and automated order notifications to local customers."
            if "wi-fi" in product.product_name.lower():
                return f"Allows offering separated, secure guest Wi-Fi for visiting retail customers."
            if "website" in product.product_name.lower():
                return f"Establishes a local digital storefront and Google search presence for {seg_name}."

        if segment_code == TargetSegmentEnum.PROFESSIONAL_OFFICE.value:
            if "fibre" in product.product_name.lower():
                return f"Delivers high-reliability, low-latency broadband essential for {seg_name} operations."
            if "email" in product.product_name.lower():
                return f"Provides professional custom-domain email and office collaboration suite for staff."
            if "backup" in product.product_name.lower():
                return f"Secures sensitive client files, financial records, and medical histories with automatic cloud backup."
            if "security" in product.product_name.lower() or "firewall" in product.product_name.lower():
                return f"Protects office workstations from ransomware, malware, and client data breaches."
            if "sip" in product.product_name.lower() or "telephony" in product.product_name.lower() or "toll-free" in product.product_name.lower():
                return f"Provides professional multi-line phone handling with IVR call routing for clients."
            if "failover" in product.product_name.lower():
                return f"Ensures continuous zero-downtime internet for critical office workflows."

        return f"Meets operational requirements for {seg_name} in category '{product.category}'."


segment_service = SegmentService()

