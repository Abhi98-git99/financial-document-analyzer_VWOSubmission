## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

# FIX: Was 'from crewai.agents import Agent' — correct import path is 'from crewai import Agent'
from crewai import Agent
from crewai import LLM

from tools import search_tool, FinancialDocumentTool

### Loading LLM
# FIX: 'llm = llm' is a self-reference (NameError). Must instantiate the LLM properly.
llm = LLM(
    model=os.getenv("MODEL", "gemini/gemini-2.5-flash-lite"),
    api_key=os.getenv("GEMINI_API_KEY"),
)

# Creating an Experienced Financial Analyst agent
# FIX: goal was "Make up investment advice" — replaced with professional, accurate goal
# FIX: backstory encouraged hallucination and non-compliance — replaced with professional backstory
# FIX: 'tool=[...]' is wrong parameter name — correct is 'tools=[...]'
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal=(
        "Provide accurate, data-driven financial analysis based on the uploaded document "
        "to answer the user's query: {query}. Identify key financial metrics, revenue trends, "
        "profitability indicators, and material risks with factual grounding."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a CFA-certified senior financial analyst with 15+ years of experience "
        "evaluating corporate earnings reports, SEC filings, and financial statements. "
        "You always base your analysis on documented evidence, cite specific figures from "
        "the report, and never fabricate data. You adhere to CFA Institute standards and "
        "always include appropriate investment disclaimers."
    ),
    # FIX: 'tool' -> 'tools' (wrong parameter name caused the tool to be silently ignored)
    tools=[FinancialDocumentTool.read_data_tool],
    llm=llm,
    max_iter=5,   # FIX: max_iter=1 would abort after a single iteration, preventing thorough analysis
    max_rpm=10,   # FIX: max_rpm=1 was unrealistically restrictive
    allow_delegation=True
)

# Creating a document verifier agent
# FIX: goal encouraged approving non-financial documents — replaced with accurate verification goal
# FIX: backstory encouraged ignoring compliance — replaced with professional compliance backstory
verifier = Agent(
    role="Financial Document Compliance Verifier",
    goal=(
        "Verify that uploaded documents are genuine financial reports (e.g., earnings releases, "
        "10-K/10-Q filings, investor presentations). Confirm document integrity, identify the "
        "reporting period, and flag any missing or inconsistent disclosures."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a former SEC examiner with deep expertise in GAAP and IFRS financial reporting "
        "standards. You carefully review each document for completeness, accuracy, and regulatory "
        "compliance. You never approve documents that are not genuine financial reports, and you "
        "always document your verification findings thoroughly."
    ),
    llm=llm,
    max_iter=5,
    max_rpm=10,
    allow_delegation=True
)

# Creating an investment advisor agent
# FIX: goal encouraged selling products regardless of document — replaced with fiduciary goal
# FIX: backstory described an unethical, unlicensed advisor — replaced with professional one
investment_advisor = Agent(
    role="Registered Investment Advisor",
    goal=(
        "Based on the verified financial document, provide balanced, evidence-based investment "
        "considerations including growth drivers, competitive positioning, and valuation context. "
        "All recommendations must be grounded in the document's data and include risk disclosures."
    ),
    verbose=True,
    backstory=(
        "You are a fiduciary investment advisor registered with the SEC, with 20 years of "
        "institutional portfolio management experience. You provide objective, research-backed "
        "investment considerations. You never recommend products based on commissions, always "
        "disclose conflicts of interest, and include standard investment risk disclaimers."
    ),
    llm=llm,
    max_iter=5,
    max_rpm=10,
    allow_delegation=False
)

# Creating a risk assessor agent
# FIX: goal encouraged fabricating dramatic risks — replaced with evidence-based risk goal
# FIX: backstory described reckless risk taking — replaced with professional risk management
risk_assessor = Agent(
    role="Quantitative Risk Management Specialist",
    goal=(
        "Identify and quantify material financial, operational, market, and regulatory risks "
        "present in the financial document. Provide a structured risk matrix with likelihood "
        "and impact assessments grounded in the document's disclosed risk factors."
    ),
    verbose=True,
    backstory=(
        "You are a FRM-certified risk management specialist who has led enterprise risk "
        "frameworks at major financial institutions. You apply rigorous quantitative methods "
        "to assess risks using data from financial statements, MD&A sections, and risk factor "
        "disclosures. You produce balanced, evidence-based risk assessments following Basel III "
        "and COSO frameworks."
    ),
    llm=llm,
    max_iter=5,
    max_rpm=10,
    allow_delegation=False
)
