from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, 
    QGroupBox, QHBoxLayout, QPushButton
)

class AuditReportDialog(QDialog):
    """Dialog to show icon audit results."""
    
    def __init__(self, issues, comparison_stats=None, parent=None):
        super().__init__(parent)
        self.issues = issues
        self.comparison_stats = comparison_stats
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Icon Doctor Report 🩺")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Icon Analysis Report")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Issues list in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        
        has_warnings = False
        has_errors = False
        
        for issue in self.issues:
            issue_widget = QGroupBox(issue.check_name)
            issue_layout = QVBoxLayout()
            
            # Status icon and message
            status_layout = QHBoxLayout()
            if issue.severity.value == "pass":
                icon_label = QLabel("✅")
                color = "green"
            elif issue.severity.value == "warning":
                icon_label = QLabel("⚠️")
                color = "orange"
                has_warnings = True
            elif issue.severity.value == "error":
                icon_label = QLabel("❌")
                color = "red"
                has_errors = True
            else:
                icon_label = QLabel("ℹ️")
                color = "blue"
                
            msg_label = QLabel(issue.message)
            msg_label.setStyleSheet(f"color: {color};")
            msg_label.setWordWrap(True)
            
            status_layout.addWidget(icon_label)
            status_layout.addWidget(msg_label)
            status_layout.addStretch()
            issue_layout.addLayout(status_layout)
            
            # Fix button if available
            if issue.fix_available:
                fix_btn = QPushButton(f"Auto-Fix: {issue.fix_action}")
                # Connect fix action here (requires callback mechanism)
                # For now just informational
                fix_btn.setEnabled(False) 
                issue_layout.addWidget(fix_btn)
                
            issue_widget.setLayout(issue_layout)
            content_layout.addWidget(issue_widget)
            
        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        if self.comparison_stats:
            comp_group = QGroupBox("Comparison Analysis (Vs Reference)")
            comp_layout = QVBoxLayout()
            
            # Sharpness
            s_diff = self.comparison_stats['sharpness_diff'] # Yours - Ref
            s_color = "green" if s_diff >= -10 else "orange" if s_diff >= -30 else "red"
            comp_layout.addWidget(QLabel(f"Sharpness: Yours ({self.comparison_stats['yours']['sharpness']}) vs Ref ({self.comparison_stats['ref']['sharpness']})"))
            
            # Contrast
            c_diff = self.comparison_stats['contrast_diff']
            c_color = "green" if abs(c_diff) < 20 else "orange"  
            comp_layout.addWidget(QLabel(f"Contrast: Yours ({self.comparison_stats['yours']['contrast']}) vs Ref ({self.comparison_stats['ref']['contrast']})"))
            
            # Palette
            p_yours = self.comparison_stats['yours']['palette_size']
            p_ref = self.comparison_stats['ref']['palette_size']
            comp_layout.addWidget(QLabel(f"Palette Size: {p_yours} colors (Ref: {p_ref})"))
            
            comp_group.setLayout(comp_layout)
            layout.addWidget(comp_group)
            
        # Summary
        if has_errors:
            summary = "❌ Errors detected. Please fix before exporting."
            summary_color = "red"
        elif has_warnings:
            summary = "⚠️ Warnings detected. Improvement recommended."
            summary_color = "orange"
        else:
            summary = "✅ Icon looks great! Ready for export."
            summary_color = "green"
            
        summary_label = QLabel(summary)
        summary_label.setStyleSheet(f"font-weight: bold; color: {summary_color}; margin-top: 10px;")
        layout.addWidget(summary_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        
        if has_errors or has_warnings:
            fix_all_btn = QPushButton("🪄 Auto-Fix All Issues")
            fix_all_btn.clicked.connect(self.accept) # For now just closes, logic hooked up in main
            # In a real implementation this would trigger the fix
            btn_layout.addWidget(fix_all_btn)
            
        layout.addLayout(btn_layout)
        self.setLayout(layout)
