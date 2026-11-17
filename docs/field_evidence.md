# EPSA-MRS v1 —— 小目标检测评测口径最小报告规范（可机检版）

**日期**：2026-09-19　**机检**：`experiments/scripts/epsa_check.py`（退出码即判据；`--selftest` 跑负对照）
**声明样例（本项目自己吃的药）**：`experiments/results/e7_check/declaration_epsa_own_{visdrone,aitod}.json`
（每项 PASS/WARN/FAIL 的实时读数由 `epsa_check.py --json <件>` 落在同名 `_check.json`，本文件不抄计数）
**定位**：D7 的交付物不是"又一个 mAP"，是**让别人的 mAP 可复算**。只能靠人读的清单等于没有清单。

> 每条"为何必需"都必须是**本项目的实测**，不引教科书常识——否则读者会问"你为什么要我为这个"。
> 下表"证据"列的每个数都能从登记的产物文件重算出来。

| # | 必填 | 机检判据 | 为何必需（本项目实测） |
|---|---|---|---|
| **M1** | `engine{name,version,commit_or_release}` | 三项非空 | 同一批框、同为"标准 COCO 口径"，自研引擎与 ultralytics 自带 val 差 **2.7e-3 / 1.4e-3**（`g1_refcheck.json`、`e36_interp_tail.json`）——不点名实现就复算不出同一个数 |
| **M2** | `max_det{eval_value,unit,export_value}` | 三项齐 + 饱和检测 | `unit` 两义（每图 vs 每图每类）在 AI-TOD 上值 **0.0093**（md=10）；且 `export_value` 决定可测窗口：资产每图上限 300（框架默认 `max_det: 300`）⇒ **md≥300 时 `per_img` 与 `per_img_cat` 与不截断三档 AP 逐位相同**（0.162775/0.169111）。只报数值会造出"单位无差异"的假发现（本项目 P0-6 就这么错过一次）。**09-20 新证（E9）**：参考实现 pycocotools 的 **AP 行用硬编码字面量 `maxDets=100`**（`cocoeval.py:427,460`），AR 行才从 `params.maxDets[0/1/2]` 取 ⇒ "你报的 md=100 到底是参数还是实现的写死值"是必须问的；且三家按 COCO 约定的实现（自研/pycocotools/faster-coco-eval 1.8.0）在同一批框上 AP 差 **≤2.7e-7**（AP_S ≤2.1e-5、fce 与 pyc 18 格逐位相同）⇒ **约定内的实现噪声可忽略，本清单要防的是约定与管线，不是"谁的四舍五入不同"**（`e9_xframework_results.md`） |
| **M2c** | `max_det{export_cap_share, cap_sensitivity}` | 必须申报"导出上限有没有 bind"；share>0 时还须给跨 cap 敏感性，或把结论显式限制在 md≤cap 内 | **协议与资产不可组合**（自家 D5-c 实测）：协议一字不改（`md=100/每图每类`＝COCO 默认），只把导出侧每图上限 300→1000，AP 就动 **+0.002098/+0.001634（VisDrone B1/E1_off）、+0.000424/+0.000642（AI-TOD）**。自家 share＝0.894(V)/0.305(A) ⇒ 该维不是学术洁癖：`maxDet=100` 这个数的含义同时由一个没人申报的量决定（`d5c_budget_results.md`） |
| **M3** | `protocol{iou_thrs[],matcher}` | 阈值**展开成列表** + 匹配器具名 | 写 `"0.5:0.95"` 无法判定是 10 点还是 101 点扫描；匹配器语义与 maxDet 在真实框架里**纠缠**（本项目把两者解耦实测：匹配器净效应仅 −1e-4，`e35_results`） |
| **M4** | `ap_integration{interp,recall_beyond_max}` | 两项齐 | 召回超出曲线最大召回时**赋 0 还是取末值**：小目标上差 **0.05** 量级（101 点里约 70 点受影响，`epsa_ap.py` 注释即踩坑记录）；末点哨兵另值 2.7e-3 |
| **M5** | `aggregation{mode,gt_per_class}` | 模式具名 + 每类 GT 数 | macro 与 gt_weighted 使**同一模型** AP 挪 **+0.0736(VisDrone)/+0.0656(AI-TOD)**，Holm p≤0.009（`boot_*_1000_both.json`）；不给每类 GT 数就无法判断 macro 被几个稀有类绑架（VisDrone 最小类 530，AI-TOD 有 GT<20 的类 ⇒ 检查器会亮 M5b） |
| **M6** | `area_tiers{definition,thresholds,reported_layer}` | 定义具名 + 阈值给出 | "small" 在绝对像素与相对面积两种定义下不是同一集合：同层内 \|Δ\| 均值 **0.0398(VisDrone)/0.0093(AI-TOD)**（`derived_v2.txt`）。本项目一度把 D4 当"高危维度"，实为**同名不同测** |
| **M6b** | `area_tiers{size_measure,boundary_rule,filter_scope}`（所报层≠all 时必填） | 三项具名，缺一即 FAIL | **本清单里幅度最大的一条**：按已发表基准原文复原 AI-TOD 层指标（arXiv:2206.13996 §3.2 只写 "absolute size [2,8]/[8,16]/[16,32]/[32,64]"），同一批预测框在原文未定义的三轴上 **APvt 可摆 0.082、APs 0.071~0.083、APt 0.027~0.031**（`e6_tier_ambiguity.md`，13 种合法读法）。其中最大单因素不是"用哪种边长度量"，而是**分层要不要连检测框一起筛**（0.0636→0.0146）。相邻区间在 8/16/32 上按字面写法**重叠**（不是划分），√面积口径下恰落在边界上的 GT 有 819/507/16 个 |
| **M7** | `predictions{conf_threshold,source,source_detail}` | 三项齐 | **09-20 补测后本条从"叙述"升级为"实测"**：同权重、同 imgsz=640、同 `max_det=300`、同 NMS 默认，**只把推理路径从 `val` 换成 `predict`**，REF 协议下 AP 动 **+0.00097／+0.00013／−0.00077（B1，3 seed）而 −0.01280／−0.01169／−0.01100（E1_off，3 seed 同号）** ⇒ 该维**模型相关，禁写统一倍数**；照 predict 默认 conf=0.25 做事则 −0.0288／−0.0291（naive 臂，另一臂）。机制读数是候选数：E1_off 每图顶到 300 的图从 1401 降到 1117（少 3.2 万框）。出处 `m7_pipeline_gap_results.md` + `m7_pipeline_gap.json`（**此前该 0.012 被三份文档当依据引用而无产物**，见 §二.5 留痕）；导出侧 conf 默认 0.001、NMS IoU 0.7、imgsz 640 都来自 `default.yaml`，不写明就等于换被测量 |
| **M8** | `tie_break.rule` | ∈ 具名规则（`"unspecified"` **不算**具名） | 同分极多：实测每条 (类,阈值) 曲线 **35.31%** 的检测与其后继同分（`fcheck_fastpath.json`，400 图子集）⇒ 破序规则不同，逐位复现不可能，自助区间也会随之变 |
| **M9** | `join{n_gt_images,n_joined_images,zero_det_counted}` | 两数相等 + 零检出计入 | 联接键 int 化掉样：AI-TOD 少 41 图/971 GT ⇒ REF AP 虚高 **+0.0028(B1)/+0.0034(E1_off)**，VisDrone 侧严格为 0（`join_effect.json`）。**两侧同源的对照检查看不见这个错**（G1 当时全绿） |
| **M10** | `uncertainty{resample_unit,cluster_definition,B}`；簇预算另须 `n_img,n_clusters` | 单位具名；若 cluster 则必须给簇定义；**平均每簇 <2 图 ⇒ 不得称"两套独立预算"**（M10c） | 逐图自助 vs 逐视频段自助：SE 放大 **1.08–1.97 倍**，VisDrone 上唯一显著的口径效应由 p=0.009 变 p=0.153（`e5_results.md` §五）。默认单元选错会把噪声说成结论。反向的坑同样真实：VisDrone 1610 图/61 簇（26.4 图/簇）是真聚类，而 **AI-TOD 2804 图只聚成 2194 簇（1.28 图/簇）** ⇒ 该域"图像 CI 与簇 CI 都覆盖 0"其实是同一句话说了两遍，M10c 对此打 WARN |
| **M11** | `claims[].kind` | ∈ {estimator_switch, measurand_switch, stress_test, fault_injection} | 混池造出假排序：本项目"第二高危维度"实为跨层混池所得（S 2.33 → 同层重算 **0.19**） |
| **M12** | 比值型 `claims`：`{numerator,denominator,ci,denominator_excludes_zero}` | 必须有 CI 且分母显著 | 本项目据此**废止了自己的一条头条**："maxDet 效应＝方法增益的 3.7 倍"——分母 Δ̂_REF=+0.0058 的 CI 覆盖 0（Holm p=0.72），逐轮比值有 **9.4%** 的重采样里分母不为正 ⇒ 倍数无可用区间（`e5_results` §〇.1） |
| **M13** | `seed_dispersion{n_seeds,groups,sd_pooled_compliant,ci95_sd_pooled,n_cells,single_seed_groups}` | 多 seed 必须报**seed 间 sd 及其区间**；只写"跑了 3 个 seed"不算申报（缺 sd ⇒ FAIL）；确实只有单 seed ⇒ WARN，但据此写任何 1e-3 级差值都无资格 | 本项目的"可分辨对"判据 `MDE = 4.30·paired_sd/√3` 一直建立在一个**从未单独报告**的量上。补测：合规臂上换个训练 seed，单个 AP 的摆动 VisDrone 合并 sd **0.001215**（48 格/df=96，95% 区间 [0.001065, 0.001415]）、AI-TOD **0.001715**（[0.001503, 0.001997]）；n=3 ⇒ **单格 sd 的区间宽 12 倍**（乘子 [0.520, 6.286]）⇒ 只许用合并值或逐臂值。而且 sd **不是常数**：逐臂跨 5.8×（VisDrone）／16.3×（AI-TOD）⇒ "小于噪声"这类判断必须点名是哪一臂的噪声（`seed_variance_results.md`） |

