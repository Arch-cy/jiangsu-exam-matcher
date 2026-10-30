#!/usr/bin/env python3
"""Flask backend for JiangSu exam position matching system."""
import os, sqlite3, json, re, io
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "jiangsu_exam.db")
STATIC = os.path.join(os.path.dirname(BASE), "static")

app = Flask(__name__, static_folder=STATIC, static_url_path="")
CORS(app)

EDU_RANK = {"高中":1,"大专":2,"本科":3,"硕士":4,"研究生":4,"博士":5}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def edu_rank(edu):
    # Rank by the highest education level mentioned
    if not edu: return 0
    s = str(edu)
    if "博士" in s: return 5
    if "硕士" in s or "研究生" in s: return 4
    if "本科" in s: return 3
    if "大专" in s: return 2
    if "高中" in s or "中专" in s: return 1
    return 0

def edu_matches(candidate_edu, position_edu):
    c = edu_rank(candidate_edu)
    p = edu_rank(position_edu)
    if p == 0: return True  # no education requirement
    return c >= p

# Build major-to-category mapping from data
def build_major_cat_map():
    return {}

MAJOR_CAT_MAP = {}

CAT_NAMES = []

@app.before_request
def init():
    global MAJOR_CAT_MAP, CAT_NAMES
    if not MAJOR_CAT_MAP:
        MAJOR_CAT_MAP = build_major_cat_map()
    if not CAT_NAMES:
        conn = get_db()
        CAT_NAMES = [r["major_name"] for r in conn.execute("SELECT major_name FROM major_catalog WHERE is_category = 1").fetchall()]
        conn.close()


