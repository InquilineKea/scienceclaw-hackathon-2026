#!/usr/bin/env python3
"""Bounded multi-agent research team on one shared benchmark, with code-adjudicated validation.

Question: does clustered AGE crosslinking reduce damage tolerance because it blocks sliding, concentrates
load, or changes hydration? Plus two backlog gaps: independent validation of the phase map, and measured
anchors for fibril parameters and the force -> YAP response.

Division of labour
  * Gemini agents (Vertex AI, the hackathon project) only PROPOSE: hypotheses, signed predictions, and which
    whitelisted solver job to run with which parameters (team/jobs.py SCHEMA; values are clamped there).
  * Deterministic code runs every calculation on the GCP VM and decides every verdict. Paired seeds; the
    clustered and dispersed arms share a base network and crosslink count.
  * A finding is registered `verified` in experiments/registry.db only when a DIFFERENT calculation agrees
    (autograd linear-response G, closed-form fibril limits) AND the validator agent's falsification runs do
    not flip it. Agents agreeing counts for nothing.

  python3 team/team.py run [--max-calls 40] [--rounds 2]        # needs `gcloud --configuration=scienceclaw` login
Writes team/runs/<run>/ (tasks, results, decisions, raw agent records) and team/runs/<run>/REPORT.md.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "experiments"))
import jobs  # noqa: E402
import registry  # noqa: E402

PROJECT, LOCATION = "scienceclaw26bos-3008", "global"
FAST, DEEP = "gemini-3.6-flash", "gemini-4-argon"
VM = dict(user="oxt", key=str(Path.home() / ".ssh/sclaw_gcp_ed25519"), instance="oxt-cpu32", zone="us-central1-a")
REMOTE_DIR = "team-20261031"
WORKERS = 30
QUESTION = ("Does clustered AGE crosslinking reduce collagen damage tolerance because it (a) blocks intermolecular "
            "sliding, (b) concentrates load in the fibre network, or (c) changes hydration/fluid flow? Comparisons "
            "must separately control fibre content, microscopic crosslink stiffness, and initial bulk stiffness.")
METRICS = {"cluster_network": ["work_to_peak", "strain_at_peak", "strength", "max_avalanche", "G", "strain_p99_over_mean"],
           "fibril_sliding": ["work", "U_fail", "peak_force", "sliding_dissipation"]}
ROLES = {
    "architecture": "You are the ARCHITECTURE agent. You test mechanism (b): clustered vs dispersed crosslinks in the "
                    "fibre network (connectivity, load concentration, defects). Use job cluster_network. Use all three "
                    "controls across your experiments (count, no_bridge, bulk_G) because they are different experiments.",
    "sliding": "You are the SLIDING/FAILURE agent. You test mechanism (a): whether AGEs reduce damage tolerance by "
               "blocking intermolecular sliding, distinguishing higher stiffness from suppressed sliding and altered "
               "rupture thresholds. Use job fibril_sliding; choose AGE count, crosslink stiffness and rupture slip so "
               "that some conditions put interface strength above and some below molecular strength F_m.",
    "hydration": "You are the HYDRATION agent. You test mechanism (c): whether fluid flow could explain relaxation or "
                 "damage effects attributed elsewhere. Use job poro_timescale with literature-range parameters for "
                 "collagen gels, tendon/skin and cartilage, at physiological and test loading times.",
}
VALIDATOR = ("You are the INDEPENDENT VALIDATION agent. Your job is to try to FALSIFY each finding with separate "
             "calculations: larger or different lattice size, different cluster number, different z, fresh seeds, or "
             "different parameters where the claimed direction should still hold if the mechanism is real. You do not "
             "decide verdicts; code compares numbers.")
EVIDENCE = [
    ("fibril-parameters", "For a biomechanics literature review, list published values with DOIs for: type I collagen "
     "molecule Young's modulus and tensile strength; intermolecular shear/sliding strength in collagen fibrils; enzymatic and AGE crosslink "
     "rupture force; glucosepane and pentosidine content per collagen molecule in young vs aged human skin or tendon; "
     "collagen gel/tendon/cartilage permeability (m^2) and aggregate modulus."),
    ("force-yap", "Find measured dose-response curves of YAP/TAZ nuclear-to-cytoplasmic ratio versus substrate stiffness "
     "(kPa) or traction force, with DOIs: the stiffness at half-maximal nuclear YAP, Hill coefficient or curve shape, cell "
     "type, 2D vs 3D, and whether collagen or hydrogel substrates were used."),
]


# ---------------------------------------------------------------- Gemini (Vertex AI, gcloud login; no API key)

class Budget:
    def __init__(self, max_calls):
        self.max_calls, self.calls, self.tokens = max_calls, 0, 0


def _token():
    return subprocess.run(["gcloud", "--configuration=scienceclaw", "auth", "print-access-token"],
                          capture_output=True, text=True, check=True).stdout.strip()


def gemini(budget, run_dir, tag, system, user, model=FAST, json_mode=True, search=False):
    if budget.calls >= budget.max_calls:
        raise RuntimeError("agent call budget exhausted")
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 32768}}
    if json_mode and not search:
        body["generationConfig"]["responseMimeType"] = "application/json"
    if search:
        body["tools"] = [{"googleSearch": {}}]
    r, m = {}, model
    for m in (model, FAST, FAST):  # requested model, then up to two retries on the fast model
        if budget.calls >= budget.max_calls:
            break
        url = (f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}/publishers/google/"
               f"models/{m}:generateContent")
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Authorization": "Bearer " + _token(), "Content-Type": "application/json"})
        budget.calls += 1
        try:
            r = json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e:
            r = dict(error=e.code, body=e.read()[:500].decode(errors="replace"))
        if r.get("candidates") and r["candidates"][0].get("content", {}).get("parts"):
            break
        (run_dir / "agents").mkdir(exist_ok=True)
        (run_dir / "agents" / f"{budget.calls:03d}-{tag}-EMPTY.json").write_text(json.dumps(r, indent=1)[:20000])
    if not r.get("candidates"):
        return {} if json_mode else ""
    text = "".join(p.get("text", "") for p in r["candidates"][0]["content"].get("parts", []))
    budget.tokens += r.get("usageMetadata", {}).get("totalTokenCount", 0)
    rec = dict(tag=tag, model=m, system=system, user=user, text=text,
               grounding=r["candidates"][0].get("groundingMetadata"), usage=r.get("usageMetadata"))
    (run_dir / "agents").mkdir(exist_ok=True)
    (run_dir / "agents" / f"{budget.calls:03d}-{tag}.json").write_text(json.dumps(rec, indent=1))
    if not json_mode:
        return text
    m_ = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m_.group(0) if m_ else text)
    except json.JSONDecodeError:
        return {}


def menu():
    return json.dumps({k: {p: (v if isinstance(v, list) else {"min": v[0], "max": v[1], "default": v[2]})
                           for p, v in s.items()} for k, s in jobs.SCHEMA.items()
                       if k in ("cluster_network", "fibril_sliding", "poro_timescale")}, indent=1) + "\n\n" + jobs.__doc__


PROPOSE_FMT = """Return JSON: {"experiments": [ {"name": "short-slug", "hypothesis": "...", "job": "<job>",
 "fixed": {param: value}, "vary": {"param": "<one param name or empty>", "values": [up to 5 values]},
 "seeds": <2..8>, "metric": "<one metric>", "prediction": "clustered_lower" | "clustered_higher" | "no_difference",
 "why": "one sentence"} ]}  -- at most %d experiments. Placement (dispersed vs clustered) is added automatically as
