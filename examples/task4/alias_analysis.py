import json
import sys
from cfg import *
from form_blocks import *
import copy


def alias_meet(lists):
    ans = {}
    for x in lists:
        for var, v in x.items():
            if var not in ans:
                ans[var] = v
            else:
                ans[var].union(v)
    return ans


def alias_f(instrs, in_dict):
    ans = copy.deepcopy(in_dict)
    for instr in instrs:
        if instr["op"] not in ["alloc", "id", "ptradd", "load"]:
            continue
        if instr["op"] == "alloc":
            ans[instr["dest"]] = set([id(instr)])
        elif instr["op"] == "id" or instr["op"] == "ptradd":
            if instr["args"][0] in ans:
                ans[instr["dest"]] = ans[instr["args"][0]]
            else:
                ans.pop(instr["dest"], None)
        elif instr["op"] == "load":
            ans.pop(instr["dest"], None)
    return ans


def check_alias(ans, x, y):
    if x not in ans or y not in ans:
        return True
    return len(ans[x].intersection(ans[y])) > 0


def alias_post(instrs, out_dict):
    ans = copy.deepcopy(out_dict)
    data = {}
    for instr in instrs:
        if instr["op"] not in ["store", "load", "alloc", "id", "ptradd"]:
            continue
        pending_del = []
        if instr["op"] in ["store", "load"]:
            for x in data:
                if check_alias(ans, instr["args"][0], x):
                    pending_del.append(x)
        if instr["op"] in ["alloc", "id", "ptradd"]:
            pending_del.append(instr["dest"])
        if instr["op"] == "store":
            if instr["args"][0] in data:
                data[instr["args"][0]]["op"] = "nop"
        elif instr["op"] == "load":
            if instr["args"][0] in data:
                instr["op"] = "id"
                instr["args"] = [data[instr["args"][0]]["args"][1]]
        for x in pending_del:
            data.pop(x, None)
        if instr["op"] == "store":
            data[instr["args"][0]] = instr
        # print(instr)
        # print(data)


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
            post_f(blocks[x], _out[x])


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        worklist(fn['instrs'], alias_meet, alias_f, True, alias_post)
    json.dump(prog, sys.stdout, indent=2)