## 一、这套清单怎么长出来的（不是拍脑袋）

M1/M4/M8 来自"同一批框换实现/换约定"的实测；M2/M5/M6 来自 34 变体扫描的逐维拆解；
M2c 来自"同一协议换一份导出件"（D5-c 的 C-1）；M9 来自一个**自家引擎的 bug**；
M10 来自簇结构检验（M10c 来自发现 AI-TOD 根本没有簇）；M12 来自把自家头条送去自助；M6b 来自 E6 用一手文献原文复原层指标——它是唯一一条**不是**从我们自己的扫描里长出来的；
M13 来自 09-20 把"可分辨对"判据里那个从未单独报告的分母（seed 间 sd）单独量一遍（`epsa_seed_variance.py`）——量出来才发现它逐臂跨 5.8×／16.3×，不是常数。
所以它的可信度取决于两件事：**每条都能变红**（`--selftest` 用一批故意写坏的夹具逐条点亮，
每个夹具必须恰好点亮它该点的那一项；09-20 午后为 23 个——这条契约在加 M2c 的当场就抓到
M2/M2b 两个旧夹具连带点亮新项，于是 M2c 加了"三件套不齐时不重复点亮"的守卫），
以及**自家管线也过一遍**
（09-20 午后加 M13 后再跑：两域各 19 项，VisDrone 18 PASS / 1 WARN / 0 FAIL、
AI-TOD 17 PASS / 2 WARN / 0 FAIL，M13 在两侧都由 `seed_variance.json` 现读到 sd ⇒ PASS。
逐项读数见 `results/e7_check/declaration_epsa_own_*_check.json`。
WARN 分别是被 M12 抓住的自家旧头条与被 M10c 抓住的"AI-TOD 簇预算≈逐图预算"——
检查器会打自己人，说明它不是摆设）。

