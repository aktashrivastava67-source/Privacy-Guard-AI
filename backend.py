import io
import re
import time
import hashlib
from typing import Any

import pandas as pd


# ==========================================================
# CONFIGURATION
# ==========================================================

SENSITIVE_COLUMN_PATTERNS = {
    "name": re.compile(
        r"(^|[_\s-])(full[_\s-]?name|first[_\s-]?name|"
        r"last[_\s-]?name|person[_\s-]?name|customer[_\s-]?name|"
        r"patient[_\s-]?name|employee[_\s-]?name|name)([_\s-]|$)",
        re.IGNORECASE,
    ),
    "email": re.compile(r"email|e-mail|mail_address", re.IGNORECASE),
    "phone": re.compile(
        r"phone|mobile|telephone|contact_number|phone_number",
        re.IGNORECASE,
    ),
    "address": re.compile(
        r"address|street_address|postal_address|home_address",
        re.IGNORECASE,
    ),
    "government_id": re.compile(
        r"aadhaar|aadhar|passport|ssn|social_security|"
        r"government_id|national_id|tax_id",
        re.IGNORECASE,
    ),
    "financial": re.compile(
        r"credit_card|card_number|bank_account|account_number|"
        r"iban|cvv|financial_id",
        re.IGNORECASE,
    ),
    "date_of_birth": re.compile(
        r"date_of_birth|dob|birth_date|birthday",
        re.IGNORECASE,
    ),
}

PATTERN_RULES = {
    "Email address": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "Phone number": re.compile(
        r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)"
    ),
    "Possible Aadhaar-like number": re.compile(
        r"(?<!\d)(?:\d[ -]?){11}\d(?!\d)"
    ),
    "IP address": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ),
}


# ==========================================================
# FILE READING
# ==========================================================

