from pydantic import BaseModel, Field
from typing import List, Optional

class PQEvaluationResult(BaseModel):
    bidder_name: str = Field(description="Name of the bidder submitting the offer.")
    meets_technical_criteria: bool = Field(description="Whether the bidder meets the core technical criteria of the tender.")
    technical_deviations: List[str] = Field(description="List of any technical deviations from the tender requirements. Empty if none.", default_factory=list)
    risks_identified: List[str] = Field(description="Any risks identified in the bidder's proposal (e.g., financial, operational, compliance).", default_factory=list)
    compliance_summary: str = Field(description="A brief summary of the bidder's overall compliance with the tender document.")
    final_recommendation: str = Field(description="Final recommendation for this stage. Should be 'Accept', 'Reject', or 'Need Clarification'.")
    reasoning: str = Field(description="Detailed reasoning justifying the recommendation and addressing any deviations or risks.")