## 二、v1 的已知不足（写清楚，别留给审稿人发现）

1. **M2 的饱和检测只到 WARN**：它能识别"这一档构造上等于不截断"，但不能识别"这一档在报告者的数据上是不是也饱和"——那需要 `export_value` 与候选数分布同时给，v2 再加 `n_det_per_image_p50/p90`。
2. **M3 的 `iou_thrs` 只查形状不查语义**：10 点等距与 101 点等距在数值上都是合法列表，语义却是两件事。
3. **M8 的具名规则表是本项目视角**：COCO 官方实现用"gt 侧优先 + 面积序"，其具名句柄尚未纳入枚举——对不属于本框架的投稿会假红。
4. **没有"必须报告每类 AP"这一项**：因为本项目尚未量化稀有类 AP 的不稳定性（M5b 只给了个告警），等它可量化再进清单，不占空位。
5. **M7 的量级依据已落实（09-20 夜补测，此处留痕防再转录）**：原写法"val 与 predict 两条路径自算 AP 可差 0.012"
   取自本立项件 §陷阱A 的叙述，**当时全仓查无产物**（本目录无 predict 路径评测件、comb2 记录里亦搜不到该值），
   且该数被三份文档当依据引用（本件、`comb2_smalltarget/paper/eval_protocol/README.md:15`、
   `comb2c_axis_ovd_calibration_evidence.md:27`）。补测件 `epsa_e7_m7.py` 出来后：
   **0.012 被复现且定位到具体模型**——strict 臂 E1_off −0.0128/−0.0117/−0.0110（3 seed 同号）、
   B1 仅 ±0.001 内且符号不稳 ⇒ **不得写"predict 路径低 0.012"这类统一倍数**；
   另有 naive 臂（predict 默认 conf=0.25）−0.029，与 strict 臂不可混报。
   ⚠️ 未判定项照实保留：换成 predict 路径后**模型差的 seed 分散度变大**
   （VisDrone 该对：val 路径 3-seed sd 0.000937 → predict 路径 0.002294；AI-TOD 0.000547 → 0.002743），
   于是 val 路径下可分辨的 VisDrone 模型对在 predict 路径下**变得不可分辨**（名义符号相反、但 |gap| < 该路自己的 MDE）
   ⇒ 只许写"nominal 翻转"，不得写"翻掉可分辨对"（判据与 C-8 同一把尺）；
   **两个 sd 之比不得写成倍数**（分母 sd 也是 n=3 的量、其 95% 区间本身宽约 12 倍，MRS M12 同源）。

