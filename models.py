"""
models.py
──────────
6 Pydantic schemas — one per evaluation section (a–f).
Fields map 1-to-1 to the rows in each criteria markdown file.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# (a) PQC Exp. & Technical Evaluation (Contracts)
# ─────────────────────────────────────────────────────────────────────────────
class ContractsTechEvaluation(BaseModel):
    # 1.0 Experience criteria
    similar_nature_of_job: str = Field(
        description="1.1 - Similar nature of job performed (e.g., electrical jobs, instrumentation, civil). Extract from the work orders submitted.")
    value_of_work_order_required: str = Field(
        description="1.2 - Value of work order required as per tender (1xWO or 2xWO or 3xWO format with Rs. amount in Lakhs).")
    details_of_work_order_submitted: str = Field(
        description="1.3 - Details of the work order submitted by the bidder.")
    work_order_number_and_date: str = Field(
        description="1.4 - Work Order number and date as mentioned in the submitted work order document.")
    nature_of_industry: str = Field(
        description="1.5 - Nature of industry as per NIT pre-qualification (e.g., Petroleum / Petrochemical / Power / Refinery).")
    name_of_issuer: str = Field(
        description="1.6 - Name of the organization/company that issued the work order.")
    completion_certificate_details: str = Field(
        description="1.7 - Details of the completion certificate submitted against the work order (certificate number, date, issuer).")
    executed_value_as_per_completion_certificate: str = Field(
        description="1.8 - Executed/completed value in Lakhs as stated in the completion certificate.")
    value_considered_for_technical_evaluation: str = Field(
        description="1.9 - Value of the order considered for technical evaluation in Lakhs.")
    annualization_of_value: str = Field(
        description="1.10 - Annualized value if applicable for ARC (Annual Rate Contract) jobs. Write 'Not Applicable' if not an ARC job.")
    subcontract_approval_submitted: str = Field(
        description="1.11 - In case of subcontract, whether subcontract approval or certificate from the end user was submitted. Write 'Not Applicable', 'Yes', or 'No'.")
    work_order_meeting_experience_criteria: str = Field(
        description="1.12 - Details of the specific work order that meets the experience criteria.")
    # 2
    additional_technical_pqc: str = Field(
        description="2 - Additional Technical PQC requirements and whether the bidder has met them. Write 'None' if no additional PQC.")
    # 3
    deviations: List[str] = Field(
        default_factory=list,
        description="3 - List of deviations from the tender requirements found in the bid. Leave empty list [] if Nil.")
    # 4
    query_to_be_raised: List[str] = Field(
        default_factory=list,
        description="4 - List of queries/clarifications that need to be raised with the bidder.")
    # 5
    technical_acceptance_status: str = Field(
        description="5 - Technical acceptance status. Must be one of: 'Accepted', 'Under Query', or 'Rejected'.")
    # 6
    reason_for_rejection: str = Field(
        default="Not Applicable",
        description="6 - Reason for rejection if status is 'Rejected'. Write 'Not Applicable' if Accepted or Under Query.")


# ─────────────────────────────────────────────────────────────────────────────
# (b) PQC Fin. & Commercial Evaluation (Contracts)
# ─────────────────────────────────────────────────────────────────────────────
class ContractsCommercialEvaluation(BaseModel):
    # 1
    technical_qualification: str = Field(
        description="1 - Technical qualification status: 'Qualified', 'Not Qualified', or 'Under TE'.")
    # 2
    integrity_pact: str = Field(
        description="2 - Whether Integrity Pact (IP) was submitted. E.g., 'Submitted (Page: X)', 'Not Applicable', or 'Not Submitted'.")
    # 3
    emd_applicable: str = Field(
        description="3 - EMD applicability and amount submitted (e.g., 'Rs.6.93 Lakhs submitted', 'EMD exemption claimed as MSE').")
    # 3a
    emd_in_form_of_bg: str = Field(
        description="3a - EMD in the form of Bank Guarantee — validity details or 'Not Applicable'.")
    # 4
    emd_sent_to_finance: str = Field(
        description="4 - Whether EMD was sent to Finance department: 'Yes', 'Not Applicable'.")
    # 5
    annual_turnover_2021_22: str = Field(
        description="5a - Annual Turnover for FY 2021-2022 in Rs. Lakhs.")
    annual_turnover_2022_23: str = Field(
        description="5b - Annual Turnover for FY 2022-2023 in Rs. Lakhs.")
    annual_turnover_2023_24: str = Field(
        description="5c - Annual Turnover for FY 2023-2024 in Rs. Lakhs.")
    # 6
    share_capital: str = Field(
        description="6 (Share Capital) - Share Capital for FY2023-24 in Rs. Lakhs.")
    reserve_and_surplus: str = Field(
        description="6 (Reserve/Surplus) - Reserve and Surplus for FY2023-24 in Rs. Lakhs.")
    loss: str = Field(
        description="6 (Loss) - Loss amount for FY2023-24 in Rs. Lakhs (write '0' or 'Nil' if no loss).")
    networth: str = Field(
        description="6 (Networth) - Net Worth = Share Capital + Reserves - Loss for FY2023-24 in Rs. Lakhs. State if Positive or Negative.")
    # 7
    epf_code_number: str = Field(
        description="7 - EPF Code Number submitted by the bidder.")
    # 8
    esi_code_number: str = Field(
        description="8 - ESI Code Number submitted by the bidder.")
    # 9
    cpcl_vendor_code: str = Field(
        description="9 - CPCL Vendor Code of the bidder if available, else 'Not Available'.")
    # 10
    power_of_attorney_submitted: str = Field(
        description="10 - Whether Power of Attorney or Authorization document is submitted: 'Submitted', 'Not Submitted'.")
    # 11 - Formats
    format_a_submitted: str = Field(description="11a - Format A (Declaration of tender acceptance): 'Submitted', 'Not Submitted'.")
    format_b_submitted: str = Field(description="11b - Format B (Information about tenderer): 'Submitted', 'Not Submitted'.")
    format_c_submitted: str = Field(description="11c - Format C (Schedule of deviation): 'Submitted', 'Not Submitted'.")
    format_d_submitted: str = Field(description="11d - Format D (Pre-qualification details): 'Submitted', 'Not Submitted'.")
    format_e_submitted: str = Field(description="11e - Format E (Declaration for confidentiality Clause): 'Submitted', 'Not Submitted'.")
    format_f_submitted: str = Field(description="11f - Format F (IT Declaration): 'Submitted', 'Not Submitted'.")
    format_g_submitted: str = Field(description="11g - Format G (Land border sharing): 'Submitted', 'Not Submitted'.")
    format_h_submitted: str = Field(description="11h - Format H (Local content): 'Submitted', 'Not Submitted'.")
    format_i_submitted: str = Field(description="11i - Format I (ESI declaration): 'Submitted', 'Not Submitted'.")
    format_j_submitted: str = Field(description="11j - Format J (Bank details): 'Submitted', 'Not Submitted', or 'Not Applicable (CPCL VC available)'.")
    format_k_submitted: str = Field(description="11k - Format K (Declaration of single bid): 'Submitted', 'Not Submitted'.")
    appendix_iia_submitted: str = Field(description="11l - Appendix IIA (Declaration of Black Listing/Holiday Listing): 'Submitted', 'Not Submitted'.")
    # 12
    mse_status: str = Field(
        description="12 - MSE Status details: applicability, category (Micro/Small), type (Manufacturer/Service Provider), reservation type (General/Reserved/Women).")
    # 13
    mii_status: str = Field(
        description="13 - MII (Make in India) status: 'Category 1', 'Category 2', 'Category 3', or 'Not Applicable'.")
    # 14
    blacklisting_sap_cppp_gem: str = Field(
        description="14 - Blacklisting status in SAP, CPPP, and GeM portals: 'Not Blacklisted' or details if blacklisted.")
    # 15
    blacklisting_in_gst_portal: str = Field(
        description="15 - Blacklisting status in GST portal: 'No' or details if blacklisted.")
    # 16
    deviations: List[str] = Field(
        default_factory=list,
        description="16 - List of commercial deviations. Empty list [] if Nil.")
    # 17
    corrigendums_signed_submitted: str = Field(
        description="17 - Whether corrigendums duly signed are submitted: 'Submitted', 'Not Submitted', or 'Not Applicable'.")
    # 18
    queries_to_be_raised: List[str] = Field(
        default_factory=list,
        description="18 - List of commercial/technical queries to be raised with the bidder.")
    # 19
    commercial_evaluation_status: str = Field(
        description="19 - Commercial evaluation status: 'Qualified', 'Not Qualified', or 'Under Query'.")
    # 20
    reason_for_rejection: str = Field(
        default="Not Applicable",
        description="20 - Reason for rejection if status is 'Not Qualified'. Write 'Not Applicable' otherwise.")


# ─────────────────────────────────────────────────────────────────────────────
# (c) Materials - PQ Experience Criteria
# ─────────────────────────────────────────────────────────────────────────────
class MaterialsPQExperience(BaseModel):
    # 1 - PQC Experience
    po_item_description: str = Field(
        description="1a - PO Item Description: the description of the similar item supplied as per the Purchase Order.")
    po_number: str = Field(
        description="1b - Purchase Order number.")
    po_acceptable_date: str = Field(
        description="1c - PO acceptable date (must be after the specified date in the tender).")
    po_value: str = Field(
        description="1d - Purchase Order value in Rs. Lakhs.")
    po_issuer_name: str = Field(
        description="1e - Name of the organization/company that issued the Purchase Order.")
    po_receiver_name: str = Field(
        description="1f - Name of the bidder organization that received the Purchase Order.")
    po_issuer_type_of_industry: str = Field(
        description="1g - Type of industry of the PO issuer (e.g., Petroleum, Petrochemical, Power, Refinery).")
    po_supplied_value: str = Field(
        description="1h - Value of supplies made against the PO (1x PO or 2x PO or 3x PO format with Rs. Lakhs).")
    proof_of_supply: str = Field(
        description="1i - Proof of supply documents submitted: GST Invoice(s), Delivery Challan(s), or Completion Certificate(s).")
    supplied_within_india: str = Field(
        description="1j - Whether the supply was within India: 'Applicable' or 'Not Applicable'.")
    commissioned: str = Field(
        description="1k - Whether the supplied items were commissioned: 'Applicable' or 'Not Applicable'.")
    # 2
    additional_pqc: str = Field(
        description="2 - Additional PQC requirements and whether met. Write 'Not Applicable' if none.")
    queries_to_be_raised: List[str] = Field(
        default_factory=list,
        description="Queries to be raised regarding PQ experience criteria.")
    pqc_experience_status: str = Field(
        description="PQC Experience Criteria Evaluation status: 'Qualified', 'Not Qualified', or 'Query to be raised'.")
    reason_for_rejection: str = Field(
        default="Not Applicable",
        description="Reason for rejection (Not qualified). Write 'Not Applicable' if not rejected.")


# ─────────────────────────────────────────────────────────────────────────────
# (d) Materials - PQ Financial Criteria
# ─────────────────────────────────────────────────────────────────────────────
class MaterialsPQFinancial(BaseModel):
    # 1 - Annual Turnover
    annual_turnover_applicable: str = Field(
        description="1 - Whether Annual Turnover requirement is applicable and the required amount in Rs. Lakhs.")
    annual_turnover_2021_22: str = Field(
        description="1a - Annual Turnover for FY 2021-2022 in Rs. Lakhs as per submitted financials.")
    annual_turnover_2022_23: str = Field(
        description="1b - Annual Turnover for FY 2022-2023 in Rs. Lakhs as per submitted financials.")
    annual_turnover_2023_24: str = Field(
        description="1c - Annual Turnover for FY 2023-2024 in Rs. Lakhs as per submitted financials.")
    # 2
    positive_networth_for_latest_fy: str = Field(
        description="2 - Whether the bidder has a Positive Net Worth for the latest Financial Year: 'Applicable - Positive', 'Applicable - Negative', or 'Not Applicable'.")
    networth_value: str = Field(
        description="Net Worth value in Rs. Lakhs for the latest financial year.")
    queries_to_be_raised: List[str] = Field(
        default_factory=list,
        description="Queries to be raised regarding PQ financial criteria.")
    pq_financial_status: str = Field(
        description="PQ Financial Criteria Evaluation status: 'Qualified', 'Not Qualified', or 'Query to be raised'.")
    reason_for_rejection: str = Field(
        default="Not Applicable",
        description="Reason for rejection if Not Qualified. Write 'Not Applicable' otherwise.")


# ─────────────────────────────────────────────────────────────────────────────
# (e) Materials - Technical Evaluation
# ─────────────────────────────────────────────────────────────────────────────
class MaterialsTechnicalEvaluation(BaseModel):
    # 1
    technical_specification_signed_and_sealed: str = Field(
        description="1 - Whether the Technical Specification document is signed and sealed: 'Yes - Signed & Sealed', 'No', or 'Not Found'.")
    # 2
    nil_deviation_statement_signed_and_sealed: str = Field(
        description="2 - Whether the NIL Deviation Statement is signed and sealed: 'Yes - Signed & Sealed', 'No', or 'Not Found'.")
    # 3
    additional_user_department_requirement: str = Field(
        description="3 - Any additional user department requirements stated by the indenter. Write 'None' if not specified.")
    # 4
    deviations: List[str] = Field(
        default_factory=list,
        description="4 - List of technical deviations found. Empty list [] if there are no deviations.")
    query_to_be_raised: List[str] = Field(
        default_factory=list,
        description="List of technical queries to be raised with the bidder.")
    technical_evaluation_status: str = Field(
        description="Technical Evaluation status: 'Qualified', 'Not Qualified', or 'Query to be raised'.")
    reason_for_rejection: str = Field(
        default="Not Applicable",
        description="Reason for rejection if Not Qualified. Write 'Not Applicable' otherwise.")


# ─────────────────────────────────────────────────────────────────────────────
# (f) Materials - Commercial Evaluation (CBA)
# ─────────────────────────────────────────────────────────────────────────────
class MaterialsCommercialEvaluation(BaseModel):
    # 1-4 Contact details
    vendor_code: str = Field(description="1 - Vendor Code of the bidder.")
    contact_person: str = Field(description="2 - Name of the contact person of the bidder.")
    mobile_number: str = Field(description="3 - Mobile number of the contact person.")
    email_id: str = Field(description="4 - Email ID of the contact person.")
    # 5-7 EMD
    emd_applicability: str = Field(description="5 - EMD Applicability: 'Applicable' or 'Not Applicable'.")
    emd_details: str = Field(description="6 - EMD details submitted (amount, form, reference number).")
    emd_exemption_reason: str = Field(description="7 - Reason for EMD exemption (e.g., MSE exemption, NSIC registration). Write 'Not Applicable' if no exemption.")
    # 8-13 MSE
    mse_preference_applicability: str = Field(description="8 - MSE preference applicability for this tender: 'Applicable' or 'Not Applicable'.")
    mse_preference_applied_in_gem: str = Field(description="9 - Whether MSE preference was applied in GEM/e-tender portal: 'Applied' or 'Not Applied'.")
    udyam_number: str = Field(description="10 - UDYAM Registration number of the bidder if MSE. Write 'Not Applicable' if not MSE.")
    mse_category: str = Field(description="11 - MSE Category: 'Micro', 'Small', 'Medium', or 'Not Applicable'.")
    mse_pp_verification: str = Field(description="12 - MSE Purchase Preference verification status: 'Verified', 'To be Verified', or 'Not Applicable'.")
    mse_purchase_preference_eligibility: str = Field(description="13 - MSE Purchase Preference eligibility: 'Eligible' or 'Not Eligible'.")
    # 14-18 MII
    mii_preference_applicability: str = Field(description="14 - MII (Make in India) preference applicability: 'Applicable' or 'Not Applicable'.")
    mii_preference_applied_in_gem: str = Field(description="15 - Whether MII preference was applied in GEM/e-tender: 'Applied' or 'Not Applied'.")
    mii_local_content_declaration: str = Field(description="16 - MII Local Content declaration status: 'Submitted', 'To be Verified', or 'Not Applicable'.")
    local_content_percentage: str = Field(description="17 - Percentage of local content declared by the bidder.")
    mii_purchase_preference_eligibility: str = Field(description="18 - MII Purchase Preference eligibility: 'Eligible' or 'Not Eligible'.")
    # 19-25 Declarations
    integrity_pact: str = Field(description="19 - Integrity Pact status: 'Applicable - Submitted', 'Applicable - Not Submitted', or 'Not Applicable'.")
    confidentiality_clause_declaration: str = Field(description="20 - Confidentiality Clause Declaration: 'Signed & Sealed', 'Not Submitted'.")
    holiday_listing_declaration: str = Field(description="21 - Holiday Listing Declaration: 'Signed & Sealed', 'Not Submitted'.")
    land_border_sharing_declaration: str = Field(description="22 - Land Border Sharing Declaration: 'Signed & Sealed', 'Not Submitted'.")
    nil_deviations_declaration: str = Field(description="23 - NIL Deviations Declaration: 'Signed & Sealed', 'Not Submitted'.")
    details_of_deviations: List[str] = Field(default_factory=list, description="24 - Details of any commercial deviations found. Empty list [] if nil.")
    deviations_acceptance: str = Field(description="25 - Whether deviations are accepted: 'Accepted', 'Not Accepted', or 'Not Applicable'.")
    # 26-29 Misc
    validity: str = Field(description="26 - Bid validity stated by the bidder (should be 120 days from final bid due date).")
    gst_number: str = Field(description="27 - GST Registration Number of the bidder.")
    gst_filing_status: str = Field(description="28 - GST filing compliance status: 'Regular', 'Irregular', or 'Not Found'.")
    blacklisted_in_cpcl_mopng: str = Field(description="29 - Whether the bidder is blacklisted or holiday listed in CPCL/MOPNG: 'No' or details if blacklisted.")
    # Summary
    query_to_be_raised: List[str] = Field(default_factory=list, description="List of commercial queries to be raised.")
    commercial_evaluation_status: str = Field(description="Commercial Evaluation status: 'Qualified', 'Not Qualified', or 'Query to be raised'.")
    reason_for_rejection: str = Field(default="Not Applicable", description="Reason for rejection if Not Qualified. Write 'Not Applicable' otherwise.")


# ─────────────────────────────────────────────────────────────────────────────
# Legacy — kept for backward compatibility with evaluate_bid.py
# ─────────────────────────────────────────────────────────────────────────────
from typing import List as _List

class PQEvaluationResult(BaseModel):
    bidder_name: str = Field(description="Name of the bidder submitting the offer.")
    meets_technical_criteria: bool = Field(description="Whether the bidder meets the core technical criteria.")
    technical_deviations: _List[str] = Field(default_factory=list, description="List of technical deviations.")
    risks_identified: _List[str] = Field(default_factory=list, description="Risks identified in the bid.")
    compliance_summary: str = Field(description="Brief compliance summary.")
    final_recommendation: str = Field(description="'Accept', 'Reject', or 'Need Clarification'.")
    reasoning: str = Field(description="Detailed reasoning for the recommendation.")