@app.route("/api/search")
def api_search():
    majors = request.args.getlist("majors[]")
    if not majors:
        mv = request.args.get("majors", "")
        if mv: majors = [mv]
    majors = [m for m in majors if m and m.strip() and m.strip() != "不限"]
    major = "",
    cities = request.args.getlist("cities[]")
    if not cities:
        cv = request.args.get("cities", "")
        if cv: cities = [cv]
    edu = request.args.get("edu", "").strip()
    if edu == "不限": edu = ""
    fresh = request.args.get("fresh", "").strip()
    if fresh == "不限": fresh = ""
    party = request.args.get("party", "").strip()
    if party == "不限": party = ""
    gender = request.args.get("gender", "").strip()
    if gender == "不限": gender = ""
    cats = request.args.getlist("cats[]")
    if not cats:
        cv = request.args.get("cats", "")
        if cv: cats = [cv]
    cats = [c for c in cats if c and c.strip() and c.strip() != "不限"]
    keyword = request.args.get("keyword", "").strip()
    sort = request.args.get("sort", "default")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    if per_page > 100: per_page = 100
    conn = get_db()
    c = conn.cursor()
    sql = "SELECT * FROM positions WHERE year = 2027"
    params = []
    if cities:
        ph = ",".join(["?"] * len(cities))
        sql += " AND city IN (" + ph + ")"
        params.extend(cities)
    if cats:
        ph = ",".join(["?"] * len(cats))
        sql += " AND exam_category IN (" + ph + ")"
        params.extend(cats)
    if edu:

        edu_map = {

            "本科": ["本科及以上", "本科"],

            "硕士研究生": ["硕士研究生", "研究生"],

            "博士研究生": ["博士研究生"],
            "高中（中专）": ["高中（中专）及以上"],

        }

        match_edus = edu_map.get(edu, [])

        if match_edus:

            ph = ",".join(["?"] * len(match_edus))

            sql += " AND education_req IN (" + ph + ")"

            params.extend(match_edus)

        else:

            sql += " AND 1=0"

    if fresh == "应届":
        sql += " AND requires_fresh = 1"
    elif fresh == "非应届":
        sql += " AND requires_fresh = 0"
    if party == "党员":
        sql += " AND requires_party = 1"
    elif party == "非党员":
        sql += " AND requires_party = 0"
    if gender == "男":
        sql += " AND requires_female = 0"
    elif gender == "女":
        sql += " AND requires_male = 0"
    if keyword:
        sql += " AND (unit_name LIKE ? OR position_name LIKE ?)"
        params.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if majors:
        # Build match conditions: exact + parenthetical variant + category expansion
        conditions = []
        cond_params = []
        cat_names = CAT_NAMES
        for mj in majors:
            mj = mj.strip()
            if not mj: continue
            # Exact match
            conditions.append("major_name = ?")
            cond_params.append(mj)
            # Parenthetical variant match (e.g., search category matches its qualified variants)
            conditions.append("major_name LIKE ?")
            cond_params.append(mj + "（%")
            conditions.append("major_name LIKE ?")
            cond_params.append(mj + "(%")
            # Category expansion: if search term matches a category name
            for cn in cat_names:
                if mj != cn and (mj in cn or cn.replace("类", "") == mj):
                    conditions.append("major_name = ?")
                    cond_params.append(cn)
                    conditions.append("major_name LIKE ?")
                    cond_params.append(cn + "（%")
                    conditions.append("major_name LIKE ?")
                    cond_params.append(cn + "(%")
        if conditions:
            where_clause = " OR ".join(conditions)
            pid_rows = c.execute("SELECT DISTINCT position_id FROM position_majors WHERE " + where_clause, cond_params).fetchall()
            major_pids = [r["position_id"] for r in pid_rows]
            if major_pids:
                ph = ",".join(["?"] * len(major_pids))
                sql += " AND id IN (" + ph + ")"
                params.extend(major_pids)
            else:
                sql += " AND 1=0"

    # === Optimized: combine count+sum into 1 query (was 2) ===
    agg_sql = "SELECT COUNT(*) as total, COALESCE(SUM(recruit_count), 0) as total_recruit FROM (" + sql + ")"
    arow = c.execute(agg_sql, params).fetchone()
    total = arow["total"]
    total_recruit_all = arow["total_recruit"]

    # Historical stats (1 query, kept as-is)
    hist_stats_sql = "SELECT AVG(CAST(h.applicants_count AS FLOAT) / CAST(h.recruit_count AS FLOAT)) as avg_ratio, AVG(h.score_min) as avg_score, COUNT(DISTINCT p.id) as cnt FROM (" + sql + ") p JOIN positions h ON p.match_key = h.match_key AND h.year < 2027 AND h.applicants_count IS NOT NULL WHERE h.recruit_count > 0"
    hrow = c.execute(hist_stats_sql, params).fetchone()
    avg_ratio_all = round(hrow["avg_ratio"], 1) if hrow["avg_ratio"] else None
    avg_score_all = round(hrow["avg_score"], 1) if hrow["avg_score"] else None
    with_history_all = hrow["cnt"]

    # Page query
    if sort == "recruit_desc":
        sql += " ORDER BY recruit_count DESC NULLS LAST"
    elif sort == "recruit_asc":
        sql += " ORDER BY recruit_count ASC NULLS LAST"
    else:
        sql += " ORDER BY unit_name, position_code"
    offset = (page - 1) * per_page
    sql += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    rows = c.execute(sql, params).fetchall()

    # Batch history lookup (1 query replaces N per-row queries)
    match_keys = [r["match_key"] for r in rows if r["match_key"]]
    hist_map = {}
    if match_keys:
        mk_ph = ",".join(["?"] * len(match_keys))
        hist_sql = (
            "SELECT match_key, year, applicants_count, recruit_count, score_min, score_max FROM ("
            "SELECT match_key, year, applicants_count, recruit_count, score_min, score_max, "
            "ROW_NUMBER() OVER (PARTITION BY match_key ORDER BY year DESC) as rn "
            "FROM positions WHERE match_key IN (" + mk_ph + ") AND year < 2027 AND applicants_count IS NOT NULL"
            ") WHERE rn = 1"
        )
        hist_rows = c.execute(hist_sql, match_keys).fetchall()
        for h in hist_rows:
            cr = None
            if h["applicants_count"] and h["recruit_count"] and h["recruit_count"] > 0:
                cr = round(h["applicants_count"] / h["recruit_count"], 1)
            hist_map[h["match_key"]] = {
                "year": h["year"], "applicants": h["applicants_count"],
                "competition_ratio": cr, "score_min": h["score_min"], "score_max": h["score_max"]
            }

    # Build results
    results = []
    for row in rows:
        pos = dict(row)
        mk = pos.get("match_key", "")
        pos["hist_summary"] = hist_map.get(mk)
        mr = pos.get("major_req", "")
        mlist = [x for x in re.split("[，,、；;]", mr) if x.strip()] if mr else []
        pos["major_count"] = len(mlist)
        pos["major_req_short"] = (mr[:60] + "...") if mr and len(mr) > 60 else mr
        results.append(pos)
    stats = {"total": total, "page": page, "per_page": per_page, "actual_count": len(results)}
    stats["total_recruit"] = total_recruit_all
    stats["avg_ratio"] = avg_ratio_all
    stats["avg_score"] = avg_score_all
    stats["with_history"] = with_history_all
    conn.close()
    return jsonify({"results": results, "stats": stats})

