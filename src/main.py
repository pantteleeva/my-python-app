import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox
import asyncio
import asyncmy
import threading
import traceback
import logging
import xlsxwriter
import os
import logging
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

#шрифт
def register_fonts():
    """Регистрирует DejaVuSans для поддержки кириллицы."""
    font_paths = {
        'DejaVuSans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'DejaVuSans-Bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    }
    try:
        for name, path in font_paths.items():
            if os.path.isfile(path):
                pdfmetrics.registerFont(TTFont(name, path))
                logging.info(f"Шрифт {name} зарегистрирован из {path}")
        pdfmetrics.registerFontFamily(
            'DejaVuSans',
            normal='DejaVuSans',
            bold='DejaVuSans-Bold'
        )
        return True
    except Exception as e:
        logging.warning(f"Не удалось зарегистрировать DejaVu: {e}. Используется fallback Helvetica.")
        return False


FONTS_REGISTERED = register_fonts()


#стиль оформления
STYLES = {
    'Title': ParagraphStyle(
        'Title',
        fontName='DejaVuSans-Bold' if FONTS_REGISTERED else 'Helvetica-Bold',
        fontSize=24,
        alignment=1,  
        spaceAfter=30,
    ),
    'Subtitle': ParagraphStyle(
        'Subtitle',
        fontName='DejaVuSans' if FONTS_REGISTERED else 'Helvetica',
        fontSize=16,
        alignment=1,
        spaceAfter=60,
        leading=20,
    ),
    'Normal': ParagraphStyle(
        'Normal',
        fontName='DejaVuSans' if FONTS_REGISTERED else 'Helvetica',
        fontSize=12,
        leading=16,
        spaceBefore=4,
        spaceAfter=4,
    ),
    'Header1': ParagraphStyle(
        'Header1',
        fontName='DejaVuSans-Bold' if FONTS_REGISTERED else 'Helvetica-Bold',
        fontSize=18,
        spaceAfter=12,
        keepWithNext=True,
    ),
    'Header2': ParagraphStyle(
        'Header2',
        fontName='DejaVuSans-Bold' if FONTS_REGISTERED else 'Helvetica-Bold',
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
        keepWithNext=True,  
    ),
    'Small': ParagraphStyle(
        'Small',
        fontName='DejaVuSans' if FONTS_REGISTERED else 'Helvetica',
        fontSize=10,
        leading=12,
    ),
    'SmallBold': ParagraphStyle(
        'SmallBold',
        fontName='DejaVuSans-Bold' if FONTS_REGISTERED else 'Helvetica-Bold',
        fontSize=10,
        leading=12,
    ),
    'TOCEntry': ParagraphStyle(
        'TOCEntry',
        fontName='DejaVuSans' if FONTS_REGISTERED else 'Helvetica',
        fontSize=12,
        leftIndent=20,
        spaceBefore=2,
        spaceAfter=2,
    ),
}


def safe_str(value, max_len=None):
    """Безопасное приведение к строке, замена None на '-', ограничение длины."""
    if value is None:
        return "-"
    s = str(value).strip()
    if not s:
        return "-"
    if max_len and len(s) > max_len:
        return s[:max_len-1] + "…"
    return s


# генерация pdf отчетов
class PDFExporter:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.styles = STYLES

    @staticmethod
    def safe_str(value, max_len=None):
        if value is None:
            return "-"
        s = str(value).strip()
        if not s:
            return "-"
        if max_len and len(s) > max_len:
            return s[:max_len-1] + "…"
        return s

    def _build_title_page(self, report_title, author, subtitle):
        """Создание титульной страницы с поддержкой кириллицы и центрированием."""
        elements = []

        title_font = 'DejaVuSans-Bold' if FONTS_REGISTERED else 'Helvetica-Bold'
        text_font = 'DejaVuSans' if FONTS_REGISTERED else 'Helvetica'

        title_style = ParagraphStyle(
            'CustomTitle',
            fontName=title_font,
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2E4057'),
            alignment=1  # ЦЕНТР
        )
        elements.append(Paragraph(report_title, title_style))
        elements.append(Spacer(1, 20))

        if subtitle:
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                fontName=text_font,
                fontSize=16,
                textColor=colors.HexColor('#566573'),
                alignment=1
            )
            elements.append(Paragraph(subtitle, subtitle_style))
            elements.append(Spacer(1, 30))

        info_style = ParagraphStyle(
            'CustomInfo',
            fontName=text_font,
            fontSize=12,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=1
        )
        elements.append(Paragraph(f"Автор: {author}", info_style))
        elements.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", info_style))
        elements.append(Paragraph("Проект выполнила: Пантелеева Юлиана Сергеевна", info_style))
        elements.append(Spacer(1, 50))

        return elements

    def _build_improved_bar_chart(self, labels, values, title):
        """Улучшенная столбчатая диаграмма."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from io import BytesIO

            fig, ax = plt.subplots(figsize=(12, 7))
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

            bars = ax.bar(range(len(labels)), values, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)

            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Виды животных', fontsize=12)
            ax.set_ylabel('Количество', fontsize=12)

            plt.xticks(
                range(len(labels)),
                labels,
                rotation=45,
                ha='right',
                fontsize=9
            )

            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                       f'{int(value)}', ha='center', va='bottom', fontsize=9)

            ax.grid(True, alpha=0.3, axis='y')
            ax.set_axisbelow(True)
            plt.tight_layout()

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', pad_inches=0.2)
            img_buffer.seek(0)
            plt.close()

            img = Image(img_buffer, width=180*mm, height=110*mm)
            return [img, Spacer(1, 12)]

        except Exception as e:
            logging.error(f"Ошибка создания столбчатой диаграммы: {e}")
            return [Paragraph("Ошибка построения диаграммы", self.styles['Normal'])]

    def _build_improved_pie_chart(self, labels, values, title):
        """Улучшенная круговая диаграмма: легенда снизу, отступы увеличены, нет наезда."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from io import BytesIO

            non_zero_indices = [i for i, v in enumerate(values) if v > 0]
            if not non_zero_indices:
                return [Paragraph("Нет данных для построения диаграммы", self.styles['Normal'])]

            filtered_labels = [labels[i] for i in non_zero_indices]
            filtered_values = [values[i] for i in non_zero_indices]
            fig, ax = plt.subplots(figsize=(10, 9))

            colors = plt.cm.Pastel1(np.linspace(0, 1, len(filtered_labels)))
            wedges, texts, autotexts = ax.pie(
                filtered_values,
                labels=None,  
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                pctdistance=0.75,  
                textprops={'fontsize': 10, 'weight': 'bold'}
            )

            #настройка процентов 
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontsize(10)

            ax.set_title(title, fontsize=14, fontweight='bold', pad=30)

            #легенда диаграмма
            legend_labels = [f"{label} — {value} шт." for label, value in zip(filtered_labels, filtered_values)]
            legend = ax.legend(
                wedges, legend_labels,
                title="Распределение",
                loc='upper center',
                bbox_to_anchor=(0.5, -0.12),  
                ncol=2,
                fontsize=9,
                frameon=True,
                fancybox=True,
                shadow=True
            )
            legend.get_title().set_fontsize('10')
            legend.get_title().set_fontweight('bold')

            ax.axis('equal')
            plt.tight_layout(pad=3.0)  

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', pad_inches=0.3)
            img_buffer.seek(0)
            plt.close()

            img = Image(img_buffer, width=160*mm, height=120*mm)
            return [img, Spacer(1, 20)]

        except Exception as e:
            logging.error(f"Ошибка создания круговой диаграммы: {e}")
            return [Paragraph("Ошибка построения диаграммы", self.styles['Normal'])]

    def _build_toc(self, entries):
        """Оглавление на отдельной странице."""
        story = []
        story.append(Paragraph("Оглавление", self.styles['Header1']))
        story.append(Spacer(1, 12))
        for entry in entries:
            story.append(Paragraph(f"• {entry}", self.styles['TOCEntry']))
        story.append(PageBreak())
        return story

    def _build_table(self, headers, rows, col_widths=None, min_rows=10):
        """Генерация таблицы с дополняющими строками."""
        data = [[Paragraph(h, self.styles['SmallBold']) for h in headers]]
        for row in rows:
            data.append([Paragraph(self.safe_str(cell, 30), self.styles['Small']) for cell in row])
        while len(data) < min_rows + 1:
            data.append([Paragraph("-", self.styles['Small']) for _ in headers])

        if col_widths is None:
            col_widths = [80] * len(headers)
            total = sum(col_widths)
            if total > 500:
                scale = 500 / total
                col_widths = [int(w * scale) for w in col_widths]

        table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
        header_font = 'DejaVuSans-Bold' if FONTS_REGISTERED else 'Helvetica-Bold'
        cell_font = 'DejaVuSans' if FONTS_REGISTERED else 'Helvetica'
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), header_font),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), cell_font),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
        ]))
        return [table, Spacer(1, 15)]

    def export_statistical_report(self, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "статистический отчет.pdf" 

        try:
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                topMargin=20 * mm,
                bottomMargin=20 * mm,
                leftMargin=15 * mm,   
                rightMargin=15 * mm
            )
            story = []

            #титульная страница
            story.extend(self._build_title_page(
                report_title="Статистический отчёт",
                author="Система отчетности",
                subtitle="Аналитика и метрики"
            ))
            story.append(PageBreak())

            #оглавление на отдельной странице
            toc_entries = [
                "1. Общая статистика",
                "2. Распределение по видам",
                "3. Состояние здоровья животных"
            ]
            story.extend(self._build_toc(toc_entries))

            #данные из бд
            total_animals = self.db_manager.get_animals_count() or 0
            total_staff = len(self.db_manager.get_all_staff() or [])
            total_habitats = len(self.db_manager.get_all_habitats() or [])
            total_species = len(self.db_manager.get_all_species() or [])
            feedings_30 = self.db_manager.get_recent_feedings_count(30) or 0
            observations_30 = self.db_manager.get_new_observations_count(30) or 0

            species_data = self.db_manager.get_species_distribution() or []
            species_labels = [item['name'] for item in species_data]
            species_values = [item['count'] for item in species_data]

            health_data = self.db_manager.get_health_distribution() or [0, 0, 0, 0]
            health_labels = ["Отличное", "Хорошее", "Удовл.", "Требует внимания"]

            #общая статистика
            story.append(Paragraph("1. Общая статистика", self.styles['Header1']))
            metrics = [
                ("Всего животных", total_animals),
                ("Сотрудников", total_staff),
                ("Мест обитания", total_habitats),
                ("Видов животных", total_species),
                ("Кормлений за 30 дней", feedings_30),
                ("Осмотр здоровья за 30 дней", observations_30),
            ]
            for title, value in metrics:
                story.append(Paragraph(f"• <b>{title}:</b> {value}", self.styles['Normal']))
            story.append(Spacer(1, 20))

            #график: Распределение по видам
            bar_title = Paragraph("2. Распределение по видам", self.styles['Header2'])
            bar_chart = self._build_improved_bar_chart(species_labels[:12], species_values[:12], "Количество животных по видам")
            story.append(KeepTogether([bar_title] + bar_chart))

            #график: Состояние здоровья 
            pie_title = Paragraph("3. Состояние здоровья животных", self.styles['Header2'])
            pie_chart = self._build_improved_pie_chart(health_labels, health_data, "Распределение по состоянию здоровья")
            story.append(KeepTogether([pie_title] + pie_chart))

            doc.build(story)
            logging.info(f"✅ Статистический отчёт сохранён: {filename}")
            return filename

        except Exception as e:
            logging.error(f"❌ Ошибка генерации статистического отчёта: {e}", exc_info=True)
            return None

    def export_detailed_report(self, filename=None):
        if not filename:
            filename = "детальный отчет.pdf"

        try:
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                topMargin=20 * mm,
                bottomMargin=20 * mm,
                leftMargin=15 * mm,
                rightMargin=15 * mm
            )
            story = []

            #титульная страница
            story.extend(self._build_title_page(
                report_title="Детальный отчёт",
                author="Система отчетности",
                subtitle="Табличные данные"
            ))
            story.append(PageBreak())

            #оглавление
            toc_entries = [
                "1. Сотрудники заповедника",
                "2. Животные",
                "3. Кормления",
                "4. Наблюдения за здоровьем",
                "5. Места обитания",
                "6. Виды животных"
            ]
            story.extend(self._build_toc(toc_entries))

            #сотрудники
            story.append(Paragraph("1. Сотрудники заповедника", self.styles['Header1']))
            staff = self.db_manager.get_all_staff() or []
            staff.sort(key=lambda x: x.get('full_name', '').lower())
            staff_rows = [
                [s['full_name'], s['post'], s['email']]
                for s in staff
            ]
            story.extend(self._build_table(
                headers=["ФИО", "Должность", "Email"],
                rows=staff_rows,
                col_widths=[180, 120, 150],
                min_rows=10
            ))
            story.append(PageBreak())

            #животные
            story.append(Paragraph("2. Животные", self.styles['Header1']))
            animals = self.db_manager.get_all_animals() or []
            animals.sort(key=lambda x: (x.get('nickname') or '').lower())
            animal_rows = [
                [
                    a['nickname'] or "-",
                    a['species_name'] or "-",
                    a['gender_name'] or "-",
                    str(a['date_of_birth']) if a['date_of_birth'] else "-",
                    a['habitat_name'] or "-",
                    a['special_signs'][:40] + "…" if a.get('special_signs') and len(a['special_signs']) > 40 else (a.get('special_signs') or "-")
                ]
                for a in animals
            ]
            story.extend(self._build_table(
                headers=["Кличка", "Вид", "Пол", "Дата рождения", "Место обитания", "Особые приметы"],
                rows=animal_rows,
                col_widths=[80, 80, 50, 80, 90, 100],
                min_rows=10
            ))
            story.append(PageBreak())

            #кормления
            story.append(Paragraph("3. Кормления", self.styles['Header1']))
            feedings = self.db_manager.get_all_feedings() or []
            feedings.sort(key=lambda x: x.get('feeding_date', ''), reverse=True)
            feeding_rows = [
                [
                    str(f['feeding_date']) if f['feeding_date'] else "-",
                    f['animal_name'] or "-",
                    f['food_type'] or "-",
                    f['appetite_assessment'],
                    f['staff_name'] or "-"
                ]
                for f in feedings
            ]
            story.extend(self._build_table(
                headers=["Дата", "Животное", "Тип корма", "Оценка аппетита", "Сотрудник"],
                rows=feeding_rows,
                col_widths=[80, 85, 120, 100, 100],
                min_rows=10
            ))
            story.append(PageBreak())

            #наблюдения за здоровьем
            story.append(Paragraph("4. Наблюдения за здоровьем", self.styles['Header1']))
            obs = self.db_manager.get_all_health_observations() or []
            obs.sort(key=lambda x: x.get('date_of_inspection', ''), reverse=True)
            obs_rows = [
                [
                    str(o['date_of_inspection']) if o['date_of_inspection'] else "-",
                    o['animal_name'] or "-",
                    o['general_condition'] or "-",
                    o['diagnosis'][:30] + "…" if o.get('diagnosis') and len(o['diagnosis']) > 30 else (o.get('diagnosis') or "-"),
                    o['notes'][:30] + "…" if o.get('notes') and len(o['notes']) > 30 else (o.get('notes') or "-"),
                    o['staff_name'] or "-"
                ]
                for o in obs
            ]
            story.extend(self._build_table(
                headers=["Дата", "Животное", "Состояние", "Диагноз", "Примечания", "Сотрудник"],
                rows=obs_rows,
                col_widths=[80, 75, 80, 95, 95, 80],
                min_rows=10
            ))
            story.append(PageBreak())

            #места обитания
            story.append(Paragraph("5. Места обитания", self.styles['Header1']))
            habitats = self.db_manager.get_all_habitats() or []
            habitats.sort(key=lambda x: x.get('name', '').lower())
            habitat_rows = [
                [
                    h['name'],
                    h['terrain_type'] or "-",
                    str(h['square']) + " м²" if h['square'] else "-",
                    h['description'][:50] + "…" if h.get('description') and len(h['description']) > 50 else (h.get('description') or "-")
                ]
                for h in habitats
            ]
            story.extend(self._build_table(
                headers=["Название", "Тип местности", "Площадь", "Описание"],
                rows=habitat_rows,
                col_widths=[120, 100, 80, 200],
                min_rows=10
            ))
            story.append(PageBreak())

            #виды животных
            story.append(Paragraph("6. Виды животных", self.styles['Header1']))
            species = self.db_manager.get_all_species() or []
            species.sort(key=lambda x: x.get('name', '').lower())
            species_rows = [
                [s['name'], s['scientific_name'] or "-", s['status'] or "-"]
                for s in species
            ]
            story.extend(self._build_table(
                headers=["Название вида", "Научное название", "Статус"],
                rows=species_rows,
                col_widths=[160, 180, 120],
                min_rows=10
            ))

            #сохрнение
            doc.build(story)
            logging.info(f"✅ Детальный отчёт сохранён: {filename}")
            return filename

        except Exception as e:
            logging.error(f"❌ Ошибка генерации детального отчёта: {e}", exc_info=True)
            return None

    
