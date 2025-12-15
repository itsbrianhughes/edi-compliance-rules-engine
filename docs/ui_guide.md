# EDI Compliance Validator - UI Guide

## Overview

The EDI Compliance Validator provides a web-based interface built with Streamlit for validating EDI documents against X12 standards and retailer-specific requirements.

## Features

### 1. Input Methods

The UI supports three ways to provide EDI documents:

#### Upload File
- Supports `.txt`, `.edi`, and `.x12` file formats
- Drag-and-drop or browse to select file
- Displays file name confirmation after upload

#### Paste Text
- Large text area for pasting raw EDI content
- Useful for quick validation of EDI snippets
- 300-line height for comfortable viewing

#### Use Sample File
- Pre-loaded sample files for testing:
  - **850 - Valid PO**: Compliant purchase order
  - **850 - Invalid PO**: PO with intentional errors
  - **856 - Valid ASN**: Compliant advance ship notice
  - **810 - Valid Invoice**: Compliant invoice
- Instant loading with confirmation message

### 2. Configuration Panel

Located in the sidebar, allows selection of:

#### Document Type
- **850** - Purchase Order
- **856** - Advance Ship Notice
- **810** - Invoice

#### Retailer Requirements
- **None (Base Rules Only)** - X12 standard + document-specific rules
- **Walmart** - Walmart-specific compliance requirements
- **Amazon** - Amazon-specific compliance requirements
- **Target** - Target-specific compliance requirements

### 3. Validation Execution

- **Run Validation** button triggers validation process
- Displays spinner with "Validating EDI document..." message
- Automatic error handling with detailed error messages
- Results stored in session state for persistent viewing

### 4. Results Display

#### Compliance Status
- ✅ **COMPLIANT** - Green success message (document passed all validation rules)
- ❌ **NON-COMPLIANT** - Red error message with error count

#### Quick Stats
Three-column metric display:
- **Errors** - Blocking issues (ERROR severity)
- **Warnings** - Review recommended (WARNING severity)
- **Total Issues** - Combined count (ERROR + WARNING + INFO)

#### Four Result Tabs

**Tab 1: Dashboard**
- Visual summary with box-drawing characters
- Quick stats at a glance
- Document information (type, sender, receiver)
- Top segments with issues (bar chart visualization)
- Validation info (execution time, retailer)
- Recommended actions (for non-compliant documents)
- Ready for transmission (for compliant documents)

**Tab 2: Detailed Report**
- Full text report in scrollable text area
- Document information section
- Validation information section
- Compliance status summary
- Issues grouped by severity (ERRORS, WARNINGS, INFORMATIONAL)
- Each issue shows:
  - Line number and segment location
  - Rule ID and message
  - Expected vs. actual values (when applicable)

**Tab 3: Issues List**
- Interactive issue browser
- Filter by severity (ERROR, WARNING, INFO)
- Multi-select dropdown for filtering
- Expandable cards for each issue showing:
  - 🔴 ERROR / 🟡 WARNING / 🔵 INFO indicators
  - Rule ID
  - Segment ID
  - Line number
  - Full message
  - Expected/actual values
- "No issues found" message for compliant documents

**Tab 4: Downloads**
Four download buttons in 2x2 grid:
- **Text Report** (.txt) - Human-readable detailed report
- **JSON Report** (.json) - Structured data for API integration
- **CSV Report** (.csv) - Spreadsheet-compatible issue list
- **Dashboard** (.txt) - Visual summary dashboard

All downloads include document type in filename (e.g., `validation_report_850.txt`)

### 5. Document Preview

- Expandable "Preview EDI Content" section
- Shows first 20 lines of EDI document
- Displays total line count if > 20 lines
- Monospace font for proper EDI formatting

### 6. About Section

Collapsible sidebar section with:
- Tool description
- Supported document types
- Supported retailers
- Validation scope (X12, document, retailer rules)

## Usage Examples

### Example 1: Upload and Validate Purchase Order

1. Select **Document Type**: 850 - Purchase Order
2. Select **Retailer**: Walmart
3. Choose **Upload File** input method
4. Upload your EDI file (e.g., `my_po.txt`)
5. Click **Run Validation**
6. Review results in Dashboard tab
7. Download Text Report for detailed analysis

### Example 2: Quick Paste Validation

1. Select **Document Type**: 856 - Advance Ship Notice
2. Select **Retailer**: None (Base Rules Only)
3. Choose **Paste Text** input method
4. Paste your EDI content into the text area
5. Click **Run Validation**
6. Review Issues List tab to filter by severity
7. Download CSV Report for spreadsheet analysis

### Example 3: Test with Sample Files

1. Select **Document Type**: 850 - Purchase Order
2. Select **Retailer**: Target
3. Choose **Use Sample File** input method
4. Select **850 - Invalid PO**
5. Expand **Preview EDI Content** to inspect
6. Click **Run Validation**
7. Review Detailed Report tab to see all issues
8. Compare with **850 - Valid PO** to see differences

## Running the UI

### Start the Application

```bash
streamlit run src/ui/streamlit_app.py
```

The application will open in your default browser at `http://localhost:8501`

### Command-Line Options

```bash
# Custom port
streamlit run src/ui/streamlit_app.py --server.port 8080

# Headless mode (no browser)
streamlit run src/ui/streamlit_app.py --server.headless true

# Enable CORS for external access
streamlit run src/ui/streamlit_app.py --server.enableCORS true
```

## Technical Architecture

### Session State

The UI uses Streamlit session state to persist:
- `validation_result` - ValidationResult object
- `report_generator` - ReportGenerator instance
- `parsed_edi` - Parsed EDI document structure

This allows results to remain visible across tab switches and interactions.

### Workflow

```
User Input → Configuration → Validation Button
    ↓
EDIParser.parse_text(edi_text)
    ↓
RuleLoader.load_rules(doc_type, retailer)
    ↓
ValidationEngine.validate(parsed_edi, rules, retailer)
    ↓
ReportGenerator(result)
    ↓
Display Results + Download Options
```

### Error Handling

- File upload errors: Handled with UTF-8 decoding
- Sample file errors: Displays "Sample file not found" message
- Validation errors: Shows error message with full exception details
- All errors preserve user configuration and allow retry

## File Locations

- **UI Application**: `src/ui/streamlit_app.py`
- **Sample Files**: `samples/edi_*.txt`
- **Output Directory**: `output/` (for downloaded reports)

## Dependencies

Required packages (from `requirements.txt`):
```
streamlit>=1.28.0
```

## Browser Compatibility

Tested and supported on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Validation time: < 1 second for typical EDI documents (20-100 segments)
- UI responsiveness: Instant tab switching via session state
- File upload: Supports files up to 200MB

## Troubleshooting

### Issue: Validation button does nothing
**Solution**: Ensure you have provided EDI input via one of the three input methods

### Issue: Sample file not found
**Solution**: Verify `samples/` directory exists in project root with sample files

### Issue: Download buttons not appearing
**Solution**: Click "Run Validation" first to generate results

### Issue: UI shows old results
**Solution**: Run validation again to refresh results in session state

## Future Enhancements

Potential additions for future versions:
- Batch validation (multiple files)
- Comparison view (side-by-side document comparison)
- Rule editing interface
- Validation history/logging
- Export to Excel with formatting
- Real-time validation as you type
- Dark mode theme
