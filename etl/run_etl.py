#!/usr/bin/env python3
import os, re, sqlite3, xlrd, openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DDIR = os.path.join(os.path.expanduser("~"), "Desktop", "江苏省省考岗位表")
F27 = os.path.join(DDIR, "27江苏省考职位合并表(1).xls")
FH = os.path.join(DDIR, "2019-2026江苏省考历年职位表_报考情况_入面分.xlsx")
DB = os.path.join(BASE, "backend", "jiangsu_exam.db")

CS = ["南京市","无锡市","徐州市","常州市","苏州市","南通市","连云港市","淮安市","盐城市","扬州市","镇江市","泰州市","宿迁市"]
CM = {"00":"省级机关","01":"南京市","02":"无锡市","03":"徐州市","04":"常州市","05":"苏州市","06":"南通市","07":"连云港市","08":"淮安市","09":"盐城市","10":"扬州市","11":"镇江市","12":"泰州市","13":"宿迁市"}

def cstr(v):
    if v is None: return ""
    if isinstance(v,float) and v!=v: return ""
    return str(v).strip().replace("\u3000","")

def cint(v):
    if v is None or v=="": return None
    if isinstance(v,float) and v!=v: return None
    s=str(v).strip()
    if s in("#N/A","#REF!","#VALUE!","#DIV/0!","None"): return None
    s=re.sub(r"[^0-9.]","",s)
    if not s: return None
    try: return int(float(s))
    except: return None

def cflt(v):
    if v is None or v=="": return None
    if isinstance(v,float) and v!=v: return None
    s=str(v).strip()
    if s in("#N/A","#REF!","#VALUE!","#DIV/0!","None","null"): return None
    s=re.sub(r"[^0-9.]","",s)
    if not s: return None
    try: return float(s)
    except: return None

def xcity(rn,rc,ss=""):
    if rn:
        for c in CS:
            if c in str(rn): return c
    if rc and len(str(rc))>=2 and str(rc)[:2] in CM: return CM[str(rc)[:2]]
    if ss:
        for c in CS:
            if c in ss: return c
        if "省级" in ss: return "省级机关"
    if rn and str(rn).strip()=="江苏省": return "省级机关"
    return ss or "未知"

def pother(t):
    t=t or ""
    return {"requires_fresh":int(bool(re.search("应届",t))),"requires_party":int(bool(re.search("中共党员|含预备",t))),"requires_male":int(bool(re.search("男性|适合男性",t))),"requires_female":int(bool(re.search("女性|适合女性",t))),"requires_degree":int(bool(re.search("取得相应.*学位",t))),"requires_work_exp":int(bool(re.search("基层工作经历|两年以上",t))),"requires_legal_cert":int(bool(re.search("法律职业资格|A类",t)))}

def smaj(m):
    if not m: return []
    # Split on delimiters but NOT inside parentheses
    result = []
    current = ''
    depth = 0
    for ch in str(m):
        if ch in "（（(":
            depth += 1
            current += ch
        elif ch in "））)":
            depth = max(0, depth - 1)
            current += ch
        elif depth == 0 and ch in "，,、；;":
            if current.strip():
                result.append(current.strip().replace("　",""))
            current = ''
        else:
            current += ch
    if current.strip():
        result.append(current.strip().replace("　",""))
    return result

def iscat(n):
    base = n.split("（")[0].split("(")[0]
    return base.endswith("类")


