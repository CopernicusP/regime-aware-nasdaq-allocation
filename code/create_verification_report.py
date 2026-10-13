"""Render the release assessment as a paginated PDF (ReportLab 4.4.9)."""
from pathlib import Path
import re,html,matplotlib
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
def main():
    font=Path(matplotlib.get_data_path())/'fonts/ttf'
    for name,file in [('ReportSans','DejaVuSans.ttf'),('ReportSans-Bold','DejaVuSans-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(font/file)))
    pdfmetrics.registerFontFamily('ReportSans',normal='ReportSans',bold='ReportSans-Bold',italic='ReportSans',boldItalic='ReportSans-Bold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Body',fontName='ReportSans',fontSize=10.3,leading=14.3,spaceAfter=8,textColor=HexColor('#202B33')))
    styles.add(ParagraphStyle(name='Title2',fontName='ReportSans-Bold',fontSize=24,leading=27,spaceAfter=17,textColor=HexColor('#163C52')))
    styles.add(ParagraphStyle(name='Section2',fontName='ReportSans-Bold',fontSize=13.5,leading=17,spaceBefore=15,spaceAfter=7,keepWithNext=True,textColor=HexColor('#163C52')))
    def markup(s):
        s=html.escape(s)
        return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s).replace('`','')
    paragraphs=(ROOT/'docs/VERIFICATION_REPORT.md').read_text().split('\n\n');story=[]
    for p in paragraphs:
        if p.startswith('# '):story.append(Paragraph(markup(p[2:]),styles['Title2']))
        elif p.startswith('## '):story.append(Paragraph(markup(p[3:]),styles['Section2']))
        else:story.append(Paragraph(markup(p).replace('  \n','<br/>').replace('\n',' '),styles['Body']))
    dest=ROOT/'docs/Verification_Report.pdf'
    def page(c,d):
        c.saveState();c.setStrokeColor(HexColor('#B8C8D0'));c.setLineWidth(.4);c.line(48, forty:=40,564,forty)
        c.setFont('ReportSans',8);c.setFillColor(HexColor('#516573'));c.drawString(48,27,'Yudian Pan  |  Research verification  |  13 October 2026')
        c.drawRightString(564,27,str(d.page));c.restoreState()
    doc=SimpleDocTemplate(str(dest),pagesize=(612,792),rightMargin=48,leftMargin=48,topMargin=45,bottomMargin=54,title='Research Verification and Release Assessment',author='Yudian Pan',allowSplitting=1)
    doc.build(story,onFirstPage=page,onLaterPages=page)
    print(dest)
if __name__=='__main__':main()
