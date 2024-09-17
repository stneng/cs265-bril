import json
import sys


def ldce(instrs):
    unused = {}
    remove_list = set()
    for i, instr in enumerate(instrs):
        for arg in instr.get("args", []):
            unused.pop(arg, None)
        if "dest" in instr:
            if instr["dest"] in unused:
                remove_list.add(unused[instr["dest"]])
            unused[instr["dest"]] = i
    return [instr for i, instr in enumerate(instrs) if i not in remove_list]


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for _ in range(5):
        for fn in prog["functions"]:
            used = set()
            for instr in fn["instrs"]:
                used.update(instr.get("args", []))
            fn["instrs"] = [instr for instr in fn["instrs"] if not ("dest" in instr and instr["dest"] not in used and instr["op"] not in ["jmp", "br", "call", "ret", "print"])]

        for fn in prog["functions"]:
            ans = []
            basic_block = []
            for instr in fn["instrs"]:
                if "op" in instr:
                    basic_block.append(instr)
                    if instr["op"] in ["br", "jmp", "ret"]:
                        ans += ldce(basic_block)
                        basic_block = []
                else:
                    ans += ldce(basic_block)
                    basic_block = []
                    ans.append(instr)
            ans += ldce(basic_block)
            fn["instrs"] = ans

    json.dump(prog, sys.stdout, indent=2)