def read_2027():
    positions = []
    wb = xlrd.open_workbook(F27)
    for sn in wb.sheet_names():
        sh = wb.sheet_by_name(sn)
        if sh.nrows < 4: continue
        for ri in range(3, sh.nrows):
            row = [sh.cell_value(ri, c) for c in range(sh.ncols)]
            if not any(str(v).strip() for v in row if v is not None): continue
            aff = cstr(row[0]) if len(row)>0 else ""
            rcode = cstr(row[1]) if len(row)>1 else ""
            rname = cstr(row[2]) if len(row)>2 else ""
            ucode = cstr(row[3]) if len(row)>3 else ""
            uname = cstr(row[4]) if len(row)>4 else ""
            pcode = cstr(row[5]) if len(row)>5 else ""
            pname = cstr(row[6]) if len(row)>6 else ""
            pdesc = cstr(row[7]) if len(row)>7 else ""
            ecat = cstr(row[8]) if len(row)>8 else ""
            oratio = cstr(row[9]) if len(row)>9 else ""
            rcount = cint(row[10]) if len(row)>10 else None
            edu = cstr(row[11]) if len(row)>11 else ""
            maj = cstr(row[12]) if len(row)>12 else ""
            oth = cstr(row[13]) if len(row)>13 else ""
            if not uname and not pname: continue
            ct = xcity(rname, rcode, sn)
            of = pother(oth)
            mk = ucode + "-" + pcode if ucode and pcode else ""
            p = {"year":2027,"affiliation":aff,"region_code":rcode,"region_name":rname,"unit_code":ucode,"unit_name":uname,"position_code":pcode,"position_name":pname,"position_desc":pdesc,"exam_category":ecat,"open_ratio":oratio,"recruit_count":rcount,"education_req":edu,"major_req":maj,"other_req":oth,"source_sheet":sn,"applicants_count":None,"score_max":None,"score_min":None,"city":ct,"match_key":mk}
            p.update(of)
            positions.append(p)
    wb.release_resources()
    print("  2027: " + str(len(positions)) + " records")
    return positions

HCM = {
    "2026年":{0:"source_sheet",1:"affiliation",2:"region_code",3:"region_name",4:"unit_code",5:"unit_name",6:"position_code",7:"position_name",8:"position_desc",9:"exam_category",10:"open_ratio",11:"recruit_count",12:"education_req",13:"major_req",14:"other_req",15:"applicants_count",16:"score_max",17:"score_min"},
    "2025年":{0:"source_sheet",1:"affiliation",2:"region_code",3:"region_name",4:"unit_code",5:"unit_name",6:"position_code",7:"position_name",8:"position_desc",9:"exam_category",10:"open_ratio",11:"recruit_count",12:"education_req",13:"major_req",14:"other_req",15:"applicants_count",16:"score_max",17:"score_min"},
    "2024年":{0:"source_sheet",1:"affiliation",2:"region_code",3:"region_name",4:"unit_code",5:"unit_name",6:"position_code",7:"position_name",8:"position_desc",9:"exam_category",10:"open_ratio",11:"recruit_count",12:"education_req",13:"major_req",14:"other_req",15:"applicants_count",16:"score_max",17:"score_min"},
    "2023年":{0:"source_sheet",2:"affiliation",3:"region_code",5:"region_name",6:"unit_code",8:"unit_name",9:"position_code",11:"position_name",12:"position_desc",13:"exam_category",14:"open_ratio",15:"recruit_count",16:"education_req",17:"major_req",18:"other_req",20:"applicants_count",21:"score_min"},
    "2022年":{0:"affiliation",1:"region_code",2:"region_name",3:"unit_code",4:"unit_name",5:"position_code",6:"position_name",7:"position_desc",8:"exam_category",9:"open_ratio",10:"recruit_count",11:"education_req",12:"major_req",13:"other_req",15:"applicants_count",16:"score_min"},
    "2021年":{0:"affiliation",1:"region_code",2:"region_name",3:"unit_code",4:"unit_name",5:"position_code",6:"position_name",7:"position_desc",8:"exam_category",9:"open_ratio",10:"recruit_count",11:"education_req",12:"major_req",13:"other_req",15:"applicants_count",16:"score_min",17:"score_max"},
    "2020年":{0:"affiliation",1:"region_code",2:"region_name",3:"unit_code",4:"unit_name",5:"position_code",6:"position_name",7:"position_desc",8:"exam_category",9:"open_ratio",10:"recruit_count",11:"education_req",12:"major_req",13:"other_req",14:"applicants_count",15:"score_min",16:"score_max"},
    "2019年":{0:"affiliation",1:"region_code",2:"region_name",3:"unit_code",4:"unit_name",5:"position_code",6:"position_name",7:"position_desc",8:"exam_category",9:"open_ratio",10:"recruit_count",11:"education_req",12:"major_req",13:"other_req",14:"applicants_count",15:"score_min",16:"score_max"},
}
HYM = {"2026年":2026,"2025年":2025,"2024年":2024,"2023年":2023,"2022年":2022,"2021年":2021,"2020年":2020,"2019年":2019}

