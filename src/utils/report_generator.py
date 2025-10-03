"""
Report Generator for Student Attendance System
Tạo các báo cáo và thống kê cho hệ thống điểm danh
"""

import pandas as pd
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
import sqlite3

class AttendanceReportGenerator:
    def __init__(self, database_manager):
        self.db = database_manager
        
        # Create reports directory
        self.reports_dir = "attendance_system/reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Set up matplotlib for Vietnamese font
        plt.rcParams['font.family'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
        sns.set_style("whitegrid")
        
    def generate_daily_report(self, class_id, report_date=None):
        """Tạo báo cáo điểm danh hàng ngày"""
        if report_date is None:
            report_date = date.today()
        
        # Get attendance data
        conn = self.db.get_connection()
        query = '''
        SELECT 
            s.student_id,
            s.full_name,
            ar.check_in_time,
            ar.check_out_time,
            ar.status,
            ar.confidence_score,
            ses.session_name
        FROM students s
        LEFT JOIN attendance_records ar ON s.id = ar.student_id
        LEFT JOIN attendance_sessions ses ON ar.session_id = ses.id
        WHERE s.class_id = ? 
        AND (ses.session_date = ? OR ses.session_date IS NULL)
        AND s.is_active = 1
        ORDER BY s.full_name
        '''
        
        df = pd.read_sql_query(query, conn, params=[class_id, report_date.isoformat()])
        conn.close()
        
        # Create report
        report_data = []
        for _, row in df.iterrows():
            report_data.append({
                'Mã HS': row['student_id'],
                'Họ và tên': row['full_name'],
                'Giờ vào': row['check_in_time'] if pd.notna(row['check_in_time']) else 'Vắng',
                'Giờ ra': row['check_out_time'] if pd.notna(row['check_out_time']) else '',
                'Trạng thái': row['status'] if pd.notna(row['status']) else 'absent',
                'Độ tin cậy': f"{row['confidence_score']:.1f}%" if pd.notna(row['confidence_score']) else '',
                'Phiên': row['session_name'] if pd.notna(row['session_name']) else ''
            })
        
        return pd.DataFrame(report_data)
    
    def generate_monthly_report(self, class_id, month=None, year=None):
        """Tạo báo cáo điểm danh hàng tháng"""
        if month is None:
            month = date.today().month
        if year is None:
            year = date.today().year
        
        # Get class info
        classes = self.db.get_all_classes()
        class_name = "Unknown"
        for cls in classes:
            if cls[0] == class_id:
                class_name = cls[1]
                break
        
        # Get attendance data for the month
        conn = self.db.get_connection()
        query = '''
        SELECT 
            s.student_id,
            s.full_name,
            ses.session_date,
            ses.session_name,
            ar.check_in_time,
            ar.status,
            ar.confidence_score
        FROM students s
        LEFT JOIN attendance_records ar ON s.id = ar.student_id
        LEFT JOIN attendance_sessions ses ON ar.session_id = ses.id
        WHERE s.class_id = ? 
        AND strftime('%Y', ses.session_date) = ?
        AND strftime('%m', ses.session_date) = ?
        AND s.is_active = 1
        ORDER BY s.full_name, ses.session_date
        '''
        
        df = pd.read_sql_query(query, conn, params=[class_id, str(year), f"{month:02d}"])
        conn.close()
        
        if df.empty:
            return pd.DataFrame(), {}
        
        # Create pivot table
        df['session_date'] = pd.to_datetime(df['session_date'])
        df['status_symbol'] = df['status'].map({
            'present': 'Có mặt',
            'late': 'Muộn', 
            'absent': 'Vắng'
        }).fillna('Vắng')
        
        # Create summary statistics
        stats = {
            'total_students': len(df['student_id'].unique()),
            'total_sessions': len(df['session_date'].unique()),
            'total_attendances': len(df[df['status'] == 'present']),
            'attendance_rate': 0
        }
        
        if stats['total_students'] > 0 and stats['total_sessions'] > 0:
            stats['attendance_rate'] = (stats['total_attendances'] / 
                                      (stats['total_students'] * stats['total_sessions']) * 100)
        
        return df, stats
    
    def export_to_excel(self, data, filename, sheet_name="Attendance"):
        """Xuất báo cáo ra file Excel"""
        filepath = os.path.join(self.reports_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Format the Excel file
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Header styling
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            header_alignment = Alignment(horizontal='center', vertical='center')
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Add borders
            thin_border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            
            for row in worksheet.rows:
                for cell in row:
                    cell.border = thin_border
        
        return filepath
    
    def create_attendance_chart(self, data, title="Thống kê Điểm danh"):
        """Tạo biểu đồ thống kê điểm danh"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Chart 1: Attendance by status
        if 'status' in data.columns:
            status_counts = data['status'].value_counts()
            status_labels = {
                'present': 'Có mặt',
                'absent': 'Vắng',
                'late': 'Muộn'
            }
            
            labels = [status_labels.get(status, status) for status in status_counts.index]
            colors = ['#2ECC71', '#E74C3C', '#F39C12']
            
            ax1.pie(status_counts.values, labels=labels, autopct='%1.1f%%', 
                   colors=colors, startangle=90)
            ax1.set_title('Tỷ lệ Điểm danh')
        
        # Chart 2: Daily attendance trend
        if 'session_date' in data.columns and not data.empty:
            daily_stats = data.groupby('session_date').agg({
                'status': lambda x: (x == 'present').sum()
            }).reset_index()
            
            daily_stats['session_date'] = pd.to_datetime(daily_stats['session_date'])
            
            ax2.plot(daily_stats['session_date'], daily_stats['status'], 
                    marker='o', linewidth=2, markersize=6)
            ax2.set_title('Xu hướng Điểm danh theo Ngày')
            ax2.set_xlabel('Ngày')
            ax2.set_ylabel('Số học sinh có mặt')
            ax2.tick_params(axis='x', rotation=45)
            
            # Format dates on x-axis
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        plt.tight_layout()
        return fig
    
    def generate_student_report(self, student_id, days=30):
        """Tạo báo cáo cá nhân cho học sinh"""
        # Get student info
        student = self.db.get_student_by_id(student_id)
        if not student:
            return None, "Không tìm thấy học sinh"
        
        # Get attendance history
        history = self.db.get_student_attendance_history(student_id, days)
        
        if not history:
            return pd.DataFrame(), "Không có dữ liệu điểm danh"
        
        # Convert to DataFrame
        df = pd.DataFrame(history, columns=[
            'record_id', 'session_id', 'student_id', 'check_in_time', 
            'check_out_time', 'status', 'confidence_score', 'notes',
            'created_at', 'session_name', 'session_date', 'class_name'
        ])
        
        # Calculate statistics
        total_sessions = len(df)
        present_sessions = len(df[df['status'] == 'present'])
        attendance_rate = (present_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        stats = {
            'student_name': student[2],  # full_name
            'student_code': student[1],  # student_id
            'class_name': student[-1],   # class_name
            'total_sessions': total_sessions,
            'present_sessions': present_sessions,
            'absent_sessions': total_sessions - present_sessions,
            'attendance_rate': attendance_rate
        }
        
        return df, stats
    
    def export_comprehensive_report(self, class_id, start_date=None, end_date=None):
        """Xuất báo cáo tổng hợp"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        # Get class info
        classes = self.db.get_all_classes()
        class_info = None
        for cls in classes:
            if cls[0] == class_id:
                class_info = cls
                break
        
        if not class_info:
            return None
        
        # Create comprehensive Excel report
        filename = f"BaoCao_TongHop_{class_info[2]}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Summary
            summary_data = self.get_class_summary(class_id, start_date, end_date)
            summary_data.to_excel(writer, sheet_name='Tổng quan', index=False)
            
            # Sheet 2: Daily reports
            for single_date in pd.date_range(start_date, end_date):
                daily_data = self.generate_daily_report(class_id, single_date.date())
                if not daily_data.empty:
                    sheet_name = f"Ngày {single_date.strftime('%d-%m')}"
                    daily_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Sheet 3: Student statistics
            student_stats = self.get_student_statistics(class_id, start_date, end_date)
            student_stats.to_excel(writer, sheet_name='Thống kê Cá nhân', index=False)
        
        return filepath
    
    def get_class_summary(self, class_id, start_date, end_date):
        """Lấy tổng quan lớp học"""
        conn = self.db.get_connection()
        query = '''
        SELECT 
            DATE(ses.session_date) as date,
            ses.session_name,
            COUNT(DISTINCT s.id) as total_students,
            COUNT(ar.id) as present_count,
            ROUND(
                CAST(COUNT(ar.id) AS REAL) / COUNT(DISTINCT s.id) * 100, 2
            ) as attendance_rate
        FROM attendance_sessions ses
        JOIN classes c ON ses.class_id = c.id
        LEFT JOIN students s ON s.class_id = c.id AND s.is_active = 1
        LEFT JOIN attendance_records ar ON ar.session_id = ses.id AND ar.student_id = s.id
        WHERE c.id = ? 
        AND DATE(ses.session_date) BETWEEN ? AND ?
        GROUP BY ses.id, ses.session_date, ses.session_name
        ORDER BY ses.session_date
        '''
        
        df = pd.read_sql_query(query, conn, params=[class_id, start_date, end_date])
        conn.close()
        
        return df
    
    def get_student_statistics(self, class_id, start_date, end_date):
        """Lấy thống kê từng học sinh"""
        conn = self.db.get_connection()
        query = '''
        SELECT 
            s.student_id,
            s.full_name,
            COUNT(DISTINCT ses.id) as total_sessions,
            COUNT(ar.id) as present_sessions,
            COUNT(DISTINCT ses.id) - COUNT(ar.id) as absent_sessions,
            ROUND(
                CAST(COUNT(ar.id) AS REAL) / COUNT(DISTINCT ses.id) * 100, 2
            ) as attendance_rate
        FROM students s
        CROSS JOIN attendance_sessions ses
        LEFT JOIN attendance_records ar ON ar.student_id = s.id AND ar.session_id = ses.id
        WHERE s.class_id = ? 
        AND s.is_active = 1
        AND ses.class_id = ?
        AND DATE(ses.session_date) BETWEEN ? AND ?
        GROUP BY s.id, s.student_id, s.full_name
        ORDER BY s.full_name
        '''
        
        df = pd.read_sql_query(query, conn, params=[class_id, class_id, start_date, end_date])
        conn.close()
        
        return df

# Test function
def test_reports():
    """Test report generation"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from database.models import DatabaseManager
    
    db = DatabaseManager()
    reporter = AttendanceReportGenerator(db)
    
    # Test daily report
    classes = db.get_all_classes()
    if classes:
        class_id = classes[0][0]
        daily_report = reporter.generate_daily_report(class_id)
        print("Daily Report:")
        print(daily_report)
        
        # Export to Excel
        if not daily_report.empty:
            filepath = reporter.export_to_excel(
                daily_report, 
                f"daily_report_{date.today().strftime('%Y%m%d')}.xlsx"
            )
            print(f"Report exported to: {filepath}")

if __name__ == "__main__":
    test_reports()