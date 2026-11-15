"""Local, versioned retrieval of approved KNTT reference passages and Toán THPT topic packs."""

from .mas_adapter import build_mas_intake_rag_entries, render_reference_material
from .matrix_retriever import (
    default_toan_thpt_matrix,
    parse_matrix_request,
    retrieve_exam_context,
)
from .profile_pack import export_release_pack, get_topic_pack, load_profile_release

__all__ = [
    "build_mas_intake_rag_entries",
    "default_toan_thpt_matrix",
    "export_release_pack",
    "get_topic_pack",
    "load_profile_release",
    "parse_matrix_request",
    "render_reference_material",
    "retrieve_exam_context",
]