def load_dataset(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    Load CSV or Excel data from uploaded file bytes.
    """

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    extension = filename.lower().rsplit(".", 1)[-1]

    try:
        if extension == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))

        elif extension in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes))

        else:
            raise ValueError(
                "Unsupported file format. Upload CSV, XLSX, or XLS."
            )

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            "Could not read this file. Check its format and contents."
        ) from exc

    if df.empty:
        raise ValueError("The uploaded file contains no data rows.")

    if len(df.columns) == 0:
        raise ValueError("The file contains no columns.")

    if len(df) > 100_000 or len(df.columns) > 200:
        raise ValueError(
            "For this prototype, the maximum is 100,000 rows "
            "and 200 columns."
        )

    # Normalize column names and make duplicates unique.
    original_columns = [str(c).strip() for c in df.columns]
    unique_columns = []
    seen = {}

    for col in original_columns:
        count = seen.get(col, 0)
        seen[col] = count + 1

        unique_columns.append(
            col if count == 0 else f"{col}_{count + 1}"
        )

    df.columns = unique_columns

    return df


# ==========================================================
# AGENT 1: PRIVATE DATA DETECTION
# ==========================================================

def detect_sensitive_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Detect columns that appear sensitive from their names.
    """

    detected = {}

    for category, pattern in SENSITIVE_COLUMN_PATTERNS.items():
        matching = [
            str(col)
            for col in df.columns
            if pattern.search(str(col))
        ]

        if matching:
            detected[category] = matching

    return detected


def detect_private_patterns(df: pd.DataFrame) -> dict[str, int]:
    """
    Count common private-data patterns in textual cells.

    Counts are pattern matches, not unique people or records.
    """

    counts = {name: 0 for name in PATTERN_RULES}

    for col in df.columns:
        for value in df[col].dropna():

            # Only inspect string values.
            if not isinstance(value, str):
                continue

            for label, pattern in PATTERN_RULES.items():
                counts[label] += len(pattern.findall(value))

    return counts


# ==========================================================
# AGENT 2: ANONYMIZATION
# ==========================================================

def mask_text(value: Any) -> Any:
    """
    Mask common detectable private-data patterns in text.
    """

    if not isinstance(value, str):
        return value

    text = value

    replacements = [
        (PATTERN_RULES["Email address"], "[EMAIL_REDACTED]"),
        (PATTERN_RULES["Phone number"], "[PHONE_REDACTED]"),
        (
            PATTERN_RULES["Possible Aadhaar-like number"],
            "[ID_REDACTED]",
        ),
        (PATTERN_RULES["IP address"], "[IP_REDACTED]"),
    ]

    for pattern, replacement in replacements:
        text = pattern.sub(replacement, text)

    return text


def anonymize_dataset(
    df: pd.DataFrame,
    detected_columns: dict[str, list[str]],
    selected_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, int]:
    """
    Mask sensitive columns and common patterns in text fields.

    Returns:
        Protected dataframe and number of changed cells.
    """

    protected = df.copy(deep=True)

    all_detected = set()

    for columns in detected_columns.values():
        all_detected.update(columns)

    # If the user selected columns explicitly, use those.
    columns_to_mask = (
        set(selected_columns)
        if selected_columns is not None
        else all_detected
    )

    unknown_columns = columns_to_mask - set(protected.columns)

    if unknown_columns:
        raise ValueError(
            f"Unknown columns selected: {sorted(unknown_columns)}"
        )

    changed_cells = 0

    for col in protected.columns:

        for index, value in protected[col].items():

            if pd.isna(value):
                continue

            # Mask explicitly identified sensitive columns.
            if col in columns_to_mask:

                # Hash the original value only to generate a stable,
                # non-reversible-looking token. This is NOT encryption
                # or a formal anonymization guarantee.
                value_string = str(value)

                token = hashlib.sha256(
                    value_string.encode("utf-8")
                ).hexdigest()[:10]

                replacement = f"[{col.upper()}_{token}]"

                if value_string != replacement:
                    protected.at[index, col] = replacement
                    changed_cells += 1

            # Mask common patterns in all other text columns.
            elif isinstance(value, str):

                new_value = mask_text(value)

                if new_value != value:
                    protected.at[index, col] = new_value
                    changed_cells += 1

    return protected, changed_cells


# ==========================================================
# AGENT 3: VALIDATION
# ==========================================================

def validate_protected_data(
    protected: pd.DataFrame,
    masked_columns: list[str],
) -> dict[str, Any]:
    """
    Check for common patterns remaining in unmasked columns.
    """

    findings = {name: 0 for name in PATTERN_RULES}

    # Explicitly masked columns are skipped because their original
    # contents have been replaced.
    columns_to_check = [
        col for col in protected.columns
        if col not in masked_columns
    ]

    for col in columns_to_check:
        for value in protected[col].dropna():

            if not isinstance(value, str):
                continue

            for label, pattern in PATTERN_RULES.items():
                findings[label] += len(pattern.findall(value))

    total_findings = sum(findings.values())

    return {
        "remaining_pattern_counts": findings,
        "total_remaining_patterns": total_findings,
        "columns_checked": len(columns_to_check),
        "validation_status": (
            "No tested patterns detected"
            if total_findings == 0
            else "Potential sensitive patterns remain"
        ),
    }


# ==========================================================
# MULTI-AGENT PIPELINE AND PERFORMANCE MATRIX
# ==========================================================

def run_privacy_pipeline(
    df: pd.DataFrame,
    selected_columns: list[str] | None = None,
    agent_count: int = 3,
    coordination_cost_ms: float = 0.1,
) -> dict[str, Any]:
    """
    Run detection, anonymization, and validation.

    Agent execution is sequential in this prototype.
    Coordination overhead is modeled, not network-measured.
    """

    if not 3 <= agent_count <= 10:
        raise ValueError("Agent count must be between 3 and 10.")

    if coordination_cost_ms < 0:
        raise ValueError("Coordination cost cannot be negative.")

    rows = len(df)

    # Agent 1: detect potentially sensitive columns and patterns.
    start = time.perf_counter()

    detected_columns = detect_sensitive_columns(df)
    before_patterns = detect_private_patterns(df)

    detection_seconds = time.perf_counter() - start

    all_detected_columns = sorted({
        col
        for cols in detected_columns.values()
        for col in cols
    })

    columns_to_mask = (
        selected_columns
        if selected_columns is not None
        else all_detected_columns
    )

    # Agent 2: anonymize.
    start = time.perf_counter()

    protected, changed_cells = anonymize_dataset(
        df,
        detected_columns,
        columns_to_mask,
    )

    anonymization_seconds = time.perf_counter() - start

    # Agent 3: validate.
    start = time.perf_counter()

    validation = validate_protected_data(
        protected,
        columns_to_mask,
    )

    validation_seconds = time.perf_counter() - start

    measured_compute_seconds = (
        detection_seconds
        + anonymization_seconds
        + validation_seconds
    )

    # Additional agents are conceptual worker slots in this version.
    # We model the communication cost; we do not claim to execute
    # distributed agents or measure real network latency.
    modeled_messages = max(agent_count - 1, 0)

    coordination_seconds = (
        modeled_messages * coordination_cost_ms / 1000
    )

    total_seconds = (
        measured_compute_seconds + coordination_seconds
    )

    throughput = (
        rows / total_seconds
        if total_seconds > 0
        else 0
    )

    performance_matrix = pd.DataFrame([
        {
            "Agent": "Detection Agent",
            "Task": "Detect sensitive columns and patterns",
            "Records": rows,
            "Execution Time (ms)": round(
                detection_seconds * 1000, 3
            ),
            "Throughput (records/sec)": round(
                rows / detection_seconds
                if detection_seconds > 0 else 0,
                2,
            ),
            "Execution Type": "Measured local processing",
        },
        {
            "Agent": "Anonymization Agent",
            "Task": "Mask selected columns and text patterns",
            "Records": rows,
            "Execution Time (ms)": round(
                anonymization_seconds * 1000, 3
            ),
            "Throughput (records/sec)": round(
                rows / anonymization_seconds
                if anonymization_seconds > 0 else 0,
                2,
            ),
            "Execution Type": "Measured local processing",
        },
        {
            "Agent": "Validation Agent",
            "Task": "Check for remaining tested patterns",
            "Records": rows,
            "Execution Time (ms)": round(
                validation_seconds * 1000, 3
            ),
            "Throughput (records/sec)": round(
                rows / validation_seconds
                if validation_seconds > 0 else 0,
                2,
            ),
            "Execution Type": "Measured local processing",
        },
    ])

    return {
        "protected_df": protected,
        "detected_columns": detected_columns,
        "columns_to_mask": list(columns_to_mask),
        "before_patterns": before_patterns,
        "validation": validation,
        "changed_cells": changed_cells,
        "row_count": rows,
        "column_count": len(df.columns),
        "agent_count": agent_count,
        "modeled_messages": modeled_messages,
        "coordination_cost_ms_per_message": coordination_cost_ms,
        "detection_ms": detection_seconds * 1000,
        "anonymization_ms": anonymization_seconds * 1000,
        "validation_ms": validation_seconds * 1000,
        "measured_compute_ms": measured_compute_seconds * 1000,
        "coordination_ms": coordination_seconds * 1000,
        "total_ms": total_seconds * 1000,
        "throughput": throughput,
        "performance_matrix": performance_matrix,
    }