def read_hist():
    positions = []
    wb = openpyxl.load_workbook(FH, read_only=True, data_only=True)
    for sn in wb.sheetnames:
        if sn not in HCM: continue
        yr = HYM[sn]
        cm = HCM[sn]
        ws = wb[sn]
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2: continue
        count = 0
        for row in rows[1:]:
            if not row or not any(v is not None and str(v).strip() for v in row): continue
            d = {}
            for ci, fn in cm.items():
                d[fn] = row[ci] if ci < len(row) else None
            uname = cstr(d.get("unit_name"))
            pname = cstr(d.get("position_name"))
            if not uname and not pname: continue
            aff = cstr(d.get("affiliation"))
            rcode = cstr(d.get("region_code"))
            rname = cstr(d.get("region_name"))
            ucode = cstr(d.get("unit_code"))
            pcode = cstr(d.get("position_code"))
            pdesc = cstr(d.get("position_desc"))
            ecat = cstr(d.get("exam_category"))
            oratio = cstr(d.get("open_ratio"))
            rcount = cint(d.get("recruit_count"))
            edu = cstr(d.get("education_req"))
            maj = cstr(d.get("major_req"))
            oth = cstr(d.get("other_req"))
            ss = cstr(d.get("source_sheet"))
            ac = cint(d.get("applicants_count"))
            smax = cflt(d.get("score_max"))
            smin = cflt(d.get("score_min"))
            ct = xcity(rname, rcode, ss)
            of = pother(oth)
            mk = ucode + "-" + pcode if ucode and pcode else ""
            p = {"year":yr,"affiliation":aff,"region_code":rcode,"region_name":rname,"unit_code":ucode,"unit_name":uname,"position_code":pcode,"position_name":pname,"position_desc":pdesc,"exam_category":ecat,"open_ratio":oratio,"recruit_count":rcount,"education_req":edu,"major_req":maj,"other_req":oth,"source_sheet":ss,"applicants_count":ac,"score_max":smax,"score_min":smin,"city":ct,"match_key":mk}
            p.update(of)
            positions.append(p)
            count += 1
        print("  " + sn + ": " + str(count) + " records")
    wb.close()
    return positions

