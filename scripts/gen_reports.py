#!/usr/bin/env python3
"""
Generate 65 varied lab reports across 15 clinical categories.
Output: sample-lab-reports/<category>/<filename>.pdf + INDEX.md
"""
from fpdf import FPDF
import os, random, json

random.seed(2026)

BASE_DIR = "/home/sasi-kumar/project-monorepo-team-48/sample-lab-reports"
FLAG_LABEL = {"L": "LOW", "H": "HIGH", "N": "Normal"}
FC = {"L": (180, 40, 40), "H": (160, 80, 0), "N": (40, 40, 40)}

# ─── helpers ────────────────────────────────────────────────────────────────

def rnd(lo, hi, dec=1):
    return round(random.uniform(lo, hi), dec)

def flg(val, lo, hi):
    if lo is not None and val < lo: return "L"
    if hi is not None and val > hi: return "H"
    return "N"

# ─── value generator ────────────────────────────────────────────────────────

def gen(p):
    c = p["conditions"]
    f = p["gender"] == "F"

    ana   = "anaemia"        in c
    dm    = "diabetes"       in c
    pre   = "prediabetes"    in c
    hc    = "high_chol"      in c
    met   = "metabolic"      in c
    hypo  = "hypothyroid"    in c
    hyper = "hyperthyroid"   in c
    hash_ = "hashimoto"      in c
    ckd   = "ckd"            in c
    liver = "liver"          in c
    pcos  = "pcos"           in c
    ra    = "ra"             in c
    sle   = "sle"            in c
    vdd   = "vit_d_def"      in c
    b12d  = "b12_def"        in c

    hb    = rnd(8.0, 11.5) if ana else (rnd(11.5, 15.0) if f else rnd(13.5, 17.0))
    mcv   = rnd(68, 80)    if ana else rnd(84, 100)
    mch   = rnd(21, 26)    if ana else rnd(27, 32)
    rdw   = rnd(16, 22)    if ana else rnd(11.5, 13.8)
    wbc   = rnd(4600, 10800, 0)
    plts  = rnd(1.5, 4.0)

    s_fe  = rnd(28, 58)    if ana else rnd(65, 160)
    tibc  = rnd(380, 460)  if ana else rnd(250, 365)
    fe_sat = round(s_fe / tibc * 100, 1)
    ferr  = rnd(4, 11)     if ana else rnd(18, 145)

    fbg   = rnd(210, 340)  if dm else (rnd(107, 125) if pre else rnd(75, 98))
    ppg   = rnd(260, 410)  if dm else (rnd(141, 199) if pre else rnd(88, 135))
    hba1c = rnd(8.5, 13.0) if dm else (rnd(5.7, 6.4) if pre else rnd(4.5, 5.5))
    homa  = rnd(4.5, 9.0)  if dm else (rnd(2.6, 4.2) if (pre or met) else rnd(0.9, 2.3))

    lipid_bad = hc or met or dm
    ldl   = rnd(148, 225)  if lipid_bad else rnd(62, 99)
    hdl   = rnd(28, 44)    if lipid_bad else rnd(48, 78)
    tg    = rnd(185, 420)  if lipid_bad else rnd(55, 148)
    tchol = round(ldl + hdl + tg / 5, 0)
    non_hdl = round(tchol - hdl, 0)

    tsh   = rnd(7.5, 28.0) if hypo else (rnd(0.01, 0.3) if hyper else rnd(0.5, 3.8))
    ft3   = rnd(1.4, 2.1)  if hypo else (rnd(5.2, 9.0)  if hyper else rnd(2.5, 4.0))
    ft4   = rnd(0.45, 0.72)if hypo else (rnd(2.1, 4.8)  if hyper else rnd(0.85, 1.7))
    anti_tpo = rnd(85, 650) if hash_ else rnd(3, 28)

    alt   = rnd(85, 280)   if liver else rnd(10, 42)
    ast   = rnd(70, 220)   if liver else rnd(10, 36)
    ggt   = rnd(90, 320)   if liver else rnd(10, 44)
    alp   = rnd(160, 420)  if liver else rnd(50, 135)
    tbili = rnd(1.6, 4.2)  if liver else rnd(0.3, 1.0)
    albumin = rnd(2.4, 3.2)if liver else rnd(3.6, 4.8)

    creat = rnd(1.6, 3.8)  if ckd   else rnd(0.55, 1.05)
    bun   = rnd(30, 72)    if ckd   else rnd(8, 18)
    egfr  = int(rnd(22, 55)if ckd   else rnd(72, 105))
    uric  = rnd(7.8, 11.0) if ckd   else rnd(3.2, 5.8)

    vit_d = rnd(5, 17)     if vdd   else rnd(22, 72)
    b12   = rnd(95, 205)   if b12d  else rnd(260, 880)

    lh    = rnd(14, 28)    if pcos  else rnd(3, 10)
    fsh   = rnd(3.5, 8.0)  if pcos  else rnd(3.5, 10)
    testo = rnd(72, 130)   if pcos  else rnd(14, 65)

    rf_v  = rnd(25, 140)   if ra    else rnd(2, 10)
    accp  = rnd(28, 180)   if ra    else rnd(1, 7)
    ana_r = "Positive (1:160)" if sle else "Negative"

    inflam = any(x in c for x in ["anaemia", "liver", "ra", "sle", "hashimoto"])
    esr   = rnd(32, 85)    if inflam else rnd(4, 17)
    crp   = rnd(10, 52)    if inflam else rnd(0.5, 4.2)
    hsCRP = rnd(1.8, 9.5)  if inflam else rnd(0.1, 0.9)

    def v(val, lo, hi, unit="", ref=""):
        return val, flg(val, lo, hi), unit, ref

    return {
        "hb":       (str(hb),  flg(hb,  11.5 if f else 13.0, 16.0 if f else 17.0), "g/dL",     "F:12-16 / M:13.5-17"),
        "mcv":      (str(mcv), flg(mcv, 83, 101),   "fL",       "83 - 101"),
        "mch":      (str(mch), flg(mch, 27, 32),    "pg",       "27 - 32"),
        "rdw":      (str(rdw), flg(rdw, None, 14.0),"% ",       "< 14.0"),
        "wbc":      (str(int(wbc)), flg(wbc, 4500, 11000), "cells/cmm", "4500-11000"),
        "plts":     (str(plts),flg(plts,1.5, 4.0),  "lakh/cmm", "1.5 - 4.0"),
        "s_fe":     (str(s_fe),flg(s_fe, 60, 170),  "ug/dL",    "60 - 170"),
        "tibc":     (str(tibc),flg(tibc, 250, 370), "ug/dL",    "250 - 370"),
        "fe_sat":   (str(fe_sat),flg(fe_sat,20,50), "% ",       "20 - 50"),
        "ferr":     (str(ferr),flg(ferr, 12 if f else 30, 150),"ng/mL","F:12-150 / M:30-400"),
        "fbg":      (str(fbg), flg(fbg,  70, 100),  "mg/dL",    "70 - 100"),
        "ppg":      (str(ppg), flg(ppg,  70, 140),  "mg/dL",    "< 140"),
        "hba1c":    (str(hba1c),flg(hba1c,None,5.7),"% ",       "< 5.7"),
        "homa":     (str(homa),flg(homa, None, 2.5),"",         "< 2.5"),
        "ldl":      (str(ldl), flg(ldl,  None, 100),"mg/dL",    "< 100"),
        "hdl":      (str(hdl), flg(hdl,  50, None), "mg/dL",    "> 50"),
        "tg":       (str(tg),  flg(tg,   None, 150),"mg/dL",    "< 150"),
        "tchol":    (str(int(tchol)),flg(tchol,None,200),"mg/dL","< 200"),
        "non_hdl":  (str(int(non_hdl)),flg(non_hdl,None,130),"mg/dL","< 130"),
        "tsh":      (str(tsh), flg(tsh,  0.4, 4.0), "uIU/mL",  "0.4 - 4.0"),
        "ft3":      (str(ft3), flg(ft3,  2.3, 4.2), "pg/mL",   "2.3 - 4.2"),
        "ft4":      (str(ft4), flg(ft4,  0.8, 1.8), "ng/dL",   "0.8 - 1.8"),
        "anti_tpo": (str(anti_tpo),flg(anti_tpo,None,35),"IU/mL","< 35"),
        "alt":      (str(alt), flg(alt,  None, 56),  "U/L",     "7 - 56"),
        "ast":      (str(ast), flg(ast,  None, 40),  "U/L",     "10 - 40"),
        "ggt":      (str(ggt), flg(ggt,  None, 48),  "U/L",     "9 - 48"),
        "alp":      (str(alp), flg(alp,  44, 147),   "U/L",     "44 - 147"),
        "tbili":    (str(tbili),flg(tbili,0.2,1.2),  "mg/dL",   "0.2 - 1.2"),
        "albumin":  (str(albumin),flg(albumin,3.5,5.0),"g/dL",  "3.5 - 5.0"),
        "creat":    (str(creat),flg(creat,0.5,1.1 if f else 1.3),"mg/dL","F:0.5-1.1 / M:0.7-1.3"),
        "bun":      (str(bun), flg(bun,  7, 20),     "mg/dL",   "7 - 20"),
        "egfr":     (str(egfr),flg(egfr, 60, None),  "mL/min",  "> 60"),
        "uric":     (str(uric),flg(uric, 2.4, 6.0 if f else 7.0),"mg/dL","F:2.4-6 / M:3.5-7"),
        "vit_d":    (str(vit_d),flg(vit_d,30,100),   "ng/mL",   "30 - 100"),
        "b12":      (str(b12), flg(b12, 211, 911),   "pg/mL",   "211 - 911"),
        "lh":       (str(lh),  flg(lh,  2.4, 12.6),  "mIU/mL",  "2.4 - 12.6"),
        "fsh":      (str(fsh), flg(fsh, 3.5, 12.5),  "mIU/mL",  "3.5 - 12.5"),
        "testo":    (str(testo),flg(testo,15,70 if f else 300),"ng/dL","F:15-70 / M:270-1070"),
        "rf":       (str(rf_v),flg(rf_v, None, 14),  "IU/mL",   "< 14"),
        "accp":     (str(accp),flg(accp, None, 20),  "U/mL",    "< 20"),
        "ana":      (ana_r,    "H" if sle else "N",  "",         "Negative"),
        "esr":      (str(esr), flg(esr,  None, 20),  "mm/hr",   "0 - 20"),
        "crp":      (str(crp), flg(crp,  None, 5.0), "mg/L",    "< 5.0"),
        "hs_crp":   (str(hsCRP),flg(hsCRP,None,1.0),"mg/L",    "< 1.0"),
    }

