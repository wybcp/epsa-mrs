#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPSA (comb2c) E7 —— `epsa_check`：按 EPSA-MRS v1 机检一份"评测口径声明"

用法：
  python epsa_check.py declaration.json            # 退出码 0 = 全绿
  python epsa_check.py --selftest                  # 夹具自测：好件全绿 + 每个坏件恰好点亮它该亮的项
  python epsa_check.py declaration.json --strict    # 把 WARN 也计入失败

为什么要有这个东西：D7 的产出不是"又一个 mAP"，而是**让别人的 mAP 可复算**。
一条只能靠人读的清单等于没有清单——本文件把每条要求编译成退出码。
自测里那些"故意写坏"的夹具是判据的一部分：**点不亮任何检查项的检查不算检查**。

每条判据后面注的 § 指 `00_task_progress/epsa_mrs_v1.md`，其"为何必需"全部由本项目的实测支撑
（E1/G1、E3.5、E3.6、E3-v2、E4-M、E5），不引用教科书常识。
"""
import os
import sys
import json
import copy
import argparse

INF = float("inf")


# ---------------------------------------------------------------- 工具
def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


_JOIN_CACHE = {}


def _join_effect():
    """读 `join_effect.json`（由 epsa_e7_join_effect.py 实测产出），把两个模型的虚高量取出来。

    取不到就返回 None ⇒ 消息里不带数，**绝不回退到手写常数**：
    这个检查器曾手抄过一个假数（+0.0116，实为 D4 层内最大 |Δ| 串位），
    所以现在的规则是"数从件里来，没件就没数"。
    """
    if "v" in _JOIN_CACHE:
        return _JOIN_CACHE["v"]
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     os.pardir, "results", "e7_check", "join_effect.json")
    v = None
    try:
        d = json.load(open(p, encoding="utf-8"))
        v = {k: ("%.4f" % round(abs(x["inflation"]), 4)) for k, x in d.items()
             if isinstance(x, dict) and x.get("inflation") is not None}
    except Exception:
        v = None
    _JOIN_CACHE["v"] = v
    return v


def _get(d, path, default=None):
    cur = d
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


class Report(object):
    def __init__(self):
        self.items = []

    def add(self, mid, title, ok, msg, level="FAIL"):
        """ok=True 记 PASS；否则按 level 记 FAIL / WARN。"""
        self.items.append({"id": mid, "title": title, "pass": bool(ok),
                           "level": ("PASS" if ok else level), "msg": msg})
        return ok

    def n_fail(self):
        return sum(1 for i in self.items if i["level"] == "FAIL")

    def n_warn(self):
        return sum(1 for i in self.items if i["level"] == "WARN")

    def failed_ids(self):
        return sorted(i["id"] for i in self.items if not i["pass"])


# ---------------------------------------------------------------- 11 条机检
def check_all(dec, rep=None):
    """按 MRS v1 检查一份声明；返回 Report。缺字段一律算不通过（缺东西正是要防的事）。"""
    rep = rep or Report()

    # M1 实现与版本
    eng = _get(dec, "engine") or {}
    rep.add("M1", "评测实现与版本",
            bool(eng.get("name")) and bool(eng.get("version")) and bool(eng.get("commit_or_release")),
            "engine{name,version,commit_or_release} 三项齐（同一批框换实现可差 2.7e-3，见 §M1）")

    # M2 maxDet 三件套：数值 + 语义单位 + 导出侧上限
    md = _get(dec, "max_det") or {}
    have = _num(md.get("eval_value")) and md.get("unit") in ("per_img_cat", "per_img") \
        and _num(md.get("export_value"))
    rep.add("M2", "maxDet 数值 + 语义单位 + 导出侧上限", have,
            "max_det{eval_value,unit,export_value} 三项齐；只给数值等于没给（两种单位差可达 0.02+）")
    if have:
        ev, xv = md["eval_value"], md["export_value"]
        sat = (ev == INF) or (xv != INF and ev >= xv)
        rep.add("M2b", "maxDet 档是否落在饱和点",
                not sat,
                "eval_value=%s ≥ export_value=%s ⇒ 该档构造上等于不截断，"
                "其'零效应'是探针退化不是发现（§M2，本项目 P0-6 的成因）" % (ev, xv),
                level="WARN")

    # M2c 导出侧上限是否 bind。动机是自家 D5-c 实测：**协议一字不改**
    # （md=100/每图每类＝REF），只把导出侧每图上限从 300 抬到 1000，
    # AP 就动 +0.0004~+0.0021 ⇒ "maxDet=100" 这个数的含义同时由一个没人申报的量决定。
    share = md.get("export_cap_share")
    if not have:
        pass                       # 三件套都没申报，红字归 M2，不重复点亮 M2c
    elif not _num(share):
        rep.add("M2c", "导出侧上限是否 bind", False,
                "缺 max_det.export_cap_share（候选数顶到导出上限的图占比）；"
                "share>0 时每一个 per_img_cat 档的数值都被导出上限二次截断（§M2c）",
                level="WARN")
    elif share > 0 and md.get("cap_sensitivity") is None:
        rep.add("M2c", "导出侧上限是否 bind", False,
                "share=%.3f>0 但未给 cap_sensitivity（抬高导出上限引起的 AP 移动）⇒ "
                "要么实测该移动，要么将全部结论显式限制在 md ≤ 导出上限内" % share,
                level="WARN")
    else:
        rep.add("M2c", "导出侧上限是否 bind", True,
                "share=%.3f ｜ 跨 cap 敏感性 %s（§M2c）"
                % (share, "未 bind 无需给" if share == 0 else md.get("cap_sensitivity")))

    # M3 IoU 阈值集合 + 匹配器语义
    pr = _get(dec, "protocol") or {}
    thrs = pr.get("iou_thrs")
    ok3 = isinstance(thrs, list) and len(thrs) >= 1 and all(_num(t) for t in thrs) \
        and pr.get("matcher") in ("greedy_score", "greedy_iou", "hungarian", "ultralytics_batch")
    rep.add("M3", "IoU 阈值集合（列全）+ 匹配器语义", ok3,
            "protocol.iou_thrs 必须是展开的列表（写 '0.5:0.95' 无法判定是 10 点还是 101 点扫描），"
            "protocol.matcher ∈ 已知语义集合")
    if ok3 and len(thrs) == 1 and thrs[0] == 0.5:
        rep.add("M3b", "单阈值 0.50 与被测量之争", True,
                "只报 mAP@0.50：注意这与 mAP@0.50:0.95 在部分分类法里属**不同被测量**而非同量换配方"
                "（本项目 E5：换到 mAP50 使同一模型 AP 挪 +0.118/+0.204，Holm p≤0.009）",
                level="WARN")

    # M4 AP 积分末点/哨兵约定
    ap = _get(dec, "ap_integration") or {}
    rep.add("M4", "AP 积分末点/哨兵约定",
            ap.get("interp") in ("coco101", "all_point", "voc11", "ult_trapezoid")
            and "recall_beyond_max" in ap,
            "ap_integration{interp, recall_beyond_max}；召回超过曲线最大召回的点**赋 0 还是取末值**"
            "可使小目标 AP 差 0.05 量级（§M4）")

    # M5 类别聚合 + 有效类别数 + 每类 GT 数
    agg = _get(dec, "aggregation") or {}
    gt_cls = agg.get("gt_per_class")
    ok5 = agg.get("mode") in ("macro", "micro", "gt_weighted") and isinstance(gt_cls, dict) \
        and len(gt_cls) >= 1 and all(_num(v) and v >= 0 for v in gt_cls.values())
    rep.add("M5", "类别聚合方式 + 每类 GT 数", ok5,
            "aggregation{mode, gt_per_class}；macro 与 gt_weighted 对同一模型可差 0.07（§M5），"
            "不报每类 GT 数则无法判断 macro 被几个稀有类主导")
    if ok5:
        nz = [v for v in gt_cls.values() if _num(v)]
        thin = sorted([c for c, v in gt_cls.items() if _num(v) and v < 20])
        rep.add("M5b", "稀有类对 macro 的支配度", len(thin) == 0,
                "%d/%d 个类 GT<20 ⇒ macro AP 的分母里这些类各占 1/N 但抽样极不稳定"
                % (len(thin), len(nz)), level="WARN")

    # M6 面积/尺度分层定义
    ar = _get(dec, "area_tiers") or {}
    ok6 = bool(ar.get("definition")) and ar.get("definition") in ("coco_abs", "rel_area", "none", "aitod_abs_size") \
        and (ar.get("thresholds") is not None or ar.get("definition") == "none") \
        and ar.get("reported_layer") in ("all", "small", "medium", "large", None)
    rep.add("M6", "尺度分层的**定义**与所报层", ok6,
            "area_tiers{definition,thresholds,reported_layer}；'small' 一词在不同实现里不是同一个集合"
            "（本项目 D4 属'同名不同测'，同层内两种定义 |Δ| 均值 0.0398/0.0093）")

    # M6b 分层三要素（E6 实测：已发表基准只给边界、不给这三样 ⇒ 同一批框层 AP 极差最大 0.041）
    if ok6 and ar.get("definition") in ("coco_abs", "aitod_abs_size")             and ar.get("reported_layer") not in (None, "all"):   # M6 不计时不重复点亮 M6b
        need = ("size_measure", "boundary_rule", "filter_scope")
        miss = [k for k in need if not ar.get(k)]
        rep.add("M6b", "分层的 size 度量 / 边界开闭 / 筛选范围三项具名", not miss,
                "缺 area_tiers.{%s}；只给阈值不算给出分层——本项目按已发表基准的边界复原 AI-TOD 层 AP，"
                "这三轴未定义时的读法间极差达 0.018~0.041（e6_tier_ambiguity.md）"
                % ",".join(miss))

    # M7 置信度阈值与预测来源路径
    pd = _get(dec, "predictions") or {}
    ok7 = _num(pd.get("conf_threshold")) and pd.get("source") in \
        ("validator", "predict", "export_file", "other") and bool(pd.get("source_detail"))
    rep.add("M7", "置信度阈值 + 检测框产生路径", ok7,
            "predictions{conf_threshold, source, source_detail}；"
            "val 与 predict 两条路径自算 AP 可差 0.012 量级（§M7）")

    # M8 同分破序规则
    tb = _get(dec, "tie_break") or {}
    rep.add("M8", "同分（并列置信度）破序规则",
            tb.get("rule") in ("score_then_image_order", "score_then_draw_order",
                               "score_then_file_order"),
            "tie_break.rule ∈ 具名规则；实测每条 (类,阈值) 曲线 35.31% 的检测与后继同分"
            "⇒ 不写明无法逐位复现。注意 **\"unspecified\" 不算具名规则**"
            "（把\"没写\"当成一个合法取值＝这条检查永远不会红，等于没有检查）")

    # M9 图像联接完整性（join）
    jn = _get(dec, "join") or {}
    n_gt_img, n_join = jn.get("n_gt_images"), jn.get("n_joined_images")
    ok9 = _num(n_gt_img) and _num(n_join) and n_gt_img > 0
    rep.add("M9", "图像联接完整性（GT 图数 == join 图数）", ok9,
            "join{n_gt_images,n_joined_images,zero_det_counted}")
    if ok9:
        # "少图会虚高多少"这个数从 `join_effect.json` 取（由 epsa_e7_join_effect.py 实测产出）。
        # 这里曾手写过 0.0116 —— 那是把 D4 层内最大 |Δ| 串过来的**假数**，
        # 实测只有 +0.0028/+0.0034。手抄的数一旦串位，检查器就会替假数背书，故改成读件。
        je = _join_effect()
        amt = "" if je is None else ("（本项目实测 +%s/+%s，AI-TOD 两个模型；VisDrone 侧 0）"
                                     % (je["AITOD_B1_s42"], je["AITOD_E1_off_s42"]))
        rep.add("M9b", "是否存在有 GT 却掉出分母的图", n_join == n_gt_img,
                "n_gt_images=%d 而 n_joined_images=%d ⇒ %d 张图的 GT 不进召回分母，"
                "AP 系统性虚高%s；两侧同源的对照检查看不见它（§M9）"
                % (n_gt_img, n_join, n_gt_img - n_join, amt))

        rep.add("M9c", "真·零检出图是否计入", jn.get("zero_det_counted") is True,
                "join.zero_det_counted 必须为 true：被省略的零检出图=漏检不进分母", level="WARN")

    # M10 不确定度单位
    un = _get(dec, "uncertainty") or {}
    ok10 = un.get("resample_unit") in ("image", "cluster") and \
        (un.get("resample_unit") == "image" or bool(un.get("cluster_definition"))) \
        and _num(un.get("B"))
    rep.add("M10", "不确定度的抽样单位与簇定义", ok10,
            "uncertainty{resample_unit,cluster_definition,B}；换视频段做簇自助可使 SE 放大 1.08–1.97 倍"
            "并让'显著'变不显著（§M10）")
    if un.get("claims_significance") and un.get("resample_unit") == "image" \
            and un.get("clusters_exist") is True:
        rep.add("M10b", "有簇结构却只报逐图自助", False,
                "数据存在天然簇（如视频段）而不确定度只按逐图自助 ⇒ 区间偏窄，须并列报簇自助",
                level="WARN")

    # M10c 簇自助是否**真的**是第二个独立预算：平均每簇图数太小 ⇒ 簇重抽样≈逐图重抽样。
    # 动机是自家实测：某域 2804 图只聚成 2194 簇（中位 1 图/簇），两区间高度同源，
    # 写成"两套独立预算都覆盖 0"其实是同一句话说了两遍。
    nc, ni = un.get("n_clusters"), un.get("n_img")
    if _num(nc) and _num(ni) and nc > 0:
        per = float(ni) / float(nc)
        if per >= 2.0:
            rep.add("M10c", "簇自助与逐图自助是否两套独立预算", True,
                    "n_img/n_clusters = %.2f（平均每簇 %.2f 图）⇒ 簇重抽样与逐图重抽样可分，"
                    "两套区间可当两个预算并列报" % (per, per))
        else:
            rep.add("M10c", "簇自助与逐图自助是否两套独立预算", False,
                    "n_img/n_clusters = %.2f ⇒ 平均每簇仅 %.2f 图，簇重抽样与逐图重抽样高度同源，"
                    "不得并称『两套独立预算』，只能写成对抽样单位的敏感性检查" % (per, per),
                    level="WARN")

    # M13 seed 数与 seed 间分散度（兑现规划 §八.8）：只说"跑了 3 个 seed"不算申报。
    # 动机是自家实测：本项目的"可分辨对"判据里的 MDE 就建立在 seed 间 sd 上，而该 sd 从未单独报告；
    # 不报 sd，读者就无法判断一个 1e-3 量级的差是口径效应还是换 run 的噪声。
    sdd = _get(dec, "seed_dispersion") or {}
    n_seed = sdd.get("n_seeds")
    if not _num(n_seed) or n_seed < 2:
        rep.add("M13", "seed 数与 seed 间分散度", False,
                "没报 seed 数或只跑了 1 个 ⇒ 任何 1e-3 量级的差都不能归因于口径；"
                "多 seed 资产在盘上却不报 sd，等同没测（§M13）", level="WARN")
    else:
        sd, ci = sdd.get("sd_pooled_compliant"), sdd.get("ci95_sd_pooled")
        ok13 = _num(sd) and isinstance(ci, list) and len(ci) == 2 and all(_num(x) for x in ci)
        rep.add("M13", "seed 数与 seed 间分散度", ok13,
                "n_seeds=%d（组：%s）｜合规臂合并 sd %s（95%% 区间 %s，%s 格）"
                "｜只有单 seed 的组：%s。n=3 ⇒ 单格 sd 只能定到约 12 倍内，"
                "结论必须用合并值或逐臂值（§M13）"
                % (n_seed, "、".join(sdd.get("groups") or []) or "—",
                   ("%.6f" % sd) if _num(sd) else "**缺**",
                   ("[%.6f, %.6f]" % tuple(ci)) if ok13 else "**缺**",
                   sdd.get("n_cells") if sdd.get("n_cells") is not None else "**缺**",
                   "、".join(sdd.get("single_seed_groups") or []) or "无"))

    # M11 每个数值声明的估计量类别
    cl = _get(dec, "claims") or []
    bad = [c.get("label", "?") for c in cl
           if not isinstance(c, dict) or c.get("kind") not in
           ("estimator_switch", "measurand_switch", "stress_test", "fault_injection")]
    rep.add("M11", "每条数值声明标注了估计量类别", len(bad) == 0 and len(cl) > 0,
            "claims[].kind ∈ {estimator_switch, measurand_switch, stress_test, fault_injection}；"
            "混着比会造出'高危维度'假象（§M11）" + ("｜缺标记：%s" % bad if bad else ""))

    # 比值型主张（如"X 是 Y 的 k 倍"）必须有区间且分母显著
    for c in cl:
        if isinstance(c, dict) and c.get("form") == "ratio":
            r_ok = _num(c.get("numerator")) and _num(c.get("denominator")) \
                and c.get("ci") is not None and c.get("denominator_excludes_zero") is True
            rep.add("M12:%s" % c.get("label", "?"), "比值型主张须给区间且分母显著", r_ok,
                    "比值 = 已舍入统计量相除，且分母区间覆盖 0 时符号不定 ⇒ 该'倍数'无可用区间"
                    "（本项目据此废止一条 3.7× 头条，§M12）", level="WARN")
    return rep


# ---------------------------------------------------------------- 夹具（自测用）
GOOD = {
    "engine": {"name": "epsa (pycocotools-aligned)", "version": "self",
               "commit_or_release": "1d5b610"},
    "max_det": {"eval_value": 100, "unit": "per_img_cat", "export_value": 1000,
                "export_cap_share": 0.0, "cap_sensitivity": None},
    "protocol": {"iou_thrs": [round(0.5 + 0.05 * i, 2) for i in range(10)],
                 "matcher": "greedy_score"},
    "ap_integration": {"interp": "coco101", "recall_beyond_max": "zero"},
    "aggregation": {"mode": "macro",
                    "gt_per_class": {str(i): 7000 + i for i in range(10)}},
    "area_tiers": {"definition": "coco_abs", "thresholds": [1024, 9216],
                   "reported_layer": "all"},
    "predictions": {"conf_threshold": 0.001, "source": "validator",
                    "source_detail": "model.val(save_json=True), imgsz=640"},
    "tie_break": {"rule": "score_then_image_order"},
    "join": {"n_gt_images": 1610, "n_joined_images": 1610, "zero_det_counted": True},
    "uncertainty": {"resample_unit": "cluster",
                    "cluster_definition": "VisDrone 视频段（stem 前缀，61 簇）", "B": 1000,
                    "claims_significance": True, "clusters_exist": True,
                    "n_img": 1610, "n_clusters": 61},
    # 夹具里的 seed 数值是**合成**的（不是实测值），免得有人把它当读数
    "seed_dispersion": {"n_seeds": 3, "groups": ["B1", "E1_off"],
                        "sd_pooled_compliant": 0.002500,
                        "ci95_sd_pooled": [0.001900, 0.004100], "n_cells": 48,
                        "single_seed_groups": ["B2", "E2", "P2"],
                        "source": "seed_variance.json"},
    "claims": [{"label": "protocol 挪动量 vs 模型差", "kind": "estimator_switch"},
               {"label": "AP 末点约定", "kind": "estimator_switch"}],
}


def _broken_variants():
    """每个坏件必须**恰好**让它该亮的那一项变红；多亮或漏亮都算自测失败。"""
    out = {}

    d = copy.deepcopy(GOOD)
    d["engine"].pop("version")
    out["M1"] = (d, {"M1"})

    d = copy.deepcopy(GOOD)
    d["max_det"] = {"eval_value": 100, "unit": "per_img_cat"}
    out["M2"] = (d, {"M2"})

    d = copy.deepcopy(GOOD)                    # 饱和档：只该点亮 M2b（WARN）
    d["max_det"] = {"eval_value": 300, "unit": "per_img", "export_value": 300,
                    "export_cap_share": 1.0, "cap_sensitivity": 0.0021}   # 只该点亮 M2b
    out["M2b"] = (d, {"M2b"})

    d = copy.deepcopy(GOOD)                    # 没申报"导出上限是否 bind"
    d["max_det"] = {"eval_value": 100, "unit": "per_img_cat", "export_value": 300}
    out["M2c"] = (d, {"M2c"})

    d = copy.deepcopy(GOOD)                    # bind 了但不给跨 cap 敏感性
    d["max_det"] = {"eval_value": 100, "unit": "per_img_cat", "export_value": 300,
                    "export_cap_share": 0.984, "cap_sensitivity": None}
    out["M2c-未测敏感性"] = (d, {"M2c"})

    d = copy.deepcopy(GOOD)
    d["protocol"]["iou_thrs"] = "0.5:0.95"
    out["M3"] = (d, {"M3"})

    d = copy.deepcopy(GOOD)
    d["ap_integration"].pop("recall_beyond_max")
    out["M4"] = (d, {"M4"})

    d = copy.deepcopy(GOOD)
    d["aggregation"]["gt_per_class"] = {}
    out["M5"] = (d, {"M5"})

    d = copy.deepcopy(GOOD)
    d["area_tiers"] = {"definition": "coco_abs", "reported_layer": "small"}
    out["M6"] = (d, {"M6"})

    d = copy.deepcopy(GOOD)                    # 报了分层却没给三要素 ⇒ 只该点亮 M6b
    d["area_tiers"] = {"definition": "aitod_abs_size", "thresholds": [64.0, 256.0],
                       "reported_layer": "small"}      # 三要素没给 ⇒ 只该点亮 M6b
    out["M6b"] = (d, {"M6b"})

    d = copy.deepcopy(GOOD)
    d["predictions"]["source_detail"] = ""
    out["M7"] = (d, {"M7"})

    d = copy.deepcopy(GOOD)
    d["tie_break"] = {"rule": "unspecified"}
    out["M8"] = (d, {"M8"})
    d = copy.deepcopy(GOOD)
    d.pop("tie_break")
    out["M8-缺字段"] = (d, {"M8"})

    d = copy.deepcopy(GOOD)                    # 少 41 图：正是本项目踩过的坑
    d["join"] = {"n_gt_images": 2804, "n_joined_images": 2763, "zero_det_counted": True}
    out["M9b"] = (d, {"M9b"})

    d = copy.deepcopy(GOOD)
    d["join"]["zero_det_counted"] = False
    out["M9c"] = (d, {"M9c"})

    d = copy.deepcopy(GOOD)
    d["uncertainty"] = {"resample_unit": "cluster", "B": 1000}
    out["M10"] = (d, {"M10"})

    d = copy.deepcopy(GOOD)
    d["uncertainty"] = {"resample_unit": "image", "B": 1000, "claims_significance": True,
                        "clusters_exist": True}
    out["M10b"] = (d, {"M10b"})

    d = copy.deepcopy(GOOD)                    # 簇自助≈逐图自助：每簇 1.28 图
    d["uncertainty"] = dict(GOOD["uncertainty"], n_img=2804, n_clusters=2194)
    out["M10c"] = (d, {"M10c"})

    d = copy.deepcopy(GOOD)
    d["claims"] = [{"label": "翻转率"}]
    out["M11"] = (d, {"M11"})

    d = copy.deepcopy(GOOD)                    # 比值主张没给区间、分母不显著
    d["claims"].append({"label": "maxDet 效应 = 方法增益的 3.7 倍", "form": "ratio",
                        "kind": "estimator_switch", "numerator": 0.0217, "denominator": 0.0058,
                        "ci": None, "denominator_excludes_zero": False})
    out["M12"] = (d, {"M12:maxDet 效应 = 方法增益的 3.7 倍"})

    d = copy.deepcopy(GOOD)                    # 跑了 3 个 seed 却不报 sd ⇒ 只该点亮 M13
    d["seed_dispersion"] = {"n_seeds": 3, "groups": ["B1", "E1_off"],
                            "sd_pooled_compliant": None, "ci95_sd_pooled": None}
    out["M13-缺sd"] = (d, {"M13"})

    d = copy.deepcopy(GOOD)                    # 整个 seed_dispersion 块缺失 ⇒ 也算"没报 seed 数"
    d.pop("seed_dispersion")
    out["M13-整块缺"] = (d, {"M13"})

    d = copy.deepcopy(GOOD)                    # 单 seed：WARN 级（不是 FAIL，如实申报就不拦）
    d["seed_dispersion"] = {"n_seeds": 1, "groups": ["B1"]}
    out["M13-单seed"] = (d, {"M13"})
    return out


def selftest(log):
    ok = True
    rep = check_all(GOOD)
    hard = [i for i in rep.items if not i["pass"] and i["level"] == "FAIL"]
    warn = [i for i in rep.items if i["level"] == "WARN"]
    log("好件：PASS %d / WARN %d / FAIL %d（期望 FAIL=0）" % (
        sum(1 for i in rep.items if i["pass"]), len(warn), len(hard)))
    for i in hard:
        log("  !! 好件里变红：%s %s" % (i["id"], i["msg"]))
    ok &= not hard
    for i in warn:
        log("  （WARN 允许存在，但必须能解释：%s）" % i["id"])

    for name, (dec, expect) in sorted(_broken_variants().items()):
        r = check_all(dec)
        got = set(r.failed_ids()) | {i["id"] for i in r.items if i["level"] == "WARN"
                                      and not i["pass"]}
        hit = got == expect
        log("  坏件 %-5s 期望点亮 %-40s 实得 %-40s %s"
            % (name, sorted(expect), sorted(got), "OK" if hit else "FAIL"))
        if not hit:
            ok = False
    log("\n自测判定：%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decl", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--strict", action="store_true", help="WARN 也计入失败")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    def log(m):
        print(m)

    if a.selftest:
        return selftest(log)
    if not a.decl:
        print("用法：epsa_check.py declaration.json | --selftest")
        return 2
    dec = json.load(open(a.decl, encoding="utf-8"))
    rep = check_all(dec)
    width = max(len(i["id"]) for i in rep.items)
    for i in rep.items:
        mark = "PASS" if i["pass"] else i["level"]
        log("%-*s %-4s %s%s" % (width, i["id"], mark, i["title"],
                                 "" if i["pass"] else "  ← " + i["msg"]))
    nf, nw = rep.n_fail(), rep.n_warn()
    log("\nEPSA-MRS v1 判定：%s（%d 项，FAIL %d / WARN %d）"
        % ("放行" if nf == 0 and (nw == 0 or not a.strict) else "不放行",
           len(rep.items), nf, nw))
    if a.json:
        out = os.path.splitext(a.decl)[0] + "_check.json"
        json.dump({"mrs_version": "v1", "items": rep.items, "n_fail": nf, "n_warn": nw},
                  open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        log("-> %s" % out)
    return 1 if (nf or (a.strict and nw)) else 0


if __name__ == "__main__":
    sys.exit(main())
