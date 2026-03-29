#!/usr/bin/env python3
"""Generate Word document status report with logo header."""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_logo_header(doc, logo_path):
    """Add logo to document header."""
    section = doc.sections[0]
    header = section.header
    
    # Clear existing header content
    header.paragraphs.clear()
    
    # Add logo paragraph
    logo_para = header.add_paragraph()
    logo_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    try:
        run = logo_para.add_run()
        run.add_picture(logo_path, height=Inches(0.8))
    except Exception as e:
        # If image fails, add text placeholder
        run = logo_para.add_run("[LOGO PLACEHOLDER]")
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(128, 128, 128)
    
    # Add horizontal line below logo
    line_para = header.add_paragraph()
    line_run = line_para.add_run("─" * 80)
    line_run.font.size = Pt(8)
    line_run.font.color.rgb = RGBColor(200, 200, 200)
    
    return header

def create_status_report():
    """Create the branding kit status report."""
    doc = Document()
    
    # Add logo header
    add_logo_header(doc, "latency_chart.png")
    
    # Title
    title = doc.add_heading('Branding Kit Status Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Date
    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_run = date_para.add_run('Generated: March 29, 2026')
    date_run.font.size = Pt(10)
    date_run.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.add_paragraph()
    
    # Executive Summary
    doc.add_heading('Executive Summary', level=1)
    summary = doc.add_paragraph()
    summary.add_run('This report summarizes the latest batch of branding kit illustrations and project files committed to the Aurora Branding repository. The commit includes 71 files with significant additions to the project structure.')
    
    # Commit Details
    doc.add_heading('Commit Details', level=1)
    
    commit_table = doc.add_table(rows=4, cols=2)
    commit_table.style = 'Light Grid Accent 1'
    
    commit_data = [
        ('Commit Message', 'Branding kit illustrations batch completed - initial commit'),
        ('Commit Hash', '21a0c35'),
        ('Branch', 'master'),
        ('Remote', 'https://github.com/StudioTanaka/aurora-branding.git')
    ]
    
    for i, (label, value) in enumerate(commit_data):
        cell_label = commit_table.rows[i].cells[0]
        cell_value = commit_table.rows[i].cells[1]
        cell_label.text = label
        cell_value.text = value
        cell_label.paragraphs[0].runs[0].font.bold = True
    
    doc.add_paragraph()
    
    # File Changes Summary
    doc.add_heading('File Changes Summary', level=1)
    
    changes_para = doc.add_paragraph()
    changes_para.add_run('Total Files Changed: ').bold = True
    changes_para.add_run('71 files\n')
    changes_para.add_run('Total Insertions: ').bold = True
    changes_para.add_run('8,664 lines added\n')
    changes_para.add_run('Total Deletions: ').bold = True
    changes_para.add_run('354 lines removed')
    
    doc.add_paragraph()
    
    # New Files
    doc.add_heading('New Files Added', level=2)
    
    new_files = [
        'AGENTS.md, SOUL.md, USER.md, IDENTITY.md (Workspace configuration)',
        'BGC_Incident_Briefing_Report.docx (Existing document)',
        'Diabetes_Prevention_Workshop_Script.md',
        'METRO_TOWER_DATA_REQUIREMENTS.md',
        'Metro_Tower_Q4_Safety_Compliance_Executive_Summary.md',
        'Q3_Care_Access_Memo.md, Q4_Vendor_Lead_Time_Buffer_Briefing.md',
        'compliance_analysis_report.md, compliance_notification_email.md',
        'compliance_registry.json, compliance_workflow_outputs.md',
        'docs/concurrency_control_protocol.md',
        'downtown_zoning_erd.md, firmware-validation-report.md',
        'k8s-security-manifest.yaml',
        'latency_chart.png (Placeholder logo - 96.5 KB)',
        'line4_batch_compliance_checker.py, line4_compliance_*.md',
        'schema_installation.sql, schema_installation_automation.py',
        'sector_compliance_*.md, sector_emissions_registry.yaml',
        'sector_notification_email.md (488 lines)',
        'seismic_analysis/ (4 files)',
        'site_inspections_*.mp4 (2 video files)',
        'solar_monitor.py, solar_status.json (417 lines)',
        'telemetry_analysis.py, telemetry_results.json',
        'test_budget_calculator.py',
        'vendor_config.json',
        'workflow_summary.md'
    ]
    
    for f in new_files:
        doc.add_paragraph(f'• {f}', style='List Bullet')
    
    doc.add_paragraph()
    
    # Deleted Files
    doc.add_heading('Files Removed', level=2)
    
    deleted_files = [
        'analyze_satisfaction.py (78 lines)',
        'resort_report_summary.md (56 lines)',
        'satisfaction_metrics.txt (14 lines)',
        'sunrise_header.py (121 lines)',
        'sunrise_ocean_header.png (35.9 KB)',
        'thematic_analysis.md (85 lines)'
    ]
    
    for f in deleted_files:
        doc.add_paragraph(f'• {f}', style='List Bullet')
    
    doc.add_paragraph()
    
    # Key Highlights
    doc.add_heading('Key Highlights', level=1)
    
    highlights = [
        ('📁 Workspace Configuration', 'Complete OpenClaw agent setup with SOUL.md, AGENTS.md, and memory system'),
        ('📊 Compliance Documentation', 'Extensive compliance reports for Metro Tower, Line 4, and Sector projects'),
        ('🔧 Automation Scripts', 'New Python scripts for schema installation, solar monitoring, and telemetry analysis'),
        ('📹 Media Assets', 'Site inspection videos and latency chart graphics added'),
        ('🧪 Testing', 'Test suite for budget calculator module')
    ]
    
    for title, desc in highlights:
        p = doc.add_paragraph()
        p.add_run(title + ': ').bold = True
        p.add_run(desc)
    
    doc.add_paragraph()
    
    # Next Steps
    doc.add_heading('Next Steps', level=1)
    
    next_steps = [
        '⚠️ Push to remote repository pending (repository URL verification needed)',
        '🔄 Replace placeholder logo (latency_chart.png) with aurora_logo.svg when available',
        '📂 Add aurora_branding/ folder with illustration files when uploaded',
        '✅ Verify all compliance documents with stakeholders'
    ]
    
    for step in next_steps:
        doc.add_paragraph(step, style='List Bullet')
    
    doc.add_paragraph()
    
    # Footer
    footer_para = doc.add_paragraph()
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_para.add_run('---\nGenerated by OpenClaw Agent | Aurora Branding Project')
    footer_run.font.size = Pt(9)
    footer_run.font.color.rgb = RGBColor(150, 150, 150)
    
    # Save document
    output_path = 'Branding_Kit_Status_Report.docx'
    doc.save(output_path)
    print(f"✓ Status report saved to: {output_path}")
    return output_path

if __name__ == '__main__':
    create_status_report()
