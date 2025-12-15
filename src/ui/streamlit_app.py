"""
Streamlit Web UI for EDI Compliance Validation

Usage:
    streamlit run src/ui/streamlit_app.py

Features:
- File upload or text paste
- Document type and retailer selection
- Real-time validation
- Multi-format report viewing
- Downloadable reports
"""

import streamlit as st
import sys
from pathlib import Path
from io import BytesIO, StringIO
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.parser.edi_parser import EDIParser
from src.rules.rule_loader import RuleLoader
from src.validator.validation_engine import ValidationEngine
from src.reporting.report_generator import ReportGenerator


# Page configuration
st.set_page_config(
    page_title="EDI Compliance Validator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main Streamlit application."""

    # Header
    st.title("📋 EDI Compliance Validation Tool")
    st.markdown("---")

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # Document type selection
    doc_type = st.sidebar.selectbox(
        "Document Type",
        options=["850", "856", "810"],
        format_func=lambda x: {
            "850": "850 - Purchase Order",
            "856": "856 - Advance Ship Notice",
            "810": "810 - Invoice"
        }[x],
        help="Select the EDI document type to validate"
    )

    # Retailer selection
    retailer_options = {
        "None (Base Rules Only)": None,
        "Walmart": "walmart",
        "Amazon": "amazon",
        "Target": "target"
    }

    retailer_display = st.sidebar.selectbox(
        "Retailer Requirements",
        options=list(retailer_options.keys()),
        help="Select retailer for specific compliance requirements"
    )
    retailer = retailer_options[retailer_display]

    st.sidebar.markdown("---")

    # Input method selection
    st.sidebar.header("📁 Input Method")
    input_method = st.sidebar.radio(
        "Choose input method:",
        options=["Upload File", "Paste Text", "Use Sample File"],
        help="Select how to provide the EDI document"
    )

    st.sidebar.markdown("---")

    # Information
    with st.sidebar.expander("ℹ️ About"):
        st.markdown("""
        **EDI Compliance Validator**

        This tool validates EDI X12 documents against:
        - X12 standard requirements
        - Document-specific rules
        - Retailer-specific requirements

        **Supported Documents:**
        - 850 (Purchase Order)
        - 856 (Advance Ship Notice)
        - 810 (Invoice)

        **Supported Retailers:**
        - Walmart
        - Amazon
        - Target
        """)

    # Main content area
    col1, col2 = st.columns([2, 3])

    with col1:
        st.header("📄 EDI Document Input")

        edi_text = None
        file_name = None

        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload EDI file",
                type=["txt", "edi", "x12"],
                help="Select an EDI file to validate"
            )

            if uploaded_file:
                edi_text = uploaded_file.read().decode('utf-8')
                file_name = uploaded_file.name
                st.success(f"✅ Loaded: {file_name}")

        elif input_method == "Paste Text":
            edi_text = st.text_area(
                "Paste EDI content",
                height=300,
                placeholder="ISA*00*          *00*          *ZZ*SENDER...",
                help="Paste the raw EDI document text"
            )
            file_name = "pasted_content.txt"

        else:  # Use Sample File
            sample_files = {
                "850 - Valid PO": "samples/edi_850_valid.txt",
                "850 - Invalid PO": "samples/edi_850_invalid.txt",
                "856 - Valid ASN": "samples/edi_856_valid.txt",
                "810 - Valid Invoice": "samples/edi_810_valid.txt"
            }

            selected_sample = st.selectbox(
                "Select sample file",
                options=list(sample_files.keys())
            )

            sample_path = sample_files[selected_sample]

            try:
                with open(sample_path, 'r') as f:
                    edi_text = f.read()
                file_name = sample_path
                st.success(f"✅ Loaded: {selected_sample}")
            except FileNotFoundError:
                st.error(f"❌ Sample file not found: {sample_path}")

        # Preview
        if edi_text:
            with st.expander("📝 Preview EDI Content"):
                lines = edi_text.split('\n')
                preview = '\n'.join(lines[:20])
                if len(lines) > 20:
                    preview += f"\n\n... ({len(lines) - 20} more lines)"
                st.code(preview, language="text")

    with col2:
        st.header("🔍 Validation Results")

        if edi_text:
            # Validate button
            if st.button("🚀 Run Validation", type="primary", use_container_width=True):
                with st.spinner("Validating EDI document..."):
                    try:
                        # Parse EDI
                        parser = EDIParser()
                        parsed_edi = parser.parse_text(edi_text)

                        # Load rules
                        loader = RuleLoader()
                        rules = loader.load_rules(doc_type, retailer)

                        # Validate
                        engine = ValidationEngine()
                        result = engine.validate(parsed_edi, rules, retailer)

                        # Generate reports
                        generator = ReportGenerator(result)

                        # Store in session state
                        st.session_state['validation_result'] = result
                        st.session_state['report_generator'] = generator
                        st.session_state['parsed_edi'] = parsed_edi

                    except Exception as e:
                        st.error(f"❌ Validation Error: {str(e)}")
                        st.exception(e)

        # Display results if available
        if 'validation_result' in st.session_state:
            result = st.session_state['validation_result']
            generator = st.session_state['report_generator']

            # Compliance status
            if result.is_compliant():
                st.success("✅ COMPLIANT - Document passed all validation rules")
            else:
                st.error(f"❌ NON-COMPLIANT - {result.error_count()} error(s) found")

            # Quick stats
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Errors", result.error_count(), delta=None)
            with col_b:
                st.metric("Warnings", result.warning_count(), delta=None)
            with col_c:
                st.metric("Total Issues", result.total_issues(), delta=None)

            st.markdown("---")

            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📝 Detailed Report", "📋 Issues List", "💾 Downloads"])

            with tab1:
                st.subheader("Validation Dashboard")
                dashboard = generator.generate_dashboard()
                st.code(dashboard, language="text")

            with tab2:
                st.subheader("Detailed Text Report")
                text_report = generator.generate_text_report()
                st.text_area("Report Content", text_report, height=400)

            with tab3:
                st.subheader("Issues List")

                if result.total_issues() > 0:
                    issues = result.get_all_issues()

                    # Filter by severity
                    severity_filter = st.multiselect(
                        "Filter by severity",
                        options=["ERROR", "WARNING", "INFO"],
                        default=["ERROR", "WARNING", "INFO"]
                    )

                    filtered_issues = [i for i in issues if i.severity in severity_filter]

                    st.write(f"Showing {len(filtered_issues)} of {len(issues)} issues")

                    # Display issues
                    for idx, issue in enumerate(filtered_issues, 1):
                        severity_color = {
                            "ERROR": "🔴",
                            "WARNING": "🟡",
                            "INFO": "🔵"
                        }.get(issue.severity, "⚪")

                        with st.expander(f"{severity_color} Issue #{idx} - {issue.severity} - Line {issue.line_number or 'N/A'}"):
                            st.write(f"**Rule:** {issue.rule_id}")
                            st.write(f"**Segment:** {issue.segment_id or 'N/A'}")
                            st.write(f"**Message:** {issue.message}")

                            if issue.expected_value:
                                st.write(f"**Expected:** {issue.expected_value}")
                            if issue.actual_value:
                                st.write(f"**Actual:** {issue.actual_value}")
                else:
                    st.success("✅ No issues found - document is fully compliant!")

            with tab4:
                st.subheader("Download Reports")

                col_d1, col_d2 = st.columns(2)

                with col_d1:
                    # Text report download
                    text_report = generator.generate_text_report()
                    st.download_button(
                        label="📄 Download Text Report",
                        data=text_report,
                        file_name=f"validation_report_{doc_type}.txt",
                        mime="text/plain"
                    )

                    # JSON report download
                    json_report = generator.generate_json_report()
                    st.download_button(
                        label="📊 Download JSON Report",
                        data=json_report,
                        file_name=f"validation_report_{doc_type}.json",
                        mime="application/json"
                    )

                with col_d2:
                    # CSV report download
                    csv_report = generator.generate_csv_report()
                    st.download_button(
                        label="📈 Download CSV Report",
                        data=csv_report,
                        file_name=f"validation_report_{doc_type}.csv",
                        mime="text/csv"
                    )

                    # Dashboard download
                    dashboard = generator.generate_dashboard()
                    st.download_button(
                        label="📋 Download Dashboard",
                        data=dashboard,
                        file_name=f"validation_dashboard_{doc_type}.txt",
                        mime="text/plain"
                    )

                st.info("💡 All reports are available for download in multiple formats")

        else:
            st.info("👆 Configure settings and click 'Run Validation' to see results")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>EDI Compliance Rules Engine | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
