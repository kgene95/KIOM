#!/usr/bin/env python3
"""Validate structural completion of a network-pharmacology run directory."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from traceability import validate_traceability


REQUIRED = [
    "NP_checkpoint.md",
    "job_ledger.csv",
    "compound_identity.csv",
    "compound_targets.csv",
    "disease_targets.csv",
    "overlap_primary.csv",
    "branch_registry.csv",
    "PPI_results.csv",
    "enrichment_results.csv",
    "mapping_corrections.csv",
    "NP_manifest.json",
]


def csv_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def unique_genes(path):
    """Read a canonical gene table without assuming one project-specific schema."""
    rows = csv_rows(path)
    if not rows:
        return set()
    fields = rows[0].keys()
    gene_field = next((name for name in ("gene", "gene_symbol", "normalized_gene") if name in fields), None)
    if not gene_field:
        raise ValueError("no gene/gene_symbol/normalized_gene column")
    genes = set()
    for row in rows:
        if "included" in row and (row.get("included") or "").strip().casefold() not in {"true", "1", "yes"}:
            continue
        gene = (row.get(gene_field) or "").strip().upper()
        if gene:
            genes.add(gene)
    return genes


def semicolon_set(value):
    return {item.strip().upper() for item in str(value or "").split(";") if item.strip()}


def utc_datetime(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("blank timestamp")
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must include UTC offset")
    return parsed


def validate_v5_metadata(manifest):
    problems = []
    timestamps = {}
    for field in ("analysis_started_utc", "analysis_completed_utc"):
        try:
            timestamps[field] = utc_datetime(manifest.get(field))
        except (TypeError, ValueError):
            problems.append(f"contract v5 manifest requires valid UTC {field}")
    if len(timestamps) == 2 and timestamps["analysis_completed_utc"] < timestamps["analysis_started_utc"]:
        problems.append("analysis_completed_utc precedes analysis_started_utc")

    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict) or not all(runtime.get(k) for k in ("python", "platform")):
        problems.append("contract v5 manifest requires runtime.python and runtime.platform")

    inventories = (
        ("software_inventory", ("name", "version", "role")),
        ("database_inventory", ("name", "release_or_version", "access_date")),
    )
    for field, required in inventories:
        rows = manifest.get(field)
        if not isinstance(rows, list) or not rows:
            problems.append(f"contract v5 manifest requires nonempty {field}")
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or any(not str(row.get(k) or "").strip() for k in required):
                problems.append(f"{field} row {index}: missing {', '.join(required)}")
    parameters = manifest.get("analysis_parameters")
    if not isinstance(parameters, dict) or not parameters:
        problems.append("contract v5 manifest requires nonempty analysis_parameters")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    root = args.run_dir.resolve()

    problems = []
    manifest = {}
    contract_version = 0
    for name in REQUIRED:
        path = root / name
        if not path.is_file():
            problems.append(f"missing: {name}")
        elif path.stat().st_size == 0:
            problems.append(f"empty: {name}")

    manifest_path = root / "NP_manifest.json"
    if manifest_path.is_file() and manifest_path.stat().st_size:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            problems.append(f"invalid NP_manifest.json: {exc}")
            manifest = {}
        if manifest.get("status") != "NP_COMPLETE_DOCKING_NOT_STARTED":
            problems.append("manifest status must be NP_COMPLETE_DOCKING_NOT_STARTED")
        broad_first = manifest.get("workflow_strategy") == "BROAD_FIRST_ADAPTIVE_NARROWING"
        try:
            contract_version = int(manifest.get("contract_version", 0))
        except (TypeError, ValueError):
            problems.append("manifest contract_version must be an integer")
            contract_version = 0
        if broad_first:
            for name in ("broad_target_pool.csv", "narrowing_audit.csv"):
                path = root / name
                if not path.is_file():
                    problems.append(f"broad-first run missing: {name}")
                elif path.stat().st_size == 0:
                    problems.append(f"broad-first run empty: {name}")
        if contract_version >= 3:
            v3_files = {
                *REQUIRED, "NP_checkpoint.json", "broad_target_pool.csv",
                "narrowing_audit.csv", "docking_candidate_handoff.csv",
            }
            for name in sorted(v3_files):
                path = root / name
                if not path.is_file() or path.stat().st_size == 0:
                    problems.append(f"contract v3 run missing or empty: {name}")
            listed = set(manifest.get("files", []))
            missing_listed = v3_files - listed
            if missing_listed:
                problems.append(
                    f"contract v3 manifest files missing: {', '.join(sorted(missing_listed))}"
                )
        if contract_version >= 4:
            availability = root / "source_availability.csv"
            if not availability.is_file() or availability.stat().st_size == 0:
                problems.append("contract v4 run missing or empty: source_availability.csv")
            if "source_availability.csv" not in set(manifest.get("files", [])):
                problems.append("contract v4 manifest files missing: source_availability.csv")
        if contract_version >= 5:
            problems.extend(validate_v5_metadata(manifest))
        if contract_version >= 6:
            listed = set(manifest.get("files", []))
            enrichment_qc = root / "enrichment_qc.json"
            if not enrichment_qc.is_file() or enrichment_qc.stat().st_size == 0:
                problems.append("contract v6 run missing or empty: enrichment_qc.json")
            elif "enrichment_qc.json" not in listed:
                problems.append("contract v6 manifest files missing: enrichment_qc.json")
            params = manifest.get("analysis_parameters") if isinstance(manifest.get("analysis_parameters"), dict) else {}
            for flag in ("cytoscape_used", "hub_robustness_performed"):
                if flag not in params or not isinstance(params.get(flag), bool):
                    problems.append(f"contract v6 analysis_parameters requires boolean {flag}")
            if params.get("cytoscape_used"):
                path = root / "cytoscape_automation.json"
                if not path.is_file() or path.stat().st_size == 0:
                    problems.append("contract v6 Cytoscape run missing or empty: cytoscape_automation.json")
                elif "cytoscape_automation.json" not in listed:
                    problems.append("contract v6 manifest files missing: cytoscape_automation.json")
            if params.get("hub_robustness_performed"):
                path = root / "hub_robustness.csv"
                if not path.is_file() or path.stat().st_size == 0:
                    problems.append("contract v6 robustness run missing or empty: hub_robustness.csv")
                elif "hub_robustness.csv" not in listed:
                    problems.append("contract v6 manifest files missing: hub_robustness.csv")
        if contract_version >= 7:
            if manifest.get("source_archive_policy_version") != 2:
                problems.append("contract v7 requires source_archive_policy_version=2")
            problems.extend(validate_traceability(root, manifest))
        branches = manifest.get("branches")
        if contract_version >= 3 and (not isinstance(branches, dict) or not branches):
            problems.append("contract v3 run requires a nonempty branches object")
        if branches is not None:
            if not isinstance(branches, dict) or not branches:
                problems.append("manifest branches must be a nonempty object")
            else:
                valid_classes = {"primary", "sensitivity", "broad_exploratory", "proxy"}
                valid_status = {"PENDING", "FAILED", "COMPLETED"}
                completed_primary = 0
                broad_branches = 0
                for branch_id, branch in branches.items():
                    if not isinstance(branch, dict):
                        problems.append(f"branch {branch_id}: definition must be an object")
                        continue
                    if branch.get("class") not in valid_classes:
                        problems.append(f"branch {branch_id}: invalid class {branch.get('class')!r}")
                    if branch.get("class") == "primary" and str(branch.get("status") or "").split("_", 1)[0] == "COMPLETED":
                        completed_primary += 1
                    if branch.get("class") == "broad_exploratory":
                        broad_branches += 1
                    status = str(branch.get("status") or "")
                    if status.split("_", 1)[0] not in valid_status:
                        problems.append(f"branch {branch_id}: invalid status {status!r}")
                    genes = [str(gene).strip().upper() for gene in branch.get("genes", []) if str(gene).strip()]
                    if len(genes) != len(set(genes)):
                        problems.append(f"branch {branch_id}: genes contains duplicates")
                    expected = branch.get("gene_count")
                    if expected is not None and expected != len(genes):
                        problems.append(f"branch {branch_id}: gene_count does not match genes")
                    exact_file = branch.get("exact_gene_file")
                    if status.split("_", 1)[0] == "COMPLETED" and not exact_file:
                        problems.append(f"branch {branch_id}: completed branch lacks exact_gene_file")
                    if exact_file:
                        path = root / exact_file
                        if not path.is_file() or path.stat().st_size == 0:
                            problems.append(f"branch {branch_id}: exact_gene_file missing or empty: {exact_file}")
                        else:
                            try:
                                file_genes = unique_genes(path)
                            except ValueError as exc:
                                problems.append(f"branch {branch_id}: {exact_file}: {exc}")
                            else:
                                if set(genes) != file_genes:
                                    problems.append(f"branch {branch_id}: manifest genes do not match {exact_file}")
                if (broad_first or contract_version >= 3) and completed_primary != 1:
                    problems.append("run must have exactly one completed primary/final branch")
                if broad_first and broad_branches < 1:
                    problems.append("broad-first run must retain at least one broad_exploratory branch")
        else:
            primary = manifest.get("primary_genes", [])
            sensitivity = manifest.get("sensitivity_candidate_genes", [])
            if len(primary) != len(set(primary)):
                problems.append("primary_genes contains duplicates")
            if len(sensitivity) != len(set(sensitivity)):
                problems.append("sensitivity_candidate_genes contains duplicates")
            expected_primary = manifest.get("counts", {}).get("primary", {}).get("overlap")
            if expected_primary is not None and expected_primary != len(primary):
                problems.append("primary overlap count does not match primary_genes")
        for name in manifest.get("files", []):
            path = root / name
            if not path.is_file() or path.stat().st_size == 0:
                problems.append(f"manifest file missing or empty: {name}")

    ledger_path = root / "job_ledger.csv"
    if ledger_path.is_file() and ledger_path.stat().st_size:
        rows = csv_rows(ledger_path)
        valid = {"PENDING", "FAILED", "COMPLETED"}
        for index, row in enumerate(rows, 2):
            base = (row.get("status") or "").split("_", 1)[0]
            if base not in valid:
                problems.append(f"job_ledger.csv line {index}: invalid status {row.get('status')!r}")

    registry_by_id = {}
    registry_path = root / "branch_registry.csv"
    if registry_path.is_file() and registry_path.stat().st_size:
        rows = csv_rows(registry_path)
        required = {
            "branch_id", "branch_class", "parent_branch", "purpose", "compound_rule",
            "disease_rule", "sources", "cutoffs", "species", "mapping_state",
            "gene_count", "exact_gene_file", "status", "permitted_interpretation", "created_utc",
        }
        if not rows:
            problems.append("branch_registry.csv has no branch rows")
        else:
            missing = required - set(rows[0])
            if missing:
                problems.append(f"branch_registry.csv missing columns: {', '.join(sorted(missing))}")
            seen = set()
            valid_classes = {"primary", "sensitivity", "broad_exploratory", "proxy"}
            valid_status = {"PENDING", "FAILED", "COMPLETED"}
            for index, row in enumerate(rows, 2):
                branch_id = (row.get("branch_id") or "").strip()
                if not branch_id:
                    problems.append(f"branch_registry.csv line {index}: blank branch_id")
                elif branch_id in seen:
                    problems.append(f"branch_registry.csv line {index}: duplicate branch_id {branch_id}")
                seen.add(branch_id)
                if branch_id:
                    registry_by_id[branch_id] = row
                if (row.get("branch_class") or "").strip() not in valid_classes:
                    problems.append(f"branch_registry.csv line {index}: invalid branch_class")
                status = (row.get("status") or "").strip()
                if status.split("_", 1)[0] not in valid_status:
                    problems.append(f"branch_registry.csv line {index}: invalid status")
                try:
                    count = int((row.get("gene_count") or "").strip())
                except ValueError:
                    problems.append(f"branch_registry.csv line {index}: gene_count must be an integer")
                    continue
                exact_file = (row.get("exact_gene_file") or "").strip()
                if status.split("_", 1)[0] == "COMPLETED":
                    path = root / exact_file
                    if not exact_file or not path.is_file() or path.stat().st_size == 0:
                        problems.append(f"branch_registry.csv line {index}: completed branch exact file missing")
                    else:
                        try:
                            if len(unique_genes(path)) != count:
                                problems.append(f"branch_registry.csv line {index}: gene_count does not match {exact_file}")
                        except ValueError as exc:
                            problems.append(f"branch_registry.csv line {index}: {exact_file}: {exc}")

            manifest_branches = manifest.get("branches")
            if isinstance(manifest_branches, dict):
                if set(manifest_branches) != set(registry_by_id):
                    problems.append("manifest branch IDs do not match branch_registry.csv")
                for branch_id in set(manifest_branches) & set(registry_by_id):
                    branch = manifest_branches[branch_id]
                    row = registry_by_id[branch_id]
                    if isinstance(branch, dict):
                        if branch.get("class") != row.get("branch_class"):
                            problems.append(f"branch {branch_id}: class differs between manifest and registry")
                        try:
                            registry_count = int(row.get("gene_count") or "")
                        except ValueError:
                            continue
                        if branch.get("gene_count") is not None and branch.get("gene_count") != registry_count:
                            problems.append(f"branch {branch_id}: count differs between manifest and registry")

    broad_pool_path = root / "broad_target_pool.csv"
    if broad_pool_path.is_file() and broad_pool_path.stat().st_size:
        rows = csv_rows(broad_pool_path)
        required = {
            "compound", "gene_symbol", "stable_id", "source", "score_name", "raw_score",
            "rank", "evidence_type", "species", "source_record_id", "included", "qc_status",
            "exclusion_reason",
        }
        if not rows:
            problems.append("broad_target_pool.csv has no rows")
        else:
            missing = required - set(rows[0])
            if missing:
                problems.append(f"broad_target_pool.csv missing columns: {', '.join(sorted(missing))}")
            if contract_version >= 4:
                v4_evidence = {"evidence_class", "evidence_subtype"}
                missing_v4 = v4_evidence - set(rows[0])
                if missing_v4:
                    problems.append(
                        f"contract v4 broad_target_pool.csv missing columns: {', '.join(sorted(missing_v4))}"
                    )

    availability_path = root / "source_availability.csv"
    if availability_path.is_file() and availability_path.stat().st_size:
        rows = csv_rows(availability_path)
        required = {
            "compound", "source", "source_type", "accessible", "exact_identity_verified",
            "species_available", "raw_export_available", "native_score_available",
            "included_in_broad", "included_in_primary", "branch", "exclusion_reason",
            "access_date",
        }
        if not rows:
            problems.append("source_availability.csv has no rows")
        else:
            missing = required - set(rows[0])
            if missing:
                problems.append(
                    f"source_availability.csv missing columns: {', '.join(sorted(missing))}"
                )
            else:
                truthy = {"true", "1", "yes"}
                allowed_types = {
                    "target_prediction", "integrated_association", "measured_database"
                }
                for index, row in enumerate(rows, 2):
                    source_type = (row.get("source_type") or "").strip()
                    if not source_type:
                        problems.append(
                            f"source_availability.csv line {index}: blank source_type"
                        )
                    elif source_type not in allowed_types and not source_type.startswith("other:"):
                        problems.append(
                            f"source_availability.csv line {index}: undocumented source_type {source_type!r}"
                        )
                    included = any(
                        (row.get(column) or "").strip().casefold() in truthy
                        for column in ("included_in_broad", "included_in_primary")
                    )
                    if included:
                        for column in (
                            "accessible", "exact_identity_verified", "species_available",
                            "raw_export_available", "native_score_available",
                        ):
                            if (row.get(column) or "").strip().casefold() not in truthy:
                                problems.append(
                                    f"source_availability.csv line {index}: included source requires {column}=true"
                                )
                        for column in ("compound", "source", "branch", "access_date"):
                            if not (row.get(column) or "").strip():
                                problems.append(
                                    f"source_availability.csv line {index}: included source has blank {column}"
                                )

    audit_path = root / "narrowing_audit.csv"
    if audit_path.is_file() and audit_path.stat().st_size:
        rows = csv_rows(audit_path)
        required = {
            "step_id", "parent_set", "new_set", "changed_rule", "source", "threshold_or_rule",
            "before_count", "after_count", "overlap_before", "overlap_after", "ppi_nodes_before",
            "ppi_nodes_after", "ppi_edges_before", "ppi_edges_after", "gained_genes", "lost_genes",
            "enrichment_change", "hub_change", "reason", "decision", "created_utc",
        }
        if not rows:
            problems.append("narrowing_audit.csv has no decision rows")
        else:
            missing = required - set(rows[0])
            if missing:
                problems.append(f"narrowing_audit.csv missing columns: {', '.join(sorted(missing))}")
            seen_steps = set()
            for index, row in enumerate(rows, 2):
                step = (row.get("step_id") or "").strip()
                if not step:
                    problems.append(f"narrowing_audit.csv line {index}: blank step_id")
                elif step in seen_steps:
                    problems.append(f"narrowing_audit.csv line {index}: duplicate step_id {step}")
                seen_steps.add(step)
                for column in ("before_count", "after_count", "overlap_before", "overlap_after"):
                    try:
                        int((row.get(column) or "").strip())
                    except ValueError:
                        problems.append(f"narrowing_audit.csv line {index}: {column} must be an integer")
                for column in ("parent_set", "new_set"):
                    branch_id = (row.get(column) or "").strip()
                    if registry_by_id and branch_id not in registry_by_id:
                        problems.append(
                            f"narrowing_audit.csv line {index}: {column} {branch_id!r} not in branch_registry.csv"
                        )
                parent_id = (row.get("parent_set") or "").strip()
                new_id = (row.get("new_set") or "").strip()
                if parent_id in registry_by_id and new_id in registry_by_id:
                    parent_path = root / (registry_by_id[parent_id].get("exact_gene_file") or "")
                    new_path = root / (registry_by_id[new_id].get("exact_gene_file") or "")
                    if parent_path.is_file() and new_path.is_file():
                        try:
                            parent_genes = unique_genes(parent_path)
                            new_genes = unique_genes(new_path)
                            overlap_before = int((row.get("overlap_before") or "").strip())
                            overlap_after = int((row.get("overlap_after") or "").strip())
                        except ValueError:
                            pass
                        else:
                            if overlap_before != len(parent_genes):
                                problems.append(
                                    f"narrowing_audit.csv line {index}: overlap_before does not match {parent_id}"
                                )
                            if overlap_after != len(new_genes):
                                problems.append(
                                    f"narrowing_audit.csv line {index}: overlap_after does not match {new_id}"
                                )
                            if semicolon_set(row.get("gained_genes")) != new_genes - parent_genes:
                                problems.append(f"narrowing_audit.csv line {index}: gained_genes mismatch")
                            if semicolon_set(row.get("lost_genes")) != parent_genes - new_genes:
                                problems.append(f"narrowing_audit.csv line {index}: lost_genes mismatch")

    docking_path = root / "docking_candidate_handoff.csv"
    if docking_path.is_file() and docking_path.stat().st_size:
        rows = csv_rows(docking_path)
        required = {
            "target", "ligand", "compound_target_evidence", "compound_target_provenance",
            "disease_overlap", "supporting_branch", "hub_or_centrality", "pathway_evidence",
            "animal_validation", "cell_validation", "direct_biochemical_evidence",
            "pdb_structural_suitability", "binding_pocket_suitability",
            "known_ligand_or_cocrystal_control", "key_limitation", "candidate_tier",
            "recommendation_class", "selection_basis", "gpt_assessment", "docking_status",
        }
        allowed_bases = {
            "topology_derived", "pathway_derived", "experimental_alignment",
            "compound_evidence_derived", "historical_manuscript",
        }
        allowed_tiers = {
            "Tier 1 — NP + experimental concordance",
            "Tier 2 — NP-driven candidate",
            "Tier 3 — Experimental/mechanistic candidate outside final hub set",
        }
        allowed_recommendations = {
            "Primary recommendation", "Alternative", "Mechanistic secondary candidate", "Not recommended",
        }
        if rows:
            missing = required - set(rows[0])
            if missing:
                problems.append(f"docking_candidate_handoff.csv missing columns: {', '.join(sorted(missing))}")
            for index, row in enumerate(rows, 2):
                supporting_branch = (row.get("supporting_branch") or "").strip()
                if registry_by_id and supporting_branch not in registry_by_id:
                    problems.append(
                        f"docking_candidate_handoff.csv line {index}: supporting_branch {supporting_branch!r} not registered"
                    )
                bases = {value.strip() for value in (row.get("selection_basis") or "").split(";") if value.strip()}
                if not bases:
                    problems.append(f"docking_candidate_handoff.csv line {index}: no selection basis")
                unknown = bases - allowed_bases
                if unknown:
                    problems.append(
                        f"docking_candidate_handoff.csv line {index}: invalid selection basis {', '.join(sorted(unknown))}"
                    )
                if (row.get("candidate_tier") or "").strip() not in allowed_tiers:
                    problems.append(f"docking_candidate_handoff.csv line {index}: invalid candidate_tier")
                if (row.get("recommendation_class") or "").strip() not in allowed_recommendations:
                    problems.append(f"docking_candidate_handoff.csv line {index}: invalid recommendation_class")
                if (row.get("docking_status") or "").strip() != "DOCKING_NOT_STARTED":
                    problems.append(f"docking_candidate_handoff.csv line {index}: docking_status must be DOCKING_NOT_STARTED")
        else:
            problems.append("docking_candidate_handoff.csv has no candidate rows")

    if problems:
        for problem in problems:
            print(problem)
        raise SystemExit(1)
    print(f"NP completion structure valid: {root}")


if __name__ == "__main__":
    main()
