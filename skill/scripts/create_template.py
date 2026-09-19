#!/usr/bin/env python3
"""Create the standard workbook template bundled with this Skill."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

OUT = Path(__file__).resolve().parents[1] / "assets" / "案件材料汇总模板.xlsx"
NAVY, TEAL, PALE, BLUE = "17324D", "167D86", "E8F3F4", "0000FF"
SHEETS = {
    "案件链路总览": ["项目", "内容", "依据/事件编号"],
    "文件清单": ["材料编号", "原始文件名", "原始路径", "标准文件名", "归档路径", "扩展名", "SHA-256", "解析状态", "重复组", "版本组", "备注"],
    "主体信息": ["主体编号", "标准名称", "主体类型", "别名", "案件角色", "强标识摘要", "来源材料编号", "原文定位", "置信状态", "待核事项"],
    "音视频核对": ["材料编号", "媒体文件", "逐字稿文件", "匹配状态", "是否纳入文本分析", "备注"],
    "时间轴": ["事件编号", "事件发生时间", "材料形成时间", "时间精度", "地点/渠道", "涉及主体", "事件描述", "主要材料编号", "全部关联材料编号", "原文定位", "归档路径", "记载性质", "冲突/待核"],
    "冲突与待核": ["问题编号", "问题", "涉及事件", "涉及材料", "可能影响", "建议补充/核验", "状态"],
}


def main() -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for index, (name, headers) in enumerate(SHEETS.items(), 1):
        ws = wb.create_sheet(name)
        ws["A1"] = name
        ws["A1"].font = Font(name="Arial", size=18, bold=True, color="FFFFFF")
        ws["A1"].fill = PatternFill("solid", fgColor=NAVY)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        ws["A2"] = "蓝色示例行仅说明填写格式，生成正式结果时删除；不确定内容填写“待核”，不得猜测。"
        ws["A2"].font = Font(name="Arial", size=10, color=BLUE)
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
        for col, header in enumerate(headers, 1):
            cell = ws.cell(3, col, header)
            cell.font = Font(name="Arial", bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor=TEAL)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        example = ["示例（生成时删除）"] + ["示例值"] * (len(headers) - 1)
        if name == "案件链路总览":
            example = ["起因", "材料显示双方于2025年3月形成合同关系。", "EVT-001；MAT-0001"]
        elif name == "时间轴":
            example = ["EVT-001", "2025-03-03 10:18", "2025-03-03", "分钟", "网上银行", "甲公司、乙公司", "甲公司支付首付款。", "MAT-0001", "MAT-0001；MAT-0002", "回单第1页", "002 基础资料/250303-首付款回单.pdf", "客观系统记录", "核验原始回单"]
        for col, value in enumerate(example, 1):
            cell = ws.cell(4, col, value)
            cell.font = Font(name="Arial", color=BLUE)
            cell.fill = PatternFill("solid", fgColor=PALE)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        ws.freeze_panes = "A4"
        ws.auto_filter.ref = f"A3:{ws.cell(3, len(headers)).coordinate}"
        ws.row_dimensions[1].height = 28
        ws.row_dimensions[3].height = 32
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[ws.cell(3, col).column_letter].width = 18 if col > 1 else 16
        ws.sheet_view.showGridLines = False
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
