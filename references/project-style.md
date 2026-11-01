# 项目风格与模块接口

来源项目：`XinyuYuan-latest`。以下为创建 skill 时从 `main.tex`、`contents/paper1.tex` 和现有成品观察到的风格；执行时重新读取实际文件，不把快照当成不可变配置。

## 文件和模板边界

```text
main.tex                  唯一主文档，使用 include 接入论文
contents/
  paper1.tex              一篇论文的全部正文
  paper2.tex              后续论文
figures/
  paper1/                 该论文的所有图
  paper2/
build/                    编译产物和临时预览
```

`main.tex` 使用 16:9 `ctexbeamer`、SJTUBeamer 的 `en,maxplus,light,infolines` 主题、Times New Roman 和 Noto CJK 字体。白底、深红导航/标题、橙色 `alertblock`、学校徽标和页脚共同定义视觉风格；复用这些已有设置，不在论文模块中重新设颜色、主题、字体或页面大小。

主文件已有 `\AtBeginSection` 节页和 `\AtBeginSubsection` 目录页。新增 section/subsection 会自动产生过渡页，正文不重复生成封面、目录、章节页或 Thank You 页。预估讲述长度时将这些自动页面计入。

只允许为接入论文增加所需 include。主文件原有元信息、`\graphicspath`、包、目录钩子、`\maketitle`、`\makebottom`、所有其他 include 保持原样。使用已有包提供的环境，不为某张图引入全局依赖。

## 单篇文件的开头

```latex
% Paper: verified title and source URL/identifier
% Source version: checked version/date
\sectioninfo{已核实的作者\\已核实的发表渠道与日期}
\section[简短中文标题]{Original English Paper Title}

\subsection{问题定义和研究背景}
```

作者信息顺序与论文一致。长标题用 section 的可选短标题保护页眉；subsection 名称短而明确，避免把完整公式塞进导航标签。

## 叙事节奏

现有论文的有效特征：先提出研究问题及贡献，用 overview 建立地图，再在理论转向处提出整页问题，依次解释理论连接、算法及数值证据，最后用关系链总结。

新论文应复用这种“问题驱动”的节奏，不复刻原论文的具体主题，也不机械地把每个论文小节变成 subsection。每个 subsection 应解决一个讲述任务；每个关键问题都应有后续回答。结尾总结要回到开场问题，区分论文已证明的部分和进一步研究方向。

## 局部排版决策

- 普通正文优先默认字号或 `\small`。图注可用 `\footnotesize`；不要沿袭旧页面中个别 `\tiny` 图注和负间距堆叠。
- `block` 承载模型、定义和正式条件，`alertblock` 承载核心结果，`\alert` 强调一句结论。避免整页都高亮。
- 公式用 `aligned`/`align*` 按逻辑断行。单页放不下推导时，将相同目标分成连续页面，保留必要符号提示。
- 双栏用 `\begin{columns}[T,onlytextwidth]`，列宽总和略小于正文宽度，例如 `0.55\textwidth` 与 `0.42\textwidth`。狭窄列中的长公式移到全宽区域。
- 图常用 `width=\linewidth` 或同时设置宽高与 `keepaspectratio`。高度上限依页面剩余空间决定，不能把图标题、图注挤到页脚。
- 大字问题页保留原有页眉/页脚，用普通无标题 frame、`\centering`、`\LARGE\bfseries` 与一句小字提示。长问题允许自然换行，先缩短措辞，不靠整体缩放。
- 默认保持现有静态逐页讲述，不主动加入 overlay。用户明确要求交互揭示时按其要求处理。
- 新宏确有必要时使用 `paperX` 命名前缀且检查重名，避免修改已有宏或留下全局样式变化。图、公式和 frame 标签同样加 `paperX:` 前缀。

## 不移植的外部默认项

数学严谨性参考了 [math-beamer-slides-skill](https://github.com/YixuanYang00/math-beamer-slides-skill) 的思想，重点是声明条件、证明路线、符号依赖和验证闭环。本 skill 的模板、语言、目录和图片策略以本项目与用户要求为准；无需移植其独立模板、英文默认、背景位图配额或额外的 Publications/manifest 页面。