## 三、与规划判据的对账（09-20 二次改判）

`experiment_plan.md` §七 给 E7 的原判据是"按 MRS 报告后 `P_sig` 相对基线显著下降"——
`comb2c_assessment.md` P0-5 判其结构性不可满足。**该处的理由已过时**：它写"P_sig 构造恒为 0"，
而 09-20 分母对账（`epsa_derived_reconcile.py`）改判为 `P_sig` **可测**（基线件两侧名义翻转为 0 时才恒 0；
现行 34 臂件 AI-TOD 有 1 次名义翻转，两套 B=1000 自助读 0）。判据本身仍然不可满足，但**不能再说它是恒真统计量**。

评估 P0-5 建议的两种可检验形式，本轮**逐条实测/论证后均判为不可用**（`e7_decisive_criterion_plan.md`）：
① "AP 差被声明不确定度覆盖 ≥95%"——同一族判据在**模型对间距**与 **AP 水平**两个被测量上给出相反结论
（间距族：绝大多数换口径读数仍落在盲报区间内；水平族：几乎全部落在区间外，见 `e7_decisive_criterion_results.md`）
⇒ "选哪个被测量"就是把判据写成想要的结论；且这两个读数都**不是**频率学派的覆盖率，正文不得用"覆盖率"一词。
② "区间宽度相对基线下降 ≥X%"——MRS 的作用是把此前未声明的不确定度来源纳入声明，纳进来只会让区间**变宽**，方向相反。