class ExcelExporter:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    def export_complete_report(self, filename=None):
        """Создание полного отчета в формате XLSX"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wildlife_reserve_report_{timestamp}.xlsx"
        try:
            workbook = xlsxwriter.Workbook(filename, {'default_date_format': 'dd.mm.yyyy'})
            self._create_main_data_sheet(workbook) 
            self._create_analytics_sheet(workbook)
            self._create_visualization_sheet(workbook)
            workbook.close()
            self.logger.info(f"Отчет успешно создан: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Ошибка при создании отчета: {e}\n{traceback.format_exc()}")
            return None

    def _create_main_data_sheet(self, workbook):
        """Лист 1: Основные данные (все таблицы на одном листе)"""
        worksheet = workbook.add_worksheet('Основные данные')
        
        #настройка ширины колонок
        column_widths = [8, 20, 15, 10, 12, 12, 20, 25, 30, 15, 20, 15, 25, 20, 20, 25, 20, 20]
        for col, width in enumerate(column_widths[:18]):
            worksheet.set_column(col, col, width)
        
        #стиль оформления
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'bg_color': '#2E7D32',  
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4CAF50',  
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })
        
        border_format = workbook.add_format({'border': 1})
        center_format = workbook.add_format({'align': 'center', 'border': 1})
        date_format = workbook.add_format({'num_format': 'dd.mm.yyyy', 'border': 1})
        wrap_format = workbook.add_format({'text_wrap': True, 'border': 1, 'valign': 'top'})
        
        current_row = 0
        
        #животные
        worksheet.merge_range(f'A{current_row+1}:H{current_row+1}', 'ЖИВОТНЫЕ', title_format)
        current_row += 1
        
        #заголовки
        animal_headers = ['ID', 'Кличка', 'Вид', 'Пол', 'Дата рождения', 'Дата поступления', 'Место обитания', 'Особые приметы']
        for col, header in enumerate(animal_headers):
            worksheet.write(current_row, col, header, header_format)
        current_row += 1
        
        #данные животных
        animals_data = self.db_manager.get_all_animals()
        for animal in animals_data:
            worksheet.write(current_row, 0, animal['id'], center_format)
            
            nickname = animal['nickname'] or '-'
            if len(str(nickname)) > 15:
                worksheet.write(current_row, 1, nickname, wrap_format)
            else:
                worksheet.write(current_row, 1, nickname, border_format)
            
            #Вид
            species = animal['species_name'] or '-'
            if len(str(species)) > 12:
                worksheet.write(current_row, 2, species, wrap_format)
            else:
                worksheet.write(current_row, 2, species, border_format)
            
            worksheet.write(current_row, 3, animal['gender_name'], center_format)
            
            #Даты
            if animal['date_of_birth']:
                try:
                    birth_date = datetime.strptime(str(animal['date_of_birth']), '%Y-%m-%d')
                    worksheet.write(current_row, 4, birth_date, date_format)
                except:
                    worksheet.write(current_row, 4, str(animal['date_of_birth']), center_format)
            else:
                worksheet.write(current_row, 4, '-', center_format)
                
            if animal['date_of_admission']:
                try:
                    admission_date = datetime.strptime(str(animal['date_of_admission']), '%Y-%m-%d')
                    worksheet.write(current_row, 5, admission_date, date_format)
                except:
                    worksheet.write(current_row, 5, str(animal['date_of_admission']), center_format)
            else:
                worksheet.write(current_row, 5, '-', center_format)
            
            #Место обитания
            habitat = animal['habitat_name'] or '-'
            if len(str(habitat)) > 15:
                worksheet.write(current_row, 6, habitat, wrap_format)
            else:
                worksheet.write(current_row, 6, habitat, border_format)
            
            #Особые приметы
            special_signs = animal['special_signs'] or '-'
            worksheet.write(current_row, 7, special_signs, wrap_format)
            
            current_row += 1
        
        current_row += 2  
        
        #сотрудники
        worksheet.merge_range(f'A{current_row+1}:D{current_row+1}', 'СОТРУДНИКИ', title_format)
        current_row += 1
        
        #заголовки таблицы 
        staff_headers = ['ID', 'ФИО', 'Должность', 'Email']
        for col, header in enumerate(staff_headers):
            worksheet.write(current_row, col, header, header_format)
        current_row += 1
        
        #данные 
        staff_data = self.db_manager.get_all_staff()
        for staff in staff_data:
            worksheet.write(current_row, 0, staff['id'], center_format)
            
            #ФИО
            full_name = staff['full_name'] or '-'
            if len(str(full_name)) > 20:
                worksheet.write(current_row, 1, full_name, wrap_format)
            else:
                worksheet.write(current_row, 1, full_name, border_format)
            
            #Должность
            post = staff['post'] or '-'
            if len(str(post)) > 15:
                worksheet.write(current_row, 2, post, wrap_format)
            else:
                worksheet.write(current_row, 2, post, border_format)
            
            #Email
            email = staff['email'] or '-'
            worksheet.write(current_row, 3, email, wrap_format)
            
            current_row += 1
        
        current_row += 2  
        
        #кормления
        worksheet.merge_range(f'A{current_row+1}:F{current_row+1}', 'КОРМЛЕНИЯ', title_format)
        current_row += 1
        
        #Заголовки
        feeding_headers = ['ID', 'Дата', 'Животное', 'Тип корма', 'Оценка аппетита', 'Сотрудник']
        for col, header in enumerate(feeding_headers):
            worksheet.write(current_row, col, header, header_format)
        current_row += 1
        
        #данные
        feedings_data = self.db_manager.get_all_feedings()
        for feeding in feedings_data:
            worksheet.write(current_row, 0, feeding['id'], center_format)
            
            if feeding['feeding_date']:
                try:
                    feed_date = datetime.strptime(str(feeding['feeding_date']), '%Y-%m-%d')
                    worksheet.write(current_row, 1, feed_date, date_format)
                except:
                    worksheet.write(current_row, 1, str(feeding['feeding_date']), border_format)
            else:
                worksheet.write(current_row, 1, '-', center_format)
            
            #животное
            animal_name = feeding['animal_name'] or '-'
            if len(str(animal_name)) > 15:
                worksheet.write(current_row, 2, animal_name, wrap_format)
            else:
                worksheet.write(current_row, 2, animal_name, border_format)
            
            #тип корма
            food_type = feeding['food_type'] or '-'
            if len(str(food_type)) > 15:
                worksheet.write(current_row, 3, food_type, wrap_format)
            else:
                worksheet.write(current_row, 3, food_type, border_format)
            
            worksheet.write(current_row, 4, feeding['appetite_assessment'], center_format)
            
            #сотрудник
            staff_name = feeding['staff_name'] or '-'
            if len(str(staff_name)) > 20:
                worksheet.write(current_row, 5, staff_name, wrap_format)
            else:
                worksheet.write(current_row, 5, staff_name, border_format)
            
            current_row += 1
        
        current_row += 2 
        
        #место обитания
        worksheet.merge_range(f'A{current_row+1}:E{current_row+1}', 'МЕСТА ОБИТАНИЯ', title_format)
        current_row += 1
        
        # Заголовки таблицы
        habitat_headers = ['ID', 'Название', 'Площадь', 'Тип местности', 'Описание']
        for col, header in enumerate(habitat_headers):
            worksheet.write(current_row, col, header, header_format)
        current_row += 1
        
        # Данные
        habitats_data = self.db_manager.get_all_habitats()
        for habitat in habitats_data:
            worksheet.write(current_row, 0, habitat['id'], center_format)
            
            # Название
            name = habitat['name'] or '-'
            if len(str(name)) > 15:
                worksheet.write(current_row, 1, name, wrap_format)
            else:
                worksheet.write(current_row, 1, name, border_format)
            
            worksheet.write(current_row, 2, habitat['square'] or 0, center_format)
            
            #Тип местности
            terrain_type = habitat['terrain_type'] or '-'
            if len(str(terrain_type)) > 15:
                worksheet.write(current_row, 3, terrain_type, wrap_format)
            else:
                worksheet.write(current_row, 3, terrain_type, border_format)
            
            #Описание
            description = habitat['description'] or '-'
            worksheet.write(current_row, 4, description, wrap_format)
            
            current_row += 1
        
        current_row += 2  
        
        #наблюдение за здоровьем 
        worksheet.merge_range(f'A{current_row+1}:G{current_row+1}', 'НАБЛЮДЕНИЯ ЗА ЗДОРОВЬЕМ', title_format)
        current_row += 1
        
        #заголовки
        observation_headers = ['ID', 'Дата осмотра', 'Животное', 'Общее состояние', 'Диагноз', 'Примечания', 'Сотрудник']
        for col, header in enumerate(observation_headers):
            worksheet.write(current_row, col, header, header_format)
        current_row += 1
        
        #данные
        observations_data = self.db_manager.get_all_health_observations()
        for observation in observations_data:
            worksheet.write(current_row, 0, observation['id'], center_format)
            
            if observation['date_of_inspection']:
                try:
                    inspection_date = datetime.strptime(str(observation['date_of_inspection']), '%Y-%m-%d')
                    worksheet.write(current_row, 1, inspection_date, date_format)
                except:
                    worksheet.write(current_row, 1, str(observation['date_of_inspection']), border_format)
            else:
                worksheet.write(current_row, 1, '-', center_format)
            
            #Животное
            animal_name = observation['animal_name'] or '-'
            if len(str(animal_name)) > 15:
                worksheet.write(current_row, 2, animal_name, wrap_format)
            else:
                worksheet.write(current_row, 2, animal_name, border_format)
            
            #Общее состояние
            condition = observation['general_condition'] or '-'
            if len(str(condition)) > 15:
                worksheet.write(current_row, 3, condition, wrap_format)
            else:
                worksheet.write(current_row, 3, condition, border_format)
            
            #Диагноз
            diagnosis = observation['diagnosis'] or '-'
            if len(str(diagnosis)) > 20:
                worksheet.write(current_row, 4, diagnosis, wrap_format)
            else:
                worksheet.write(current_row, 4, diagnosis, border_format)
            
            #Примечания 
            notes = observation['notes'] or '-'
            worksheet.write(current_row, 5, notes, wrap_format)
            
            #Сотрудник
            staff_name = observation['staff_name'] or '-'
            if len(str(staff_name)) > 15:
                worksheet.write(current_row, 6, staff_name, wrap_format)
            else:
                worksheet.write(current_row, 6, staff_name, border_format)
            
            current_row += 1

        #Автофильтры
        if animals_data:
            worksheet.autofilter(1, 0, 1 + len(animals_data), len(animal_headers) - 1)
        
        staff_start = 3 + len(animals_data)
        if staff_data:
            worksheet.autofilter(staff_start, 0, staff_start + len(staff_data), len(staff_headers) - 1)
        
        feedings_start = staff_start + len(staff_data) + 3
        if feedings_data:
            worksheet.autofilter(feedings_start, 0, feedings_start + len(feedings_data), len(feeding_headers) - 1)
        
        habitats_start = feedings_start + len(feedings_data) + 3
        if habitats_data:
            worksheet.autofilter(habitats_start, 0, habitats_start + len(habitats_data), len(habitat_headers) - 1)
        
        observations_start = habitats_start + len(habitats_data) + 3
        if observations_data:
            worksheet.autofilter(observations_start, 0, observations_start + len(observations_data), len(observation_headers) - 1)

    def _create_analytics_sheet(self, workbook):
        """Лист 2: Аналитика"""
        worksheet = workbook.add_worksheet('Аналитика')
        #Настройка ширины колонок
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        #Стили с зеленой цветовой схемой
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'bg_color': '#2E7D32',  
            'font_color': 'white', 'align': 'center', 'border': 1
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4CAF50', 'font_color': 'white', 
            'border': 1, 'align': 'center'
        })
        number_format = workbook.add_format({'num_format': '#,##0', 'border': 1})
        percent_format = workbook.add_format({'num_format': '0.0%', 'border': 1})
        border_format = workbook.add_format({'border': 1})
        bold_format = workbook.add_format({'bold': True, 'border': 1})
        wrap_format = workbook.add_format({'text_wrap': True, 'border': 1, 'valign': 'top'})
        #Заголовок с ФИО 
        worksheet.merge_range('A1:D1', 'АНАЛИТИКА ЗАПОВЕДНИКА', title_format)
        worksheet.merge_range('A2:D2', 'Проект выполнила: Пантелеева Юлиана Сергеевна', title_format)
        #Блок  Основные метрики
        worksheet.merge_range('A4:D4', 'КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ', header_format)
        #Получаем данные для аналитики
        total_animals = self.db_manager.get_animals_count() or 0
        species_data = self.db_manager.get_species_distribution() or []
        health_data = self.db_manager.get_health_distribution() or [0, 0, 0, 0]
        feedings_count = self.db_manager.get_recent_feedings_count(30) or 0
        observations_count = self.db_manager.get_new_observations_count(30) or 0
        staff_count = len(self.db_manager.get_all_staff() or [])
        habitats_count = len(self.db_manager.get_all_habitats() or [])
        metrics = [
            ('Общее количество животных', total_animals),
            ('Количество сотрудников', staff_count),
            ('Количество мест обитания', habitats_count),
            ('Кормлений за последние 30 дней', feedings_count),
            ('Осмотров здоровья за 30 дней', observations_count),
            ('Количество видов животных', len(species_data))
        ]
        for row, (metric, value) in enumerate(metrics, 5):
            if len(str(metric)) > 25:
                worksheet.write(row, 0, metric, wrap_format)
            else:
                worksheet.write(row, 0, metric, border_format)
            worksheet.write(row, 1, value, number_format)
        #Блок 2 Распределение по видам
        species_row = len(metrics) + 7
        worksheet.merge_range(f'A{species_row}:D{species_row}', 'РАСПРЕДЕЛЕНИЕ ПО ВИДАМ', header_format)
        worksheet.write(species_row + 1, 0, 'Вид', header_format)
        worksheet.write(species_row + 1, 1, 'Количество', header_format)
        worksheet.write(species_row + 1, 2, 'Доля', header_format)
        total_species_count = sum(item['count'] for item in species_data) if species_data else 1
        for i, species in enumerate(species_data, species_row + 2):
            #Название вида 
            species_name = species['name'] or '-'
            if len(str(species_name)) > 25:
                worksheet.write(i, 0, species_name, wrap_format)
            else:
                worksheet.write(i, 0, species_name, border_format)
            worksheet.write(i, 1, species['count'], number_format)
            if total_species_count > 0:
                worksheet.write(i, 2, species['count'] / total_species_count, percent_format)
        #Итог по видам
        if species_data:
            total_row = species_row + 2 + len(species_data)
            worksheet.write(total_row, 0, 'ВСЕГО', bold_format)
            worksheet.write(total_row, 1, total_species_count, bold_format)
            worksheet.write(total_row, 2, 1.0, percent_format)
        #Блок 3 Состояние здоровья
        health_row = species_row + len(species_data) + 5 if species_data else species_row + 5
        worksheet.merge_range(f'A{health_row}:D{health_row}', 'СОСТОЯНИЕ ЗДОРОВЬЯ ЖИВОТНЫХ', header_format)
        health_labels = ['Отличное', 'Хорошее', 'Удовлетворительное', 'Требует внимания']
        worksheet.write(health_row + 1, 0, 'Состояние', header_format)
        worksheet.write(health_row + 1, 1, 'Количество', header_format)
        worksheet.write(health_row + 1, 2, 'Доля', header_format)
        total_health = sum(health_data) if health_data else 1
        for i, (label, count) in enumerate(zip(health_labels, health_data)):
            #Состояние здоровья
            if len(str(label)) > 25:
                worksheet.write(health_row + 2 + i, 0, label, wrap_format)
            else:
                worksheet.write(health_row + 2 + i, 0, label, border_format)
            worksheet.write(health_row + 2 + i, 1, count, number_format)
            if total_health > 0:
                worksheet.write(health_row + 2 + i, 2, count / total_health, percent_format)
        #Итог по здоровью
        health_total_row = health_row + 2 + len(health_labels)
        worksheet.write(health_total_row, 0, 'ВСЕГО', bold_format)
        worksheet.write(health_total_row, 1, total_health, bold_format)
        worksheet.write(health_total_row, 2, 1.0, percent_format)
        #Блок 4 Статистика кормлений по типам корма
        feeding_stats_row = health_total_row + 3
        worksheet.merge_range(f'A{feeding_stats_row}:D{feeding_stats_row}', 'СТАТИСТИКА КОРМЛЕНИЙ ПО ТИПАМ КОРМА', header_format)
        worksheet.write(feeding_stats_row + 1, 0, 'Тип корма', header_format)
        worksheet.write(feeding_stats_row + 1, 1, 'Количество кормлений', header_format)
        #данные о кормлениях для статистики
        feedings_data = self.db_manager.get_all_feedings() or []
        food_stats = {}
        for feeding in feedings_data:
            food_type = feeding['food_type']
            if food_type in food_stats:
                food_stats[food_type] += 1
            else:
                food_stats[food_type] = 1
        for i, (food_type, count) in enumerate(food_stats.items(), feeding_stats_row + 2):
            #Тип корма с переносом текста
            if len(str(food_type)) > 25:
                worksheet.write(i, 0, food_type, wrap_format)
            else:
                worksheet.write(i, 0, food_type, border_format)
            worksheet.write(i, 1, count, number_format)
        #Блок 5 Выводы
        conclusions_row = feeding_stats_row + len(food_stats) + 4
        worksheet.merge_range(f'A{conclusions_row}:D{conclusions_row}', 'ВЫВОДЫ ПО АНАЛИТИКЕ', header_format)
        #анализир данные для выводов
        dominant_species = max(species_data, key=lambda x: x['count']) if species_data else None
        health_status = self._get_health_summary(health_data)
        conclusions = [
            f"Всего в заповеднике содержится {total_animals} животных",
            f"Заповедник обслуживают {staff_count} сотрудников",
            f"Представлено {len(species_data)} различных видов животных",
            f"Наиболее распространенный вид: {dominant_species['name'] if dominant_species else 'нет данных'}",
            f"За последний месяц проведено {feedings_count} кормлений и {observations_count} осмотров",
            f"Общее состояние животных: {health_status}"
        ]
        for i, conclusion in enumerate(conclusions, conclusions_row + 1):
            worksheet.merge_range(f'A{i}:D{i}', f"• {conclusion}", wrap_format)

    def _create_visualization_sheet(self, workbook):
        """Лист 3: Визуализация"""
        worksheet = workbook.add_worksheet('Визуализация')
        #настройка ширины колонок
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        #Стили
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'bg_color': '#2E7D32', 
            'font_color': 'white', 'align': 'center'
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4CAF50', 'font_color': 'white',  
            'align': 'center'
        })
        wrap_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1
        })
        # Заголовок с ФИО студента
        worksheet.merge_range('A1:C1', 'ВИЗУАЛИЗАЦИЯ ДАННЫХ ЗАПОВЕДНИКА', title_format)
        worksheet.merge_range('A2:C2', 'Проект выполнила: Пантелеева Юлиана Сергеевна', title_format)
        # Получаем данные для графиков
        species_data = self.db_manager.get_species_distribution() or []
        health_data = self.db_manager.get_health_distribution() or [0, 0, 0, 0]
        habitats_data = self.db_manager.get_all_habitats() or []
        # Диаграмма 1: Распределение по видам (столбчатая)
        if species_data:
            # Подготавливаем данные для диаграммы
            data_row = 4
            worksheet.write(data_row, 0, 'Вид', header_format)
            worksheet.write(data_row, 1, 'Количество животных', header_format)
            for i, species in enumerate(species_data, data_row + 1):
                # Название вида с переносом текста
                species_name = species['name'] or '-'
                if len(str(species_name)) > 20:
                    worksheet.write(i, 0, species_name, wrap_format)
                else:
                    worksheet.write(i, 0, species_name)
                worksheet.write(i, 1, species['count'])
            chart1 = workbook.add_chart({'type': 'column'})
            chart1.add_series({
                'name': 'Количество животных',
                'categories': f'=Визуализация!$A${data_row + 2}:$A${data_row + 1 + len(species_data)}',
                'values': f'=Визуализация!$B${data_row + 2}:$B${data_row + 1 + len(species_data)}',
                'data_labels': {'value': True, 'position': 'outside_end'},
                'fill': {'color': '#4CAF50'}  # Зеленый цвет
            })
            chart1.set_title({'name': 'Распределение животных по видам'})
            chart1.set_x_axis({'name': 'Виды животных'})
            chart1.set_y_axis({'name': 'Количество животных'})
            chart1.set_style(11)
            worksheet.insert_chart('E2', chart1, {'x_offset': 25, 'y_offset': 10, 'x_scale': 1.5, 'y_scale': 1.3})
        #диаграмма 2 Состояние здоровья
        if health_data and sum(health_data) > 0:
            health_labels = ['Отличное', 'Хорошее', 'Удовлетворительное', 'Требует внимания']
            health_row = data_row + len(species_data) + 5
            worksheet.write(health_row, 0, 'Состояние здоровья', header_format)
            worksheet.write(health_row, 1, 'Количество', header_format)
            for i, (label, count) in enumerate(zip(health_labels, health_data)):
                #Состояние здоровья
                if len(str(label)) > 15:
                    worksheet.write(health_row + 1 + i, 0, label, wrap_format)
                else:
                    worksheet.write(health_row + 1 + i, 0, label)
                worksheet.write(health_row + 1 + i, 1, count)
            chart2 = workbook.add_chart({'type': 'pie'})
            chart2.add_series({
                'name': 'Состояние здоровья',
                'categories': f'=Визуализация!$A${health_row + 2}:$A${health_row + 1 + len(health_labels)}',
                'values': f'=Визуализация!$B${health_row + 2}:$B${health_row + 1 + len(health_labels)}',
                'data_labels': {
                    'percentage': True,
                    'leader_lines': True,
                    'category': True,
                    'position': 'outside_end'
                }
            })
            chart2.set_title({'name': 'Состояние здоровья животных'})
            chart2.set_style(10)
            worksheet.insert_chart('E20', chart2, {'x_offset': 25, 'y_offset': 10, 'x_scale': 1.3, 'y_scale': 1.3})
        #диаграмма 3 распределение по полу
        animals_data = self.db_manager.get_all_animals() or []
        if animals_data:
            gender_stats = {}
            for animal in animals_data:
                gender = animal['gender_name']
                if gender in gender_stats:
                    gender_stats[gender] += 1
                else:
                    gender_stats[gender] = 1
            gender_row = health_row + len(health_labels) + 5
            worksheet.write(gender_row, 0, 'Пол', header_format)
            worksheet.write(gender_row, 1, 'Количество', header_format)
            for i, (gender, count) in enumerate(gender_stats.items(), gender_row + 1):
                worksheet.write(i, 0, gender)
                worksheet.write(i, 1, count)
            chart3 = workbook.add_chart({'type': 'bar'})
            chart3.add_series({
                'name': 'Распределение по полу',
                'categories': f'=Визуализация!$A${gender_row + 2}:$A${gender_row + 1 + len(gender_stats)}',
                'values': f'=Визуализация!$B${gender_row + 2}:$B${gender_row + 1 + len(gender_stats)}',
                'data_labels': {'value': True},
                'fill': {'color': '#66BB6A'}  
            })
            chart3.set_title({'name': 'Распределение животных по полу'})
            chart3.set_x_axis({'name': 'Количество животных'})
            chart3.set_y_axis({'name': 'Пол'})
            chart3.set_style(8)
            worksheet.insert_chart('E38', chart3, {'x_offset': 25, 'y_offset': 10, 'x_scale': 1.3, 'y_scale': 1.0})
        #диаграмма 4 площади мест обитания
        if habitats_data:
            habitats_row = gender_row + len(gender_stats) + 5
            worksheet.write(habitats_row, 0, 'Место обитания', header_format)
            worksheet.write(habitats_row, 1, 'Площадь (кв.м)', header_format)
            for i, habitat in enumerate(habitats_data, habitats_row + 1):
                #название места обитания
                habitat_name = habitat['name'] or '-'
                if len(str(habitat_name)) > 20:
                    worksheet.write(i, 0, habitat_name, wrap_format)
                else:
                    worksheet.write(i, 0, habitat_name)
                worksheet.write(i, 1, habitat['square'] or 0)
            chart4 = workbook.add_chart({'type': 'line'})
            chart4.add_series({
                'name': 'Площадь мест обитания',
                'categories': f'=Визуализация!$A${habitats_row + 2}:$A${habitats_row + 1 + len(habitats_data)}',
                'values': f'=Визуализация!$B${habitats_row + 2}:$B${habitats_row + 1 + len(habitats_data)}',
                'marker': {'type': 'circle', 'size': 6},
                'line': {'color': '#388E3C', 'width': 2.5}
            })
            chart4.set_title({'name': 'Площади мест обитания'})
            chart4.set_x_axis({'name': 'Места обитания'})
            chart4.set_y_axis({'name': 'Площадь (кв.м)'})
            chart4.set_style(2)
            worksheet.insert_chart('E55', chart4, {'x_offset': 25, 'y_offset': 10, 'x_scale': 1.5, 'y_scale': 1.0})
        #инфографика
        summary_row = habitats_row + len(habitats_data) + 5 if habitats_data else gender_row + len(gender_stats) + 5
        worksheet.merge_range(f'A{summary_row}:C{summary_row}', 'СВОДКА ПО ЗАПОВЕДНИКУ', title_format)
        total_animals = len(animals_data)
        total_species = len(species_data)
        total_habitats = len(habitats_data)
        total_staff = len(self.db_manager.get_all_staff() or [])
        summary_data = [
            f"Всего животных: {total_animals}",
            f"Видов животных: {total_species}",
            f"Мест обитания: {total_habitats}",
            f"Сотрудников: {total_staff}",
            f"Состояние системы: {'Отличное' if total_animals > 0 else 'Требует внимания'}"
        ]
        for i, line in enumerate(summary_data, summary_row + 1):
            worksheet.merge_range(f'A{i}:C{i}', f"📊 {line}", header_format)

    def _get_health_summary(self, health_data):
        """Анализ состояния здоровья животных"""
        if not health_data or sum(health_data) == 0:
            return "нет данных"
        excellent, good, satisfactory, needs_attention = health_data
        total = sum(health_data)
        excellent_percent = (excellent / total) * 100
        good_percent = (good / total) * 100
        if excellent_percent > 70:
            return "Отличное"
        elif excellent_percent + good_percent > 80:
            return "Хорошее"
        elif excellent_percent + good_percent > 60:
            return "Удовлетворительное"
        else:
            return "Требует внимания"


class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.is_connected = False
        self.loop = None
        self._lock = threading.Lock()


#подключение к бд
    async def connect(self):
        """Асинхронное подключение к базе данных"""
        try:
            self.connection = await asyncmy.connect(
                host='pma.panteleeva.info',
                port=3306,
                user='phpmyadmin',
                password='0907',
                database='phpmyadmin'
            )
            self.is_connected = True
            logging.info("Успешное подключение к базе данных")
            return True
        except Exception as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            return False

    def run_async(self, coroutine):
        """Запуск асинхронной функции в отдельном потоке с единым циклом событий"""
        def run_in_thread():
            with self._lock:
                if self.loop is None or self.loop.is_closed():
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                try:
                    return self.loop.run_until_complete(coroutine)
                except Exception as e:
                    logging.error(f"Ошибка выполнения запроса: {e}")
                    logging.error(traceback.format_exc())
                    return None
        return run_in_thread()

    async def _execute_query(self, query, params=None):
        """Внутренный метод выполнения SQL запроса"""
        try:
            if not self.is_connected or self.connection is None:
                success = await self.connect()
                if not success:
                    return None
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, params or ())
                if query.strip().upper().startswith('SELECT'):
                    result = await cursor.fetchall()
                    return result
                else:
                    await self.connection.commit()
                    if query.strip().upper().startswith('INSERT'):
                        return cursor.lastrowid
                    else:
                        return cursor.rowcount
        except Exception as e:
            logging.error(f"Ошибка выполнения запроса: {e}")
            logging.error(traceback.format_exc())
            return None

    #методы для животных
    def get_animals_count(self):
        async def query():
            result = await self._execute_query("SELECT COUNT(*) as count FROM animal")
            return result[0][0] if result else 0
        logging.info("Запрос количества животных")
        return self.run_async(query())

    def get_all_animals(self):
        query_str = """
        SELECT a.id, a.nickname, a.description, a.date_of_birth, a.special_signs,
               a.date_of_admission, ta.name as species_name, g.gender as gender_name,
               h.name as habitat_name, a.id_type, a.id_gender
        FROM animal a
        JOIN type_animal ta ON a.id_type = ta.id
        JOIN gender g ON a.id_gender = g.id
        LEFT JOIN animal_habitat ah ON a.id = ah.id_animal
        LEFT JOIN habitat h ON ah.id_habitat = h.id
        ORDER BY a.nickname
        """
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос всех животных")
        if not result:
            return []
        animals = []
        for row in result:
            animal_dict = {
                'id': row[0],
                'nickname': row[1],
                'description': row[2],
                'date_of_birth': row[3],
                'special_signs': row[4],
                'date_of_admission': row[5],
                'species_name': row[6],
                'gender_name': row[7],
                'habitat_name': row[8],
                'id_type': row[9],
                'id_gender': row[10]
            }
            animals.append(animal_dict)
        return animals

    def add_animal(self, animal_data):
        query_str = """
        INSERT INTO animal (nickname, description, date_of_birth, special_signs,
                           date_of_admission, id_type, id_gender)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        async def query():
            return await self._execute_query(query_str, animal_data)
        logging.info(f"Добавление животного: {animal_data}")
        return self.run_async(query())

    def update_animal(self, animal_id, animal_data):
        query_str = """
        UPDATE animal
        SET nickname=%s, description=%s, date_of_birth=%s, special_signs=%s,
            date_of_admission=%s, id_type=%s, id_gender=%s
        WHERE id=%s
        """
        async def query():
            return await self._execute_query(query_str, animal_data + (animal_id,))
        logging.info(f"Обновление животного ID {animal_id}: {animal_data}")
        return self.run_async(query())

    def delete_animal(self, animal_id):
        async def delete_operations():
            await self._execute_query("DELETE FROM animal_habitat WHERE id_animal = %s", (animal_id,))
            await self._execute_query("DELETE FROM animal_feeding WHERE id_animal = %s", (animal_id,))
            await self._execute_query("DELETE FROM health_monitoring WHERE id_animal = %s", (animal_id,))
            return await self._execute_query("DELETE FROM animal WHERE id = %s", (animal_id,))
        logging.info(f"Удаление животного ID {animal_id}")
        return self.run_async(delete_operations())

    #методы для получения справочных данных
    def get_species_list(self):
        query_str = "SELECT id, name FROM type_animal ORDER BY name"
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос списка видов животных")
        return result if result else []

    def get_genders_list(self):
        query_str = "SELECT id, gender FROM gender ORDER BY id"
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос списка полов")
        return result if result else []

    def get_habitats_list(self):
        query_str = "SELECT id, name FROM habitat ORDER BY name"
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос списка мест обитания")
        return result if result else []

    def get_staff_list(self):
        query_str = "SELECT id, full_name FROM staff ORDER BY full_name"
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос списка сотрудников")
        return result if result else []

    def get_food_types_list(self):
        query_str = "SELECT id, name_food FROM type_of_food ORDER BY name_food"
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос списка типов корма")
        return result if result else []

    #методы для сотрудников
    def get_all_staff(self):
        query_str = """
        SELECT s.id, s.full_name, s.post, s.email
        FROM staff s
        ORDER BY s.full_name
        """
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос всех сотрудников")
        if not result:
            return []
        staff_list = []
        for row in result:
            staff_dict = {
                'id': row[0],
                'full_name': row[1],
                'post': row[2],
                'email': row[3]
            }
            staff_list.append(staff_dict)
        return staff_list

    def add_staff(self, staff_data):
        query_str = """
        INSERT INTO staff (full_name, post, email)
        VALUES (%s, %s, %s)
        """
        async def query():
            return await self._execute_query(query_str, staff_data)
        logging.info(f"Добавление сотрудника: {staff_data}")
        return self.run_async(query())

    def update_staff(self, staff_id, staff_data):
        query_str = """
        UPDATE staff
        SET full_name=%s, post=%s, email=%s
        WHERE id=%s
        """
        async def query():
            return await self._execute_query(query_str, staff_data + (staff_id,))
        logging.info(f"Обновление сотрудника ID {staff_id}: {staff_data}")
        return self.run_async(query())

    def delete_staff(self, staff_id):
        async def delete_operations():
            await self._execute_query("DELETE FROM staff_feeding WHERE id_staff = %s", (staff_id,))
            await self._execute_query("DELETE FROM staff_health_monitoring WHERE id_staff = %s", (staff_id,))
            return await self._execute_query("DELETE FROM staff WHERE id = %s", (staff_id,))
        logging.info(f"Удаление сотрудника ID {staff_id}")
        return self.run_async(delete_operations())

    #методы для видов животных
    def get_all_species(self):
        query_str = "SELECT id, name, scientific_name, status FROM type_animal ORDER BY name"
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос всех видов животных")
        if not result:
            return []
        species_list = []
        for row in result:
            species_dict = {
                'id': row[0],
                'name': row[1],
                'scientific_name': row[2],
                'status': row[3]
            }
            species_list.append(species_dict)
        return species_list

    def add_species(self, species_data):
        query_str = "INSERT INTO type_animal (name, scientific_name, status) VALUES (%s, %s, %s)"
        async def query():
            return await self._execute_query(query_str, species_data)
        logging.info(f"Добавление вида животного: {species_data}")
        return self.run_async(query())

    def update_species(self, species_id, species_data):
        query_str = """
        UPDATE type_animal
        SET name=%s, scientific_name=%s, status=%s
        WHERE id=%s
        """
        async def query():
            return await self._execute_query(query_str, species_data + (species_id,))
        logging.info(f"Обновление вида животного ID {species_id}: {species_data}")
        return self.run_async(query())

    def delete_species(self, species_id):
        async def delete_operations():
            count_result = await self._execute_query("SELECT COUNT(*) FROM animal WHERE id_type = %s", (species_id,))
            if count_result and count_result[0][0] > 0:
                logging.warning(f"Cannot delete species ID {species_id} because it is used in animals")
                return 0
            return await self._execute_query("DELETE FROM type_animal WHERE id = %s", (species_id,))
        logging.info(f"Удаление вида животного ID {species_id}")
        return self.run_async(delete_operations())

    #методы для мест обитания
    def get_all_habitats(self):
        query_str = """
        SELECT h.id, h.name, h.square, h.description, tot.name as terrain_type, h.id_type_of_terrain
        FROM habitat h
        JOIN type_of_terrain tot ON h.id_type_of_terrain = tot.id
        ORDER BY h.name
        """
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос всех мест обитания")
        if not result:
            return []
        habitats_list = []
        for row in result:
            habitat_dict = {
                'id': row[0],
                'name': row[1],
                'square': row[2],
                'description': row[3],
                'terrain_type': row[4],
                'id_type_of_terrain': row[5]
            }
            habitats_list.append(habitat_dict)
        return habitats_list

    def get_terrain_types_list(self):
        query_str = "SELECT id, name FROM type_of_terrain ORDER BY name"
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос списка типов местности")
        return result if result else []

    def add_habitat(self, habitat_data):
        query_str = "INSERT INTO habitat (name, square, description, id_type_of_terrain) VALUES (%s, %s, %s, %s)"
        async def query():
            return await self._execute_query(query_str, habitat_data)
        logging.info(f"Добавление места обитания: {habitat_data}")
        return self.run_async(query())

    def update_habitat(self, habitat_id, habitat_data):
        query_str = """
        UPDATE habitat
        SET name=%s, square=%s, description=%s, id_type_of_terrain=%s
        WHERE id=%s
        """
        async def query():
            return await self._execute_query(query_str, habitat_data + (habitat_id,))
        logging.info(f"Обновление места обитания ID {habitat_id}: {habitat_data}")
        return self.run_async(query())

    def delete_habitat(self, habitat_id):
        async def delete_operations():
            await self._execute_query("DELETE FROM animal_habitat WHERE id_habitat = %s", (habitat_id,))
            return await self._execute_query("DELETE FROM habitat WHERE id = %s", (habitat_id,))
        logging.info(f"Удаление места обитания ID {habitat_id}")
        return self.run_async(delete_operations())

    #методы для кормлений
    def get_all_feedings(self):
        query_str = """
        SELECT f.id, f.feeding_date, f.appetite_assessment,
               a.nickname as animal_name, s.full_name as staff_name,
               tof.name_food as food_type, f.id_type_of_food, a.id as animal_id
        FROM feeding f
        JOIN animal_feeding af ON f.id = af.id_feeding
        JOIN animal a ON af.id_animal = a.id
        JOIN staff_feeding sf ON f.id = sf.id_feeding
        JOIN staff s ON sf.id_staff = s.id
        JOIN type_of_food tof ON f.id_type_of_food = tof.id
        ORDER BY f.feeding_date DESC
        """
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос всех кормлений")
        if not result:
            return []
        feedings_list = []
        for row in result:
            feeding_dict = {
                'id': row[0],
                'feeding_date': row[1],
                'appetite_assessment': row[2],
                'animal_name': row[3],
                'staff_name': row[4],
                'food_type': row[5],
                'id_type_of_food': row[6],
                'animal_id': row[7]
            }
            feedings_list.append(feeding_dict)
        return feedings_list

    def add_feeding(self, feeding_data, animal_id, staff_id):
        async def add_operations():
            #добавляем кормление
            feeding_query = """
            INSERT INTO feeding (feeding_date, appetite_assessment, id_type_of_food)
            VALUES (%s, %s, %s)
            """
            feeding_id = await self._execute_query(feeding_query, feeding_data)
            if feeding_id is not None and feeding_id > 0:
                #связываем кормление с животным
                animal_feeding_query = "INSERT INTO animal_feeding (id_animal, id_feeding) VALUES (%s, %s)"
                await self._execute_query(animal_feeding_query, (animal_id, feeding_id))
                #связываем кормление с сотрудником
                staff_feeding_query = "INSERT INTO staff_feeding (id_staff, id_feeding) VALUES (%s, %s)"
                await self._execute_query(staff_feeding_query, (staff_id, feeding_id))
            return feeding_id
        logging.info(f"Добавление кормления: {feeding_data}, животное ID {animal_id}, сотрудник ID {staff_id}")
        return self.run_async(add_operations())

    def update_feeding(self, feeding_id, feeding_data, animal_id, staff_id):
        async def update_operations():
            #обновляем кормление
            feeding_query = """
            UPDATE feeding
            SET feeding_date=%s, appetite_assessment=%s, id_type_of_food=%s
            WHERE id=%s
            """
            rowcount = await self._execute_query(feeding_query, feeding_data + (feeding_id,))
            if rowcount is not None:
                #обновляем связь с животным
                await self._execute_query("DELETE FROM animal_feeding WHERE id_feeding = %s", (feeding_id,))
                animal_feeding_query = "INSERT INTO animal_feeding (id_animal, id_feeding) VALUES (%s, %s)"
                await self._execute_query(animal_feeding_query, (animal_id, feeding_id))
                #обновляем связь с сотрудником
                await self._execute_query("DELETE FROM staff_feeding WHERE id_feeding = %s", (feeding_id,))
                staff_feeding_query = "INSERT INTO staff_feeding (id_staff, id_feeding) VALUES (%s, %s)"
                await self._execute_query(staff_feeding_query, (staff_id, feeding_id))
            return rowcount
        logging.info(f"Обновление кормления ID {feeding_id}: {feeding_data}, животное ID {animal_id}, сотрудник ID {staff_id}")
        return self.run_async(update_operations())

    def delete_feeding(self, feeding_id):
        async def delete_operations():
            await self._execute_query("DELETE FROM animal_feeding WHERE id_feeding = %s", (feeding_id,))
            await self._execute_query("DELETE FROM staff_feeding WHERE id_feeding = %s", (feeding_id,))
            return await self._execute_query("DELETE FROM feeding WHERE id = %s", (feeding_id,))
        logging.info(f"Удаление кормления ID {feeding_id}")
        return self.run_async(delete_operations())

    #методы для наблюдений за здоровьем
    def get_all_health_observations(self):
        query_str = """
        SELECT 
            hm.id,
            hm.date_of_inspection,
            hm.general_condition,
            hm.diagnosis,
            hm.notes,
            GROUP_CONCAT(DISTINCT a.nickname ORDER BY a.nickname SEPARATOR ', ') as animal_names,
            GROUP_CONCAT(DISTINCT s.full_name ORDER BY s.full_name SEPARATOR ', ') as staff_names,
            hm.id_animal
        FROM health_monitoring hm
        LEFT JOIN animal a ON hm.id_animal = a.id
        LEFT JOIN staff_health_monitoring shm ON hm.id = shm.id_health_monitoring
        LEFT JOIN staff s ON shm.id_staff = s.id
        GROUP BY hm.id
        ORDER BY hm.date_of_inspection DESC
        """
        async def query():
            return await self._execute_query(query_str)
        result = self.run_async(query())
        logging.info("Запрос всех наблюдений за здоровьем (с группировкой)")
        if not result:
            return []
        observations_list = []
        for row in result:
            observation_dict = {
                'id': row[0],
                'date_of_inspection': row[1],
                'general_condition': row[2],
                'diagnosis': row[3],
                'notes': row[4],
                'animal_name': row[5] or "-",
                'staff_name': row[6] or "-",
                'animal_id': row[7]
            }
            observations_list.append(observation_dict)
        return observations_list

    def add_health_observation(self, health_data, staff_id):
        async def add_operations():
            #добавляем наблюдение за здоровьем
            health_query = """
            INSERT INTO health_monitoring (general_condition, diagnosis, date_of_inspection,
                                         notes, id_animal)
            VALUES (%s, %s, %s, %s, %s)
            """
            health_id = await self._execute_query(health_query, health_data)
            if health_id is not None and health_id > 0:
                #связываем наблюдение с сотрудником
                staff_health_query = "INSERT INTO staff_health_monitoring (id_staff, id_health_monitoring) VALUES (%s, %s)"
                await self._execute_query(staff_health_query, (staff_id, health_id))
            return health_id
        logging.info(f"Добавление наблюдения за здоровьем: {health_data}, сотрудник ID {staff_id}")
        return self.run_async(add_operations())

    def update_health_observation(self, health_id, health_data, staff_id):
        async def update_operations():
            #обновляем наблюдение за здоровьем
            health_query = """
            UPDATE health_monitoring
            SET general_condition=%s, diagnosis=%s, date_of_inspection=%s,
                notes=%s, id_animal=%s
            WHERE id=%s
            """
            rowcount = await self._execute_query(health_query, health_data + (health_id,))
            if rowcount is not None:
                #обновляем связь с сотрудником
                await self._execute_query("DELETE FROM staff_health_monitoring WHERE id_health_monitoring = %s", (health_id,))
                staff_health_query = "INSERT INTO staff_health_monitoring (id_staff, id_health_monitoring) VALUES (%s, %s)"
                await self._execute_query(staff_health_query, (staff_id, health_id))
            return rowcount
        logging.info(f"Обновление наблюдения за здоровьем ID {health_id}: {health_data}, сотрудник ID {staff_id}")
        return self.run_async(update_operations())

    def delete_health_observation(self, health_id):
        async def delete_operations():
            await self._execute_query("DELETE FROM staff_health_monitoring WHERE id_health_monitoring = %s", (health_id,))
            return await self._execute_query("DELETE FROM health_monitoring WHERE id = %s", (health_id,))
        logging.info(f"Удаление наблюдения за здоровьем ID {health_id}")
        return self.run_async(delete_operations())

    #методы для дашборда
    def get_animals_under_observation(self):
        count = self.get_animals_count()
        return count if count is not None else 0

    async def _load_dashboard_data(self, period_days, limit=5):
        try:
            total_animals_res = await self._execute_query("SELECT COUNT(*) as count FROM animal")
            total_animals = total_animals_res[0][0] if total_animals_res else 0
            under_observation = total_animals 
            feedings_res = await self._execute_query("""
                SELECT COUNT(*) as count FROM feeding
                WHERE feeding_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (period_days,))
            feedings = feedings_res[0][0] if feedings_res else 0
            new_observations_res = await self._execute_query("""
                SELECT COUNT(*) as count FROM health_monitoring
                WHERE date_of_inspection >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (period_days,))
            new_observations = new_observations_res[0][0] if new_observations_res else 0
            species_res = await self._execute_query("""
                SELECT ta.name, COUNT(a.id) as count
                FROM animal a
                JOIN type_animal ta ON a.id_type = ta.id
                GROUP BY ta.name
                ORDER BY COUNT(a.id) DESC
            """)
            health_res = await self._execute_query("""
                SELECT
                    COALESCE(SUM(CASE WHEN hm.general_condition = 'Отличное' THEN 1 ELSE 0 END), 0) as excellent,
                    COALESCE(SUM(CASE WHEN hm.general_condition = 'Хорошее' THEN 1 ELSE 0 END), 0) as good,
                    COALESCE(SUM(CASE WHEN hm.general_condition = 'Удовлетворительное' THEN 1 ELSE 0 END), 0) as satisfactory,
                    COALESCE(SUM(CASE WHEN hm.general_condition = 'Тяжелое' THEN 1 ELSE 0 END), 0) as needs_attention
                FROM (
                    SELECT hm2.id_animal, MAX(hm2.date_of_inspection) as last_date
                    FROM health_monitoring hm2
                    GROUP BY hm2.id_animal
                ) latest
                JOIN health_monitoring hm 
                    ON hm.id_animal = latest.id_animal 
                    AND hm.date_of_inspection = latest.last_date
            """)
            health_data = [health_res[0][i] or 0 for i in range(4)] if health_res and health_res[0] else [0, 0, 0, 0]
            events_res = await self._execute_query("""
                (SELECT 'feeding' as type,
                        CONCAT('Кормление: ', a.nickname, ' - ', f.appetite_assessment) as description,
                        f.feeding_date as event_date
                 FROM feeding f
                 JOIN animal_feeding af ON f.id = af.id_feeding
                 JOIN animal a ON af.id_animal = a.id
                 ORDER BY f.feeding_date DESC LIMIT %s)
                UNION ALL
                (SELECT 'health' as type,
                        CONCAT('Осмотр здоровья: ', a.nickname, ' - ', hm.general_condition) as description,
                        hm.date_of_inspection as event_date
                 FROM health_monitoring hm
                 JOIN animal a ON hm.id_animal = a.id
                 ORDER BY hm.date_of_inspection DESC LIMIT %s)
                ORDER BY event_date DESC
                LIMIT %s
            """, (limit, limit, limit))
            return {
                "total_animals": total_animals,
                "under_observation": under_observation,
                "feedings": feedings,
                "new_observations": new_observations,
                "species_data": species_res or [],
                "health_data": health_data,
                "events": events_res or []
            }
        except Exception as e:
            logging.error(f"Ошибка загрузки данных дашборда: {e}")
            return None

    def load_dashboard_data(self, period_days):
        logging.info(f"Загрузка данных дашборда за {period_days} дней")
        return self.run_async(self._load_dashboard_data(period_days))

    def get_recent_feedings_count(self, period_days):
        async def query():
            result = await self._execute_query("""
                SELECT COUNT(*) as count FROM feeding
                WHERE feeding_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (period_days,))
            return result[0][0] if result else 0
        logging.info(f"Запрос количества кормлений за {period_days} дней")
        return self.run_async(query())

    def get_new_observations_count(self, period_days):
        async def query():
            result = await self._execute_query("""
                SELECT COUNT(*) as count FROM health_monitoring
                WHERE date_of_inspection >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (period_days,))
            return result[0][0] if result else 0
        logging.info(f"Запрос количества новых наблюдений за {period_days} дней")
        return self.run_async(query())

    def get_species_distribution(self):
        async def query():
            result = await self._execute_query("""
                SELECT ta.name, COUNT(a.id) as count
                FROM animal a
                JOIN type_animal ta ON a.id_type = ta.id
                GROUP BY ta.name
                ORDER BY COUNT(a.id) DESC
            """)
            return [{'name': row[0], 'count': row[1]} for row in result] if result else []
        logging.info("Запрос распределения по видам")
        return self.run_async(query())

    def get_health_distribution(self):
        async def query():
            result = await self._execute_query("""
                SELECT 
                    COALESCE(SUM(CASE WHEN latest_condition = 'Отличное' THEN 1 ELSE 0 END), 0) as excellent,
                    COALESCE(SUM(CASE WHEN latest_condition = 'Хорошее' THEN 1 ELSE 0 END), 0) as good,
                    COALESCE(SUM(CASE WHEN latest_condition = 'Удовлетворительное' THEN 1 ELSE 0 END), 0) as satisfactory,
                    COALESCE(SUM(CASE WHEN latest_condition = 'Тяжелое' THEN 1 ELSE 0 END), 0) as needs_attention
                FROM (
                    SELECT 
                        a.id as animal_id,
                        hm.general_condition as latest_condition
                    FROM animal a
                    LEFT JOIN (
                        SELECT 
                            hm1.id_animal,
                            hm1.general_condition,
                            ROW_NUMBER() OVER (
                                PARTITION BY hm1.id_animal 
                                ORDER BY hm1.date_of_inspection DESC
                            ) as rn
                        FROM health_monitoring hm1
                    ) hm ON a.id = hm.id_animal AND hm.rn = 1
                ) sub;
            """)
            if result and result[0]:
                row = result[0]
                return [int(row[i] or 0) for i in range(4)]
            else:
                return [0, 0, 0, 0]
        logging.info("Запрос распределения по здоровью (по последнему осмотру на животное)")
        return self.run_async(query())

    def get_recent_events(self, limit=5):
        async def query():
            result = await self._execute_query("""
                (SELECT 'feeding' as type,
                        CONCAT('Кормление: ', a.nickname, ' - ', f.appetite_assessment) as description,
                        f.feeding_date as event_date
                 FROM feeding f
                 JOIN animal_feeding af ON f.id = af.id_feeding
                 JOIN animal a ON af.id_animal = a.id
                 ORDER BY f.feeding_date DESC LIMIT %s)
                UNION ALL
                (SELECT 'health' as type,
                        CONCAT('Осмотр здоровья: ', a.nickname, ' - ', hm.general_condition) as description,
                        hm.date_of_inspection as event_date
                 FROM health_monitoring hm
                 JOIN animal a ON hm.id_animal = a.id
                 ORDER BY hm.date_of_inspection DESC LIMIT %s)
                ORDER BY event_date DESC
                LIMIT %s
            """, (limit, limit, limit))
            return [{'type': row[0], 'description': row[1], 'event_date': row[2]} for row in result] if result else []
        logging.info(f"Запрос последних событий (лимит {limit})")
        return self.run_async(query())

    def close_connection(self):
        if self.connection:
            async def close():
                await self.connection.close()
            self.run_async(close())
            self.is_connected = False
            logging.info("Закрытие соединения с базой данных")

    async def close(self):
        if self.connection is not None and not self.connection.closed:
            try:
                await self.connection.close()
                logging.info("Соединение с БД закрыто")
            except Exception as e:
                logging.error(f"Ошибка при закрытии: {e}")
            finally:
                self.connection = None
                self.is_connected = False
        if self.loop and not self.loop.is_closed():
            self.loop.close()

    def __del__(self):
        if self.connection and hasattr(self.connection, 'closed') and not self.connection.closed:
            self.run_async(self.close())


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, db_manager, main_app):
        super().__init__(parent)
        self.db_manager = db_manager
        self.main_app = main_app
        self.current_period = "month"
        self.species_canvas = None
        self.health_canvas = None
        self.create_widgets()
        self.update_dashboard()

    def create_widgets(self):
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkLabel(title_frame, text="Панель управления заповедником",
                     font=("Arial", 20, "bold")).pack(side="left", pady=10)
        controls_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        controls_frame.pack(side="right", pady=10)
        ctk.CTkButton(controls_frame, text="Обновить данные",
                      command=self.refresh_data, width=120).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Экспорт данных",
                      command=self.export_data, width=120).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Полный отчет Excel",
                      command=self.export_full_report, width=140).pack(side="left", padx=5)
        #кнопки для pdf
        ctk.CTkButton(controls_frame, text="PDF: Статистика",
                      command=self.export_pdf_stat, width=120).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="PDF: Детальный",
                      command=self.export_pdf_detail, width=120).pack(side="left", padx=5)
        filter_frame = ctk.CTkFrame(self, corner_radius=10)
        filter_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkLabel(filter_frame, text="Период:", font=("Arial", 12)).pack(side="left", padx=10)
        periods = [
            ("Сегодня", "today"),
            ("Месяц", "month"),
            ("Квартал", "quarter")
        ]
        self.period_buttons = {}
        for text, period_key in periods:
            btn = ctk.CTkButton(
                filter_frame,
                text=text,
                width=80,
                command=lambda pk=period_key: self.change_period(pk),
                fg_color="#2ecc71" if period_key == self.current_period else "gray"
            )
            btn.pack(side="left", padx=5)
            self.period_buttons[period_key] = btn
        self.cards_frame = ctk.CTkFrame(self)
        self.cards_frame.pack(fill='x', padx=10, pady=5)
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        charts_top_frame = ctk.CTkFrame(left_frame)
        charts_top_frame.pack(fill='both', expand=True, pady=(0, 10))
        self.species_frame = ctk.CTkFrame(charts_top_frame, corner_radius=10)
        self.species_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        self.health_frame = ctk.CTkFrame(charts_top_frame, corner_radius=10)
        self.health_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        self.events_frame = ctk.CTkFrame(left_frame, corner_radius=10, height=120)
        self.events_frame.pack(fill='x', pady=(0, 0))
        self.events_frame.pack_propagate(False)

    def change_period(self, period_key):
        self.current_period = period_key
        for key, btn in self.period_buttons.items():
            btn.configure(fg_color="#2ecc71" if key == period_key else "gray")
        self.update_dashboard()

    def refresh_data(self):
        self.update_dashboard()
        messagebox.showinfo("Обновление", "Данные успешно обновлены!")

    def export_full_report(self):
        """Экспорт полного отчета в Excel"""
        if hasattr(self.main_app, 'export_to_excel'):
            self.main_app.export_to_excel()

    def export_pdf_stat(self):
        """Экспорт статистического PDF-отчёта"""
        if hasattr(self.main_app, 'export_pdf_stat'):
            self.main_app.export_pdf_stat()

    def export_pdf_detail(self):
        """Экспорт детального PDF-отчёта"""
        if hasattr(self.main_app, 'export_pdf_detail'):
            self.main_app.export_pdf_detail()

    def load_data_from_db(self):
        try:
            period_days = {
                "today": 1,
                "month": 30,
                "quarter": 90
            }.get(self.current_period, 30)
            total_animals = self.db_manager.get_animals_count()
            under_observation = self.db_manager.get_animals_under_observation()
            feedings = self.db_manager.get_recent_feedings_count(period_days)
            new_observations = self.db_manager.get_new_observations_count(period_days)
            species_data = self.db_manager.get_species_distribution()
            health_data = self.db_manager.get_health_distribution()
            events = self.db_manager.get_recent_events(5)
            species_counts = []
            species_names = []
            if species_data:
                for item in species_data:
                    species_names.append(item['name'])
                    species_counts.append(item['count'])
            while len(species_counts) < 4:
                species_counts.append(0)
                species_names.append("Нет данных")
            formatted_events = []
            if events:
                for event in events:
                    formatted_events.append((event['description'], str(event['event_date'])))
            return {
                "total_animals": str(total_animals) if total_animals else "0",
                "under_observation": str(under_observation),
                "feedings": str(feedings),
                "new_observations": str(new_observations),
                "species_data": species_counts,
                "species_names": species_names,
                "health_data": health_data,
                "events": formatted_events
            }
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return None

    def update_dashboard(self):
        def load_and_update():
            data = self.load_data_from_db()
            if data:
                self.after(0, lambda: self.update_ui_with_data(data))
            else:
                self.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось загрузить данные"))
        thread = threading.Thread(target=load_and_update)
        thread.daemon = True
        thread.start()

    def update_ui_with_data(self, data):
        self.update_metrics_cards(data)
        self.update_charts(data)
        self.update_events_section(data)

    def update_metrics_cards(self, data):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        metrics_data = [
            ("Всего животных", data["total_animals"]),
            ("Под наблюдением", data["under_observation"]),
            ("Кормлений", data["feedings"]),
            ("Новых наблюдений", data["new_observations"])
        ]
        for i, (title, value) in enumerate(metrics_data):
            card = ctk.CTkFrame(self.cards_frame, corner_radius=8, height=70)
            card.grid(row=0, column=i, padx=5, sticky='ew')
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=value, font=("Arial", 16, "bold")).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=title, font=("Arial", 11)).pack(pady=(0, 8))
        self.cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

    def update_charts(self, data):
        self.create_species_chart(data["species_names"], data["species_data"])
        self.create_health_chart(data["health_data"])

    def create_species_chart(self, labels, values):
        for widget in self.species_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.species_frame, text="Распределение по видам",
                     font=("Arial", 14, "bold")).pack(pady=5)
        fig, ax = plt.subplots(figsize=(5, 3), facecolor='#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
        bars = ax.bar(range(len(labels)), values, color=colors)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', color='white')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom', color='white')
        fig.tight_layout()
        if self.species_canvas:
            self.species_canvas.get_tk_widget().destroy()
        self.species_canvas = FigureCanvasTkAgg(fig, self.species_frame)
        self.species_canvas.draw()
        self.species_canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)

    def create_health_chart(self, health_data):
        for widget in self.health_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.health_frame, text="Состояние здоровья",
                     font=("Arial", 14, "bold")).pack(pady=5)
        fig, ax = plt.subplots(figsize=(5, 3), facecolor='#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        conditions = ['Отличное', 'Хорошее', 'Удовл.', 'Требует внимания']
        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
        #фильтр нулевых значений
        filtered_data = []
        filtered_labels = []
        filtered_colors = []
        for i, (data, label, color) in enumerate(zip(health_data, conditions, colors)):
            if data > 0:
                filtered_data.append(data)
                filtered_labels.append(label)
                filtered_colors.append(color)
        if filtered_data:
            wedges, texts, autotexts = ax.pie(
                filtered_data,
                labels=filtered_labels,
                colors=filtered_colors,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'color': 'white'}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        else:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                    transform=ax.transAxes, fontsize=12, color='white')
        fig.tight_layout()
        if self.health_canvas:
            self.health_canvas.get_tk_widget().destroy()
        self.health_canvas = FigureCanvasTkAgg(fig, self.health_frame)
        self.health_canvas.draw()
        self.health_canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)

    def update_events_section(self, data):
        for widget in self.events_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.events_frame, text="Последние события",
                     font=("Arial", 14, "bold")).pack(pady=5)
        events_text = ctk.CTkTextbox(self.events_frame, height=80)
        events_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        if data["events"]:
            for description, date in data["events"]:
                events_text.insert("end", f"• {description} ({date})\n")
        else:
            events_text.insert("end", "Нет данных о событиях")
        events_text.configure(state="disabled")

    def export_data(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                data = self.load_data_from_db()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Отчет по заповеднику\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Всего животных: {data['total_animals']}\n")
                    f.write(f"Под наблюдением: {data['under_observation']}\n")
                    f.write(f"Кормлений за период: {data['feedings']}\n")
                    f.write(f"Новых наблюдений: {data['new_observations']}\n")
                    f.write("Распределение по видам:\n")
                    for name, count in zip(data['species_names'], data['species_data']):
                        f.write(f"  {name}: {count}\n")
                    f.write("\nПоследние события:\n")
                    for description, date in data['events']:
                        f.write(f"  {description} ({date})\n")
                messagebox.showinfo("Экспорт", "Данные успешно экспортированы!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {e}")


class DataManagementFrame(ctk.CTkFrame):
    def __init__(self, parent, db_manager, main_app):
        super().__init__(parent)
        self.db_manager = db_manager
        self.main_app = main_app
        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkLabel(title_frame, text="Управление данными заповедника",
                     font=("Arial", 20, "bold")).pack(side="left", pady=10)
        controls_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        controls_frame.pack(side="right", pady=10)
        ctk.CTkButton(controls_frame, text="Обновить",
                      command=self.refresh_data, width=100).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Экспорт в Excel",
                      command=self.export_to_excel, width=120).pack(side="left", padx=5)
        #добавляем кнопки PDF
        ctk.CTkButton(controls_frame, text="PDF: Статистика",
                      command=self.export_pdf_stat, width=120).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="PDF: Детальный",
                      command=self.export_pdf_detail, width=120).pack(side="left", padx=5)
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        left_frame = ctk.CTkFrame(main_frame, width=200)
        left_frame.pack(side='left', fill='y', padx=(0, 10))
        left_frame.pack_propagate(False)
        self.content_frame = ctk.CTkFrame(main_frame)
        self.content_frame.pack(side='right', fill='both', expand=True)
        self.create_navigation(left_frame)

    def create_navigation(self, parent):
        ctk.CTkLabel(parent, text="Разделы данных",
                     font=("Arial", 16, "bold")).pack(pady=10)
        sections = [
            ("Животные", self.show_animals),
            ("Сотрудники", self.show_staff),
            ("Виды животных", self.show_species),
            ("Места обитания", self.show_habitats),
            ("Кормления", self.show_feedings),
            ("Наблюдения за здоровьем", self.show_health_observations)
        ]
        for text, command in sections:
            btn = ctk.CTkButton(
                parent,
                text=text,
                command=command,
                width=180,
                height=35,
                corner_radius=8
            )
            btn.pack(pady=5)

    def load_initial_data(self):
        self.show_animals()

    def refresh_data(self):
        logging.info("Обновление данных в управлении")
        current_content = getattr(self, 'current_content', None)
        if current_content:
            current_content()
        messagebox.showinfo("Обновление", "Данные успешно обновлены!")

    def export_to_excel(self):
        """Экспорт данных в Excel"""
        if hasattr(self.main_app, 'export_to_excel'):
            self.main_app.export_to_excel()

    def export_pdf_stat(self):
        """Экспорт статистического PDF-отчёта"""
        if hasattr(self.main_app, 'export_pdf_stat'):
            self.main_app.export_pdf_stat()

    def export_pdf_detail(self):
        """Экспорт детального PDF-отчёта"""
        if hasattr(self.main_app, 'export_pdf_detail'):
            self.main_app.export_pdf_detail()

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_animals(self):
        logging.info("Открытие раздела 'Животные'")
        self.current_content = self.show_animals
        self.clear_content_frame()
        title_label = ctk.CTkLabel(self.content_frame, text="Управление животными",
                                   font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        controls_frame = ctk.CTkFrame(self.content_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(controls_frame, text="Добавить животное",
                      command=self.open_add_animal_dialog, width=150).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Обновить список",
                      command=self.refresh_animals, width=150).pack(side="left", padx=5)
        self.animals_tree = ctk.CTkScrollableFrame(self.content_frame)
        self.animals_tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.load_animals_data()

    def load_animals_data(self):
        for widget in self.animals_tree.winfo_children():
            widget.destroy()
        def load_data():
            animals = self.db_manager.get_all_animals()
            self.after(0, lambda: self.display_animals(animals))
        threading.Thread(target=load_data, daemon=True).start()

    def display_animals(self, animals):
        for widget in self.animals_tree.winfo_children():
            widget.destroy()
        if not animals:
            ctk.CTkLabel(self.animals_tree, text="Нет данных о животных").pack(pady=20)
            return
        #создаем заголовки
        headers_frame = ctk.CTkFrame(self.animals_tree)
        headers_frame.pack(fill='x', pady=(0, 5))
        headers = ["ID", "Кличка", "Вид", "Пол", "Дата рождения", "Дата поступления", "Место обитания", "Действия"]
        for i, col in enumerate(headers):
            header = ctk.CTkLabel(headers_frame, text=col, font=("Arial", 12, "bold"),
                                  width=120 if i > 0 else 60, height=30)
            header.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        #заполняем данными
        for row_idx, animal in enumerate(animals, 1):
            animal_frame = ctk.CTkFrame(self.animals_tree)
            animal_frame.pack(fill='x', padx=1, pady=1)
            # ID
            ctk.CTkLabel(animal_frame, text=str(animal['id']), width=60, height=30).grid(
                row=0, column=0, padx=1, pady=1, sticky="ew")
            #кличка
            nickname = animal['nickname'] or ''
            if len(nickname) > 15:
                nickname = nickname[:15] + '...'
            ctk.CTkLabel(animal_frame, text=nickname, width=120, height=30).grid(
                row=0, column=1, padx=1, pady=1, sticky="ew")
            #вид
            species = animal['species_name'] or ''
            if len(species) > 15:
                species = species[:15] + '...'
            ctk.CTkLabel(animal_frame, text=species, width=120, height=30).grid(
                row=0, column=2, padx=1, pady=1, sticky="ew")
            #пол
            ctk.CTkLabel(animal_frame, text=animal['gender_name'], width=120, height=30).grid(
                row=0, column=3, padx=1, pady=1, sticky="ew")
            #дата рождения
            dob = str(animal['date_of_birth'] or '')
            ctk.CTkLabel(animal_frame, text=dob, width=120, height=30).grid(
                row=0, column=4, padx=1, pady=1, sticky="ew")
            #дата поступления
            doa = str(animal['date_of_admission'] or '')
            ctk.CTkLabel(animal_frame, text=doa, width=120, height=30).grid(
                row=0, column=5, padx=1, pady=1, sticky="ew")
            #место обитания
            habitat = animal['habitat_name'] or ''
            if len(habitat) > 20:
                habitat = habitat[:20] + '...'
            ctk.CTkLabel(animal_frame, text=habitat, width=120, height=30).grid(
                row=0, column=6, padx=1, pady=1, sticky="ew")
            actions_frame = ctk.CTkFrame(animal_frame, fg_color="transparent", width=120)
            actions_frame.grid(row=0, column=7, padx=1, pady=1, sticky="ew")
            actions_frame.grid_propagate(False)
            ctk.CTkButton(actions_frame, text="✏️", width=30, height=25,
                          command=lambda a=animal: self.open_edit_animal_dialog(a)).pack(side="left", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️", width=30, height=25,
                          command=lambda a=animal: self.delete_animal(a)).pack(side="left", padx=2)
            for j in range(len(headers)):
                animal_frame.columnconfigure(j, weight=1)

    def open_add_animal_dialog(self):
        logging.info("Открытие диалога добавления животного")
        dialog = AnimalDialog(self, self.db_manager, title="Добавить животное")
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_animals()

    def open_edit_animal_dialog(self, animal):
        logging.info(f"Открытие диалога редактирования животного ID {animal['id']}")
        dialog = AnimalDialog(self, self.db_manager, title="Редактировать животное", animal=animal)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_animals()

    def delete_animal(self, animal):
        if messagebox.askyesno("Подтверждение", f"Удалить животное '{animal['nickname']}'?"):
            def delete():
                success = self.db_manager.delete_animal(animal['id'])
                self.after(0, lambda: self.handle_delete_result(success, "Животное удалено", "Не удалось удалить животное"))
            threading.Thread(target=delete, daemon=True).start()

    def refresh_animals(self):
        logging.info("Обновление списка животных")
        self.load_animals_data()

    def handle_delete_result(self, success, success_msg, error_msg):
        if success is not None and success > 0:
            messagebox.showinfo("Успех", success_msg)
            self.refresh_data()
        else:
            messagebox.showerror("Ошибка", error_msg)

    def show_staff(self):
        logging.info("Открытие раздела 'Сотрудники'")
        self.current_content = self.show_staff
        self.clear_content_frame()
        title_label = ctk.CTkLabel(self.content_frame, text="Управление сотрудниками",
                                   font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        controls_frame = ctk.CTkFrame(self.content_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(controls_frame, text="Добавить сотрудника",
                      command=self.open_add_staff_dialog, width=150).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Обновить список",
                      command=self.refresh_staff, width=150).pack(side="left", padx=5)
        self.staff_tree = ctk.CTkScrollableFrame(self.content_frame)
        self.staff_tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.load_staff_data()

    def load_staff_data(self):
        for widget in self.staff_tree.winfo_children():
            widget.destroy()
        def load_data():
            staff_list = self.db_manager.get_all_staff()
            self.after(0, lambda: self.display_staff(staff_list))
        threading.Thread(target=load_data, daemon=True).start()

    def display_staff(self, staff_list):
        for widget in self.staff_tree.winfo_children():
            widget.destroy()
        if not staff_list:
            ctk.CTkLabel(self.staff_tree, text="Нет данных о сотрудниках").pack(pady=20)
            return
        #заголовки
        headers_frame = ctk.CTkFrame(self.staff_tree)
        headers_frame.pack(fill='x', pady=(0, 5))
        headers = ["ID", "ФИО", "Должность", "Email", "Действия"]
        for i, col in enumerate(headers):
            header = ctk.CTkLabel(headers_frame, text=col, font=("Arial", 12, "bold"),
                                  width=120, height=30)
            header.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        #данные
        for row_idx, staff in enumerate(staff_list, 1):
            staff_frame = ctk.CTkFrame(self.staff_tree)
            staff_frame.pack(fill='x', padx=1, pady=1)
            ctk.CTkLabel(staff_frame, text=str(staff['id']), width=120, height=30).grid(
                row=0, column=0, padx=1, pady=1, sticky="ew")
            #ФИО
            full_name = staff['full_name'] or ''
            if len(full_name) > 25:
                full_name = full_name[:25] + '...'
            ctk.CTkLabel(staff_frame, text=full_name, width=120, height=30).grid(
                row=0, column=1, padx=1, pady=1, sticky="ew")
            #Должность
            post = staff['post'] or ''
            if len(post) > 20:
                post = post[:20] + '...'
            ctk.CTkLabel(staff_frame, text=post, width=120, height=30).grid(
                row=0, column=2, padx=1, pady=1, sticky="ew")
            #Email
            email = staff['email'] or ''
            if len(email) > 25:
                email = email[:25] + '...'
            ctk.CTkLabel(staff_frame, text=email, width=120, height=30).grid(
                row=0, column=3, padx=1, pady=1, sticky="ew")
            actions_frame = ctk.CTkFrame(staff_frame, fg_color="transparent", width=120)
            actions_frame.grid(row=0, column=4, padx=1, pady=1, sticky="ew")
            actions_frame.grid_propagate(False)
            ctk.CTkButton(actions_frame, text="✏️", width=30, height=25,
                          command=lambda s=staff: self.open_edit_staff_dialog(s)).pack(side="left", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️", width=30, height=25,
                          command=lambda s=staff: self.delete_staff(s)).pack(side="left", padx=2)
            for j in range(len(headers)):
                staff_frame.columnconfigure(j, weight=1)

    def open_add_staff_dialog(self):
        logging.info("Открытие диалога добавления сотрудника")
        dialog = StaffDialog(self, self.db_manager, title="Добавить сотрудника")
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_staff()

    def open_edit_staff_dialog(self, staff):
        logging.info(f"Открытие диалога редактирования сотрудника ID {staff['id']}")
        dialog = StaffDialog(self, self.db_manager, title="Редактировать сотрудника", staff=staff)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_staff()

    def delete_staff(self, staff):
        if messagebox.askyesno("Подтверждение", f"Удалить сотрудника '{staff['full_name']}'?"):
            def delete():
                success = self.db_manager.delete_staff(staff['id'])
                self.after(0, lambda: self.handle_delete_result(success, "Сотрудник удален", "Не удалось удалить сотрудника"))
            threading.Thread(target=delete, daemon=True).start()

    def refresh_staff(self):
        logging.info("Обновление списка сотрудников")
        self.load_staff_data()

    def show_species(self):
        logging.info("Открытие раздела 'Виды животных'")
        self.current_content = self.show_species
        self.clear_content_frame()
        title_label = ctk.CTkLabel(self.content_frame, text="Управление видами животных",
                                   font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        controls_frame = ctk.CTkFrame(self.content_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(controls_frame, text="Добавить вид",
                      command=self.open_add_species_dialog, width=150).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Обновить список",
                      command=self.refresh_species, width=150).pack(side="left", padx=5)
        self.species_tree = ctk.CTkScrollableFrame(self.content_frame)
        self.species_tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.load_species_data()

    def load_species_data(self):
        for widget in self.species_tree.winfo_children():
            widget.destroy()
        def load_data():
            species_list = self.db_manager.get_all_species()
            self.after(0, lambda: self.display_species(species_list))
        threading.Thread(target=load_data, daemon=True).start()

    def display_species(self, species_list):
        for widget in self.species_tree.winfo_children():
            widget.destroy()
        if not species_list:
            ctk.CTkLabel(self.species_tree, text="Нет данных о видах животных").pack(pady=20)
            return
        #заголовки
        headers_frame = ctk.CTkFrame(self.species_tree)
        headers_frame.pack(fill='x', pady=(0, 5))
        headers = ["ID", "Название", "Научное название", "Статус", "Действия"]
        for i, col in enumerate(headers):
            header = ctk.CTkLabel(headers_frame, text=col, font=("Arial", 12, "bold"),
                                  width=120, height=30)
            header.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        #заполнение данными
        for row_idx, species in enumerate(species_list, 1):
            species_frame = ctk.CTkFrame(self.species_tree)
            species_frame.pack(fill='x', padx=1, pady=1)
            ctk.CTkLabel(species_frame, text=str(species['id']), width=120, height=30).grid(
                row=0, column=0, padx=1, pady=1, sticky="ew")
            #название вида
            name = species['name'] or ''
            if len(name) > 15:
                name = name[:15] + '...'
            ctk.CTkLabel(species_frame, text=name, width=120, height=30).grid(
                row=0, column=1, padx=1, pady=1, sticky="ew")
            #научное название
            scientific_name = species['scientific_name'] or ''
            if len(scientific_name) > 20:
                scientific_name = scientific_name[:20] + '...'
            ctk.CTkLabel(species_frame, text=scientific_name, width=120, height=30).grid(
                row=0, column=2, padx=1, pady=1, sticky="ew")
            #статус
            status = species['status'] or ''
            if len(status) > 15:
                status = status[:15] + '...'
            ctk.CTkLabel(species_frame, text=status, width=120, height=30).grid(
                row=0, column=3, padx=1, pady=1, sticky="ew")
            actions_frame = ctk.CTkFrame(species_frame, fg_color="transparent", width=120)
            actions_frame.grid(row=0, column=4, padx=1, pady=1, sticky="ew")
            actions_frame.grid_propagate(False)
            ctk.CTkButton(actions_frame, text="✏️", width=30, height=25,
                          command=lambda s=species: self.open_edit_species_dialog(s)).pack(side="left", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️", width=30, height=25,
                          command=lambda s=species: self.delete_species(s)).pack(side="left", padx=2)
            for j in range(len(headers)):
                species_frame.columnconfigure(j, weight=1)

    def open_add_species_dialog(self):
        logging.info("Открытие диалога добавления вида животного")
        dialog = SpeciesDialog(self, self.db_manager, title="Добавить вид животного")
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_species()

    def open_edit_species_dialog(self, species):
        logging.info(f"Открытие диалога редактирования вида животного ID {species['id']}")
        dialog = SpeciesDialog(self, self.db_manager, title="Редактировать вид животного", species=species)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_species()

    def delete_species(self, species):
        if messagebox.askyesno("Подтверждение", f"Удалить вид '{species['name']}'?"):
            def delete():
                success = self.db_manager.delete_species(species['id'])
                self.after(0, lambda: self.handle_delete_result(success, "Вид животного удален", "Не удалось удалить вид животного"))
            threading.Thread(target=delete, daemon=True).start()

    def refresh_species(self):
        logging.info("Обновление списка видов животных")
        self.load_species_data()

    def show_habitats(self):
        logging.info("Открытие раздела 'Места обитания'")
        self.current_content = self.show_habitats
        self.clear_content_frame()
        title_label = ctk.CTkLabel(self.content_frame, text="Управление местами обитания",
                                   font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        controls_frame = ctk.CTkFrame(self.content_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(controls_frame, text="Добавить место обитания",
                      command=self.open_add_habitat_dialog, width=180).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Обновить список",
                      command=self.refresh_habitats, width=150).pack(side="left", padx=5)
        self.habitats_tree = ctk.CTkScrollableFrame(self.content_frame)
        self.habitats_tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.load_habitats_data()

    def load_habitats_data(self):
        for widget in self.habitats_tree.winfo_children():
            widget.destroy()
        def load_data():
            habitats_list = self.db_manager.get_all_habitats()
            self.after(0, lambda: self.display_habitats(habitats_list))
        threading.Thread(target=load_data, daemon=True).start()

    def display_habitats(self, habitats_list):
        for widget in self.habitats_tree.winfo_children():
            widget.destroy()
        if not habitats_list:
            ctk.CTkLabel(self.habitats_tree, text="Нет данных о местах обитания").pack(pady=20)
            return
        #заголовки
        headers_frame = ctk.CTkFrame(self.habitats_tree)
        headers_frame.pack(fill='x', pady=(0, 5))
        headers = ["ID", "Название", "Площадь", "Тип местности", "Описание", "Действия"]
        for i, col in enumerate(headers):
            header = ctk.CTkLabel(headers_frame, text=col, font=("Arial", 12, "bold"),
                                  width=120, height=30)
            header.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        #заполнение данными
        for row_idx, habitat in enumerate(habitats_list, 1):
            habitat_frame = ctk.CTkFrame(self.habitats_tree)
            habitat_frame.pack(fill='x', padx=1, pady=1)
            ctk.CTkLabel(habitat_frame, text=str(habitat['id']), width=120, height=30).grid(
                row=0, column=0, padx=1, pady=1, sticky="ew")
            #название
            name = habitat['name'] or ''
            if len(name) > 15:
                name = name[:15] + '...'
            ctk.CTkLabel(habitat_frame, text=name, width=120, height=30).grid(
                row=0, column=1, padx=1, pady=1, sticky="ew")
            ctk.CTkLabel(habitat_frame, text=str(habitat['square']), width=120, height=30).grid(
                row=0, column=2, padx=1, pady=1, sticky="ew")
            #тип местности
            terrain_type = habitat['terrain_type'] or ''
            if len(terrain_type) > 15:
                terrain_type = terrain_type[:15] + '...'
            ctk.CTkLabel(habitat_frame, text=terrain_type, width=120, height=30).grid(
                row=0, column=3, padx=1, pady=1, sticky="ew")
            #описание
            description = habitat['description'] or ''
            if len(description) > 25:
                description = description[:25] + '...'
            ctk.CTkLabel(habitat_frame, text=description,
                         width=120, height=30).grid(row=0, column=4, padx=1, pady=1, sticky="ew")
            actions_frame = ctk.CTkFrame(habitat_frame, fg_color="transparent", width=120)
            actions_frame.grid(row=0, column=5, padx=1, pady=1, sticky="ew")
            actions_frame.grid_propagate(False)
            ctk.CTkButton(actions_frame, text="✏️", width=30, height=25,
                          command=lambda h=habitat: self.open_edit_habitat_dialog(h)).pack(side="left", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️", width=30, height=25,
                          command=lambda h=habitat: self.delete_habitat(h)).pack(side="left", padx=2)
            for j in range(len(headers)):
                habitat_frame.columnconfigure(j, weight=1)

    def open_add_habitat_dialog(self):
        logging.info("Открытие диалога добавления места обитания")
        dialog = HabitatDialog(self, self.db_manager, title="Добавить место обитания")
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_habitats()

    def open_edit_habitat_dialog(self, habitat):
        logging.info(f"Открытие диалога редактирования места обитания ID {habitat['id']}")
        dialog = HabitatDialog(self, self.db_manager, title="Редактировать место обитания", habitat=habitat)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_habitats()

    def delete_habitat(self, habitat):
        if messagebox.askyesno("Подтверждение", f"Удалить место обитания '{habitat['name']}'?"):
            def delete():
                success = self.db_manager.delete_habitat(habitat['id'])
                self.after(0, lambda: self.handle_delete_result(success, "Место обитания удалено", "Не удалось удалить место обитания"))
            threading.Thread(target=delete, daemon=True).start()

    def refresh_habitats(self):
        logging.info("Обновление списка мест обитания")
        self.load_habitats_data()

    def show_feedings(self):
        logging.info("Открытие раздела 'Кормления'")
        self.current_content = self.show_feedings
        self.clear_content_frame()
        title_label = ctk.CTkLabel(self.content_frame, text="Управление кормлениями",
                                   font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        controls_frame = ctk.CTkFrame(self.content_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(controls_frame, text="Добавить кормление",
                      command=self.open_add_feeding_dialog, width=150).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Обновить список",
                      command=self.refresh_feedings, width=150).pack(side="left", padx=5)
        self.feedings_tree = ctk.CTkScrollableFrame(self.content_frame)
        self.feedings_tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.load_feedings_data()

    def load_feedings_data(self):
        for widget in self.feedings_tree.winfo_children():
            widget.destroy()
        def load_data():
            feedings_list = self.db_manager.get_all_feedings()
            self.after(0, lambda: self.display_feedings(feedings_list))
        threading.Thread(target=load_data, daemon=True).start()

    def display_feedings(self, feedings_list):
        for widget in self.feedings_tree.winfo_children():
            widget.destroy()
        if not feedings_list:
            ctk.CTkLabel(self.feedings_tree, text="Нет данных о кормлениях").pack(pady=20)
            return
        #заголовки
        headers_frame = ctk.CTkFrame(self.feedings_tree)
        headers_frame.pack(fill='x', pady=(0, 5))
        headers = ["ID", "Дата кормления", "Животное", "Тип корма", "Оценка аппетита", "Сотрудник", "Действия"]
        for i, col in enumerate(headers):
            header = ctk.CTkLabel(headers_frame, text=col, font=("Arial", 12, "bold"),
                                  width=120, height=30)
            header.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        #заполнение данными
        for row_idx, feeding in enumerate(feedings_list, 1):
            feeding_frame = ctk.CTkFrame(self.feedings_tree)
            feeding_frame.pack(fill='x', padx=1, pady=1)
            ctk.CTkLabel(feeding_frame, text=str(feeding['id']), width=120, height=30).grid(
                row=0, column=0, padx=1, pady=1, sticky="ew")
            ctk.CTkLabel(feeding_frame, text=str(feeding['feeding_date']), width=120, height=30).grid(
                row=0, column=1, padx=1, pady=1, sticky="ew")
            #животное
            animal_name = feeding['animal_name'] or ''
            if len(animal_name) > 15:
                animal_name = animal_name[:15] + '...'
            ctk.CTkLabel(feeding_frame, text=animal_name, width=120, height=30).grid(
                row=0, column=2, padx=1, pady=1, sticky="ew")
            #тип корма
            food_type = feeding['food_type'] or ''
            if len(food_type) > 15:
                food_type = food_type[:15] + '...'
            ctk.CTkLabel(feeding_frame, text=food_type, width=120, height=30).grid(
                row=0, column=3, padx=1, pady=1, sticky="ew")
            ctk.CTkLabel(feeding_frame, text=feeding['appetite_assessment'], width=120, height=30).grid(
                row=0, column=4, padx=1, pady=1, sticky="ew")
            #сотрудник
            staff_name = feeding['staff_name'] or ''
            if len(staff_name) > 15:
                staff_name = staff_name[:15] + '...'
            ctk.CTkLabel(feeding_frame, text=staff_name, width=120, height=30).grid(
                row=0, column=5, padx=1, pady=1, sticky="ew")
            actions_frame = ctk.CTkFrame(feeding_frame, fg_color="transparent", width=120)
            actions_frame.grid(row=0, column=6, padx=1, pady=1, sticky="ew")
            actions_frame.grid_propagate(False)
            ctk.CTkButton(actions_frame, text="✏️", width=30, height=25,
                          command=lambda f=feeding: self.open_edit_feeding_dialog(f)).pack(side="left", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️", width=30, height=25,
                          command=lambda f=feeding: self.delete_feeding(f)).pack(side="left", padx=2)
            for j in range(len(headers)):
                feeding_frame.columnconfigure(j, weight=1)

    def open_add_feeding_dialog(self):
        logging.info("Открытие диалога добавления кормления")
        dialog = FeedingDialog(self, self.db_manager, title="Добавить кормление")
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_feedings()

    def open_edit_feeding_dialog(self, feeding):
        logging.info(f"Открытие диалога редактирования кормления ID {feeding['id']}")
        dialog = FeedingDialog(self, self.db_manager, title="Редактировать кормление", feeding=feeding)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_feedings()

    def delete_feeding(self, feeding):
        if messagebox.askyesno("Подтверждение", f"Удалить запись о кормлении от {feeding['feeding_date']}?"):
            def delete():
                success = self.db_manager.delete_feeding(feeding['id'])
                self.after(0, lambda: self.handle_delete_result(success, "Запись о кормлении удалена", "Не удалось удалить запись о кормлении"))
            threading.Thread(target=delete, daemon=True).start()

    def refresh_feedings(self):
        logging.info("Обновление списка кормлений")
        self.load_feedings_data()

    def show_health_observations(self):
        logging.info("Открытие раздела 'Наблюдения за здоровьем'")
        self.current_content = self.show_health_observations
        self.clear_content_frame()
        title_label = ctk.CTkLabel(self.content_frame, text="Наблюдения за здоровьем",
                                   font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        controls_frame = ctk.CTkFrame(self.content_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(controls_frame, text="Добавить наблюдение",
                      command=self.open_add_health_observation_dialog, width=180).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Обновить список",
                      command=self.refresh_health_observations, width=150).pack(side="left", padx=5)
        self.health_tree = ctk.CTkScrollableFrame(self.content_frame)
        self.health_tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.load_health_observations_data()

    def load_health_observations_data(self):
        for widget in self.health_tree.winfo_children():
            widget.destroy()
        def load_data():
            observations_list = self.db_manager.get_all_health_observations()
            self.after(0, lambda: self.display_health_observations(observations_list))
        threading.Thread(target=load_data, daemon=True).start()

    def display_health_observations(self, observations_list):
        for widget in self.health_tree.winfo_children():
            widget.destroy()
        if not observations_list:
            ctk.CTkLabel(self.health_tree, text="Нет данных о наблюдениях за здоровьем").pack(pady=20)
            return
        #заголовки
        headers_frame = ctk.CTkFrame(self.health_tree)
        headers_frame.pack(fill='x', pady=(0, 5))
        headers = ["ID", "Дата осмотра", "Животное", "Общее состояние", "Диагноз", "Сотрудник", "Действия"]
        for i, col in enumerate(headers):
            header = ctk.CTkLabel(headers_frame, text=col, font=("Arial", 12, "bold"),
                                  width=120, height=30)
            header.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        #заполнение данными
        for row_idx, observation in enumerate(observations_list, 1):
            observation_frame = ctk.CTkFrame(self.health_tree)
            observation_frame.pack(fill='x', padx=1, pady=1)
            ctk.CTkLabel(observation_frame, text=str(observation['id']), width=120, height=30).grid(
                row=0, column=0, padx=1, pady=1, sticky="ew")
            ctk.CTkLabel(observation_frame, text=str(observation['date_of_inspection']), width=120, height=30).grid(
                row=0, column=1, padx=1, pady=1, sticky="ew")
            #животное
            animal_name = observation['animal_name'] or ''
            if len(animal_name) > 15:
                animal_name = animal_name[:15] + '...'
            ctk.CTkLabel(observation_frame, text=animal_name, width=120, height=30).grid(
                row=0, column=2, padx=1, pady=1, sticky="ew")
            #общее состояние
            condition = observation['general_condition'] or ''
            if len(condition) > 15:
                condition = condition[:15] + '...'
            ctk.CTkLabel(observation_frame, text=condition, width=120, height=30).grid(
                row=0, column=3, padx=1, pady=1, sticky="ew")
            #диагноз
            diagnosis = observation['diagnosis'] or ''
            if len(diagnosis) > 15:
                diagnosis = diagnosis[:15] + '...'
            ctk.CTkLabel(observation_frame, text=diagnosis, width=120, height=30).grid(
                row=0, column=4, padx=1, pady=1, sticky="ew")
            #сотрудник
            staff_name = observation['staff_name'] or ''
            if len(staff_name) > 15:
                staff_name = staff_name[:15] + '...'
            ctk.CTkLabel(observation_frame, text=staff_name, width=120, height=30).grid(
                row=0, column=5, padx=1, pady=1, sticky="ew")
            actions_frame = ctk.CTkFrame(observation_frame, fg_color="transparent", width=120)
            actions_frame.grid(row=0, column=6, padx=1, pady=1, sticky="ew")
            actions_frame.grid_propagate(False)
            ctk.CTkButton(actions_frame, text="✏️", width=30, height=25,
                          command=lambda o=observation: self.open_edit_health_observation_dialog(o)).pack(side="left", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️", width=30, height=25,
                          command=lambda o=observation: self.delete_health_observation(o)).pack(side="left", padx=2)
            for j in range(len(headers)):
                observation_frame.columnconfigure(j, weight=1)

    def open_add_health_observation_dialog(self):
        logging.info("Открытие диалога добавления наблюдения за здоровьем")
        dialog = HealthObservationDialog(self, self.db_manager, title="Добавить наблюдение за здоровьем")
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_health_observations()

    def open_edit_health_observation_dialog(self, observation):
        logging.info(f"Открытие диалога редактирования наблюдения за здоровьем ID {observation['id']}")
        dialog = HealthObservationDialog(self, self.db_manager, title="Редактировать наблюдение за здоровьем", observation=observation)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_health_observations()

    def delete_health_observation(self, observation):
        if messagebox.askyesno("Подтверждение", f"Удалить запись о наблюдении от {observation['date_of_inspection']}?"):
            def delete():
                success = self.db_manager.delete_health_observation(observation['id'])
                self.after(0, lambda: self.handle_delete_result(success, "Запись о наблюдении удалена", "Не удалось удалить запись о наблюдении"))
            threading.Thread(target=delete, daemon=True).start()

    def refresh_health_observations(self):
        logging.info("Обновление списка наблюдений за здоровьем")
        self.load_health_observations_data()


#класс для диалоговых окон
class BaseDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, width=500, height=400):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(parent)
        #центр относительно родительского окна
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{x}+{y}")
        self.result = None
        self.after(100, self.grab_set)


class AnimalDialog(BaseDialog):
    def __init__(self, parent, db_manager, title, animal=None):
        super().__init__(parent, title, 500, 600)
        self.db_manager = db_manager
        self.animal = animal
        self.create_widgets()
        self.load_data()
        if animal:
            self.fill_form()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.nickname_var = ctk.StringVar()
        self.description_var = ctk.StringVar()
        self.date_of_birth_var = ctk.StringVar()
        self.special_signs_var = ctk.StringVar()
        self.date_of_admission_var = ctk.StringVar()
        self.species_var = ctk.StringVar()
        self.gender_var = ctk.StringVar()
        fields = [
            ("Кличка:", self.nickname_var),
            ("Описание:", self.description_var),
            ("Дата рождения (ГГГГ-ММ-ДД):", self.date_of_birth_var),
            ("Особые приметы:", self.special_signs_var),
            ("Дата поступления (ГГГГ-ММ-ДД):", self.date_of_admission_var)
        ]
        for i, (label, var) in enumerate(fields):
            ctk.CTkLabel(main_frame, text=label, font=("Arial", 12)).grid(row=i, column=0, sticky="w", pady=10)
            ctk.CTkEntry(main_frame, textvariable=var, width=300).grid(row=i, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Вид:", font=("Arial", 12)).grid(row=5, column=0, sticky="w", pady=10)
        self.species_combo = ctk.CTkComboBox(main_frame, variable=self.species_var, width=300)
        self.species_combo.grid(row=5, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Пол:", font=("Arial", 12)).grid(row=6, column=0, sticky="w", pady=10)
        self.gender_combo = ctk.CTkComboBox(main_frame, variable=self.gender_var, width=300)
        self.gender_combo.grid(row=6, column=1, sticky="ew", pady=10, padx=(10, 0))
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Сохранить", command=self.save).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=10)
        main_frame.columnconfigure(1, weight=1)

    def load_data(self):
        def load():
            species_list = self.db_manager.get_species_list()
            genders_list = self.db_manager.get_genders_list()
            self.after(0, lambda: self.update_combos(species_list, genders_list))
        threading.Thread(target=load, daemon=True).start()

    def update_combos(self, species_list, genders_list):
        if species_list:
            species_values = [f"{s[0]} - {s[1]}" for s in species_list]
            self.species_combo.configure(values=species_values)
            if species_values:
                self.species_combo.set(species_values[0])
        if genders_list:
            gender_values = [f"{g[0]} - {g[1]}" for g in genders_list]
            self.gender_combo.configure(values=gender_values)
            if gender_values:
                self.gender_combo.set(gender_values[0])

    def fill_form(self):
        if self.animal:
            self.nickname_var.set(self.animal['nickname'] or "")
            self.description_var.set(self.animal['description'] or "")
            self.date_of_birth_var.set(str(self.animal['date_of_birth']) if self.animal['date_of_birth'] else "")
            self.special_signs_var.set(self.animal['special_signs'] or "")
            self.date_of_admission_var.set(str(self.animal['date_of_admission']) if self.animal['date_of_admission'] else "")
            def load_species_genders():
                species_list = self.db_manager.get_species_list()
                genders_list = self.db_manager.get_genders_list()
                self.after(0, lambda: self.set_selected_values(species_list, genders_list))
            threading.Thread(target=load_species_genders, daemon=True).start()

    def set_selected_values(self, species_list, genders_list):
        if species_list:
            for species in species_list:
                if species[0] == self.animal['id_type']:
                    self.species_var.set(f"{species[0]} - {species[1]}")
                    break
        if genders_list:
            for gender in genders_list:
                if gender[0] == self.animal['id_gender']:
                    self.gender_var.set(f"{gender[0]} - {gender[1]}")
                    break

    def save(self):
        def save_data():
            try:
                nickname = self.nickname_var.get().strip()
                description = self.description_var.get().strip()
                date_of_birth = self.date_of_birth_var.get().strip() or None
                special_signs = self.special_signs_var.get().strip()
                date_of_admission = self.date_of_admission_var.get().strip() or None
                species_str = self.species_var.get()
                gender_str = self.gender_var.get()
                if not nickname:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Поле 'Кличка' обязательно для заполнения"))
                    return
                if date_of_birth:
                    datetime.strptime(date_of_birth, '%Y-%m-%d')  # Validate date
                if date_of_admission:
                    datetime.strptime(date_of_admission, '%Y-%m-%d')
                species_id = int(species_str.split(' - ')[0]) if species_str else None
                gender_id = int(gender_str.split(' - ')[0]) if gender_str else None
                if species_id is None or gender_id is None:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Выберите вид и пол"))
                    return
                animal_data = (
                    nickname,
                    description if description else "",
                    date_of_birth,
                    special_signs if special_signs else "",
                    date_of_admission,
                    species_id,
                    gender_id
                )
                if self.animal:
                    success = self.db_manager.update_animal(self.animal['id'], animal_data)
                    message = "Животное обновлено"
                else:
                    success = self.db_manager.add_animal(animal_data)
                    message = "Животное добавлено"
                self.after(0, lambda: self.handle_save_result(success, message))
            except ValueError as ve:
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Неверный формат даты: {str(ve)}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}"))
        threading.Thread(target=save_data, daemon=True).start()

    def handle_save_result(self, success, message):
        if success is not None:
            if success == 0:
                messagebox.showwarning("Предупреждение", "Запись не изменена (возможно, не найдена или данные идентичны)")
            else:
                messagebox.showinfo("Успех", message)
                self.result = True
                self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить данные")

    def cancel(self):
        self.destroy()


class StaffDialog(BaseDialog):
    def __init__(self, parent, db_manager, title, staff=None):
        super().__init__(parent, title, 500, 400)
        self.db_manager = db_manager
        self.staff = staff
        self.create_widgets()
        if staff:
            self.fill_form()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.full_name_var = ctk.StringVar()
        self.post_var = ctk.StringVar()
        self.email_var = ctk.StringVar()
        fields = [
            ("ФИО:", self.full_name_var),
            ("Должность:", self.post_var),
            ("Email:", self.email_var)
        ]
        for i, (label, var) in enumerate(fields):
            ctk.CTkLabel(main_frame, text=label, font=("Arial", 12)).grid(row=i, column=0, sticky="w", pady=15)
            ctk.CTkEntry(main_frame, textvariable=var, width=300).grid(row=i, column=1, sticky="ew", pady=15, padx=(10, 0))
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Сохранить", command=self.save).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=10)
        main_frame.columnconfigure(1, weight=1)

    def fill_form(self):
        if self.staff:
            self.full_name_var.set(self.staff['full_name'] or "")
            self.post_var.set(self.staff['post'] or "")
            self.email_var.set(self.staff['email'] or "")

    def save(self):
        def save_data():
            try:
                full_name = self.full_name_var.get().strip()
                post = self.post_var.get().strip()
                email = self.email_var.get().strip()
                if not full_name:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Поле 'ФИО' обязательно для заполнения"))
                    return
                staff_data = (full_name, post, email)
                if self.staff:
                    success = self.db_manager.update_staff(self.staff['id'], staff_data)
                    message = "Сотрудник обновлен"
                else:
                    success = self.db_manager.add_staff(staff_data)
                    message = "Сотрудник добавлен"
                self.after(0, lambda: self.handle_save_result(success, message))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}"))
        threading.Thread(target=save_data, daemon=True).start()

    def handle_save_result(self, success, message):
        if success is not None:
            if success == 0:
                messagebox.showwarning("Предупреждение", "Запись не изменена (возможно, не найдена или данные идентичны)")
            else:
                messagebox.showinfo("Успех", message)
                self.result = True
                self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить данные")

    def cancel(self):
        self.destroy()


class SpeciesDialog(BaseDialog):
    def __init__(self, parent, db_manager, title, species=None):
        super().__init__(parent, title, 500, 400)
        self.db_manager = db_manager
        self.species = species
        self.create_widgets()
        if species:
            self.fill_form()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.name_var = ctk.StringVar()
        self.scientific_name_var = ctk.StringVar()
        self.status_var = ctk.StringVar()
        fields = [
            ("Название:", self.name_var),
            ("Научное название:", self.scientific_name_var),
            ("Статус:", self.status_var)
        ]
        for i, (label, var) in enumerate(fields):
            ctk.CTkLabel(main_frame, text=label, font=("Arial", 12)).grid(row=i, column=0, sticky="w", pady=15)
            ctk.CTkEntry(main_frame, textvariable=var, width=300).grid(row=i, column=1, sticky="ew", pady=15, padx=(10, 0))
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Сохранить", command=self.save).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=10)
        main_frame.columnconfigure(1, weight=1)

    def fill_form(self):
        if self.species:
            self.name_var.set(self.species['name'] or "")
            self.scientific_name_var.set(self.species['scientific_name'] or "")
            self.status_var.set(self.species['status'] or "")

    def save(self):
        def save_data():
            try:
                name = self.name_var.get().strip()
                scientific_name = self.scientific_name_var.get().strip()
                status = self.status_var.get().strip()
                if not name:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Поле 'Название' обязательно для заполнения"))
                    return
                species_data = (name, scientific_name, status)
                if self.species:
                    success = self.db_manager.update_species(self.species['id'], species_data)
                    message = "Вид животного обновлен"
                else:
                    success = self.db_manager.add_species(species_data)
                    message = "Вид животного добавлен"
                self.after(0, lambda: self.handle_save_result(success, message))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}"))
        threading.Thread(target=save_data, daemon=True).start()

    def handle_save_result(self, success, message):
        if success is not None:
            if success == 0:
                messagebox.showwarning("Предупреждение", "Запись не изменена (возможно, не найдена или данные идентичны)")
            else:
                messagebox.showinfo("Успех", message)
                self.result = True
                self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить данные")

    def cancel(self):
        self.destroy()


class HabitatDialog(BaseDialog):
    def __init__(self, parent, db_manager, title, habitat=None):
        super().__init__(parent, title, 500, 500)
        self.db_manager = db_manager
        self.habitat = habitat
        self.create_widgets()
        self.load_data()
        if habitat:
            self.fill_form()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.name_var = ctk.StringVar()
        self.square_var = ctk.StringVar()
        self.description_var = ctk.StringVar()
        self.terrain_type_var = ctk.StringVar()
        fields = [
            ("Название:", self.name_var),
            ("Площадь:", self.square_var),
            ("Описание:", self.description_var)
        ]
        for i, (label, var) in enumerate(fields):
            ctk.CTkLabel(main_frame, text=label, font=("Arial", 12)).grid(row=i, column=0, sticky="w", pady=10)
            ctk.CTkEntry(main_frame, textvariable=var, width=300).grid(row=i, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Тип местности:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=10)
        self.terrain_type_combo = ctk.CTkComboBox(main_frame, variable=self.terrain_type_var, width=300)
        self.terrain_type_combo.grid(row=3, column=1, sticky="ew", pady=10, padx=(10, 0))
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Сохранить", command=self.save).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=10)
        main_frame.columnconfigure(1, weight=1)

    def load_data(self):
        def load():
            terrain_types = self.db_manager.get_terrain_types_list()
            self.after(0, lambda: self.update_terrain_combo(terrain_types))
        threading.Thread(target=load, daemon=True).start()

    def update_terrain_combo(self, terrain_types):
        if terrain_types:
            terrain_values = [f"{t[0]} - {t[1]}" for t in terrain_types]
            self.terrain_type_combo.configure(values=terrain_values)
            if terrain_values:
                self.terrain_type_combo.set(terrain_values[0])

    def fill_form(self):
        if self.habitat:
            self.name_var.set(self.habitat['name'] or "")
            self.square_var.set(str(self.habitat['square']) if self.habitat['square'] else "")
            self.description_var.set(self.habitat['description'] or "")
            def load_terrain():
                terrain_types = self.db_manager.get_terrain_types_list()
                self.after(0, lambda: self.set_selected_terrain(terrain_types))
            threading.Thread(target=load_terrain, daemon=True).start()

    def set_selected_terrain(self, terrain_types):
        if terrain_types:
            for terrain in terrain_types:
                if terrain[0] == self.habitat['id_type_of_terrain']:
                    self.terrain_type_var.set(f"{terrain[0]} - {terrain[1]}")
                    break

    def save(self):
        def save_data():
            try:
                name = self.name_var.get().strip()
                square_str = self.square_var.get().strip()
                description = self.description_var.get().strip()
                terrain_str = self.terrain_type_var.get()
                if not name:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Поле 'Название' обязательно для заполнения"))
                    return
                square = float(square_str) if square_str else 0.0
                terrain_id = int(terrain_str.split(' - ')[0]) if terrain_str else None
                habitat_data = (
                    name,
                    square,
                    description if description else "",
                    terrain_id
                )
                if self.habitat:
                    success = self.db_manager.update_habitat(self.habitat['id'], habitat_data)
                    message = "Место обитания обновлено"
                else:
                    success = self.db_manager.add_habitat(habitat_data)
                    message = "Место обитания добавлено"
                self.after(0, lambda: self.handle_save_result(success, message))
            except ValueError:
                self.after(0, lambda: messagebox.showerror("Ошибка", "Неверный формат площади"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}"))
        threading.Thread(target=save_data, daemon=True).start()

    def handle_save_result(self, success, message):
        if success is not None:
            if success == 0:
                messagebox.showwarning("Предупреждение", "Запись не изменена (возможно, не найдена или данные идентичны)")
            else:
                messagebox.showinfo("Успех", message)
                self.result = True
                self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить данные")

    def cancel(self):
        self.destroy()


class FeedingDialog(BaseDialog):
    def __init__(self, parent, db_manager, title, feeding=None):
        super().__init__(parent, title, 500, 500)
        self.db_manager = db_manager
        self.feeding = feeding
        self.create_widgets()
        self.load_data()
        if feeding:
            self.fill_form()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.feeding_date_var = ctk.StringVar()
        self.appetite_assessment_var = ctk.StringVar()
        self.animal_var = ctk.StringVar()
        self.staff_var = ctk.StringVar()
        self.food_type_var = ctk.StringVar()
        fields = [
            ("Дата кормления (ГГГГ-ММ-ДД):", self.feeding_date_var),
            ("Оценка аппетита:", self.appetite_assessment_var)
        ]
        for i, (label, var) in enumerate(fields):
            ctk.CTkLabel(main_frame, text=label, font=("Arial", 12)).grid(row=i, column=0, sticky="w", pady=10)
            ctk.CTkEntry(main_frame, textvariable=var, width=300).grid(row=i, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Животное:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=10)
        self.animal_combo = ctk.CTkComboBox(main_frame, variable=self.animal_var, width=300)
        self.animal_combo.grid(row=2, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Сотрудник:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=10)
        self.staff_combo = ctk.CTkComboBox(main_frame, variable=self.staff_var, width=300)
        self.staff_combo.grid(row=3, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Тип корма:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", pady=10)
        self.food_type_combo = ctk.CTkComboBox(main_frame, variable=self.food_type_var, width=300)
        self.food_type_combo.grid(row=4, column=1, sticky="ew", pady=10, padx=(10, 0))
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Сохранить", command=self.save).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=10)
        main_frame.columnconfigure(1, weight=1)

    def load_data(self):
        def load():
            animals = self.db_manager.get_all_animals()
            staff_list = self.db_manager.get_staff_list()
            food_types = self.db_manager.get_food_types_list()
            self.after(0, lambda: self.update_combos(animals, staff_list, food_types))
        threading.Thread(target=load, daemon=True).start()

    def update_combos(self, animals, staff_list, food_types):
        if animals:
            animal_values = [f"{a['id']} - {a['nickname']}" for a in animals]
            self.animal_combo.configure(values=animal_values)
            if animal_values:
                self.animal_combo.set(animal_values[0])
        if staff_list:
            staff_values = [f"{s[0]} - {s[1]}" for s in staff_list]
            self.staff_combo.configure(values=staff_values)
            if staff_values:
                self.staff_combo.set(staff_values[0])
        if food_types:
            food_values = [f"{f[0]} - {f[1]}" for f in food_types]
            self.food_type_combo.configure(values=food_values)
            if food_values:
                self.food_type_combo.set(food_values[0])

    def fill_form(self):
        if self.feeding:
            self.feeding_date_var.set(str(self.feeding['feeding_date']) if self.feeding['feeding_date'] else "")
            self.appetite_assessment_var.set(self.feeding['appetite_assessment'] or "")
            def load_combos():
                animals = self.db_manager.get_all_animals()
                staff_list = self.db_manager.get_staff_list()
                food_types = self.db_manager.get_food_types_list()
                self.after(0, lambda: self.set_selected_values(animals, staff_list, food_types))
            threading.Thread(target=load_combos, daemon=True).start()

    def set_selected_values(self, animals, staff_list, food_types):
        if animals:
            for animal in animals:
                if animal['id'] == self.feeding['animal_id']:
                    self.animal_var.set(f"{animal['id']} - {animal['nickname']}")
                    break
        if staff_list:
            for staff in staff_list:
                if staff[1] == self.feeding['staff_name']:
                    self.staff_var.set(f"{staff[0]} - {staff[1]}")
                    break
        if food_types:
            for food in food_types:
                if food[0] == self.feeding['id_type_of_food']:
                    self.food_type_var.set(f"{food[0]} - {food[1]}")
                    break

    def save(self):
        def save_data():
            try:
                feeding_date = self.feeding_date_var.get().strip()
                appetite_assessment = self.appetite_assessment_var.get().strip()
                animal_str = self.animal_var.get()
                staff_str = self.staff_var.get()
                food_str = self.food_type_var.get()
                if not feeding_date:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Поле 'Дата кормления' обязательно для заполнения"))
                    return
                datetime.strptime(feeding_date, '%Y-%m-%d')  # Validate
                animal_id = int(animal_str.split(' - ')[0]) if animal_str else None
                staff_id = int(staff_str.split(' - ')[0]) if staff_str else None
                food_id = int(food_str.split(' - ')[0]) if food_str else None
                if animal_id is None or staff_id is None or food_id is None:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Выберите животное, сотрудника и тип корма"))
                    return
                feeding_data = (feeding_date, appetite_assessment, food_id)
                if self.feeding:
                    success = self.db_manager.update_feeding(self.feeding['id'], feeding_data, animal_id, staff_id)
                    message = "Кормление обновлено"
                else:
                    success = self.db_manager.add_feeding(feeding_data, animal_id, staff_id)
                    message = "Кормление добавлено"
                self.after(0, lambda: self.handle_save_result(success, message))
            except ValueError:
                self.after(0, lambda: messagebox.showerror("Ошибка", "Неверный формат даты"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}"))
        threading.Thread(target=save_data, daemon=True).start()

    def handle_save_result(self, success, message):
        if success is not None:
            if success == 0:
                messagebox.showwarning("Предупреждение", "Запись не изменена (возможно, не найдена или данные идентичны)")
            else:
                messagebox.showinfo("Успех", message)
                self.result = True
                self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить данные")

    def cancel(self):
        self.destroy()


class HealthObservationDialog(BaseDialog):
    def __init__(self, parent, db_manager, title, observation=None):
        super().__init__(parent, title, 500, 500)
        self.db_manager = db_manager
        self.observation = observation
        self.create_widgets()
        self.load_data()
        if observation:
            self.fill_form()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.date_of_inspection_var = ctk.StringVar()
        self.general_condition_var = ctk.StringVar()
        self.diagnosis_var = ctk.StringVar()
        self.notes_var = ctk.StringVar()
        self.animal_var = ctk.StringVar()
        self.staff_var = ctk.StringVar()
        fields = [
            ("Дата осмотра (ГГГГ-ММ-ДД):", self.date_of_inspection_var),
            ("Общее состояние:", self.general_condition_var),
            ("Диагноз:", self.diagnosis_var),
            ("Примечания:", self.notes_var)
        ]
        for i, (label, var) in enumerate(fields):
            ctk.CTkLabel(main_frame, text=label, font=("Arial", 12)).grid(row=i, column=0, sticky="w", pady=10)
            ctk.CTkEntry(main_frame, textvariable=var, width=300).grid(row=i, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Животное:", font=("Arial", 12)).grid(row=4, column=0, sticky="w", pady=10)
        self.animal_combo = ctk.CTkComboBox(main_frame, variable=self.animal_var, width=300)
        self.animal_combo.grid(row=4, column=1, sticky="ew", pady=10, padx=(10, 0))
        ctk.CTkLabel(main_frame, text="Сотрудник:", font=("Arial", 12)).grid(row=5, column=0, sticky="w", pady=10)
        self.staff_combo = ctk.CTkComboBox(main_frame, variable=self.staff_var, width=300)
        self.staff_combo.grid(row=5, column=1, sticky="ew", pady=10, padx=(10, 0))
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Сохранить", command=self.save).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=10)
        main_frame.columnconfigure(1, weight=1)

    def load_data(self):
        def load():
            animals = self.db_manager.get_all_animals()
            staff_list = self.db_manager.get_staff_list()
            self.after(0, lambda: self.update_combos(animals, staff_list))
        threading.Thread(target=load, daemon=True).start()

    def update_combos(self, animals, staff_list):
        if animals:
            animal_values = [f"{a['id']} - {a['nickname']}" for a in animals]
            self.animal_combo.configure(values=animal_values)
            if animal_values:
                self.animal_combo.set(animal_values[0])
        if staff_list:
            staff_values = [f"{s[0]} - {s[1]}" for s in staff_list]
            self.staff_combo.configure(values=staff_values)
            if staff_values:
                self.staff_combo.set(staff_values[0])

    def fill_form(self):
        if self.observation:
            self.date_of_inspection_var.set(str(self.observation['date_of_inspection']) if self.observation['date_of_inspection'] else "")
            self.general_condition_var.set(self.observation['general_condition'] or "")
            self.diagnosis_var.set(self.observation['diagnosis'] or "")
            self.notes_var.set(self.observation['notes'] or "")
            def load_combos():
                animals = self.db_manager.get_all_animals()
                staff_list = self.db_manager.get_staff_list()
                self.after(0, lambda: self.set_selected_values(animals, staff_list))
            threading.Thread(target=load_combos, daemon=True).start()

    def set_selected_values(self, animals, staff_list):
        if animals:
            for animal in animals:
                if animal['id'] == self.observation['animal_id']:
                    self.animal_var.set(f"{animal['id']} - {animal['nickname']}")
                    break
        if staff_list:
            for staff in staff_list:
                if staff[0] == self.observation['staff_id']:
                    self.staff_var.set(f"{staff[0]} - {staff[1]}")
                    break

    def save(self):
        def save_data():
            try:
                date_of_inspection = self.date_of_inspection_var.get().strip()
                general_condition = self.general_condition_var.get().strip()
                diagnosis = self.diagnosis_var.get().strip()
                notes = self.notes_var.get().strip()
                animal_str = self.animal_var.get()
                staff_str = self.staff_var.get()
                if not date_of_inspection:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Поле 'Дата осмотра' обязательно для заполнения"))
                    return
                datetime.strptime(date_of_inspection, '%Y-%m-%d')  # Validate
                animal_id = int(animal_str.split(' - ')[0]) if animal_str else None
                staff_id = int(staff_str.split(' - ')[0]) if staff_str else None
                if animal_id is None or staff_id is None:
                    self.after(0, lambda: messagebox.showerror("Ошибка", "Выберите животное и сотрудника"))
                    return
                health_data = (general_condition, diagnosis, date_of_inspection, notes, animal_id)
                if self.observation:
                    success = self.db_manager.update_health_observation(self.observation['id'], health_data, staff_id)
                    message = "Наблюдение обновлено"
                else:
                    success = self.db_manager.add_health_observation(health_data, staff_id)
                    message = "Наблюдение добавлено"
                self.after(0, lambda: self.handle_save_result(success, message))
            except ValueError:
                self.after(0, lambda: messagebox.showerror("Ошибка", "Неверный формат даты"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}"))
        threading.Thread(target=save_data, daemon=True).start()

    def handle_save_result(self, success, message):
        if success is not None:
            if success == 0:
                messagebox.showwarning("Предупреждение", "Запись не изменена (возможно, не найдена или данные идентичны)")
            else:
                messagebox.showinfo("Успех", message)
                self.result = True
                self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить данные")

    def cancel(self):
        self.destroy()


class WildlifeReserveSystem(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.title("Система учета дикой природы заповедника")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.db_manager = DatabaseManager()
        self.create_widgets()
        self.setup_database()

    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.add("Главная")
        self.tabview.add("Дашборд")
        self.tabview.add("Управление данными")
        self.dashboard_frame = DashboardFrame(self.tabview.tab("Дашборд"), self.db_manager, self)
        self.dashboard_frame.pack(fill="both", expand=True)
        self.data_frame = DataManagementFrame(self.tabview.tab("Управление данными"), self.db_manager, self)
        self.data_frame.pack(fill="both", expand=True)
        self.create_home_content()

    def create_home_content(self):
        home_frame = self.tabview.tab("Главная")
        center_frame = ctk.CTkFrame(home_frame, fg_color="transparent")
        center_frame.pack(expand=True)
        title_label = ctk.CTkLabel(
            center_frame,
            text="Система учета дикой природы заповедника",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=20)
        status_text = "Подключение к базе данных..." if not self.db_manager.is_connected else "Подключено к базе данных"
        status_color = "orange" if not self.db_manager.is_connected else "green"
        self.status_label = ctk.CTkLabel(
            center_frame,
            text=status_text,
            text_color=status_color,
            font=("Arial", 12, "bold")
        )
        self.status_label.pack(pady=5)
        info_text = """Добро пожаловать в систему управления заповедником!
Для работы с системой используйте вкладки навигации:
• Дашборд - просмотр статистики и аналитики
• Управление данными - управление записями базы данных
Доступные функции:
- Управление животными и их местами обитания
- Контроль кормлений и состояния здоровья
- Управление сотрудниками и видами животных
- Аналитика и отчетность
- Экспорт данных в Excel и PDF"""
        info_label = ctk.CTkLabel(
            center_frame,
            text=info_text,
            font=("Arial", 14),
            justify="left"
        )
        info_label.pack(pady=20, padx=20)
        
        #фрейм для кнопок экспорта
        btns_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        btns_frame.pack(pady=20)
        
        #кнопка экспорта excel на главной странице
        ctk.CTkButton(
            btns_frame,
            text="Экспорт полного отчета в Excel",
            command=self.export_to_excel,
            width=250,
            height=35,
            font=("Arial", 12)
        ).pack(pady=5)
        
        #кнопки pdf отчётов
        ctk.CTkButton(
            btns_frame,
            text="PDF: Статистический отчёт",
            command=self.export_pdf_stat,
            width=250,
            height=35,
            font=("Arial", 12)
        ).pack(pady=5)
        
        ctk.CTkButton(
            btns_frame,
            text="PDF: Детальный отчёт",
            command=self.export_pdf_detail,
            width=250,
            height=35,
            font=("Arial", 12)
        ).pack(pady=5)

    def setup_database(self):
        def connect_db():
            #подключение
            async def connect_coroutine():
                return await self.db_manager.connect()
            success = self.db_manager.run_async(connect_coroutine())
            if success:
                self.after(0, self.update_connection_status)
        thread = threading.Thread(target=connect_db)
        thread.daemon = True
        thread.start()

    def update_connection_status(self):
        if hasattr(self, 'status_label'):
            self.status_label.configure(
                text="Подключено к базе данных",
                text_color="green"
            )

    def on_closing(self):
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.db_manager.close_connection()
            self.destroy()

    def export_to_excel(self):
        """Экспорт данных в Excel"""
        try:
            exporter = ExcelExporter(self.db_manager)
            filename = exporter.export_complete_report()
            if filename:
                messagebox.showinfo("Успех", f"Отчет успешно создан:\n{filename}")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать отчет")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте: {str(e)}\n{traceback.format_exc()}")

    def export_pdf_stat(self):
        """Экспорт статистического PDF-отчёта"""
        try:
            exporter = PDFExporter(self.db_manager)
            filename = exporter.export_statistical_report()
            if filename:
                messagebox.showinfo("Успех", f"Статистический PDF-отчёт создан:\n{filename}")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать PDF-отчёт")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании PDF:\n{str(e)}\n{traceback.format_exc()}")

    def export_pdf_detail(self):
        """Экспорт детального PDF-отчёта"""
        try:
            exporter = PDFExporter(self.db_manager)
            filename = exporter.export_detailed_report()
            if filename:
                messagebox.showinfo("Успех", f"Детальный PDF-отчёт создан:\n{filename}")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать PDF-отчёт")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании PDF:\n{str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    app = WildlifeReserveSystem()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
