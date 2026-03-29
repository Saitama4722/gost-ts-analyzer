"""Structural and content checks (staged implementation)."""

from backend.app.checks.acceptance_criteria_check import check_document_acceptance_criteria
from backend.app.checks.appendix_references_check import check_document_appendix_references
from backend.app.checks.figure_references_check import check_document_figure_references
from backend.app.checks.table_references_check import check_document_table_references
from backend.app.checks.functional_requirements_check import check_document_functional_requirements
from backend.app.checks.nonfunctional_requirements_check import check_document_nonfunctional_requirements
from backend.app.checks.measurement_units_check import check_document_measurement_units
from backend.app.checks.numerical_characteristics_check import check_document_numerical_characteristics
from backend.app.checks.purpose_check import check_document_purpose
from backend.app.checks.scope_check import check_document_scope
from backend.app.checks.required_sections_check import check_required_sections_presence
from backend.app.checks.section_order_check import check_section_order
from backend.app.checks.structure_completeness_check import check_structure_completeness
from backend.app.checks.terminology_consistency_check import check_document_terminology_consistency
from backend.app.checks.duplicate_formulations_check import check_document_duplicate_formulations
from backend.app.checks.unverifiable_requirements_check import check_document_unverifiable_requirements
from backend.app.checks.vague_wording_check import check_document_vague_wording

__all__ = [
    "check_document_appendix_references",
    "check_document_figure_references",
    "check_document_table_references",
    "check_document_acceptance_criteria",
    "check_document_functional_requirements",
    "check_document_nonfunctional_requirements",
    "check_document_measurement_units",
    "check_document_numerical_characteristics",
    "check_document_purpose",
    "check_document_scope",
    "check_required_sections_presence",
    "check_section_order",
    "check_structure_completeness",
    "check_document_unverifiable_requirements",
    "check_document_vague_wording",
    "check_document_terminology_consistency",
    "check_document_duplicate_formulations",
]
