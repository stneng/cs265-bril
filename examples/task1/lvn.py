import json
import random
import sys


def lvn(instrs):
    val2num: dict = {}
    num2val: dict = {}
    var2num: dict = {}
    num2var: dict = {}
    cnt = 0

    for instr in instrs:
        # print(instr)
        if "dest" not in instr:
            continue
        if type(instr["type"]) is not str:
            continue

        if instr["op"] not in ["add", "mul", "sub", "div", "eq", "lt", "gt", "le", "ge", "not", "and", "or", "id"]:
            cnt += 1
            num = cnt
            # val2num[value] = num
            num2val[num] = None
        else:
            args = []
            if "args" in instr:
                for i, arg in enumerate(instr["args"]):
                    num = var2num.get(arg)
                    if num is None:
                        args.append(arg)
                    else:
                        if num2var[num][0] != arg:
                            instr["args"][i] = num2var[num][0]
                        args.append(f"#.{num}")
            if instr["op"] in ["add", "mul"]:
                args.sort()
            if instr["op"] == "const":
                value = "const "+str(instr["value"])
            else:
                value = instr["op"]+instr["type"]+str(args)
            # print(value)
            if instr["op"] == "id":
                num = var2num.get(instr["args"][0])
            else:
                num = val2num.get(value)
            # print(num)
            if num is None:
                cnt += 1
                num = cnt
                val2num[value] = num
                num2val[num] = value
            else:
                instr["op"] = "id"
                instr["args"] = [num2var[num][0]]
                instr.pop("funcs", None)

        if instr["dest"] in var2num:
            onum = var2num[instr["dest"]]
            num2var[onum].remove(instr["dest"])
            if len(num2var[onum]) == 0:
                oval = num2val[onum]
                if oval is not None:
                    val2num.pop(oval)
                num2val.pop(onum)
        var2num[instr["dest"]] = num
        if num not in num2var:
            num2var[num] = [instr["dest"]]
        else:
            num2var[num].append(instr["dest"])

    return instrs


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        ans = []
        basic_block = []
        for instr in fn["instrs"]:
            if "op" in instr:
                basic_block.append(instr)
                if instr["op"] in ["br", "jmp", "ret"]:
                    ans += lvn(basic_block)
                    basic_block = []
            else:
                ans += lvn(basic_block)
                basic_block = []
                ans.append(instr)
        ans += lvn(basic_block)
        fn["instrs"] = ans
    json.dump(prog, sys.stdout, indent=2)
