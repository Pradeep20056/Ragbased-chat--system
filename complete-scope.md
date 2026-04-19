Scope of Work: AI-Based Tender Evaluation System Integration with TMS 
(THIS IS FULL SCOPE OF PROJECT , WE ARE ONLY DOING THE EVALUVATION ENGINE , THIS FILE IS ONLY TO PROVIDE CONTEXT !!!! )
1. Background 
The organization operates a Tender Management System (TMS) developed in .NET and running in the organization’s intranet environment. Bidder offers and tender documents are stored in the organization's file server, typically as one ZIP file per bidder. The organization intends to implement an AI-based evaluation system hosted in a cloud environment to assist in the evaluation of bidder offers. 
2. Objective 
The objective of this project is to design, develop, and implement an AI-based evaluation system integrated with the existing TMS to: 
• Upload bidder offer files and tender documents to cloud storage 
• Perform automated AI-based document analysis 
• Generate structured evaluation outputs 
• Display AI outputs within TMS evaluation pages 
• Allow human review and override 
• Store final evaluation decisions in the local TMS database 
3. Existing System 
The current environment includes: 
• Tender Management System (TMS) built on .NET 
• Bidder offers stored in internal file servers 
• Each bidder offer stored as one ZIP file per bidder 
• Evaluation performed manually through PQ, Technical, commercial and financial evaluation pages within TMS 
4. Upload of Bidder Offers to Cloud 
The vendor shall provide a mechanism to upload bidder offer ZIP files from the TMS to cloud storage. The Offer Upload Page in TMS shall contain an additional link/button such as: “Upload to AI Cloud”. Clicking this link shall invoke the vendor-provided secure Upload API. 
4.1 Upload API Requirements 
The vendor shall develop a secure API capable of: 
• Receiving bidder ZIP files 
• Accepting metadata information 
• Validating files 
• Uploading files to cloud storage 
• Returning upload status responses 
All communication shall be through HTTPS. 
4.2 Metadata Sent During Upload 
The upload request shall include: 
• Tender Number 
• Bidder Name 
• File Name 
• Upload Timestamp 
• Uploaded By (User ID) 
4.3 Cloud Storage Structure 
Uploaded files shall be stored using structured hierarchy: 
tenders/ 
TenderNo/ 
Tender doc/ 
bidders/ 
Bidder1.zip 
Bidder2.zip 
5. Upload Validation and Error Handling 
The upload process shall validate: 
• File format 
• File size limits 
• Mandatory metadata 
• Duplicate file uploads 
Appropriate error messages shall be generated for: 
• Invalid file format 
• Missing metadata 
• File size exceeded 
• Upload failure 
• Network issues 
6. Upload Logging 
The system shall maintain logs including: 
• Tender Number 
• Bidder Name 
• File Name 
• Upload Time 
• Upload Status 
• Error Message (if any) 
7. Triggering AI Evaluation 
AI evaluation shall be triggered after successful upload through: 
• Automatic event-based triggering, or 
• API invocation from TMS. 
8. AI Document Processing 
The AI system shall: 
• Access ZIP files stored in cloud storage 
• Extract documents contained in ZIP files 
• Process documents including PDF including scanned, Excel,and Word files 
• Perform automated analysis based on defined evaluation criteria 
9. AI Evaluation Output 
The AI system shall generate outputs in the predefined format given by CPCL 
10. Storage of AI Results 
AI results shall be stored in a cloud database including: 
• Tender Number 
• Bidder Name 
• Evaluation Stage (PQ / Technical / Financial/Commercial) 
• AI Evaluation Output 
• Processing Status 
• Evaluation Timestamp 
11. Retrieval of AI Results 
Vendor shall provide secure APIs enabling TMS to retrieve AI outputs using: 
• Tender Number 
• Bidder Identifier 
• Evaluation Stage 
12. Rendering AI Output in TMS 
The TMS contains evaluation pages including: 
	PQ Evaluation Page 
	Technical Evaluation Page 
	Financial Evaluation Page 
	Commercial Evaluation Page 

Each page shall include a link such as “View AI Evaluation”. 
Clicking this link shall retrieve AI results via API and display them to the user. 
13. Human Override 
Authorized users shall be able to: 
• Review AI-generated evaluation 
• Accept AI recommendations 
• Modify or override AI outputs 
Final decisions shall remain with human evaluators. 
14. Override Audit Trail 
When overrides occur, the system shall record: 
• Tender Number 
• Bidder Identifier 
• Evaluation Stage 
• AI Result 
• Final Human Decision 
• Override Reason 
• User ID 
• Timestamp 
15. Storage of Final Results in Local Database 
The final evaluation results after human review shall be stored in the organization’s local TMS database server. 
16. Security Requirements 
The system shall implement: 
• HTTPS encrypted communication 
• API authentication 
• Role-based access control 
• Protection of confidential tender data 
17. Performance Requirements 
The system shall support: 
• Processing multiple bidders simultaneously 
• Processing multiple tenders 
• Handling large ZIP files 
• Reliable operation without data loss 
18. Documentation and Deliverables 
Vendor shall provide: 
• System architecture documentation 
• API documentation 
• Database schema documentation 
• Integration guide 
• User manual 
• Administration manual 
• Functional testing 
• Integration testing 
• Performance testing 
19. Service Level Agreement (SLA) System shall maintain minimum availability of 99.5% excluding scheduled maintenance. 20. Data Ownership and Confidentiality All tender data shall remain the exclusive property of the organization. Vendor shall maintain strict confidentiality and shall not use tender data for any external purposes. 21. Testing and Acceptance Vendor shall conduct:
