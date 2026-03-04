"""
governance_schema.py
====================

MongoDB Governance Gatekeeper for Credit Applications

This script applies a MongoDB JSON Schema validator to a collection so that governance
controls are enforced *at ingestion time* (i.e., before data is stored/used downstream).

What this supports:
- Governance-at-ingestion via JSON Schema validation (types, required fields, enums)
- Consent + lawful basis metadata capture (GDPR governance)
- Retention + erasure workflow metadata capture (storage limitation / right to erasure)
- Human oversight + override documentation fields (automated decision controls)
- Model/decision traceability metadata (versioning + record keeping)
- A dedicated `audit_trail` collection with indexes to support auditability

Notes:
- This is an academic governance implementation for a course project, not legal advice.
- JSON Schema validation in MongoDB is a *baseline*; you still need access controls,
  encryption, retention enforcement jobs, and organizational policies in production.

Usage:
  python governance_schema.py --uri mongodb://localhost:27017/ --db novacred_db --collection credit_applications
"""

from __future__ import annotations

import argparse
from typing import Any, Dict

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure


def build_validator() -> Dict[str, Any]:
    """
    Build a MongoDB JSON Schema validator for the credit applications collection.

    The validator enforces:
    - Core applicant and decision structure
    - PII fields as strings (enables consistent handling/protection)
    - Governance metadata fields for consent/retention/oversight/traceability
    """
    governance_metadata_schema: Dict[str, Any] = {
        "bsonType": "object",
        "properties": {
            # Consent + lawful basis
            "consent_status": {
                "bsonType": "string",
                "enum": ["granted", "withdrawn", "not_required", "unknown"],
                "description": "Consent state (if applicable) or unknown.",
            },
            "consent_timestamp": {"bsonType": "string", "description": "ISO timestamp when consent was captured/updated."},
            "lawful_basis": {
                "bsonType": "string",
                "description": "GDPR Art. 6 lawful basis label (e.g., contract, legitimate_interest).",
            },
            # Retention + erasure workflow
            "retention_policy": {"bsonType": "string", "description": "Retention policy identifier/name."},
            "retention_until": {"bsonType": "string", "description": "ISO date/time until which record may be retained."},
            "erasure_requested": {"bsonType": "bool", "description": "Whether a deletion/erasure request was received."},
            "erasure_request_timestamp": {"bsonType": "string", "description": "ISO timestamp when erasure was requested."},
            # Human oversight / review
            "human_review_required": {"bsonType": "bool"},
            "reviewed_by": {"bsonType": "string"},
            "review_timestamp": {"bsonType": "string"},
            "override_applied": {"bsonType": "bool"},
            "override_reason": {"bsonType": "string"},
            # Model + traceability
            "model_version": {"bsonType": "string"},
            "feature_snapshot_ref": {"bsonType": "string", "description": "Reference to stored feature snapshot or lineage artifact."},
            "decision_source": {"bsonType": "string", "enum": ["manual", "model", "hybrid"]},
        },
        "description": "Governance metadata for consent, retention, oversight, and traceability.",
    }

    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "applicant_info", "financials", "decision"],
            "properties": {
                "_id": {"bsonType": "string", "description": "Application ID must be a string"},
                "processing_timestamp": {"bsonType": "string", "description": "ISO timestamp for record processing"},
                "loan_purpose": {"bsonType": "string"},
                "applicant_info": {
                    "bsonType": "object",
                    "required": ["full_name", "email", "ssn", "ip_address", "date_of_birth"],
                    "properties": {
                        "full_name": {"bsonType": "string"},
                        "email": {
                            "bsonType": "string",
                            # Basic pattern; helpful as a gatekeeper check (not perfect RFC validation).
                            "pattern": r"^.+@.+\..+$",
                            "description": "Must be a valid email format",
                        },
                        "ssn": {
                            "bsonType": "string",
                            "description": "SSN must be a string for consistent PII tracking & protection",
                        },
                        "ip_address": {"bsonType": "string", "description": "Online identifier; store as string"},
                        "date_of_birth": {"bsonType": "string", "description": "DOB stored as string/ISO date"},
                        "gender": {"bsonType": "string", "description": "Protected attribute; handle with strict access controls"},
                        "zip_code": {"bsonType": "string"},
                    },
                },
                "financials": {
                    "bsonType": "object",
                    "properties": {
                        "annual_income": {"bsonType": ["double", "int", "long"]},
                        "credit_history_months": {"bsonType": ["double", "int", "long"]},
                        "debt_to_income": {"bsonType": ["double", "int", "long"]},
                        "savings_balance": {"bsonType": ["double", "int", "long"]},
                    },
                },
                "decision": {
                    "bsonType": "object",
                    "required": ["loan_approved"],
                    "properties": {
                        "loan_approved": {"bsonType": "bool"},
                        "rejection_reason": {"bsonType": "string"},
                        "approved_amount": {"bsonType": ["double", "int", "long"]},
                        "interest_rate": {"bsonType": ["double", "int", "long"]},
                    },
                },
                # Behavioral data can exist; enforce as array if present
                "spending_behavior": {"bsonType": ["array"]},
                "notes": {"bsonType": "string"},
                # Governance metadata (new)
                "governance_metadata": governance_metadata_schema,
            },
        }
    }


def ensure_audit_trail_collection(db) -> None:
    """
    Ensure `audit_trail` collection exists and has governance-friendly indexes.
    """
    if "audit_trail" not in db.list_collection_names():
        db.create_collection("audit_trail")

    coll = db["audit_trail"]
    coll.create_index([("timestamp_utc", 1)])
    coll.create_index([("run_id", 1)])
    coll.create_index([("application_id", 1)])
    coll.create_index([("action", 1)])


def apply_validator(mongo_uri: str, db_name: str, collection_name: str) -> None:
    """
    Create the collection with validator if it does not exist,
    otherwise update the validator using collMod.
    """
    client = MongoClient(mongo_uri)
    db = client[db_name]
    validator = build_validator()

    try:
        db.create_collection(collection_name, validator=validator)
        print(f"Created collection '{collection_name}' with governance validator.")
    except CollectionInvalid:
        # Collection already exists -> update validator
        try:
            db.command("collMod", collection_name, validator=validator)
            print(f"Updated collection '{collection_name}' with governance validator.")
        except OperationFailure as e:
            raise SystemExit(
                "Failed to update validator via collMod. "
                "Check MongoDB permissions and server version.\n"
                f"OperationFailure: {e}"
            ) from e

    ensure_audit_trail_collection(db)
    print("Ensured 'audit_trail' collection + indexes.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Apply MongoDB governance JSON schema validation for credit applications."
    )
    p.add_argument("--uri", default="mongodb://localhost:27017/", help="MongoDB connection URI")
    p.add_argument("--db", default="novacred_db", help="Database name")
    p.add_argument("--collection", default="credit_applications", help="Collection name")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    apply_validator(args.uri, args.db, args.collection)


if __name__ == "__main__":
    main()
