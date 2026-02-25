## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

# FIX: Was importing 'tools' (the module itself) instead of specific tool classes
from crewai_tools import SerperDevTool
# FIX: Was importing from wrong subpath; SerperDevTool lives directly in crewai_tools
from langchain_community.document_loaders import PyPDFLoader

from crewai.tools import tool

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool
class FinancialDocumentTool():
    # FIX: Was 'async def' but crewai tools must be synchronous (no await used inside either)
    @staticmethod
    # added @tool
    @tool("Financial Document Reader")
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
        """Tool to read data from a pdf file from a path

        Args:
            path (str, optional): Path of the pdf file. Defaults to 'data/sample.pdf'.

        Returns:
            str: Full Financial Document file
        """
        # FIX: 'Pdf' was not imported/defined; correct class is PyPDFLoader from langchain
        docs = PyPDFLoader(file_path=path).load()

        full_report = ""
        for data in docs:
            # Clean and format the financial document data
            content = data.page_content

            # Remove extra whitespaces and format properly
            while "\n\n" in content:
                content = content.replace("\n\n", "\n")

            full_report += content + "\n"

        return full_report


## Creating Investment Analysis Tool
class InvestmentTool:
    # FIX: Was async; crewai tools must be synchronous
    @staticmethod
    # added @tool
    @tool("Investment Analyzer")
    def analyze_investment_tool(financial_document_data: str) -> str:
        """Analyze investment opportunities from financial document data."""
        # Process and analyze the financial document data
        processed_data = financial_document_data

        # Clean up the data format
        i = 0
        while i < len(processed_data):
            if processed_data[i:i+2] == "  ":  # Remove double spaces
                processed_data = processed_data[:i] + processed_data[i+1:]
            else:
                i += 1

        return f"Processed financial data ({len(processed_data)} chars) ready for investment analysis."


## Creating Risk Assessment Tool
class RiskTool:
    # FIX: Was async; crewai tools must be synchronous
    @staticmethod
    # Added @tool
    @tool("Risk Assessment Tool")
    def create_risk_assessment_tool(financial_document_data: str) -> str:
        """Create risk assessment from financial document data."""
        return f"Risk assessment initiated for document with {len(financial_document_data)} characters of financial data."