def create_db(positions):
    if os.path.exists(DB): os.remove(DB)
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER NOT NULL,
        affiliation TEXT, region_code TEXT, region_name TEXT, unit_code TEXT,
        unit_name TEXT, position_code TEXT, position_name TEXT, position_desc TEXT,
        exam_category TEXT, open_ratio TEXT, recruit_count INTEGER,
        education_req TEXT, major_req TEXT, other_req TEXT, source_sheet TEXT,
        applicants_count INTEGER, score_max REAL, score_min REAL,
        city TEXT, match_key TEXT,
        requires_fresh BOOLEAN DEFAULT 0, requires_party BOOLEAN DEFAULT 0,
        requires_male BOOLEAN DEFAULT 0, requires_female BOOLEAN DEFAULT 0,
        requires_degree BOOLEAN DEFAULT 0, requires_work_exp BOOLEAN DEFAULT 0,
        requires_legal_cert BOOLEAN DEFAULT 0)""")
    c.execute("CREATE INDEX idx_year ON positions(year)")
    c.execute("CREATE INDEX idx_city ON positions(city)")
    c.execute("CREATE INDEX idx_mk ON positions(match_key)")
    c.execute("CREATE INDEX idx_mk_year_app ON positions(match_key, year DESC, applicants_count)")
    c.execute("CREATE INDEX idx_edu ON positions(education_req)")
    c.execute("CREATE INDEX idx_un ON positions(unit_name)")
    c.execute("""CREATE TABLE major_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT, major_name TEXT NOT NULL,
        major_category TEXT, is_category BOOLEAN DEFAULT 0, UNIQUE(major_name))""")
    c.execute("""CREATE TABLE position_majors (
        id INTEGER PRIMARY KEY AUTOINCREMENT, position_id INTEGER NOT NULL,
        major_name TEXT NOT NULL, is_category BOOLEAN DEFAULT 0,
        FOREIGN KEY (position_id) REFERENCES positions(id))""")
    c.execute("CREATE INDEX idx_pm_major ON position_majors(major_name)")
    c.execute("CREATE INDEX idx_pm_pos ON position_majors(position_id)")
    c.execute("""CREATE TABLE favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT, position_id INTEGER NOT NULL,
        note TEXT, created_at TEXT, FOREIGN KEY (position_id) REFERENCES positions(id))""")
    amset = set()
    for p in positions:
        c.execute("""INSERT INTO positions (year,affiliation,region_code,region_name,
            unit_code,unit_name,position_code,position_name,position_desc,
            exam_category,open_ratio,recruit_count,education_req,major_req,
            other_req,source_sheet,applicants_count,score_max,score_min,
            city,match_key,requires_fresh,requires_party,requires_male,
            requires_female,requires_degree,requires_work_exp,requires_legal_cert)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p["year"],p["affiliation"],p["region_code"],p["region_name"],
             p["unit_code"],p["unit_name"],p["position_code"],p["position_name"],
             p["position_desc"],p["exam_category"],p["open_ratio"],p["recruit_count"],
             p["education_req"],p["major_req"],p["other_req"],p["source_sheet"],
             p["applicants_count"],p["score_max"],p["score_min"],
             p["city"],p["match_key"],p["requires_fresh"],p["requires_party"],
             p["requires_male"],p["requires_female"],p["requires_degree"],
             p["requires_work_exp"],p["requires_legal_cert"]))
        pid = c.lastrowid
        for m in smaj(p["major_req"]):
            amset.add(m)
            ic = 1 if iscat(m) else 0
            c.execute("INSERT INTO position_majors (position_id,major_name,is_category) VALUES (?,?,?)",
                      (pid, m, ic))
    for m in sorted(amset):
        ic = 1 if iscat(m) else 0
        cat = m if iscat(m) else None
        c.execute("INSERT OR IGNORE INTO major_catalog (major_name,major_category,is_category) VALUES (?,?,?)",
                  (m, cat, ic))
    conn.commit()
    c.execute("SELECT year, COUNT(*) FROM positions GROUP BY year ORDER BY year")
    for r in c.fetchall():
        print("  DB: year=" + str(r[0]) + " count=" + str(r[1]))
    c.execute("SELECT COUNT(*) FROM major_catalog")
    print("  DB: major_catalog=" + str(c.fetchone()[0]) + " entries")
    c.execute("SELECT COUNT(*) FROM position_majors")
    print("  DB: position_majors=" + str(c.fetchone()[0]) + " entries")
    conn.close()
    sz = os.path.getsize(DB) / 1024 / 1024
    print("  DB size: " + str(round(sz,2)) + " MB")

if __name__ == "__main__":
    print("=== ETL Start ===")
    print("Reading 2027 file...")
    p1 = read_2027()
    print("Reading historical file...")
    p2 = read_hist()
    all_p = p1 + p2
    print("Total: " + str(len(all_p)) + " records")
    print("Creating database...")
    create_db(all_p)
    print("=== ETL Done ===")

