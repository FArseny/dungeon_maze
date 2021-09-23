def getBitFence(fence):
        bf = []
        for row in fence:
            res = 0
            power = 1
            for val in reversed(row):
                res += power * val
                power *= 2
            bf.append(res)
        return bf


fsitw = 5
def getFenceByBits(bf):
    fence = []
    for row_v in bf:
        row = []
        bit_val = 1
        for bit in range(fsitw):
            res = 1 if bit_val & row_v > 0 else 0
            row.append(res)
            bit_val *= 2
        row.reverse()
        fence.append(row)
    return fence


fence = [[0, 0, 1, 1, 0], [1, 0, 1, 0, 0], [0, 0, 0, 0, 0]]
bf = getBitFence(fence)
nf = getFenceByBits(bf)
print(bf)
print(nf)
