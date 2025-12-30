import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ImprovedOCRService:
    def __init__(self, tesseract_cmd: Optional[str] = None, lang: str = 'eng'):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.lang = lang

    # -------------------------
    # High-level extraction API
    # -------------------------
    def extract_receipt_data(self, image_path: str) -> Dict[str, Optional[str]]:
        try:
            src = cv2.imread(image_path)
            if src is None:
                logger.error("Could not read image: %s", image_path)
                return self._empty_result("Could not read image")

            img_pre = self._preprocess_for_ocr(src)

            # 1) Do a full OCR (for dates, labels, currency words)
            full_text, full_lines = self._ocr_full_text(img_pre)

            # 2) Do a numeric-focused OCR (for amounts) with whitelist config
            numeric_text, numeric_lines = self._ocr_numeric(img_pre)

            # 3) Extract fields using line-aware heuristics + confidences
            amount, amount_conf = self._extract_amount_from_lines(numeric_lines, full_lines)
            date, date_conf = self._extract_date_from_lines(full_lines)
            currency = self._extract_currency(full_text + "\n" + numeric_text)

            # Compose confidence (simple normalization)
            confidence = round((amount_conf * 0.6) + (date_conf * 0.4), 2)

            logger.info("Result -> amount=%s currency=%s date=%s conf=%s",
                        amount, currency, date, confidence)

            return {
                "amount": amount,
                "date": date,
                "currency": currency,
                "confidence": confidence
            }

        except Exception as e:
            logger.exception("OCR extraction failed")
            return self._empty_result(str(e))

    # -------------------------
    # Preprocessing helpers
    # -------------------------
    def _preprocess_for_ocr(self, src: np.ndarray) -> np.ndarray:
        """
        Steps:
        - convert to gray
        - resize (scale up small images)
        - denoise (bilateral)
        - gamma correction
        - CLAHE (contrast)
        - sharpen
        - final mild adaptive thresholding for some passes (we keep the grayscale)
        """
        # Convert to gray
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

        # Resize: make width around 1000-1400 px for better OCR (if smaller)
        h, w = gray.shape[:2]
        target_w = 1200
        if w < target_w:
            scale = target_w / w
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        # Denoise
        denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

        # Gamma correction to brighten dim images
        gamma = 1.0
        mean = denoised.mean()
        if mean < 100:
            gamma = 1.4
        elif mean > 200:
            gamma = 0.9
        denoised = self._adjust_gamma(denoised, gamma)

        # CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Sharpen
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpen = cv2.filter2D(enhanced, -1, kernel)

        # Optional deskew: compute angle using edges / contours if strongly rotated (safe fallback)
        try:
            deskewed = self._deskew_if_needed(sharpen)
        except Exception:
            deskewed = sharpen

        # Return grayscale ready for OCR
        return deskewed

    def _adjust_gamma(self, image: np.ndarray, gamma: float) -> np.ndarray:
        inv = 1.0 / float(gamma)
        table = np.array([((i / 255.0) ** inv) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)

    def _deskew_if_needed(self, gray: np.ndarray) -> np.ndarray:
        # Use image moments on edges to estimate rotation angle
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=20)
        angles = []
        if lines is not None:
            for l in lines:
                x1, y1, x2, y2 = l[0]
                ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
                angles.append(ang)
        if not angles:
            return gray
        median_ang = np.median(angles)
        if abs(median_ang) < 1.0:
            return gray
        # rotate to negate median_ang
        (h, w) = gray.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), median_ang, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    # -------------------------
    # OCR passes
    # -------------------------
    def _ocr_full_text(self, gray: np.ndarray) -> Tuple[str, List[Tuple[str, float]]]:
        """
        Full-page OCR: returns the whole text and list of (line_text, avg_confidence)
        """
        pil = Image.fromarray(gray)
        config = f'--oem 3 --psm 3'  # full automatic
        data = pytesseract.image_to_data(pil, lang=self.lang, config=config, output_type=pytesseract.Output.DICT)

        lines = self._assemble_lines_from_data(data)
        full_text = "\n".join([ln for ln, _ in lines])
        return full_text, lines

    def _ocr_numeric(self, gray: np.ndarray) -> Tuple[str, List[Tuple[str, float]]]:
        """
        Numeric-optimized OCR: we whitelist digits, punctuation and currency symbols to improve numeric extraction.
        Returns text and lines with confidences.
        """
        pil = Image.fromarray(gray)
        # whitelist: digits, comma, dot, currency symbols, slash, hyphen, colon (for date)
        whitelist = '0123456789.,$₹€£:/-'
        # keep letters small for date words? We want to allow month names on full pass so numeric pass is narrow
        config = f'--oem 3 --psm 6 -c tessedit_char_whitelist={whitelist}'

        data = pytesseract.image_to_data(pil, lang=self.lang, config=config, output_type=pytesseract.Output.DICT)
        lines = self._assemble_lines_from_data(data)
        text = "\n".join([ln for ln, _ in lines])
        return text, lines

    def _assemble_lines_from_data(self, data: dict) -> List[Tuple[str, float]]:
        """
        Convert pytesseract.image_to_data output (dict) to list of (line_text, avg_confidence),
        preserving the reading order using block_num, par_num, line_num.
        """
        n = len(data['level'])
        grouped = {}
        # group by (block_num, par_num, line_num)
        for i in range(n):
            block = data['block_num'][i]
            par = data['par_num'][i]
            line = data['line_num'][i]
            key = (block, par, line)
            text = data['text'][i].strip()
            conf = float(data['conf'][i]) if data['conf'][i] != '-1' else -1.0
            grouped.setdefault(key, []).append((text, conf))

        # build ordered lines
        ordered_keys = sorted(grouped.keys())
        lines_out = []
        for key in ordered_keys:
            parts = [t for t, c in grouped[key] if t]
            confs = [c for t, c in grouped[key] if c >= 0]
            if not parts:
                continue
            line_text = " ".join(parts)
            avg_conf = float(sum(confs)) / len(confs) if confs else 0.0
            lines_out.append((line_text, round(avg_conf, 2)))
        return lines_out

    # -------------------------
    # Field extraction logic
    # -------------------------
    def _extract_amount_from_lines(self, numeric_lines: List[Tuple[str, float]],
                                   full_lines: List[Tuple[str, float]]) -> Tuple[Optional[str], float]:
        """
        Heuristic:
        1) Search lines with keywords (total, amount, grand total, balance due, net) in full_lines.
           If found, try parse numeric in same line or numeric_lines at similar text.
        2) If none, find highest numeric-looking token across numeric_lines with good confidence.
        3) Return string amount and a normalized confidence (0-100).
        """
        keyword_patterns = [
            r'\b(total|amount due|amount|grand total|balance due|amt paid|net total|subtotal|paid)\b'
        ]
        # compile
        keyword_re = re.compile("|".join(keyword_patterns), flags=re.I)

        def find_numbers(s: str) -> List[str]:
            # find numbers like 1,234.56 or 123.45 or 1234
            candidates = re.findall(r'[\$₹€£]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)', s)
            cleaned = [c.replace(',', '') for c in candidates]
            return cleaned

        # 1) keyword lines in full_lines
        for idx, (ln, conf) in enumerate(full_lines):
            if keyword_re.search(ln):
                nums = find_numbers(ln)
                if nums:
                    # pick largest valid number
                    best = self._pick_best_amount(nums)
                    amount_str = self._format_amount_str(best)
                    # confidence incorporate line OCR conf (0-100) -> map to 0-1
                    conf_score = min(1.0, conf / 100.0 + 0.5)  # keyword line boosts confidence
                    return amount_str, round(conf_score * 100, 2)

        # 2) try numeric_lines scanning for common currency tokens or large values
        numeric_candidates = []
        for ln, conf in numeric_lines:
            nums = find_numbers(ln)
            if nums:
                for n in nums:
                    numeric_candidates.append((n, conf, ln))

        if numeric_candidates:
            # prefer tokens with higher OCR confidence and larger numeric value (likely total)
            def score_candidate(item):
                n_str, conf, ln = item
                try:
                    val = float(n_str)
                except Exception:
                    val = 0.0
                return (val, conf)

            numeric_candidates.sort(key=score_candidate, reverse=True)
            best_num, best_conf, best_line = numeric_candidates[0]
            # normalize conf (0-100)
            conf_score = min(1.0, best_conf / 100.0 + 0.2)
            return self._format_amount_str(best_num), round(conf_score * 100, 2)

        # 3) fallback: None
        return None, 0.0

    def _pick_best_amount(self, nums: List[str]) -> Optional[str]:
        if not nums:
            return None
        try:
            # choose the highest numeric value (but ignore improbable extremes)
            parsed = []
            for n in nums:
                try:
                    v = float(n)
                    if 0.01 <= v <= 10_000_000:
                        parsed.append((v, n))
                except:
                    continue
            parsed.sort(reverse=True)
            return parsed[0][1] if parsed else nums[0]
        except Exception:
            return nums[0]

    def _format_amount_str(self, raw: Optional[str]) -> Optional[str]:
        if raw is None:
            return None
        # try to normalize to 2 decimal places string
        try:
            v = float(raw)
            return f"{v:.2f}"
        except:
            # remove stray characters
            cleaned = re.sub(r'[^\d\.]', '', raw)
            try:
                v = float(cleaned)
                return f"{v:.2f}"
            except:
                return raw

    # -------------------------
    # Date extraction
    # -------------------------
    def _extract_date_from_lines(self, lines: List[Tuple[str, float]]) -> Tuple[Optional[str], float]:
        """
        Search lines for date patterns, prioritize lines containing 'date' or 'invoice' etc.
        Return ISO date string and confidence (0-100)
        """
        keywords_re = re.compile(r'\b(date|invoice date|due date|paid on|bill date|txn date|transaction)\b', flags=re.I)
        # scan lines first for keyword lines
        for ln, conf in lines:
            if keywords_re.search(ln):
                found = self._search_date_in_text(ln)
                if found:
                    # use OCR line confidence as proxy
                    return found, round(min(1.0, conf / 100.0 + 0.3) * 100, 2)

        # otherwise search all lines (higher chance)
        best_date = None
        best_conf = 0.0
        for ln, conf in lines:
            found = self._search_date_in_text(ln)
            if found:
                # estimate confidence from conf and prefer earlier found ones
                score = min(1.0, conf / 100.0 + 0.1)
                if score > best_conf:
                    best_conf = score
                    best_date = found
        if best_date:
            return best_date, round(best_conf * 100, 2)
        return None, 0.0

    def _search_date_in_text(self, text: str) -> Optional[str]:
        """
        Try many regex patterns and parsing attempts; return ISO 'YYYY-MM-DD' if found & plausible.
        """
        t = text.strip()
        t = t.replace('.', '/').replace('-', '/')
        # Patterns to try (order matters)
        patterns = [
            # 2024/12/31 or 2024/12/31
            r'(?P<y>\d{4})[\/](?P<m>\d{1,2})[\/](?P<d>\d{1,2})',
            # 31/12/2024 or 31/12/24
            r'(?P<d>\d{1,2})[\/](?P<m>\d{1,2})[\/](?P<y>\d{2,4})',
            # 15 Jan 2024
            r'(?P<d>\d{1,2})\s+(?P<M>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(?P<y>\d{4})',
            # Jan 15 2024 or January 15, 2024
            r'(?P<M>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(?P<d>\d{1,2})(?:,)?\s+(?P<y>\d{4})',
            # mm/dd/yyyy (US style)
            r'(?P<m>\d{1,2})[\/](?P<d>\d{1,2})[\/](?P<y>\d{2,4})',
        ]
        for pat in patterns:
            m = re.search(pat, t, flags=re.I)
            if not m:
                continue
            gd = m.groupdict()
            try:
                y = int(gd.get('y')) if gd.get('y') else None
                mth = gd.get('m')
                d = gd.get('d')
                if gd.get('M'):
                    # month name
                    mon_name = gd['M'][:3].title()
                    m_num = datetime.strptime(mon_name, '%b').month
                else:
                    m_num = int(mth)
                d_num = int(d)
                # fix two-digit year
                if y is not None and y < 100:
                    y += 2000 if y < 50 else 1900
                elif y is None:
                    y = datetime.now().year
                parsed = datetime(year=y, month=m_num, day=d_num)
                # plausibility: between year 2000 and today
                now = datetime.now()
                if 1999 < parsed.year <= now.year and parsed <= now:
                    return parsed.strftime('%Y-%m-%d')
            except Exception:
                continue
        return None

    # -------------------------
    # Currency detection
    # -------------------------
    def _extract_currency(self, text: str) -> Optional[str]:
        t = text.upper()
        mapping = {
            'USD': ['$', 'USD', 'US DOLLAR'],
            'EUR': ['€', 'EUR', 'EURO'],
            'GBP': ['£', 'GBP', 'POUND'],
            'INR': ['₹', 'INR', 'RS', 'RUPEE']
        }
        for code, tokens in mapping.items():
            for tok in tokens:
                if tok in t:
                    return code
        # fallback: None (don't default silently)
        return None

    # -------------------------
    # utilities
    # -------------------------
    def _empty_result(self, error: Optional[str] = None) -> Dict:
        return {"amount": None, "date": None, "currency": None, "error": error}

# app/services/ocr_service.py

try:
    from app.config import settings  # or wherever your settings live
    _TESSERACT_CMD = settings.TESSERACT_CMD
except Exception:
    _TESSERACT_CMD = None

ocr_service = ImprovedOCRService(tesseract_cmd=_TESSERACT_CMD)