@app.route("/api/detail/<int:pid>")
def api_detail(pid):
    conn = get_db()
    c = conn.cursor()
    pos = c.execute("SELECT * FROM positions WHERE id = ?", (pid,)).fetchone()
    if not pos:
        conn.close()
        return jsonify({"error": "not found"}), 404
    pos = dict(pos)
    mk = pos.get("match_key", "")
    history = []
    if mk:
        hrows = c.execute("SELECT * FROM positions WHERE match_key = ? AND year < 2027 AND applicants_count IS NOT NULL GROUP BY year ORDER BY year DESC", (mk,)).fetchall()
        for h in hrows:
            h = dict(h)
            cr = None
            if h["applicants_count"] and h["recruit_count"] and h["recruit_count"] > 0:
                cr = round(h["applicants_count"] / h["recruit_count"], 1)
            history.append({"year": h["year"], "applicants_count": h["applicants_count"],
                "recruit_count": h["recruit_count"], "competition_ratio": cr,
                "score_max": h["score_max"], "score_min": h["score_min"], "match_level": "精确匹配"})
    if not history and pos.get("unit_name") and pos.get("position_name"):
        hrows = c.execute("SELECT * FROM positions WHERE unit_name = ? AND position_name = ? AND year < 2027 AND applicants_count IS NOT NULL GROUP BY year ORDER BY year DESC", (pos["unit_name"], pos["position_name"])).fetchall()
        for h in hrows:
            h = dict(h)
            cr = None
            if h["applicants_count"] and h["recruit_count"] and h["recruit_count"] > 0:
                cr = round(h["applicants_count"] / h["recruit_count"], 1)
            history.append({"year": h["year"], "applicants_count": h["applicants_count"],
                "recruit_count": h["recruit_count"], "competition_ratio": cr,
                "score_max": h["score_max"], "score_min": h["score_min"], "match_level": "名称匹配"})
    same_unit = []
    if pos.get("unit_name"):
        srows = c.execute("SELECT id, position_name, recruit_count, education_req, exam_category FROM positions WHERE unit_name = ? AND year = 2027 AND id != ? LIMIT 10", (pos["unit_name"], pid)).fetchall()
        for s in srows:
            same_unit.append(dict(s))
    conn.close()
    return jsonify({"position": pos, "history": history, "same_unit_positions": same_unit})

@app.route("/api/major/suggest")
def api_major_suggest():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"suggestions": []})
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""
        SELECT mc.major_name, mc.major_category, mc.is_category,
               COUNT(DISTINCT pm.position_id) as pos_count
        FROM major_catalog mc
        JOIN position_majors pm ON mc.major_name = pm.major_name
        JOIN positions p ON pm.position_id = p.id
        WHERE p.year = 2027 AND mc.major_name LIKE ?
        GROUP BY mc.major_name, mc.major_category, mc.is_category
        ORDER BY pos_count DESC, mc.major_name
        LIMIT 20
    """, ("%" + q + "%",)).fetchall()
    conn.close()
    return jsonify({"suggestions": [dict(r) for r in rows]})

@app.route("/api/stats")
def api_stats():
    conn = get_db()
    c = conn.cursor()
    t27 = c.execute("SELECT COUNT(*) as cnt FROM positions WHERE year = 2027").fetchone()["cnt"]
    th = c.execute("SELECT COUNT(*) as cnt FROM positions WHERE year < 2027").fetchone()["cnt"]
    years = [r["year"] for r in c.execute("SELECT DISTINCT year FROM positions ORDER BY year").fetchall()]
    cc = c.execute("SELECT COUNT(DISTINCT city) as cnt FROM positions WHERE city IS NOT NULL").fetchone()["cnt"]
    cities = [r["city"] for r in c.execute("SELECT DISTINCT city FROM positions WHERE year = 2027 AND city IS NOT NULL ORDER BY city").fetchall()]
    edus = [r["education_req"] for r in c.execute("SELECT DISTINCT education_req FROM positions WHERE year = 2027 AND education_req IS NOT NULL ORDER BY education_req").fetchall()]
    conn.close()
    return jsonify({"total_positions_2027": t27, "total_positions_history": th,
        "year_coverage": years, "city_count": cc, "cities": cities, "education_options": edus})

@app.route("/api/favorites", methods = ["GET", "POST", "DELETE"])
def api_favorites():
    conn = get_db()
    c = conn.cursor()
    if request.method == "GET":
        rows = c.execute("SELECT f.id as fid, f.note, f.created_at, p.* FROM favorites f JOIN positions p ON f.position_id = p.id ORDER BY f.created_at DESC").fetchall()
        conn.close()
        return jsonify({"favorites": [dict(r) for r in rows]})
    elif request.method == "POST":
        data = request.get_json()
        pid = data.get("position_id")
        note = data.get("note", "")
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO favorites (position_id, note, created_at) VALUES (?, ?, ?)", (pid, note, ts))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    elif request.method == "DELETE":
        fid = request.args.get("id")
        c.execute("DELETE FROM favorites WHERE id = ?", (fid,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})

@app.route("/")
def index():
    return send_from_directory(STATIC, "index.html")

if __name__ == "__main__":
    print("Starting server on http://localhost:5000")
    app.run(host = "0.0.0.0", port = 5000, debug = True)

