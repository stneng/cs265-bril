import json
import sys
from cfg import *
from form_blocks import *
import copy


def constant_meet(lists):
    ans = {}
    vars = set()
    for x in lists:
        vars = vars.union(set(x.keys()))
    vars = list(vars)
    for var in vars:
        meet = True
        for x in lists:
            if var not in x:
                meet = False
                break
            else:
                if x[var] != lists[0][var]:
                    meet = False
                    break
        if meet:
            ans[var] = lists[0][var]
    return ans


def constant_f(instrs, in_dict):
    ans = copy.deepcopy(in_dict)
    for instr in instrs:
        if instr["op"] not in ["const", "add", "mul", "sub", "div", "eq", "lt", "gt", "le", "ge", "not", "and", "or", "id"]:
            continue
        if instr["op"] == "const":
            ans[instr["dest"]] = instr["value"]
            continue
        folding = True
        for arg in instr["args"]:
            if arg not in ans:
                folding = False
                break
        if not folding:
            continue
        if instr["op"] == "add":
            ans[instr["dest"]] = ans[instr["args"][0]]+ans[instr["args"][1]]
        elif instr["op"] == "mul":
            ans[instr["dest"]] = ans[instr["args"][0]] * ans[instr["args"][1]]
        elif instr["op"] == "sub":
            ans[instr["dest"]] = ans[instr["args"][0]] - ans[instr["args"][1]]
        elif instr["op"] == "div":
            if ans[instr["args"][1]] == 0:
                continue
            ans[instr["dest"]] = ans[instr["args"][0]] // ans[instr["args"][1]]
        elif instr["op"] == "eq":
            ans[instr["dest"]] = ans[instr["args"][0]] == ans[instr["args"][1]]
            instr["type"] = "bool"
        elif instr["op"] == "lt":
            ans[instr["dest"]] = ans[instr["args"][0]] < ans[instr["args"][1]]
            instr["type"] = "bool"
        elif instr["op"] == "gt":
            ans[instr["dest"]] = ans[instr["args"][0]] > ans[instr["args"][1]]
            instr["type"] = "bool"
        elif instr["op"] == "le":
            ans[instr["dest"]] = ans[instr["args"][0]] <= ans[instr["args"][1]]
            instr["type"] = "bool"
        elif instr["op"] == "ge":
            ans[instr["dest"]] = ans[instr["args"][0]] >= ans[instr["args"][1]]
            instr["type"] = "bool"
        elif instr["op"] == "not":
            ans[instr["dest"]] = not ans[instr["args"][0]]
        elif instr["op"] == "and":
            ans[instr["dest"]] = ans[instr["args"][0]] and ans[instr["args"][1]]
        elif instr["op"] == "or":
            ans[instr["dest"]] = ans[instr["args"][0]] or ans[instr["args"][1]]
        elif instr["op"] == "id":
            ans[instr["dest"]] = ans[instr["args"][0]]
        instr["op"] = "const"
        instr["value"] = ans[instr["dest"]]
        instr.pop("args")
    return ans


def liveness_meet(lists):
    ans = {}
    for x in lists:
        ans.update(x)
    return ans


def liveness_f(instrs, out_dict):
    ans = copy.deepcopy(out_dict)
    for instr in reversed(instrs):
        if "dest" in instr:
            ans.pop(instr["dest"], None)
        for arg in instr.get("args", []):
            ans[arg] = True
    return ans


def liveness_dce(instrs, out_dict):
    ans = copy.deepcopy(out_dict)
    for instr in reversed(instrs):
        if "dest" in instr and instr["dest"] not in ans:
            instr["op"] = "nop"
            continue
        if "dest" in instr:
            ans.pop(instr["dest"], None)
        for arg in instr.get("args", []):
            ans[arg] = True


def worklist(instrs, meet, f, forward, post_f=None):
    blocks = block_map(form_blocks(instrs))
    add_terminators(blocks)
    if forward:
        preds, succs = edges(blocks)
    else:
        succs, preds = edges(blocks)

    _in = {}
    _out = {x: {} for x in blocks.keys()}
    worklist = set(blocks.keys())
    while len(worklist) > 0:
        x = worklist.pop()
        _in[x] = meet([_out[y] for y in preds[x]])
        out = f(blocks[x], _in[x])
        # print(x, _in[x], out)
        if out != _out[x]:
            _out[x] = out
            worklist = worklist.union(set(succs[x]))

    if post_f:
        for x in blocks.keys():
            post_f(blocks[x], _in[x])


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        worklist(fn['instrs'], constant_meet, constant_f, True)
        worklist(fn['instrs'], liveness_meet, liveness_f, False, liveness_dce)
    json.dump(prog, sys.stdout, indent=2)
