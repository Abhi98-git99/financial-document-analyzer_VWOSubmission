## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, FinancialDocumentTool

## Task 1: Verify the uploaded document is a valid financial report
# FIX: description encouraged hallucinating financial terms — replaced with real verification task
# FIX: expected_output told agent to lie about document type — replaced with honest verification output
verification = Task(
    description=(
        "Extract the document file path from the query if provided in format 'Document file path: <path>'. "
        "Use that path with the Financial Document Reader tool to read the document first.\n\n"
        "User query: {query}\n\n"
        "Read the financial document provided and verify it is a legitimate financial report.\n"
        "Confirm: (1) document type (earnings release, 10-K, 10-Q, investor presentation, etc.), "
        "(2) the company name and reporting period, (3) presence of key financial statements "
        "(income statement, balance sheet, cash flow). If the document is NOT a financial report, "
        "clearly state this and halt further analysis. User query: {query}"
    ),
    expected_output=(
        "A structured verification report containing:\n"
        "- Document Type: [type identified]\n"
        "- Company: [company name]\n"
        "- Reporting Period: [period]\n"
        "- Financial Statements Present: [list]\n"
        "- Verification Status: VERIFIED or NOT A FINANCIAL DOCUMENT\n"
        "- Notes: [any concerns or missing disclosures]"
    ),
    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

## Task 2: Comprehensive financial analysis
# FIX: description told agent to "use imagination" and make up URLs — replaced with real analysis task
# FIX: expected_output required made-up websites and self-contradictions — replaced with factual output
analyze_financial_document = Task(
    description=(
        "Extract the document file path from the query if provided in format 'Document file path: <path>'. "
        "Use that path with the Financial Document Reader tool to read the document first.\n\n"
        "User query: {query}\n\n"
        "Perform a comprehensive analysis of the verified financial document to address: {query}\n\n"
        "Your analysis must:\n"
        "1. Extract and summarize key financial metrics (revenue, net income, EPS, margins, cash flow)\n"
        "2. Identify YoY and QoQ trends with specific figures from the document\n"
        "3. Highlight material disclosures, guidance, and management commentary\n"
        "4. Assess the company's financial health (liquidity, solvency, efficiency ratios)\n"
        "5. Provide market context where relevant using the search tool\n"
        "All claims must be traceable to specific data points in the document."
    ),
    expected_output=(
        "A structured financial analysis report containing:\n"
        "- Executive Summary (3-5 sentences)\n"
        "- Key Financial Metrics table with actuals and YoY change\n"
        "- Revenue & Profitability Analysis\n"
        "- Balance Sheet & Liquidity Overview\n"
        "- Cash Flow Analysis\n"
        "- Management Guidance & Outlook\n"
        "- Key Takeaways\n"
        "All figures cited with their source in the document."
    ),
    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    async_execution=False,
    # FIX: Task now correctly references prior verification context
    context=[verification],
)

## Task 3: Investment considerations
# FIX: description said to recommend expensive products regardless of financials — replaced
# FIX: expected_output required fake research and contradictory strategies — replaced
investment_analysis = Task(
    description=(
        "Extract the document file path from the query if provided in format 'Document file path: <path>'. "
        "Use that path with the Financial Document Reader tool to read the document first.\n\n"
        "User query: {query}\n\n"
        "Based on the financial analysis, provide balanced investment considerations for: {query}\n\n"
        "Address:\n"
        "1. Bull case: Key growth drivers and competitive advantages shown in the document\n"
        "2. Bear case: Headwinds, risks, and concerns from the document\n"
        "3. Valuation context: How current metrics compare to historical ranges or industry norms\n"
        "4. Key catalysts and milestones to watch\n"
        "5. IMPORTANT: Include standard disclaimer that this is not personalized financial advice "
        "and readers should consult a registered financial advisor before making investment decisions."
    ),
    expected_output=(
        "A balanced investment considerations report with:\n"
        "- Bull Case (evidence-based, 3-5 points)\n"
        "- Bear Case (evidence-based, 3-5 points)\n"
        "- Valuation Context\n"
        "- Key Catalysts to Monitor\n"
        "- Standard Investment Disclaimer\n"
        "No fabricated data, no non-existent URLs, no guaranteed return claims."
    ),
    agent=investment_advisor,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
    context=[analyze_financial_document],
)

## Task 4: Risk assessment
# FIX: description told agent to recommend dangerous strategies for everyone — replaced
# FIX: expected_output required impossible risk targets and fake institutions — replaced
risk_assessment = Task(
    description=(
        "Extract the document file path from the query if provided in format 'Document file path: <path>'. "
        "Use that path with the Financial Document Reader tool to read the document first.\n\n"
        "User query: {query}\n\n"
        "Using the financial document, produce a structured risk assessment addressing: {query}\n\n"
        "Identify and evaluate:\n"
        "1. Market risks (demand, pricing, competition) disclosed in the document\n"
        "2. Operational risks (supply chain, manufacturing, regulatory) from the document\n"
        "3. Financial risks (leverage, liquidity, currency exposure) from balance sheet data\n"
        "4. Regulatory and compliance risks from risk factor disclosures\n"
        "5. Macroeconomic risks relevant to the company's industry\n"
        "For each risk, assess: Likelihood (High/Medium/Low) and Potential Impact (High/Medium/Low)."
    ),
    expected_output=(
        "A structured risk assessment containing:\n"
        "- Risk Matrix table (Risk | Category | Likelihood | Impact | Mitigation Noted in Report)\n"
        "- Top 3 Critical Risks with detailed explanation\n"
        "- Positive Risk Factors (strengths that mitigate downside)\n"
        "- Overall Risk Profile: Conservative / Moderate / Aggressive\n"
        "All risks must reference specific disclosures or data points from the document."
    ),
    agent=risk_assessor,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
    context=[analyze_financial_document],
)
