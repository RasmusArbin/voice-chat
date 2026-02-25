import logging

from agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def update_candidate_status(
    candidate_id: str,
    score: int,
    notes: str,
    recommendation: str,
) -> str:
    """
    Updates a candidate's status and score in the ATS after the interview.
    Call this when the interview is finished or a clear go/no-go decision has been reached.
    score should be 1-10. recommendation should be 'advance', 'reject', or 'hold'.
    """
    logger.info(
        "[ATS] Updating candidate %s: score=%s, recommendation=%s, notes=%r",
        candidate_id, score, recommendation, notes,
    )
    return f"Candidate {candidate_id} updated. Recommendation: {recommendation}."


@function_tool
async def lookup_candidate_document(
    candidate_id: str,
    document_type: str,
) -> str:
    """
    Retrieves the text content of a candidate document.
    document_type should be 'cv', 'cover_letter', or 'portfolio'.
    Use this before discussing the candidate's background to reference specific details.
    """
    logger.info("[Docs] Fetching %s for candidate %s", document_type, candidate_id)
    # TODO: replace with real document retrieval (ATS API, S3, etc.)
    return (
        f"[Placeholder CV for candidate {candidate_id}]: "
        "5 years of experience in Python and cloud infrastructure. "
        "Previously at Acme Corp as a backend engineer. "
        "Bachelor's degree in Computer Science. "
        "Proficient in FastAPI, PostgreSQL, AWS, and Docker."
    )


@function_tool
async def book_followup_interview(
    candidate_id: str,
    preferred_date: str,
    interviewer_email: str,
    interview_type: str,
) -> str:
    """
    Books a follow-up interview slot in the recruiter's calendar.
    preferred_date should be an ISO 8601 date string (e.g. '2025-03-15').
    interview_type should be 'technical', 'hiring_manager', or 'final'.
    Call this when the candidate has confirmed availability and a next step is agreed upon.
    """
    logger.info(
        "[Calendar] Booking %s interview for candidate %s on %s with %s",
        interview_type, candidate_id, preferred_date, interviewer_email,
    )
    # TODO: replace with real calendar integration (Google Calendar, Outlook, etc.)
    return (
        f"Follow-up {interview_type} interview booked for {preferred_date} "
        f"with {interviewer_email}. A confirmation will be sent to the candidate."
    )
