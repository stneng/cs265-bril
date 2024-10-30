import json
import sys


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        pending_del = []
        for i, instr in enumerate(fn["instrs"]):
            if "op" not in instr:
                continue
            if instr["op"] == "nop":
                pending_del.append(i)
            elif instr["op"] == "ret" and ("args" not in instr or len(instr["args"]) == 0):
                pending_del.append(i)
            elif i < len(fn["instrs"])-1 and "label" in fn["instrs"][i+1] and instr["op"] == "jmp" and instr["labels"][0] == fn["instrs"][i+1]["label"]:
                pending_del.append(i)
        fn["instrs"] = [instr for i, instr in enumerate(fn["instrs"]) if i not in pending_del]

    json.dump(prog, sys.stdout, indent=2)
