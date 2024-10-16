import json
import sys
from cfg import *
from form_blocks import *
import copy


def remove_duplicates(lst):
    seen = []
    return [x for x in lst if not (x in seen or seen.append(x))]


def reassemble_preheaders(blocks, preheaders):
    instrs = []
    for name, block in blocks.items():
        if name in preheaders:
            instrs.append({'label': f"{name}_preheader"})
            instrs += preheaders[name]
        instrs.append({'label': name})
        instrs += block
    return instrs


def licm(instrs):
    blocks = block_map(form_blocks(instrs))
    add_entry(blocks)
    add_terminators(blocks)
    preds, succs = edges(blocks)

    dom = {x: set(blocks.keys()) for x in blocks.keys()}
    entry = list(blocks.keys())[0]
    dom[entry] = {entry}
    changed = True
    while changed:
        changed = False
        for block in blocks.keys():
            new_dom = set(blocks.keys())
            for pred in preds[block]:
                new_dom = new_dom.intersection(dom[pred])
            new_dom.add(block)
            if len(preds[block]) == 0:
                new_dom = {block}
            if new_dom != dom[block]:
                dom[block] = new_dom
                changed = True
    # print(dom)

    loops = []
    for block in blocks.keys():
        for succ in succs[block]:
            if succ in dom[block]:
                loop = {block, succ}
                worklist = [block]
                while worklist:
                    node = worklist.pop()
                    for pred in preds[node]:
                        if pred not in loop:
                            loop.add(pred)
                            worklist.append(pred)
                loops.append(loop)
    loops = remove_duplicates(loops)
    # print(loops)

    preheaders = {}
    for loop in loops:
        header = None
        for block in loop:
            if len(dom[block].intersection(loop)) == 1:
                if header is not None:
                    raise Exception("Multiple headers in loop")
                header = block
        exits = []
        for block in loop:
            for succ in succs[block]:
                if succ not in loop:
                    exits.append(succ)
        # print(header, exits)

        defs = set()
        redefs = set()
        for block in loop:
            for instr in blocks[block]:
                if "dest" in instr:
                    if instr["dest"] in defs:
                        redefs.add(instr["dest"])
                    defs.add(instr["dest"])

        invariant_instrs = []
        for _ in range(4):
            for block in loop:
                flag = True
                for exit_block in exits:
                    if block not in dom[exit_block]:
                        flag = False
                        break
                if not flag:
                    continue

                for instr in blocks[block]:
                    if instr in invariant_instrs:
                        continue
                    if instr["op"] not in ["const", "add", "mul", "sub", "div", "eq", "lt", "gt", "le", "ge", "not", "and", "or", "id"]:
                        continue
                    if instr["dest"] in redefs:
                        continue
                    if instr["op"] == "const":
                        invariant_instrs.append(instr)
                        if instr["dest"] not in redefs:
                            defs.remove(instr["dest"])
                        continue
                    args = instr.get("args", [])
                    if all(arg not in defs for arg in args):
                        invariant_instrs.append(instr)
                        if instr["dest"] not in redefs:
                            defs.remove(instr["dest"])
                        continue
        # print(invariant_instrs)
        if len(invariant_instrs) == 0:
            continue

        preheader = []
        for instr in invariant_instrs:
            preheader.append(copy.deepcopy(instr))
            instr["op"] = "nop"
        preheaders[header] = preheader
        for pred in preds[header]:
            if pred in loop:
                continue
            for instr in blocks[pred]:
                if instr["op"] == "jmp":
                    instr["labels"][0] = f"{header}_preheader"
                if instr["op"] == "br":
                    if instr["labels"][0] == header:
                        instr["labels"][0] = f"{header}_preheader"
                    if instr["labels"][1] == header:
                        instr["labels"][1] = f"{header}_preheader"

    return reassemble_preheaders(blocks, preheaders)


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        fn['instrs'] = licm(fn['instrs'])
    json.dump(prog, sys.stdout, indent=2)