**现行判据 E7-D**（工具 `epsa_e7_decide.py`，退出码即裁决）：每条必报项必须绑定依据——
**量级依据**（产物里可机读的实测幅度，> 浮点噪声地板）或**可比性依据**（不报即不可逐位复现/跨论文不可比，且须绑产物指针）；
两类皆无即判据红。幅度**只报不判**，不设阈值。当前读数：**15/15 全部绑定，rc=0**
（量级 11、仅可比性 4；09-20 夜 M7 补测前是 14/15 且 rc=4，缺口即 §二.5 那条）。

另：原判据①"12 项在自家声明上机检通过"仍保留，但它只验申报齐全性（`epsa_check`），
不验条目本身有无依据（E7-D），两者不同层、不可互替。

## 四、与《Metrics reloaded》的对应关系（09-21 划界，动笔前必读）

逐条对照件：`metrics_reloaded_demarcation.md`（原文＝`arXiv:2206.01653v8`，209 页 / 1,100,989 字符，
扫描器 `research_plan/tools/metrics_reloaded_keyword_scan.py` rc=0）。三句话结论：

1. **一句话划界**：他们治"选错指标"（五类建议 implementation/aggregation/ranking/reporting/interpretation），
   我们治"同一个指标算不出同一个数"（申报字段＋可机检）。对"实现影响数值"这一条，他们开的药是
   *"Use reference implementations provided at …/MONAI/MetricsReloaded"*，我们开的是"把你用的实现写出来"。
2. **15 个键里只有 5 条净无重叠**：M2/M2c（maxDet 与导出上限是否 bind）、M7（`val`/`predict` 推理路径与 conf）、
   M8（同分破序）、M9（联接键掉样）、M11（主张类型标签）——全文词边界扫描为 0 命中。
   **其余 10 条的问题都被 ED Tab.1 点名过**（尤其 M13 的"Non-determinism → consider multiple test set runs"、
   M10 的"Respect the hierarchical data structure when aggregating metrics"、M12 的
   "Choose the number of decimal places such that they reflect … uncertainties"），
   差量一律在"要求多跑/尊重层级"与"**必须申报离散度并机检**"之间 ⇒ 措辞不得写成首次发现。
3. **小目标那两处必须引**：他们建议 size stratification（Note 2.4）＋对小目标"lower object detection
   localization threshold"（DG8.3）——D7 谈小目标不引这两处会被判没读文献。

### 计数口径（本仓三份文件曾各写各的，此处钉死）

| 数 | 含义 | 出处 |
|---|---|---|
| **13** | 编号法 M1–M13 | 审计件旧写法"13 条逐条划界"（已就地补注） |
| **15** | 申报键（M1、M2、**M2c**、M3、M4、M5、M6、**M6b**、M7、M8、M9、M10、M11、M12、M13） | 本件 §〇 表 |
| **19** | 机检项＝15 键＋四个检查子项（M2b、M5b、M9b、M9c、M10c）中实际触发的部分 | `results/e7_check/declaration_epsa_own_{visdrone,aitod}_check.json` 实测各 19 行 |

⚠️ **19 里没有 M6b，不是漏项**：`epsa_check.py:179` 的触发条件是 `reported_layer ∉ {None,"all"}`，
而自家声明现为 `reported_layer:"all"`（同一条 JSON 实测）⇒ 报分层指标时才点亮，属条件项。
另 E7-D 说的"15/15 全部绑定"用的就是 **15 键** 这把尺，与本表一致。
⚠️ 09-21 起这句话有闸门兜着：`epsa_e7_decide.py` 会**现读本表的行首键**与自己的依据登记表做双向差集
（文档有而登记表没有＝漏绑；登记表有而文档不再申报＝陈旧；同键两次＝表格写坏），不一致即 rc=1，
`--selftest` 的 N5/N6 各证一次可红与正对照。**在此之前**它只是两处各写各的数字，加一条 M14 不会让任何检查变红。