# ─── PDF helpers ────────────────────────────────────────────────────────────

def hdr(pdf, p):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 60, 140)
    pdf.cell(0, 7, "Apollo Diagnostics  -  Comprehensive Lab Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 4, "123, Nungambakkam High Road, Chennai | NABL Accredited | Category: " + p["label"],
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(20, 60, 140); pdf.set_line_width(0.4)
    pdf.line(15, pdf.get_y()+1, 195, pdf.get_y()+1); pdf.ln(4)

def patient_box(pdf, p):
    pdf.set_fill_color(240, 245, 255); pdf.set_draw_color(180, 200, 240)
    pdf.rect(15, pdf.get_y(), 180, 22, "DF")
    y = pdf.get_y() + 2
    rows = [
        ("Patient Name:", p["name"],               "Report ID:",  p["id"]),
        ("Age / Gender:", f"{p['age']}Y / {p['gender']} / {p['weight']}kg", "Category:", p["label"]),
        ("Ref. Doctor:",  p["doctor"],              "Report Date:", "15-Jan-2026"),
    ]
    for row in rows:
        pdf.set_xy(17, y)
        pdf.set_font("Helvetica","B",7); pdf.cell(32,4.5,row[0])
        pdf.set_font("Helvetica","",7);  pdf.cell(55,4.5,row[1])
        pdf.set_font("Helvetica","B",7); pdf.cell(32,4.5,row[2])
        pdf.set_font("Helvetica","",7);  pdf.cell(0, 4.5,row[3])
        y += 6
    pdf.ln(27)

def section(pdf, num, title, sub=""):
    pdf.set_fill_color(220, 232, 255); pdf.set_text_color(20, 60, 140)
    pdf.set_font("Helvetica", "B", 9)
    t = f"  {num}. {title}" + (f"  [{sub}]" if sub else "")
    pdf.cell(0, 6, t, new_x="LMARGIN", new_y="NEXT", fill=True); pdf.ln(1)

def subsec(pdf, title):
    pdf.set_font("Helvetica","BI",8); pdf.set_text_color(60,60,60)
    pdf.cell(0,5,"  "+title,new_x="LMARGIN",new_y="NEXT"); pdf.ln(0.5)

def tbl(pdf, rows):
    W = [72, 22, 20, 45, 14]
    pdf.set_fill_color(200, 218, 250); pdf.set_text_color(20,20,20)
    pdf.set_font("Helvetica","B",7)
    for i, h in enumerate(["Test","Result","Unit","Reference Range","Flag"]):
        pdf.cell(W[i], 5, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica","",7)
    for row in rows:
        val, flag_code, unit, ref = row[1], row[2], row[3], row[4]
        r,g,b = FC.get(flag_code,(40,40,40))
        pdf.set_text_color(r,g,b)
        for i, cell_val in enumerate([row[0], val, unit, ref]):
            pdf.cell(W[i], 4.5, str(cell_val), border=1)
        pdf.set_font("Helvetica","B",7)
        pdf.cell(W[4], 4.5, FLAG_LABEL.get(flag_code, flag_code), border=1)
        pdf.set_font("Helvetica","",7); pdf.ln()
    pdf.ln(2)

def note(pdf, bg, label, text):
    r,g,b = bg; x, y = pdf.get_x(), pdf.get_y()
    pdf.set_fill_color(max(r-60,0),max(g-60,0),max(b-60,0))
    pdf.rect(x, y, 2, 14, "F")
    pdf.set_fill_color(r,g,b); pdf.set_draw_color(max(r-40,0),max(g-40,0),max(b-40,0))
    pdf.rect(x+2, y, 178, 14, "DF")
    pdf.set_xy(x+5, y+1.5)
    pdf.set_font("Helvetica","B",7.5); pdf.set_text_color(max(r-80,0),max(g-70,0),max(b-60,0))
    pdf.cell(25,4,label+":")
    pdf.set_font("Helvetica","",7.5); pdf.set_text_color(40,40,40)
    pdf.multi_cell(148,4,text,new_x="LMARGIN",new_y="NEXT"); pdf.ln(3)

def summary_note(pdf, tag, text, color):
    r,g,b = color
    pdf.set_font("Helvetica","B",7.5); pdf.set_text_color(r,g,b); pdf.cell(22,5,f"[{tag}]")
    pdf.set_font("Helvetica","",7.5); pdf.set_text_color(40,40,40)
    pdf.multi_cell(0,5,text,new_x="LMARGIN",new_y="NEXT")

# ─── clinical auto-commentary ────────────────────────────────────────────────

def commentary(p, vals):
    c = p["conditions"]
    lines = []

    hb_val = float(vals["hb"][0])
    if "anaemia" in c:
        lines.append(("ABNORMAL",(180,40,40),
            f"Iron Deficiency Anaemia confirmed. Hb={hb_val} g/dL (LOW). "
            f"Ferritin={vals['ferr'][0]} ng/mL critically low. TIBC elevated. "
            "Commence iron supplementation 60 mg/day; repeat CBC in 8 weeks."))
    if "diabetes" in c:
        lines.append(("DIABETES",(160,40,40),
            f"Diabetes mellitus. FBG={vals['fbg'][0]} mg/dL, HbA1c={vals['hba1c'][0]}% (HIGH). "
            "Lifestyle modification, diet control, and anti-diabetic pharmacotherapy indicated."))
    if "prediabetes" in c:
        lines.append(("PRE-DM",(160,80,0),
            f"Pre-diabetes detected. FBG={vals['fbg'][0]}, HbA1c={vals['hba1c'][0]}%. "
            "Intensive lifestyle intervention required to prevent progression to T2DM."))
    if "high_chol" in c or "metabolic" in c:
        lines.append(("LIPIDS",(160,80,0),
            f"Dyslipidaemia. LDL={vals['ldl'][0]}, TG={vals['tg'][0]}, "
            f"Non-HDL={vals['non_hdl'][0]} mg/dL. "
            "Mediterranean diet, aerobic exercise, statin therapy review advised."))
    if "hypothyroid" in c:
        lines.append(("THYROID",(160,70,0),
            f"Hypothyroidism. TSH={vals['tsh'][0]} uIU/mL (HIGH), FT4={vals['ft4'][0]} (LOW). "
            "Levothyroxine replacement therapy recommended. Recheck TFT in 6 weeks."))
    if "hyperthyroid" in c:
        lines.append(("THYROID",(160,40,40),
            f"Hyperthyroidism. TSH={vals['tsh'][0]} (suppressed), FT3={vals['ft3'][0]}, "
            f"FT4={vals['ft4'][0]} (HIGH). Antithyroid therapy/radioiodine evaluation required."))
    if "hashimoto" in c:
        lines.append(("AUTOIMMUNE",(140,50,140),
            f"Autoimmune thyroiditis (Hashimoto's). Anti-TPO={vals['anti_tpo'][0]} IU/mL (HIGH). "
            "TSH monitoring every 6 months; supplement if hypothyroid."))
    if "ckd" in c:
        lines.append(("RENAL",(180,40,40),
            f"Chronic Kidney Disease. Creatinine={vals['creat'][0]}, eGFR={vals['egfr'][0]} mL/min. "
            "Nephrology referral, dietary protein restriction, monitor electrolytes."))
    if "liver" in c:
        lines.append(("HEPATIC",(180,40,40),
            f"Hepatic dysfunction. ALT={vals['alt'][0]}, AST={vals['ast'][0]}, "
            f"GGT={vals['ggt'][0]} U/L elevated. Hepatology review, alcohol abstinence, "
            "viral serology recommended."))
    if "pcos" in c:
        lines.append(("PCOS",(140,50,140),
            f"PCOS markers. LH={vals['lh'][0]}, Testosterone={vals['testo'][0]} ng/dL (HIGH). "
            "Gynaecology review, metformin consideration, lifestyle modification."))
    if "ra" in c:
        lines.append(("RA",(140,50,140),
            f"Rheumatoid Arthritis markers. RF={vals['rf'][0]}, Anti-CCP={vals['accp'][0]} (HIGH). "
            "Rheumatology referral. DMARD therapy evaluation."))
    if "sle" in c:
        lines.append(("AUTOIMMUNE",(140,0,140),
            f"SLE markers. ANA={vals['ana'][0]}. Rheumatology referral for full SLE workup."))
    if "vit_d_def" in c:
        lines.append(("DEFICIENCY",(160,80,0),
            f"Vitamin D Insufficiency. 25-OH Vit D={vals['vit_d'][0]} ng/mL (LOW). "
            "60,000 IU/week x 8 weeks then 1000-2000 IU/day maintenance."))
    if "b12_def" in c:
        lines.append(("DEFICIENCY",(160,80,0),
            f"Vitamin B12 Deficiency. B12={vals['b12'][0]} pg/mL (LOW). "
            "B12 IM injections or high-dose oral supplementation required."))
    not_abn = not lines
    if not_abn:
        lines.append(("NORMAL",(30,100,30),
            "All major parameters within normal limits. No significant pathology detected. "
            "Maintain lifestyle measures. Annual review recommended."))
    return lines

# ─── main PDF generator ──────────────────────────────────────────────────────

def make_pdf(p):
    vals = gen(p)
    pdf = FPDF(); pdf.set_margins(15,15,15)

    # PAGE 1 — CBC + Iron + Inflammation
    pdf.add_page(); hdr(pdf, p); patient_box(pdf, p)

    section(pdf,"1","COMPLETE BLOOD COUNT","Circulatory System")
    subsec(pdf,"Red Cell Indices")
    tbl(pdf,[
        ("Haemoglobin (Hb)",        *vals["hb"]),
        ("MCV",                     *vals["mcv"]),
        ("MCH",                     *vals["mch"]),
        ("RDW-CV",                  *vals["rdw"]),
    ])
    note(pdf,(255,235,220),"Haematology",
        f"Hb={vals['hb'][0]} g/dL. MCV={vals['mcv'][0]} fL. RDW={vals['rdw'][0]}%. "
        + ("Microcytic hypochromic picture consistent with iron deficiency." if "anaemia" in p["conditions"]
           else "Red cell indices within normal limits. No anaemia."))
    subsec(pdf,"White Cells & Platelets")
    tbl(pdf,[("WBC",*vals["wbc"]),("Platelet Count",*vals["plts"])])
    note(pdf,(220,245,220),"Note","Leukocyte and platelet counts within normal limits.")

    section(pdf,"2","IRON STUDIES","Haematopoietic")
    tbl(pdf,[
        ("Serum Iron",          *vals["s_fe"]),
        ("TIBC",                *vals["tibc"]),
        ("Transferrin Sat.",    *vals["fe_sat"]),
        ("Serum Ferritin",      *vals["ferr"]),
    ])
    ferr_val = float(vals["ferr"][0])
    iron_comment = (
        f"Ferritin critically low at {ferr_val} ng/mL. TIBC elevated - iron-depleted state confirmed."
        if "anaemia" in p["conditions"] else
        "Iron stores adequate. No iron deficiency.")
    note(pdf,(255,235,220) if "anaemia" in p["conditions"] else (220,245,220),
         "Iron Panel", iron_comment)

    section(pdf,"3","INFLAMMATORY MARKERS","Immune")
    tbl(pdf,[("ESR",*vals["esr"]),("CRP",*vals["crp"]),("hs-CRP",*vals["hs_crp"])])
    note(pdf,(220,245,220),"Inflammation",
        f"ESR={vals['esr'][0]} mm/hr. CRP={vals['crp'][0]} mg/L. " +
        ("Elevated markers consistent with underlying pathology." if float(vals["esr"][0])>20
         else "No significant inflammatory markers."))

    # PAGE 2 — Metabolic Panel
    pdf.add_page(); hdr(pdf, p)

    section(pdf,"4","DIABETES / GLUCOSE METABOLISM","Endocrine - Pancreas")
    tbl(pdf,[
        ("Fasting Blood Glucose",   *vals["fbg"]),
        ("Post-Prandial (2hr)",     *vals["ppg"]),
        ("HbA1c",                   *vals["hba1c"]),
        ("HOMA-IR",                 *vals["homa"]),
    ])
    dm_cond = "diabetes" in p["conditions"]
    pre_cond = "prediabetes" in p["conditions"]
    note(pdf,(255,215,215) if dm_cond else (255,240,210) if pre_cond else (220,245,220),
         "Glycaemia",
         f"FBG={vals['fbg'][0]}, HbA1c={vals['hba1c'][0]}%. " +
         ("DIABETES - pharmacotherapy required." if dm_cond else
          "Pre-diabetic range - intensive lifestyle modification needed." if pre_cond else
          "Normal glycaemic control. No diabetes or pre-diabetes."))

    section(pdf,"5","LIPID PROFILE","Cardiovascular Risk")
    tbl(pdf,[
        ("Total Cholesterol",   *vals["tchol"]),
        ("LDL (Bad)",           *vals["ldl"]),
        ("HDL (Good)",          *vals["hdl"]),
        ("Triglycerides",       *vals["tg"]),
        ("Non-HDL Cholesterol", *vals["non_hdl"]),
    ])
    lp_cond = "high_chol" in p["conditions"] or "metabolic" in p["conditions"] or "diabetes" in p["conditions"]
    note(pdf,(255,235,210) if lp_cond else (220,245,220),"Lipids",
        f"LDL={vals['ldl'][0]}, HDL={vals['hdl'][0]}, TG={vals['tg'][0]} mg/dL. " +
        ("Dyslipidaemia detected. Dietary + pharmacological intervention advised." if lp_cond
         else "Lipid profile within acceptable limits."))

    section(pdf,"6","THYROID FUNCTION TEST","Endocrine - Thyroid")
    tbl(pdf,[("TSH",*vals["tsh"]),("Free T3",*vals["ft3"]),("Free T4",*vals["ft4"]),
             ("Anti-TPO Antibodies",*vals["anti_tpo"])])
    thyroid_note = (
        f"HYPOTHYROIDISM: TSH={vals['tsh'][0]} HIGH, FT4={vals['ft4'][0]} LOW. Levothyroxine required."
        if "hypothyroid" in p["conditions"] else
        f"HYPERTHYROIDISM: TSH={vals['tsh'][0]} suppressed, FT3/FT4 elevated. Antithyroid Rx."
        if "hyperthyroid" in p["conditions"] else
        f"Euthyroid state. TSH={vals['tsh'][0]}, normal FT3/FT4." +
        (" Anti-TPO elevated - Hashimoto's thyroiditis." if "hashimoto" in p["conditions"] else ""))
    note(pdf,(255,215,215) if "hypothyroid" in p["conditions"] or "hyperthyroid" in p["conditions"]
         else (255,240,210) if "hashimoto" in p["conditions"] else (220,245,220),
         "Thyroid", thyroid_note)

    # PAGE 3 — Organ Function + Vitamins + Summary
    pdf.add_page(); hdr(pdf, p)

    section(pdf,"7","LIVER FUNCTION TEST","Hepatobiliary")
    tbl(pdf,[("SGPT / ALT",*vals["alt"]),("SGOT / AST",*vals["ast"]),
             ("GGT",*vals["ggt"]),("Alkaline Phosphatase",*vals["alp"]),
             ("Total Bilirubin",*vals["tbili"]),("Albumin",*vals["albumin"])])
    liver_note = (
        f"Hepatic dysfunction. ALT={vals['alt'][0]}, AST={vals['ast'][0]} elevated. "
        "Hepatology referral required." if "liver" in p["conditions"]
        else "Liver enzymes within normal reference range. No hepatocellular damage.")
    note(pdf,(255,215,215) if "liver" in p["conditions"] else (220,245,220),"LFT",liver_note)

    section(pdf,"8","RENAL FUNCTION TEST","Urinary System")
    tbl(pdf,[("Serum Creatinine",*vals["creat"]),("BUN",*vals["bun"]),
             ("eGFR",*vals["egfr"]),("Serum Uric Acid",*vals["uric"])])
    ckd_note = (
        f"CKD indicators. Creatinine={vals['creat'][0]}, eGFR={vals['egfr'][0]} mL/min (LOW). "
        "Nephrology referral." if "ckd" in p["conditions"]
        else f"Normal renal function. eGFR={vals['egfr'][0]} mL/min.")
    note(pdf,(255,215,215) if "ckd" in p["conditions"] else (220,245,220),"KFT",ckd_note)

    section(pdf,"9","VITAMINS & MINERALS","Nutritional")
    tbl(pdf,[("Vitamin D (25-OH)",*vals["vit_d"]),("Vitamin B12",*vals["b12"])])
    note(pdf,(255,240,210) if float(vals["vit_d"][0])<30 else (220,245,220),"Vitamins",
        f"Vit D={vals['vit_d'][0]} ng/mL " + ("(LOW - supplement required)." if float(vals["vit_d"][0])<30 else "(adequate).") +
        f"  B12={vals['b12'][0]} pg/mL " + ("(LOW - supplementation needed)." if float(vals["b12"][0])<211 else "(normal)."))

    if p["gender"] == "F":
        section(pdf,"10","REPRODUCTIVE HORMONES","Endocrine - HPO")
        tbl(pdf,[("FSH",*vals["fsh"]),("LH",*vals["lh"]),
                 ("Testosterone",*vals["testo"])])
        pcos_note = (
            f"PCOS markers: LH={vals['lh'][0]} (HIGH), Testosterone={vals['testo'][0]} (HIGH). "
            "Gynaecology referral." if "pcos" in p["conditions"]
            else "Reproductive hormones within normal range.")
        note(pdf,(255,215,215) if "pcos" in p["conditions"] else (220,245,220),"Hormones",pcos_note)

    if any(x in p["conditions"] for x in ["ra","sle"]):
        section(pdf,"11","AUTOIMMUNE MARKERS","Rheumatology")
        tbl(pdf,[("Rheumatoid Factor",*vals["rf"]),("Anti-CCP",*vals["accp"]),
                 ("ANA",*vals["ana"])])
        note(pdf,(255,215,215),"Autoimmune",
            f"RF={vals['rf'][0]}, Anti-CCP={vals['accp'][0]}, ANA={vals['ana'][0]}. "
            "Rheumatology/Immunology review required.")

    # Clinical Summary
    pdf.set_fill_color(220,232,255); pdf.set_text_color(20,60,140)
    pdf.set_font("Helvetica","B",9)
    pdf.cell(0,6,"  CLINICAL SUMMARY & RECOMMENDATIONS",new_x="LMARGIN",new_y="NEXT",fill=True)
    pdf.ln(2)
    for tag,color,text in commentary(p, vals):
        summary_note(pdf,tag,text,color)
    pdf.ln(3)
    pdf.set_font("Helvetica","I",7); pdf.set_text_color(140,140,140)
    pdf.multi_cell(0,4,
        f"Report for {p['name']}, {p['age']}Y {p['gender']} | Category: {p['label']} | "
        "Apollo Diagnostics NABL Accredited. Clinical correlation required.",
        new_x="LMARGIN",new_y="NEXT")

    return pdf

# ─── patient roster ──────────────────────────────────────────────────────────

PATIENTS = [
# ── HEALTHY (8) ──────────────────────────────────────────────────────────────
{"id":"RPT-001","name":"Priya Sharma",    "age":24,"gender":"F","weight":"52","doctor":"Dr. Meena Iyer",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},
{"id":"RPT-002","name":"Arjun Kumar",     "age":32,"gender":"M","weight":"74","doctor":"Dr. Ravi Nair",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},
{"id":"RPT-003","name":"Sneha Patel",     "age":19,"gender":"F","weight":"48","doctor":"Dr. Meena Iyer",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},
{"id":"RPT-004","name":"Rahul Verma",     "age":45,"gender":"M","weight":"82","doctor":"Dr. Prakash Rao",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},
{"id":"RPT-005","name":"Meena Krishnan",  "age":38,"gender":"F","weight":"61","doctor":"Dr. Anita Ghosh",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},
{"id":"RPT-006","name":"Kiran Reddy",     "age":55,"gender":"M","weight":"78","doctor":"Dr. Ravi Nair",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},
{"id":"RPT-007","name":"Pooja Nair",      "age":29,"gender":"F","weight":"56","doctor":"Dr. Priya Nair",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},
{"id":"RPT-008","name":"Suresh Babu",     "age":42,"gender":"M","weight":"85","doctor":"Dr. Ravi Nair",
 "category":"01_Healthy","label":"Healthy - All Normal","conditions":[]},

# ── IRON DEFICIENCY ANAEMIA (7) ───────────────────────────────────────────────
{"id":"RPT-009","name":"Riya Sharma",     "age":28,"gender":"F","weight":"55","doctor":"Dr. Priya Nair",
 "category":"02_Iron_Deficiency_Anaemia","label":"Iron Deficiency Anaemia","conditions":["anaemia"]},
{"id":"RPT-010","name":"Kavitha Menon",   "age":22,"gender":"F","weight":"49","doctor":"Dr. Anita Ghosh",
 "category":"02_Iron_Deficiency_Anaemia","label":"Iron Deficiency Anaemia","conditions":["anaemia"]},
{"id":"RPT-011","name":"Deepa Pillai",    "age":35,"gender":"F","weight":"58","doctor":"Dr. Priya Nair",
 "category":"02_Iron_Deficiency_Anaemia","label":"Iron Deficiency Anaemia","conditions":["anaemia"]},
{"id":"RPT-012","name":"Ananya Singh",    "age":17,"gender":"F","weight":"45","doctor":"Dr. Meena Iyer",
 "category":"02_Iron_Deficiency_Anaemia","label":"Iron Deficiency Anaemia","conditions":["anaemia"]},
{"id":"RPT-013","name":"Lalitha Kumari",  "age":48,"gender":"F","weight":"63","doctor":"Dr. Anita Ghosh",
 "category":"02_Iron_Deficiency_Anaemia","label":"Iron Deficiency Anaemia","conditions":["anaemia"]},
{"id":"RPT-014","name":"Sanjana Roy",     "age":31,"gender":"F","weight":"52","doctor":"Dr. Priya Nair",
 "category":"02_Iron_Deficiency_Anaemia","label":"Iron Deficiency Anaemia","conditions":["anaemia"]},
{"id":"RPT-015","name":"Vikram Das",      "age":14,"gender":"M","weight":"42","doctor":"Dr. Ravi Nair",
 "category":"02_Iron_Deficiency_Anaemia","label":"Iron Deficiency Anaemia","conditions":["anaemia"]},

# ── DIABETES / HIGH BLOOD SUGAR (8) ──────────────────────────────────────────
{"id":"RPT-016","name":"Ramesh Nair",     "age":52,"gender":"M","weight":"88","doctor":"Dr. Prakash Rao",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Diabetes - T2DM","conditions":["diabetes","high_chol"]},
{"id":"RPT-017","name":"Sunita Rao",      "age":58,"gender":"F","weight":"79","doctor":"Dr. Anita Ghosh",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Diabetes - T2DM","conditions":["diabetes"]},
{"id":"RPT-018","name":"Mohan Sharma",    "age":45,"gender":"M","weight":"91","doctor":"Dr. Prakash Rao",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Pre-Diabetes","conditions":["prediabetes"]},
{"id":"RPT-019","name":"Geeta Patel",     "age":62,"gender":"F","weight":"72","doctor":"Dr. Anita Ghosh",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Diabetes - T2DM Controlled","conditions":["diabetes"]},
{"id":"RPT-020","name":"Harish Gupta",    "age":48,"gender":"M","weight":"95","doctor":"Dr. Prakash Rao",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Diabetes - T2DM + Obesity","conditions":["diabetes","metabolic"]},
{"id":"RPT-021","name":"Lakshmi Devi",    "age":55,"gender":"F","weight":"78","doctor":"Dr. Anita Ghosh",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Pre-Diabetes","conditions":["prediabetes"]},
{"id":"RPT-022","name":"Arun Menon",      "age":39,"gender":"M","weight":"84","doctor":"Dr. Prakash Rao",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Pre-Diabetes Early","conditions":["prediabetes"]},
{"id":"RPT-023","name":"Champa Reddy",    "age":67,"gender":"F","weight":"68","doctor":"Dr. Anita Ghosh",
 "category":"03_Diabetes_High_Blood_Sugar","label":"Diabetes - T2DM Elderly","conditions":["diabetes"]},

# ── HIGH CHOLESTEROL (6) ──────────────────────────────────────────────────────
{"id":"RPT-024","name":"Vijay Kumar",     "age":44,"gender":"M","weight":"87","doctor":"Dr. Ravi Nair",
 "category":"04_High_Cholesterol","label":"Dyslipidaemia - High LDL","conditions":["high_chol"]},
{"id":"RPT-025","name":"Rekha Sinha",     "age":50,"gender":"F","weight":"74","doctor":"Dr. Anita Ghosh",
 "category":"04_High_Cholesterol","label":"Dyslipidaemia - High LDL","conditions":["high_chol"]},
{"id":"RPT-026","name":"Naresh Gupta",    "age":57,"gender":"M","weight":"92","doctor":"Dr. Ravi Nair",
 "category":"04_High_Cholesterol","label":"Dyslipidaemia - High TG","conditions":["high_chol"]},
{"id":"RPT-027","name":"Malathi Iyer",    "age":43,"gender":"F","weight":"70","doctor":"Dr. Anita Ghosh",
 "category":"04_High_Cholesterol","label":"Dyslipidaemia - Mixed","conditions":["high_chol"]},
{"id":"RPT-028","name":"Prakash Nair",    "age":61,"gender":"M","weight":"82","doctor":"Dr. Ravi Nair",
 "category":"04_High_Cholesterol","label":"Dyslipidaemia - High LDL","conditions":["high_chol"]},
{"id":"RPT-029","name":"Sheela Roy",      "age":47,"gender":"F","weight":"69","doctor":"Dr. Anita Ghosh",
 "category":"04_High_Cholesterol","label":"Dyslipidaemia - High LDL","conditions":["high_chol"]},

# ── HYPOTHYROIDISM (5) ────────────────────────────────────────────────────────
{"id":"RPT-030","name":"Usha Patel",      "age":37,"gender":"F","weight":"72","doctor":"Dr. Meena Iyer",
 "category":"05_Hypothyroidism","label":"Hypothyroidism - Overt","conditions":["hypothyroid"]},
{"id":"RPT-031","name":"Bhavna Sharma",   "age":44,"gender":"F","weight":"78","doctor":"Dr. Meena Iyer",
 "category":"05_Hypothyroidism","label":"Hypothyroidism - Subclinical","conditions":["hypothyroid"]},
{"id":"RPT-032","name":"Dinesh Kumar",    "age":51,"gender":"M","weight":"88","doctor":"Dr. Ravi Nair",
 "category":"05_Hypothyroidism","label":"Hypothyroidism - Overt","conditions":["hypothyroid"]},
{"id":"RPT-033","name":"Radha Menon",     "age":29,"gender":"F","weight":"67","doctor":"Dr. Meena Iyer",
 "category":"05_Hypothyroidism","label":"Hypothyroidism - Hashimoto","conditions":["hypothyroid","hashimoto"]},
{"id":"RPT-034","name":"Sushma Verma",    "age":56,"gender":"F","weight":"82","doctor":"Dr. Meena Iyer",
 "category":"05_Hypothyroidism","label":"Hypothyroidism - Overt","conditions":["hypothyroid"]},

# ── HYPERTHYROIDISM (3) ───────────────────────────────────────────────────────
{"id":"RPT-035","name":"Nandita Roy",     "age":33,"gender":"F","weight":"52","doctor":"Dr. Meena Iyer",
 "category":"06_Hyperthyroidism","label":"Hyperthyroidism - Graves","conditions":["hyperthyroid"]},
{"id":"RPT-036","name":"Pradeep Iyer",    "age":41,"gender":"M","weight":"68","doctor":"Dr. Ravi Nair",
 "category":"06_Hyperthyroidism","label":"Hyperthyroidism - Toxic Nodule","conditions":["hyperthyroid"]},
{"id":"RPT-037","name":"Meghna Patel",    "age":26,"gender":"F","weight":"48","doctor":"Dr. Meena Iyer",
 "category":"06_Hyperthyroidism","label":"Hyperthyroidism - Subclinical","conditions":["hyperthyroid"]},

# ── VITAMIN D DEFICIENCY (4) ──────────────────────────────────────────────────
{"id":"RPT-038","name":"Santosh Kumar",   "age":35,"gender":"M","weight":"75","doctor":"Dr. Ravi Nair",
 "category":"07_Vitamin_D_Deficiency","label":"Vitamin D Deficiency Severe","conditions":["vit_d_def"]},
{"id":"RPT-039","name":"Divya Nair",      "age":27,"gender":"F","weight":"58","doctor":"Dr. Priya Nair",
 "category":"07_Vitamin_D_Deficiency","label":"Vitamin D Insufficiency","conditions":["vit_d_def"]},
{"id":"RPT-040","name":"Raju Sharma",     "age":49,"gender":"M","weight":"82","doctor":"Dr. Ravi Nair",
 "category":"07_Vitamin_D_Deficiency","label":"Vitamin D Deficiency Moderate","conditions":["vit_d_def"]},
{"id":"RPT-041","name":"Anita Gupta",     "age":42,"gender":"F","weight":"65","doctor":"Dr. Anita Ghosh",
 "category":"07_Vitamin_D_Deficiency","label":"Vitamin D Insufficiency","conditions":["vit_d_def"]},

# ── CHRONIC KIDNEY DISEASE (4) ────────────────────────────────────────────────
{"id":"RPT-042","name":"Balakrishnan S.", "age":64,"gender":"M","weight":"79","doctor":"Dr. Prakash Rao",
 "category":"08_Chronic_Kidney_Disease","label":"CKD Stage 2","conditions":["ckd"]},
{"id":"RPT-043","name":"Kamala Devi",     "age":71,"gender":"F","weight":"63","doctor":"Dr. Anita Ghosh",
 "category":"08_Chronic_Kidney_Disease","label":"CKD Stage 3","conditions":["ckd"]},
{"id":"RPT-044","name":"Suresh Pillai",   "age":58,"gender":"M","weight":"85","doctor":"Dr. Prakash Rao",
 "category":"08_Chronic_Kidney_Disease","label":"CKD Stage 2","conditions":["ckd"]},
{"id":"RPT-045","name":"Padma Rao",       "age":67,"gender":"F","weight":"69","doctor":"Dr. Anita Ghosh",
 "category":"08_Chronic_Kidney_Disease","label":"CKD Stage 3","conditions":["ckd"]},

# ── LIVER DISEASE (4) ─────────────────────────────────────────────────────────
{"id":"RPT-046","name":"Mahesh Kumar",    "age":38,"gender":"M","weight":"92","doctor":"Dr. Ravi Nair",
 "category":"09_Liver_Disease","label":"NAFLD - Elevated LFT","conditions":["liver"]},
{"id":"RPT-047","name":"Savitha Reddy",   "age":45,"gender":"F","weight":"78","doctor":"Dr. Anita Ghosh",
 "category":"09_Liver_Disease","label":"Hepatitis - Elevated Enzymes","conditions":["liver"]},
{"id":"RPT-048","name":"Ganesh Iyer",     "age":52,"gender":"M","weight":"88","doctor":"Dr. Ravi Nair",
 "category":"09_Liver_Disease","label":"Alcoholic Hepatitis","conditions":["liver"]},
{"id":"RPT-049","name":"Nirmala Sharma",  "age":41,"gender":"F","weight":"72","doctor":"Dr. Anita Ghosh",
 "category":"09_Liver_Disease","label":"Elevated LFT - Drug Induced","conditions":["liver"]},

# ── PCOS (3) ──────────────────────────────────────────────────────────────────
{"id":"RPT-050","name":"Kavya Menon",     "age":23,"gender":"F","weight":"68","doctor":"Dr. Priya Nair",
 "category":"10_PCOS","label":"PCOS - Hormonal Imbalance","conditions":["pcos"]},
{"id":"RPT-051","name":"Preethi Kumar",   "age":27,"gender":"F","weight":"72","doctor":"Dr. Priya Nair",
 "category":"10_PCOS","label":"PCOS - Hyperandrogenism","conditions":["pcos"]},
{"id":"RPT-052","name":"Swathi Nair",     "age":31,"gender":"F","weight":"76","doctor":"Dr. Priya Nair",
 "category":"10_PCOS","label":"PCOS - With IR","conditions":["pcos","prediabetes"]},

# ── AUTOIMMUNE (3) ────────────────────────────────────────────────────────────
{"id":"RPT-053","name":"Manju Sharma",    "age":34,"gender":"F","weight":"61","doctor":"Dr. Anita Ghosh",
 "category":"11_Autoimmune","label":"Hashimoto Thyroiditis","conditions":["hashimoto","hypothyroid"]},
{"id":"RPT-054","name":"Leela Patel",     "age":39,"gender":"F","weight":"67","doctor":"Dr. Anita Ghosh",
 "category":"11_Autoimmune","label":"Rheumatoid Arthritis","conditions":["ra"]},
{"id":"RPT-055","name":"Subha Rao",       "age":42,"gender":"F","weight":"63","doctor":"Dr. Anita Ghosh",
 "category":"11_Autoimmune","label":"SLE Markers Positive","conditions":["sle","ra"]},

# ── COMBO: ANAEMIA + DIABETES (3) ─────────────────────────────────────────────
{"id":"RPT-056","name":"Saroja Devi",     "age":54,"gender":"F","weight":"71","doctor":"Dr. Anita Ghosh",
 "category":"12_Combo_Anaemia_Diabetes","label":"Anaemia + Diabetes T2DM","conditions":["anaemia","diabetes"]},
{"id":"RPT-057","name":"Girija Kumar",    "age":48,"gender":"F","weight":"68","doctor":"Dr. Anita Ghosh",
 "category":"12_Combo_Anaemia_Diabetes","label":"Anaemia + Pre-Diabetes","conditions":["anaemia","prediabetes"]},
{"id":"RPT-058","name":"Venkatesh Rao",   "age":61,"gender":"M","weight":"84","doctor":"Dr. Prakash Rao",
 "category":"12_Combo_Anaemia_Diabetes","label":"Anaemia + Diabetes T2DM","conditions":["anaemia","diabetes"]},

# ── COMBO: DIABETES + HIGH CHOLESTEROL (3) ────────────────────────────────────
{"id":"RPT-059","name":"Rajan Nair",      "age":56,"gender":"M","weight":"94","doctor":"Dr. Prakash Rao",
 "category":"13_Combo_Diabetes_Cholesterol","label":"Diabetes + Dyslipidaemia","conditions":["diabetes","high_chol"]},
{"id":"RPT-060","name":"Sarojini Iyer",   "age":53,"gender":"F","weight":"82","doctor":"Dr. Anita Ghosh",
 "category":"13_Combo_Diabetes_Cholesterol","label":"Diabetes + Dyslipidaemia","conditions":["diabetes","high_chol"]},
{"id":"RPT-061","name":"Devraj Sharma",   "age":60,"gender":"M","weight":"89","doctor":"Dr. Prakash Rao",
 "category":"13_Combo_Diabetes_Cholesterol","label":"Diabetes + Dyslipidaemia","conditions":["diabetes","high_chol"]},

# ── METABOLIC SYNDROME (3) ────────────────────────────────────────────────────
{"id":"RPT-062","name":"Sridhar Kumar",   "age":47,"gender":"M","weight":"102","doctor":"Dr. Prakash Rao",
 "category":"14_Metabolic_Syndrome","label":"Metabolic Syndrome - Full","conditions":["metabolic","prediabetes","high_chol"]},
{"id":"RPT-063","name":"Pushpa Patel",    "age":51,"gender":"F","weight":"97","doctor":"Dr. Anita Ghosh",
 "category":"14_Metabolic_Syndrome","label":"Metabolic Syndrome - Full","conditions":["metabolic","prediabetes","high_chol"]},
{"id":"RPT-064","name":"Aravind Reddy",   "age":44,"gender":"M","weight":"98","doctor":"Dr. Prakash Rao",
 "category":"14_Metabolic_Syndrome","label":"Metabolic Syndrome - Full","conditions":["metabolic","diabetes","high_chol"]},

# ── MULTIPLE DEFICIENCIES (4) ─────────────────────────────────────────────────
{"id":"RPT-065","name":"Gomathi Pillai",  "age":33,"gender":"F","weight":"54","doctor":"Dr. Priya Nair",
 "category":"15_Multiple_Deficiencies","label":"Vit D + Iron Deficiency","conditions":["anaemia","vit_d_def"]},
{"id":"RPT-066","name":"Chandra Babu",    "age":58,"gender":"M","weight":"71","doctor":"Dr. Ravi Nair",
 "category":"15_Multiple_Deficiencies","label":"Vit D + B12 Deficiency","conditions":["vit_d_def","b12_def"]},
{"id":"RPT-067","name":"Ambika Devi",     "age":46,"gender":"F","weight":"62","doctor":"Dr. Anita Ghosh",
 "category":"15_Multiple_Deficiencies","label":"Anaemia + B12 Deficiency","conditions":["anaemia","b12_def"]},
{"id":"RPT-068","name":"Theresa Joseph",  "age":38,"gender":"F","weight":"58","doctor":"Dr. Priya Nair",
 "category":"15_Multiple_Deficiencies","label":"Multi-Deficiency + Hypothyroid","conditions":["anaemia","vit_d_def","b12_def","hypothyroid"]},
]

# ─── build index ─────────────────────────────────────────────────────────────

def run():
    index = []
    total = 0

    for p in PATIENTS:
        cat_dir = os.path.join(BASE_DIR, p["category"])
        os.makedirs(cat_dir, exist_ok=True)

        safe_name = p["name"].replace(" ","_").replace(".","")
        filename = f"{p['id']}_{safe_name}_{p['age']}{p['gender']}.pdf"
        path = os.path.join(cat_dir, filename)

        try:
            pdf = make_pdf(p)
            pdf.output(path)
            size = os.path.getsize(path)
            total += 1
            print(f"  [{total:02d}] {filename}  ({size//1024}KB)")
            index.append({
                "id":       p["id"],
                "file":     os.path.join(p["category"], filename),
                "name":     p["name"],
                "age":      p["age"],
                "gender":   p["gender"],
                "weight_kg":p["weight"],
                "category": p["category"],
                "label":    p["label"],
                "conditions": p["conditions"],
            })
        except Exception as e:
            print(f"  ERROR {p['id']}: {e}")

    # Write INDEX.md
    md = ["# Sample Lab Reports Index\n",
          f"Generated: 15-Jan-2026 | Total: {total} reports | 15 categories\n",
          "---\n",
          "| ID | File | Patient | Age | Gender | Weight | Category | Label |\n",
          "|---|---|---|---|---|---|---|---|\n"]
    for r in index:
        md.append(f"| {r['id']} | `{r['file']}` | {r['name']} | {r['age']} | "
                  f"{r['gender']} | {r['weight_kg']}kg | {r['category']} | {r['label']} |\n")
    with open(os.path.join(BASE_DIR, "INDEX.md"), "w") as f:
        f.writelines(md)

    # Write INDEX.json
    with open(os.path.join(BASE_DIR, "INDEX.json"), "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nDone. {total} PDFs + INDEX.md + INDEX.json -> {BASE_DIR}")

if __name__ == "__main__":
    run()