a paired comparison with shared seeds; do not vary it. For poro_timescale, give "regime_prediction" instead of
metric/prediction and list parameter sets in "vary" over a single parameter. Metrics: %s."""


# ---------------------------------------------------------------- task expansion and VM execution

def expand(exp, prefix):
    job = exp["job"]
    vary = exp.get("vary") or {}
    pname, values = vary.get("param") or None, (vary.get("values") or [None])[: 3 if job == "cluster_network" else 5]
    seeds = int(min(max(int(exp.get("seeds", 4)), 2), 8)) if job != "poro_timescale" else 1
    seed0 = int(exp.get("seed0", 9000))
    tasks = []
    arms = ["dispersed", "clustered"] if job in METRICS else [None]
    for vi, v in enumerate(values):
        for s in range(seeds):
            for arm in arms:
                p = dict(exp.get("fixed") or {})
                if pname:
                    p[pname] = v
                if job in METRICS:
                    p.update(placement=arm, seed=seed0 + s)
                tasks.append(dict(task_id=f"{prefix}:{vi}:{s}:{arm}", job=job, params=jobs.clamp(job, p),
                                  exp=prefix, value_index=vi, value=v, seed_index=s, arm=arm))
    return tasks


def vm_ip():
    return subprocess.run(["gcloud", "--configuration=scienceclaw", "compute", "instances", "describe", VM["instance"],
                           "--zone", VM["zone"], "--format=value(networkInterfaces[0].accessConfigs[0].natIP)"],
                          capture_output=True, text=True, check=True).stdout.strip()


def ssh(ip, cmd, **kw):
    return subprocess.run(["ssh", "-i", VM["key"], "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
                           f"{VM['user']}@{ip}", cmd], capture_output=True, text=True, **kw)


def run_on_vm(run_dir, name, tasks):
    """Ship code + task list, run jobs.py with WORKERS processes in the reviewed venv, fetch results."""
    ip = vm_ip()
    (run_dir / f"{name}.tasks.json").write_text(json.dumps([{k: t[k] for k in ("task_id", "job", "params")} for t in tasks]))
    subprocess.run(["rsync", "-a", "-e", f"ssh -i {VM['key']} -o BatchMode=yes", "--include=oxt/***", "--include=team/",
                    "--include=team/jobs.py", "--exclude=*", f"{ROOT}/", f"{VM['user']}@{ip}:{REMOTE_DIR}/"], check=True)
    subprocess.run(["rsync", "-a", "-e", f"ssh -i {VM['key']} -o BatchMode=yes", str(run_dir / f"{name}.tasks.json"),
                    f"{VM['user']}@{ip}:{REMOTE_DIR}/"], check=True)
    out = f"{name}.out.jsonl"
    ssh(ip, f"cd {REMOTE_DIR}; setsid nohup ~/v/bin/python3 team/jobs.py run {name}.tasks.json {out} --workers {WORKERS} "
            f"> {name}.log 2>&1 < /dev/null & disown", timeout=60)
    while True:
        time.sleep(60)
        r = ssh(ip, f"cd {REMOTE_DIR} && (wc -l < {out} 2>/dev/null || echo 0); tail -1 {name}.log")
        lines = r.stdout.split("\n")
        n = int(lines[0].strip() or 0) if lines and lines[0].strip().isdigit() else 0
        print(f"  [{name}] {n}/{len(tasks)}", flush=True)
        if n >= len(tasks) or "Traceback" in r.stdout:
            break
    subprocess.run(["rsync", "-a", "-e", f"ssh -i {VM['key']} -o BatchMode=yes", f"{VM['user']}@{ip}:{REMOTE_DIR}/{out}",
                    str(run_dir)], check=True)
    res = {}
    for line in (run_dir / out).read_text().splitlines():
        d = json.loads(line)
        res[d["task_id"]] = d
    return res


# ---------------------------------------------------------------- adjudication (code only)

def evaluate(exp, tasks, res):
    """Paired clustered-minus-dispersed differences per varied value; verdict from the sign pattern."""
    job = exp["job"]
    if job == "poro_timescale":
        rows = [dict(value=t["value"], **{k: res[t["task_id"]]["result"].get(k) for k in ("tau_drain_s", "deborah", "regime")})
                for t in tasks if res.get(t["task_id"], {}).get("ok")]
        return dict(rows=rows, verdict="computed (analytic scale estimate)")
    metric = exp.get("metric") if exp.get("metric") in METRICS[job] else METRICS[job][0]
    pred = exp.get("prediction", "clustered_lower")
    rows, verdicts = [], []
    for vi in sorted({t["value_index"] for t in tasks}):
        d, base = [], []
        for t in tasks:
            if t["value_index"] != vi or t["arm"] != "clustered":
                continue
            a = res.get(t["task_id"].replace(":clustered", ":dispersed"), {})
            b = res.get(t["task_id"], {})
            if a.get("ok") and b.get("ok"):
                d.append(b["result"][metric] - a["result"][metric])
                base.append(a["result"][metric])
        d = np.array(d, float)
        if d.size == 0:
            rows.append(dict(value=t["value"], n=0))
            continue
        frac_neg, frac_pos = float((d < 0).mean()), float((d > 0).mean())
        rel = float(d.mean() / (abs(np.mean(base)) + 1e-300))
        if pred == "no_difference":
            v = "supported" if abs(rel) < 0.05 else "contradicted" if max(frac_neg, frac_pos) >= 0.75 and abs(rel) >= 0.1 else "inconclusive"
        else:
            hit = frac_neg if pred == "clustered_lower" else frac_pos
            miss = frac_pos if pred == "clustered_lower" else frac_neg
            v = ("supported" if hit >= 0.75 and d.size >= 3 else "contradicted" if miss >= 0.75 and d.size >= 3
                 else "inconclusive")
        verdicts.append(v)
        rows.append(dict(value=next(t["value"] for t in tasks if t["value_index"] == vi), n=int(d.size),
                         mean_diff=float(d.mean()), rel_effect=rel, frac_clustered_lower=frac_neg, verdict=v))
    overall = ("supported" if verdicts and all(v == "supported" for v in verdicts) else
               "contradicted" if verdicts and all(v == "contradicted" for v in verdicts) else
               "mixed" if verdicts else "no data")
    return dict(metric=metric, prediction=pred, rows=rows, verdict=overall)


def cross_solver_tasks(exp, tasks, res, prefix):
    """Different-calculation checks chosen by rule, not by an agent."""
    out = []
    if exp["job"] == "cluster_network":
        pick = [t for t in tasks if res.get(t["task_id"], {}).get("ok") and (t["params"]["control"] != "bulk_G" or t["arm"] == "dispersed")][:6]
        for t in pick:
            p = {k: t["params"][k] for k in ("W", "z", "dose", "seed", "placement", "n_clusters", "control")}
            out.append(dict(task_id=f"{prefix}:xs:{t['task_id']}", job="network_linear_G", params=jobs.clamp("network_linear_G", p),
                            ref=t["task_id"], check="G"))
    elif exp["job"] == "fibril_sliding":
        t = tasks[0]
        p = dict(t["params"], n_age=0)
        out.append(dict(task_id=f"{prefix}:xs:noage-num", job="fibril_sliding", params=jobs.clamp("fibril_sliding", p), check="pair"))
        out.append(dict(task_id=f"{prefix}:xs:noage-ana", job="fibril_analytic",
                        params=jobs.clamp("fibril_analytic", {k: v for k, v in p.items() if k in jobs.SCHEMA["fibril_analytic"]}),
                        check="pair"))
    return out


def judge_cross(exp, tasks, res, xs, xres):
    notes, ok = [], True
    if exp["job"] == "cluster_network":
        for x in xs:
            a, b = res[x["ref"]]["result"]["G"], xres.get(x["task_id"], {}).get("result", {}).get("G")
            if b is None:
                ok = False
                notes.append(f"{x['ref']}: linear-response G failed")
                continue
            rel = abs(a - b) / max(abs(b), 1e-12)
            ok &= rel <= 0.03
            notes.append(f"G relax {a:.4g} vs linear-response {b:.4g} (rel {rel:.1%})")
        if exp.get("fixed", {}).get("control") == "bulk_G":
            for t in tasks:
                if t["arm"] == "clustered" and res.get(t["task_id"], {}).get("ok"):
                    a = res.get(t["task_id"].replace(":clustered", ":dispersed"), {}).get("result", {}).get("G")
                    b = res[t["task_id"]]["result"]["G"]
                    if a:
                        ok &= abs(a - b) / a <= 0.05
            notes.append("bulk_G matching checked: clustered G within 5% of dispersed G in every pair" if ok else
                         "bulk_G matching failed in at least one pair")
    elif exp["job"] == "fibril_sliding":
        num = xres.get(f"{exp['_prefix']}:xs:noage-num", {}).get("result", {})
        ana = xres.get(f"{exp['_prefix']}:xs:noage-ana", {}).get("result", {})
        for k in ("peak_force", "work"):
            if k in ana and k in num:
                rel = abs(num[k] - ana[k]) / max(abs(ana[k]), 1e-12)
                ok &= rel <= 0.01
                notes.append(f"no-AGE {k}: numeric {num[k]:.4g} vs closed form {ana[k]:.4g} (rel {rel:.2%})")
        Fm = tasks[0]["params"]["F_m"]
        bound = all(res[t["task_id"]]["result"]["peak_force"] <= max(Fm, tasks[0]["params"]["F_y"]) * 1.02
                    for t in tasks if res.get(t["task_id"], {}).get("ok"))
        ok &= bound
        notes.append("peak force never exceeds molecular strength bound" if bound else "peak force exceeded the F_m bound")
    return ok, notes


def phase_map_backlog(prefix):
    """Rebuild exact phase-map networks (healthy and LOX-locked series) and recompute G by linear response."""
    import pandas as pd
    df = pd.read_csv(ROOT / "results/phase/cpu32.csv")
    df = df[(df["dose"] == 0) & df["z_target"].isin([3.1, 3.4, 3.7, 4.0, 4.3, 5.0])]
    out = []
    for _, r in df.iterrows():
        p = dict(W=12, z=float(r["z_target"]), dose=0.0, lock=float(r["lock"]), seed=int(r["seed"]), placement="none")
        out.append(dict(task_id=f"{prefix}:{r['seed']}:{r['z_target']}:{r['lock']}", job="network_linear_G",
                        params=jobs.clamp("network_linear_G", p), ref_G=float(r["G"])))
    return out


def crossref(doi):
    try:
        req = urllib.request.Request(f"https://api.crossref.org/works/{urllib.request.quote(doi)}",
                                     headers={"User-Agent": "scienceclaw-team/0.1 (research)"})
        d = json.load(urllib.request.urlopen(req, timeout=30))["message"]
        return dict(resolved=True, title=(d.get("title") or [""])[0], year=(d.get("issued", {}).get("date-parts") or [[None]])[0][0])
    except Exception as e:
        return dict(resolved=False, error=type(e).__name__)


# ---------------------------------------------------------------- the run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--max-calls", type=int, default=40)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--per-agent", type=int, default=3)
    a = ap.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = HERE / "runs" / stamp
    run_dir.mkdir(parents=True)
    budget = Budget(a.max_calls)
    conn = registry.connect()
    log = dict(run=stamp, question=QUESTION, experiments=[], evidence=[], backlog={}, rounds=[])
    save = lambda: (run_dir / "decisions.json").write_text(json.dumps(log, indent=1, default=str))

    # --- evidence (molecular agent), grounded search; DOIs checked against Crossref by code
    for tag, q in EVIDENCE:
        txt = gemini(budget, run_dir, f"molecular-{tag}", "You are a biomaterials literature curator helping decide which published "
                     "tissue-mechanics parameters can transfer into a fibril or network model. Prefer primary measurements. "
                     "Never invent values or DOIs; write 'not found' instead.",
                     q + '\nReturn ONLY a JSON object {"rows": [{"quantity", "value", "unit", "system", "method", '
                     '"doi", "transferable_to": "fibril|network|cell|none", "caveat"}]} with at most 14 rows.',
                     json_mode=False, search=True)
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            rows = json.loads(m.group(0))["rows"] if m else []
        except (json.JSONDecodeError, KeyError):
            rows = [dict(quantity="unparsed agent output", value=None, doi=None, caveat=txt[:300])]
        for r in rows:
            doi = str(r.get("doi") or "").strip().removeprefix("https://doi.org/")
            r["crossref"] = crossref(doi) if doi.startswith("10.") else dict(resolved=False, error="no DOI")
        log["evidence"].append(dict(tag=tag, rows=rows))
        save()

    # --- backlog: independent validation of the phase map (rule-based, no agent needed)
    bl = phase_map_backlog("backlog-phase")
    bres = run_on_vm(run_dir, "backlog", bl)
    rel = [abs(bres[t["task_id"]]["result"]["G"] - t["ref_G"]) / max(abs(bres[t["task_id"]]["result"]["G"]), 1e-12)
           for t in bl if bres.get(t["task_id"], {}).get("ok")]
    by_z = {}
    for t in bl:
        if bres.get(t["task_id"], {}).get("ok"):
            g = bres[t["task_id"]]["result"]["G"]
            by_z.setdefault((t["params"]["z"], t["params"]["lock"]), []).append(abs(g - t["ref_G"]) / max(abs(g), 1e-12))
    log["backlog"] = dict(n=len(rel), within_3pct=float(np.mean(np.array(rel) <= 0.03)) if rel else None,
                          median_rel=float(np.median(rel)) if rel else None,
                          worst_by_z_lock={f"z{k[0]}_lock{k[1]}": float(max(v)) for k, v in sorted(by_z.items())})
    save()

    # --- mechanism rounds
    history = []
    for rnd in range(a.rounds):
        summary = json.dumps([dict(id=e["id"], agent=e["agent"], hypothesis=e["hypothesis"], job=e["job"],
                                   fixed=e.get("fixed"), vary=e.get("vary"), result=e["result"], status=e["status"])
                              for e in history], default=str)[:30000]
        proposals = []
        for role, sysmsg in ROLES.items():
            js = gemini(budget, run_dir, f"r{rnd}-{role}", sysmsg,
                        f"QUESTION: {QUESTION}\n\nJOB MENU:\n{menu()}\n\nRESULTS SO FAR (code-adjudicated):\n{summary or 'none'}\n\n"
                        + PROPOSE_FMT % (a.per_agent if rnd == 0 else 2, METRICS))
            for e in js.get("experiments", [])[: a.per_agent]:
                if e.get("job") not in ("cluster_network", "fibril_sliding", "poro_timescale"):
                    continue
                if role == "architecture" and e["job"] != "cluster_network" or role == "sliding" and e["job"] != "fibril_sliding":
                    continue
                e["agent"] = role
                proposals.append(e)
        tasks, net_budget = [], 150
        for k, e in enumerate(proposals):
            e["id"] = f"team-{stamp}-r{rnd}-{e['agent']}-{k}-{re.sub('[^a-z0-9-]', '', str(e.get('name', 'x')).lower())[:24]}"
            e["_prefix"] = e["id"]
            e["tasks"] = expand(e, e["id"])
            n_net = sum(t["job"] == "cluster_network" for t in e["tasks"])
            if n_net > net_budget:
                e["skipped"] = "network task budget for this round exhausted"
                continue
            net_budget -= n_net
            tasks += e["tasks"]
            calc = {"cluster_network": "oxt L-BFGS relaxation failure_curve", "fibril_sliding": "series-chain bisection fibril",
                    "poro_timescale": "Biot scale estimate"}[e["job"]]
            try:
                registry.add_experiment(conn, e["id"], e.get("hypothesis", "")[:800], params=dict(
                    calculation=calc, job=e["job"], fixed=e.get("fixed"), vary=e.get("vary"), metric=e.get("metric"),
                    prediction=e.get("prediction"), agent=e["agent"], run=stamp), seeds=list(range(int(e.get("seeds", 4)))),
                    result_location=str(run_dir.relative_to(ROOT)))
                registry.claim_experiment(conn, e["id"], "Claude Code team.py, GCP oxt-cpu32", "claimed")
                registry.claim_experiment(conn, e["id"], "Claude Code team.py, GCP oxt-cpu32", "running")
            except registry.RegistryError as err:
                e["registry_error"] = str(err)
        net = sum(t["job"] == "cluster_network" for t in tasks)
        proposals = [e for e in proposals if "skipped" not in e]
        print(f"round {rnd}: {len(proposals)} experiments, {len(tasks)} tasks ({net} network)", flush=True)
        res = run_on_vm(run_dir, f"r{rnd}", tasks)
        for e in proposals:
            e["result"] = evaluate(e, e["tasks"], res)
            try:
                registry.claim_experiment(conn, e["id"], "Claude Code team.py, GCP oxt-cpu32", "done")
            except registry.RegistryError as err:
                e["registry_error"] = str(err)
            e["status"] = "done"

        # --- validation: rule-based cross-solver checks + validator-proposed falsification runs
        mech = [e for e in proposals if e["job"] in METRICS]
        xs = [x for e in mech for x in cross_solver_tasks(e, e["tasks"], res, e["id"])]
        val = gemini(budget, run_dir, f"r{rnd}-validator", VALIDATOR,
                     f"QUESTION: {QUESTION}\n\nJOB MENU:\n{menu()}\n\nFINDINGS:\n" +
                     json.dumps([dict(id=e["id"], job=e["job"], fixed=e.get("fixed"), vary=e.get("vary"), seeds=e.get("seeds"),
                                      metric=e["result"].get("metric"), prediction=e.get("prediction"), result=e["result"])
                                 for e in mech], default=str)[:30000] +
                     '\n\nReturn JSON {"falsify": [{"target": "<finding id>", "change": {param: value}, "seeds": <2..8>, '
                     '"seed0": <integer >= 20000>, "why": "..."}]}, at most one per finding. The finding\'s metric and '
                     'prediction are kept; only the parameters you change differ.')
        fals = []
        for f in val.get("falsify", []):
            e = next((x for x in mech if x["id"] == f.get("target")), None)
            if not e:
                continue
            fe = dict(e, fixed=dict(e.get("fixed") or {}, **(f.get("change") or {})), seeds=min(int(f.get("seeds", 4)), 4),
                      seed0=max(int(f.get("seed0", 20000)), 20000), why=f.get("why"))
            fe["_prefix"] = e["id"] + ":F"
            fe["tasks"] = expand(fe, fe["_prefix"])
            e["falsification"] = dict(change=f.get("change"), why=f.get("why"))
            fals.append((e, fe))
        vres = run_on_vm(run_dir, f"r{rnd}-validate", xs + [t for _, fe in fals for t in fe["tasks"]])
        for e in mech:
            ok, notes = judge_cross(e, e["tasks"], res, [x for x in xs if x["task_id"].startswith(e["id"] + ":xs")], vres)
            e["cross_solver"] = dict(passed=bool(ok), notes=notes)
        for e, fe in fals:
            e["falsification"]["result"] = evaluate(fe, fe["tasks"], vres)
        for e in mech:
            v0 = e["result"]["verdict"]
            v1 = e.get("falsification", {}).get("result", {}).get("verdict")
            try:
                if v0 in ("supported", "contradicted") and e["cross_solver"]["passed"] and v1 == v0:
                    registry.verify_experiment(conn, e["id"], "autograd linear-response G / closed-form fibril limits + "
                                               "validator falsification rerun", f"prediction {v0}; cross-solver: "
                                               + "; ".join(e["cross_solver"]["notes"][:4]) + f"; falsification ({e['falsification']['change']}) "
                                               f"gave the same verdict", by="Claude Code team.py")
                    e["status"] = "verified"
                elif v0 in ("supported", "contradicted") and v1 and v1 not in (v0, "mixed", "inconclusive", "no data"):
                    registry.refute_experiment(conn, e["id"], f"falsification rerun ({e['falsification']['change']}) "
                                               f"reversed the verdict: {v0} -> {v1}", by="Claude Code team.py")
                    e["status"] = "refuted"
            except registry.RegistryError as err:
                e["registry_error"] = str(err)
        for e in proposals:
            e.pop("tasks", None)
        history += proposals
        log["experiments"] = history
        log["rounds"].append(dict(round=rnd, n_experiments=len(proposals), n_tasks=len(tasks)))
        save()

    # --- synthesis: interpretation only; every number comes from decisions.json
    syn = gemini(budget, run_dir, "synthesis", "You are the SYNTHESIS agent. Interpret only what the code-adjudicated "
                 "results show. Name experiment ids. Say which of mechanisms (a) sliding, (b) load concentration, "
                 "(c) hydration the evidence favours, which controls matter, what remains unvalidated, and the next "
                 "calculation. Do not introduce numbers that are not in the input. Under 450 words, markdown.",
                 json.dumps(dict(question=QUESTION, backlog=log["backlog"], experiments=[
                     {k: e.get(k) for k in ("id", "agent", "hypothesis", "job", "fixed", "vary", "prediction", "result",
                                            "cross_solver", "falsification", "status")} for e in history],
                     evidence=log["evidence"]), default=str)[:60000], model=DEEP, json_mode=False)
    log["synthesis"] = syn
    log["budget"] = dict(calls=budget.calls, tokens=budget.tokens)
    save()
    write_report(run_dir, log)
    print(f"report: {run_dir / 'REPORT.md'}  calls={budget.calls} tokens={budget.tokens}")


def write_report(run_dir, log):
    L = [f"# Agent-team run {log['run']}", "", f"**Question.** {log['question']}", "",
         "Agents proposed; deterministic code on the GCP VM computed and adjudicated. Raw agent records: `agents/`.", "",
         "## Backlog: phase-map shear modulus by an independent calculation", "",
         f"{log['backlog'].get('n')} networks rebuilt exactly; autograd linear-response G vs the L-BFGS finite-strain G "
         f"from `results/phase/cpu32.csv`: {log['backlog'].get('within_3pct', 0):.0%} within 3%, median difference "
         f"{log['backlog'].get('median_rel', 0):.2%}.", "", "| z, lock | worst relative difference |", "|---|---|"]
    L += [f"| {k} | {v:.2%} |" for k, v in log["backlog"].get("worst_by_z_lock", {}).items()]
    L += ["", "## Mechanism experiments (paired clustered − dispersed, shared seeds)", "",
          "| id | agent | job / control | metric | prediction | verdict | cross-solver | falsification | registry |",
          "|---|---|---|---|---|---|---|---|---|"]
    for e in log["experiments"]:
        r = e.get("result", {})
        ctl = (e.get("fixed") or {}).get("control", "") if e["job"] == "cluster_network" else ""
        L.append(f"| `{e['id']}` | {e['agent']} | {e['job']} {ctl} | {r.get('metric', '')} | {e.get('prediction', e.get('regime_prediction', ''))} | "
                 f"{r.get('verdict')} | {'pass' if e.get('cross_solver', {}).get('passed') else ('fail' if 'cross_solver' in e else '—')} | "
                 f"{e.get('falsification', {}).get('result', {}).get('verdict', '—')} | {e.get('status')} |")
    L += ["", "### Per-condition effects", ""]
    for e in log["experiments"]:
        L.append(f"**`{e['id']}`** — {e.get('hypothesis', '')}  ")
        L.append(f"vary `{(e.get('vary') or {}).get('param')}`; fixed `{json.dumps(e.get('fixed'))}`")
        for row in e.get("result", {}).get("rows", []):
            L.append("- " + ", ".join(f"{k}={v:.3g}" if isinstance(v, float) else f"{k}={v}" for k, v in row.items()))
        for n in e.get("cross_solver", {}).get("notes", [])[:3]:
            L.append(f"- cross-solver: {n}")
        L.append("")
    L += ["## Evidence (grounded search; DOI existence checked against Crossref, values NOT checked)", ""]
    for ev in log["evidence"]:
        L += [f"### {ev['tag']}", "", "| quantity | value | unit | system | DOI | Crossref |", "|---|---|---|---|---|---|"]
        for r in ev["rows"]:
            c = r.get("crossref", {})
            L.append(f"| {r.get('quantity')} | {r.get('value')} | {r.get('unit')} | {r.get('system')} | {r.get('doi')} | "
                     f"{'✓ ' + str(c.get('title', ''))[:60] if c.get('resolved') else '✗ ' + str(c.get('error'))} |")
        L.append("")
    L += ["## Synthesis agent (interpretation only)", "", log.get("synthesis", ""), "",
          f"Budget: {log.get('budget')}"]
    (run_dir / "REPORT.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
