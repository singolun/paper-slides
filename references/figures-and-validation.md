# 图片组织、编译和验收

## 每篇论文的图片目录

新图只写入 `figures/paperX/`，按语义命名，例如 `method-overview.pdf`、`sampling-trajectories.pdf`、`ablation-step-size.pdf`。一篇论文的多个实验可以在目录内再细分，但不把它们散落在根目录，也不使用其他 paper 的编号。正文使用明确的后缀：

```latex
\includegraphics[width=\linewidth]{paper2/method-overview.pdf}
```

在正文的图前注释记录来源链接/文件、原文 Figure/Table 编号、PDF 页码（与印刷页码有差别时说明）、裁切范围或生成方式。原始论文不必另存为“图”；PDF 原文的副本、下载缓存放临时目录或用户指定的资料位置。

## 选择和提取图片

1. 优先使用原论文的矢量 PDF、作者正式发布的图文件，或从原论文 PDF 裁切图区域。PDF 图片尽量保持文字与曲线为矢量，不先截图再转 PDF。
2. 依据实际页面坐标选取范围，先渲染原页核对，再裁切。注意标题、轴标签、legend、颜色条、子图编号和公式标注；不要因为整页图看似很大就把小字误判为可读。
3. 重绘示意图时使用项目已有 TikZ 能力，或导出独立矢量 PDF 的绘图工具；数据图只使用真实数据。不能因为读不清原图就编造走势或估计表格数值。
4. 对原本就是照片、热图或栅格输出的内容，保留合适分辨率的 PNG/JPEG；注明栅格来源。改后缀或套一层 PDF 不提高分辨率。

可用 PyMuPDF 将源 PDF 区域嵌入新 PDF，通常能保留矢量对象。先确认当前运行时已提供它；需要时使用 Codex 的 workspace dependencies 定位已有运行时，不默认安装整套工具。

```python
import fitz

source = fitz.open("/tmp/source-paper.pdf")
page_index = 3  # zero-based；须按原文确认
clip = fitz.Rect(60, 100, 540, 350)  # PDF points；从实际页面测量
result = fitz.open()
page = result.new_page(width=clip.width, height=clip.height)
page.show_pdf_page(page.rect, source, page_index, clip=clip)
result.save("figures/paper2/method-overview.pdf")
```

这只是裁切 API 示例，坐标不能照抄。对旋转页等特殊情况，核对视觉位置和输出；渲染裁切结果再引用。

## 图文版面

一页图应有明确比较问题和一句结论。提供必要的实验设置、指标方向、基线、重复次数/误差定义，以原文实际报告为准；原文未报告就说明未报告。不要把多个图压缩成无法辨认的一页。

双栏适合“图 + 解释”和短公式；主公式较长时改全宽或独立下一页。裁切多余白边、拆 panel 或拆页优先于缩小字体。对论文表格可保留矢量裁切，或用已有 `booktabs` 重排真实数值并标来源。图注不能遮盖坐标或页脚。

## 编译现有多文件项目

入口是项目根目录的 `main.tex`。原项目已有 `latexmkrc`（XeLaTeX 模式）、Makefile 和 biblatex/biber 配置。不要更换编译器、改字体、写一个替代主模板，或对正文片段调用 standalone 编译器。

有可用 TeX 环境时，可以在项目根目录运行：

```bash
mkdir -p build/contents
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

正常的 latexmk 会按需处理 biber 和多遍交叉引用；若手动运行，遵循当前 biblatex 的 biber 后端，目录/导航变更后至少跑到第二遍且引用稳定。不要照搬使用 bibtex 的外部示例。项目 Makefile 另有最终 PDF 复制到根目录的约定；用户需要同步根目录成品时只在成功构建后复制本次 `build/main.pdf`。

当前普通图片无需 shell escape；只有已有工作流确实启用 minted/TikZ externalization 等并获授权时才启用。不要为了让构建通过改动配置。环境缺字体/包或旧代码有错时，保留源文件，报告具体依赖及是否阻碍本次验证。

输出目录必须含 `contents/`，否则 `\include` 写辅助文件可能失败。旧 `build/` 有其他测试残留时，将日志时间和本次命令结果对应起来；必要时使用 `build/paperX-check/contents/` 作为本次独立 outdir，仍编译真实 `main.tex`，不要清理用户全部构建目录。

## 验收顺序

1. **文件与模板**：运行 `project_guard.py check`，确认只改变目标模块、对应图片和必要的 include。基线发现其他修改时核对实际 diff，不自动覆盖用户并行修改。初次 guard 不通过不得宣称模板未变。
2. **数学**：依照数学参考逐行核对中心推导，对照源论文检查定理、公式、条件、实验结论与来源定位。程序扫描不能完成这一项。
3. **编译**：检查退出状态和本次 `.log`，修复本次引入的错误、缺图、未定义引用、重复标签。检查 `Overfull \\hbox`/`Overfull \\vbox` 的具体页面；原有警告与新警告分开报告。不要通过改模板来隐藏警告。
4. **视觉**：用 `pdftoppm` 等工具将本次 PDF 渲染为图片，确定新论文的页码范围，逐页看全页及必要局部。检查节目录、导航、标题、正文边界、页脚、图中文字与所有长公式；大字页是否完整、下一页是否回答问题。
5. **修正**：通过拆页、断行、精简重复表述、调整局部列宽或裁切图处理问题，重新构建并检查受影响页。关键推导和条件不因排版而丢失。

可以用工作区或 `/tmp/` 保存渲染图，不把 PNG 预览放进 `figures/paperX/` 当交付资产。编译通过、数学检查和视觉检查分别记录；不可把“脚本通过”等同于三者全部通过。若工具缺失则明确未完成项，保留可继续使用的源文件。
